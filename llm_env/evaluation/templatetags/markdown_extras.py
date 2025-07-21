# evaluation/templatetags/markdown_extras.py

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
import markdown

register = template.Library()

@register.filter(name='convert_markdown')
@stringfilter
def convert_markdown(value):
    """
    마크다운 텍스트를 HTML로 변환합니다.
    """
    return mark_safe(markdown.markdown(value, extensions=['nl2br', 'fenced_code']))