import json
from pathlib import Path

from one_dragon.utils import i18_utils


def test_detect_russian_locale(monkeypatch):
    monkeypatch.setattr(i18_utils.locale, 'getlocale', lambda: ('ru_RU', 'UTF-8'))
    assert i18_utils.detect_language() == 'ru'


def test_load_sharded_json_catalog(monkeypatch, tmp_path: Path):
    output_dir = tmp_path / 'assets' / 'text' / 'output'
    catalog_dir = output_dir / 'ru' / 'LC_MESSAGES' / 'ui'
    catalog_dir.mkdir(parents=True)

    (catalog_dir / '00-base.json').write_text(
        json.dumps({'游戏设置': 'Настройки игры'}, ensure_ascii=False),
        encoding='utf-8',
    )
    (catalog_dir / '99-corrections.json').write_text(
        json.dumps({'游戏设置': 'Параметры игры'}, ensure_ascii=False),
        encoding='utf-8',
    )

    monkeypatch.setattr(
        i18_utils.os_utils,
        'get_resource_path',
        lambda *parts: str(output_dir),
    )
    i18_utils._gt.clear()

    assert i18_utils.gt('游戏设置', lang='ru') == 'Параметры игры'
    assert i18_utils.gt('unknown', lang='ru') == 'unknown'
