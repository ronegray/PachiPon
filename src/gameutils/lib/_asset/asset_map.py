"""asset_map.py
- アセットファイル群のベースパス定義
- アセットファイルと紐づけるアセットIDの列挙
"""
from enum import IntEnum, auto


# アセットパス設定
ASSETS_PATH = "assets"


class AssetID(IntEnum):
    PYXRES = auto()
    SYSCONFIG = auto()
    KEYCONFIG = auto()
    # WINDOW_CHIP = auto()
    # FONT_BASIC = auto()
    # FONT_LARGE = auto()
    # SCRIPT_PATH = auto()
    IMAGE_CHARA = auto()
    IMAGE_SPLASH = auto()
    IMAGE_TITLE = auto()
    IMAGE_MAP = auto()
    DATA_ITEM = auto()
