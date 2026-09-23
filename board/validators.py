import os

from django.core.exceptions import ValidationError

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_AUDIO_BYTES = 15 * 1024 * 1024

ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.ogg', '.oga', '.wav', '.m4a', '.flac'}


def validate_image_size(file):
    if file.size > MAX_IMAGE_BYTES:
        raise ValidationError(f'Файл слишком большой (макс. {MAX_IMAGE_BYTES // (1024 * 1024)} МБ).')


def validate_audio_file(file):
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise ValidationError(
            f'Недопустимый формат «{ext or "без расширения"}». '
            f'Разрешены: {", ".join(sorted(ALLOWED_AUDIO_EXTENSIONS))}.'
        )
    if file.size > MAX_AUDIO_BYTES:
        raise ValidationError(f'Файл слишком большой (макс. {MAX_AUDIO_BYTES // (1024 * 1024)} МБ).')
