# Jo Pirat Forum

A small Django forum for developers — post your projects, ask questions,
discuss code and hang out in the off-topic/flood section. Styled after
classic phpBB-style forums.

A small Django forum for developers - post your projects,
Ask questions, discuss code, and spam in the off-topic. Styled as
classic phpBB forums.
You can visit my Tor site here: zd6yotzjhndh5u26oc6ya6ygw4nrmtruyezxbfeyvkbqdgc63qnfugid.onion

## Features

- Categories → topics → posts; dedicated "Flood" section
- Registration and login
- Profile: avatar, description, links (website, GitHub), status (Newbie / Member / Veteran / Moderator)
- Topic creation with optional project link (GitHub, etc.)
- Direct links to images / GIFs / video / audio in posts and private messages are shown
  right under the message (nothing is stored on the server)
- Optional file attachments for posts (off by default, `FORUM_ALLOW_UPLOADS=True` to enable)
- Phone-friendly layout
- JSON API for native/mobile clients (see below)
- User banning via the admin panel
- Django admin interface for moderation

## Run locally
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_forum   # creates the admin account (no password set — see below)
python manage.py changepassword admin   # set a real password before exposing the site
python manage.py runserver
```

The forum will be available on http://127.0.0.1:8000/

## API

A JSON API (Django REST Framework) lives under `/api/` for native clients such as
[tor-forum-client](https://github.com/Holego/tor-forum-client). Authenticate with
`Authorization: Token <key>` from the login/register endpoints.

| Method | Endpoint | |
|---|---|---|
| GET | `/api/` | API name/version — lets a client detect the forum speaks it |
| POST | `/api/auth/login/`, `/api/auth/register/` | `{username, password}` → `{token, user}` |
| POST | `/api/auth/logout/` | revoke the token |
| GET | `/api/me/` | current user + unread message count |
| GET | `/api/categories/` | categories with topic/post counts |
| GET, POST | `/api/categories/<slug>/topics/` | topics (pinned first, then latest activity); POST `{title, body}` starts one |
| GET | `/api/topics/<id>/` | topic |
| GET, POST | `/api/topics/<id>/posts/` | posts with `embeds` (linked images/GIFs/video/audio); `?page=last`; POST `{body}` replies |
| GET | `/api/messages/` | conversations |
| GET, POST | `/api/messages/<username>/` | conversation thread (marks it read); POST `{body}` sends |

Categories and topic lists are public; reading topics and everything else needs an account,
same as the website. Login/registration are rate-limited.

## Stack

- Python / Django, Django REST Framework
- SQLite (default)
- Pillow (image processing)
- Vanilla HTML/CSS without front-end frameworks
## Plans

- Personal messages
- Markdown in messages
- Search the forum
- Automatic assignment of status based on the number of messages
