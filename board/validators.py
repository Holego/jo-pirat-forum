from django.core.exceptions import ValidationError

MAX_IMAGE_BYTES = 5 * 1024 * 1024


def validate_image_size(file):
    if file.size > MAX_IMAGE_BYTES:
        raise ValidationError(f'Файл слишком большой (макс. {MAX_IMAGE_BYTES // (1024 * 1024)} МБ).')
