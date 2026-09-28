from django import template

from board.embeds import extract_embeds

register = template.Library()


@register.filter
def media_embeds(text):
    return extract_embeds(text)
