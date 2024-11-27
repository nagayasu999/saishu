from django import template

register = template.Library()

from django import template

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    辞書から指定されたキーの値を取得する。
    辞書ではない場合やキーが存在しない場合は空文字を返す。
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, "")
    return ""
