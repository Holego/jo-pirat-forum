# Jo Pirat Forum

A small Django forum for developers — post your projects, ask questions,
discuss code and hang out in the off-topic/flood section. Styled after
classic phpBB-style forums.

Небольшой форум на Django для разработчиков — выкладывай свои проекты,
задавай вопросы, обсуждай код и флуди в оффтопе. Стилизован под
классические phpBB-форумы.

## Возможности

- Категории → темы → сообщения, отдельный раздел «Флуд»
- Регистрация и вход
- Профиль: аватар, описание, ссылки (сайт, GitHub), статус (новичок / участник / ветеран / модератор)
- Создание тем с необязательной ссылкой на проект (GitHub и т.п.)
- Прикрепление картинок к сообщениям и темам
- Бан пользователей из админки
- Админка Django для модерации

## Запуск локально

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_forum   # создаёт стартовые категории и пользователя admin/admin
python manage.py runserver
```

Форум будет доступен на http://127.0.0.1:8000/

## Стек

- Python / Django
- SQLite (по умолчанию)
- Pillow (обработка изображений)
- Ванильный HTML/CSS без фронтенд-фреймворков

## Планы

- Личные сообщения
- Разметка Markdown в сообщениях
- Поиск по форуму
- Автоматическое присвоение статуса по количеству сообщений
