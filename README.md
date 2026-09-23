# Jo Pirat Forum

A small Django forum for developers — post your projects, ask questions,
discuss code and hang out in the off-topic/flood section. Styled after
classic phpBB-style forums.

A small Django forum for developers - post your projects,
Ask questions, discuss code, and spam in the off-topic. Styled as
classic phpBB forums.

## Features

- Categories → topics → posts; dedicated "Flood" section
- Registration and login
- Profile: avatar, description, links (website, GitHub), status (Newbie / Member / Veteran / Moderator)
- Topic creation with optional project link (GitHub, etc.)
- Image attachments for posts and topics
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

## Stack

- Python / Django
- SQLite (default)
- Pillow (image processing)
- Vanilla HTML/CSS without front-end frameworks
## Plans

- Personal messages
- Markdown in messages
- Search the forum
- Automatic assignment of status based on the number of messages
