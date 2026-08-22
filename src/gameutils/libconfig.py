"""
gameutilsライブラリ群で利用する設定を纏めたクラス
"""

from enum import StrEnum


class ResourcePath(StrEnum):
    """
    gameutilsライブラリで使用するリソース類のパス定義
    アプリケーションの構成で必要に応じて編集可能
    """

    WINDOW_CHIP = "gameutils/lib/window/chip_window.bmp"
    MENU_STRUCTURE = "assets/data/menu_structure.json"

    # FONT_BASIC  = "gameutils/base/text/k8x12S.bdf"
    # FONT_LARGE  = "gameutils/base/text/umplus_j10r.bdf"
    FONT_BASIC = "assets/font/k8x12S.bdf"
    # FONT_LARGE = "assets/font/umplus_j10r.bdf"
    # FONT_BASIC = "assets/font/umplus_j10r.bdf"
    FONT_LARGE = "assets/font/umplus_j12r.bdf"

    # SCRIPT_PATH = "gameutils/lib/event/script/"
    SCRIPT_PATH = "assets/script"

    # CONFIG_KEYS = "gameutils/base/input/keyconfig.json"
    CONFIG_KEYS = "keyconfig.json"

    # MUSIC_LIST  = "gameutils/lib/sound/musiclist.json"
    SCORE_LIST = "assets/sound/scorelist.json"
