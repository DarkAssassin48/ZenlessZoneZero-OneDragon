import gettext
import json
import locale
import os

from one_dragon.utils import os_utils

_gt = {}
_default_lang = 'zh'


class JsonTranslations:
    """Minimal gettext-compatible translation backed by a UTF-8 JSON file."""

    def __init__(self, catalog: dict[str, str]):
        self._catalog = catalog

    def gettext(self, message: str) -> str:
        return self._catalog.get(message, message)


def detect_language():
    """自动检测系统语言"""
    try:
        locale_names = []

        current_locale = locale.getlocale()[0]
        if current_locale:
            locale_names.append(current_locale)

        # getdefaultlocale is deprecated but still useful on older Windows
        # installations where getlocale may return an empty value.
        get_default_locale = getattr(locale, 'getdefaultlocale', None)
        if callable(get_default_locale):
            default_locale = get_default_locale()[0]
            if default_locale:
                locale_names.append(default_locale)

        for locale_name in locale_names:
            normalized = locale_name.lower().replace('-', '_')
            if normalized.startswith('zh'):
                return 'zh'
            if normalized.startswith('ru') or normalized.startswith('russian'):
                return 'ru'

        return 'en'
    except Exception:
        return 'en'


def detect_and_set_default_language():
    """
    检测系统语言并设置为默认语言
    :return:
    """
    return update_default_lang(detect_language())


def get_translations(model: str, lang: str):
    """
    加载语言
    :param model: 模块 将ocr 界面 日志等翻译区分开来
    :param lang: 语言
    :return:
    """
    translate_path = os_utils.get_resource_path('assets', 'text', 'output')
    lang_dir = os.path.join(translate_path, lang, 'LC_MESSAGES', f'{model}.mo')
    if os.path.exists(lang_dir):
        gettext.bindtextdomain(model, translate_path)
        translation = gettext.translation(model, localedir=translate_path, languages=[lang])
        # 注册翻译函数为全局函数
        translation.install()
        return translation

    # Text-only fallback used by community forks and development builds.
    # Release builds may still ship the usual compiled MO catalog.
    json_path = os.path.join(translate_path, lang, 'LC_MESSAGES', f'{model}.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as file:
                catalog = json.load(file)
            if isinstance(catalog, dict):
                return JsonTranslations({str(key): str(value) for key, value in catalog.items()})
        except (OSError, ValueError, TypeError):
            pass

    # Large community catalogs can be split into multiple UTF-8 JSON files.
    # This keeps the repository text-only while avoiding oversized individual
    # files. Files are merged in lexical order; later shards override earlier
    # values, which allows small correction shards to be added safely.
    json_dir = os.path.join(translate_path, lang, 'LC_MESSAGES', model)
    if os.path.isdir(json_dir):
        merged_catalog: dict[str, str] = {}
        try:
            for file_name in sorted(os.listdir(json_dir)):
                if not file_name.lower().endswith('.json'):
                    continue
                file_path = os.path.join(json_dir, file_name)
                with open(file_path, 'r', encoding='utf-8') as file:
                    shard = json.load(file)
                if isinstance(shard, dict):
                    merged_catalog.update({str(key): str(value) for key, value in shard.items()})
        except (OSError, ValueError, TypeError):
            return None
        if merged_catalog:
            return JsonTranslations(merged_catalog)

    return None


def gt(msg: str | None, model: str = 'ui', lang: str | None = None) -> str:
    if msg is None or len(msg) == 0:
        return ''
    if lang is None:
        lang = _default_lang
    if model not in _gt:
        _gt[model] = {}
    if lang not in _gt[model]:
        _gt[model][lang] = get_translations(model, lang)

    trans = _gt[model][lang]
    return trans.gettext(msg) if trans is not None else msg


def coalesce_gt(msg: str | None, default: str, model: str = 'ui', lang: str | None = None) -> str:
    """
    带有默认值的获取多语言
    :param msg: 原字符串
    :param default: 默认值
    :param model:
    :param lang:
    :return:
    """
    if lang is None:
        lang = _default_lang
    return gt(msg if msg is not None else default, model, lang)


def update_default_lang(lang: str):
    global _default_lang
    _default_lang = lang


def get_default_lang() -> str:
    """
    获取默认语言
    :return:
    """
    global _default_lang
    return _default_lang
