"""const.py
定数モジュール
"""

APP_WIDTH = 256
APP_HEIGHT = 256
APP_FPS = 30

APP_TITLE = "PachiPon"
APP_VERSION = "0.0.1"

# フィールド上のメッセージウインドウ高さ
FIELD_MESSAGE_HEIGHT = 56

ENCOUNT_THRESHOLD = 12  # エンカウント率の閾値（3d6の期待値）
ENEMY_ID_BASE = 10  # エネミーのIDは10～の連番

COMMAND_STEPWAIT_FRAME = APP_FPS  # コマンドマネージャの処理待ち間隔（メッセージ表示等）
DICEROLL_FRAME = int(APP_FPS * 0.6)  # ダイスロールの表示フレーム数
