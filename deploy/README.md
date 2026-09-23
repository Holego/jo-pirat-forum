# Running the forum on a phone, over Tor

One-time setup in [Termux](https://f-droid.org/packages/com.termux/) (install from
F-Droid, not Play Store — the Play Store build is outdated):

```bash
pkg update
pkg install git python tor clang libjpeg-turbo zlib
termux-setup-storage   # optional, only if you want access to phone storage
git clone https://github.com/Holego/jo-pirat-forum.git
cd jo-pirat-forum
bash deploy/run_forum.sh
```

The script installs Python deps, sets up the Tor hidden service (first run
only — it appends `deploy/torrc.forum` to Termux's `torrc`), runs migrations,
collects static files, and starts the site with gunicorn. At the end it
prints your `.onion` address — that address stays the same across restarts
as long as you don't delete `~/tor-forum`, so bookmark it once.

## Updating the site

1. On your PC: commit and `git push` as usual.
2. On the phone: `bash deploy/run_forum.sh` again.

That's the whole update flow — it pulls the new code, re-installs any
changed dependencies, re-runs migrations, and restarts gunicorn so the new
code takes effect. Nothing needs to be redone on the Tor side.

## Keeping it actually running

Android kills background processes aggressively, so for something close to
"always on":

- Disable battery optimization for Termux (Android Settings → Apps → Termux
  → Battery → Unrestricted).
- Keep the phone charging if it's going to sit as a "server".
- Set up autostart on boot (below) so a reboot doesn't take the site down
  for good.

### Autostart on boot

1. Install **Termux:Boot** from F-Droid — it's a separate app, same
   publisher as Termux: https://f-droid.org/packages/com.termux.boot/
2. Open Termux:Boot once (just launch it, no setup screen — this is what
   makes Android register its boot receiver).
3. Link the boot script in:
   ```bash
   mkdir -p ~/.termux/boot
   ln -s ~/jo-pirat-forum/deploy/termux_boot.sh ~/.termux/boot/start-forum.sh
   chmod +x ~/.termux/boot/start-forum.sh
   ```
   (adjust `~/jo-pirat-forum` if you cloned the repo somewhere else).

From then on, every reboot runs `deploy/termux_boot.sh`, which takes a
wake-lock and calls `deploy/run_forum.sh` — same update-and-start logic as
running it by hand, logged to `~/.jo-pirat-forum/boot.log`.

## Checking it's alive

```bash
tail -f ~/.jo-pirat-forum/gunicorn.log
cat ~/tor-forum/hostname
```

## Notes

- `DJANGO_ALLOWED_HOSTS` defaults to `*` here since the only way in is via
  the `.onion` address anyway. Override it by exporting the env var before
  running the script if you want to lock it down further.
- The Django secret key is generated once into
  `~/.jo-pirat-forum/secret_key` (outside the git checkout) and reused on
  every subsequent run/update.
- A `.onion` address only opens in Tor Browser — fine for personal use or
  sharing with people who have Tor, not a substitute for a normal portfolio
  link.
- `seed_forum` no longer sets a default password on the `admin` account.
  Before exposing the site, set one with `python manage.py changepassword
  admin`, or export `DJANGO_ADMIN_PASSWORD=<something-strong>` before
  running `seed_forum` for the first time.
