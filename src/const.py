"""const.py
定数モジュール
"""

APP_WIDTH = 256
APP_HEIGHT = 256
APP_FPS = 30

APP_TITLE = "PachiPon"
APP_VERSION = "0.0.1"

ENCOUNT_THRESHOLD = 11  # エンカウント率の閾値（3d6の期待値）
ENEMY_ID_BASE = 10  # エネミーのIDは10～の連番

BATTLE_MESSAGE_FRAME = APP_FPS  # バトルメッセージの表示間隔

UPPER_INT_TABLE = str.maketrans("0123456789", "０１２３４５６７８９")
