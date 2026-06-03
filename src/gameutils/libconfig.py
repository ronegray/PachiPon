"""libconfig.py
gameutilsライブラリで使用するリソースファイルのパス定義
"""
from enum import StrEnum


class ResourcePath(StrEnum):
    WINDOW_CHIP = "gameutils/lib/window/chip_window.bmp"

    # FONT_BASIC  = "gameutils/base/text/k8x12S.bdf"
    # FONT_LARGE  = "gameutils/base/text/umplus_j10r.bdf"
    FONT_BASIC = "assets/font/k8x12S.bdf"
    FONT_LARGE = "assets/font/umplus_j10r.bdf"

    # SCRIPT_PATH = "gameutils/lib/event/script/"
    SCRIPT_PATH = "assets/script"

    # CONFIG_KEYS = "gameutils/base/input/keyconfig.json"
    CONFIG_KEYS = "keyconfig.json"

    # MUSIC_LIST  = "gameutils/lib/sound/musiclist.json"
    MUSIC_LIST = "assets/sound/musiclist.json"
