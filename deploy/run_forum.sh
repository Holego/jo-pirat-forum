#!/data/data/com.termux/files/usr/bin/bash
# Start-or-update utility for running jo-pirat-forum over Tor on a phone (Termux).
#
# First run:  one-time `pkg install` steps from deploy/README.md, then just run this.
# Every later "update the site": git push from your PC, then re-run this script on
# the phone — it pulls, migrates, collects static, and restarts the server.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

DATA_DIR="$HOME/.jo-pirat-forum"
mkdir -p "$DATA_DIR"
SECRET_FILE="$DATA_DIR/secret_key"
PIDFILE="$DATA_DIR/gunicorn.pid"
LOGFILE="$DATA_DIR/gunicorn.log"

echo "==> Pulling latest code"
if [ -d .git ]; then
    git pull --ff-only
else
    echo "    not a git checkout, skipping"
fi

echo "==> Installing/updating dependencies"
pip install -q -r requirements.txt

echo "==> Preparing secret key"
if [ ! -f "$SECRET_FILE" ]; then
    python -c "import secrets; print(secrets.token_urlsafe(50))" > "$SECRET_FILE"
    chmod 600 "$SECRET_FILE"
fi
export DJANGO_SECRET_KEY="$(cat "$SECRET_FILE")"
export DJANGO_DEBUG="${DJANGO_DEBUG:-False}"
export DJANGO_ALLOWED_HOSTS="${DJANGO_ALLOWED_HOSTS:-*}"

echo "==> Applying migrations"
python manage.py migrate --noinput

echo "==> Seeding starter categories (safe to re-run)"
python manage.py seed_forum

echo "==> Collecting static files"
python manage.py collectstatic --noinput >/dev/null

echo "==> Making sure Tor hidden service config is in place"
TORRC="$PREFIX/etc/tor/torrc"
if ! grep -q "jo-pirat-forum" "$TORRC" 2>/dev/null; then
    cat deploy/torrc.forum >> "$TORRC"
    echo "    appended hidden service block to $TORRC"
fi

echo "==> Making sure Tor is running"
tor --RunAsDaemon 1 >/dev/null 2>&1 || true
sleep 2

ONION_FILE="$HOME/tor-forum/hostname"
if [ -f "$ONION_FILE" ]; then
    echo "==> Onion address: $(cat "$ONION_FILE")"
else
    echo "==> Onion address not generated yet — run this script again in a few seconds"
fi

echo "==> Restarting forum server"
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    kill "$(cat "$PIDFILE")"
    sleep 1
fi
nohup gunicorn core.wsgi:application --bind 127.0.0.1:8000 --workers 2 \
    > "$LOGFILE" 2>&1 &
echo $! > "$PIDFILE"
disown

NEEDS_PASSWORD="$(python manage.py shell -c "
from django.contrib.auth import get_user_model
u = get_user_model().objects.filter(username='admin').first()
print('yes' if u and not u.has_usable_password() else 'no')
" 2>/dev/null | tail -1)"
if [ "$NEEDS_PASSWORD" = "yes" ]; then
    echo "==> !!! admin account has NO password set — run: python manage.py changepassword admin"
fi

echo "==> Done. Logs: $LOGFILE"
