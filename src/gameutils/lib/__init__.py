"""gameutils.libパッケージ
ゲーム開発で使用頻度の高い機能をまとめたパッケージ
"""

# from .event import EventControl, EventManager
from .sound import (
    SoundManager,
)  # init, play_bgm, play_se, stop, load_bgm, fadeout, fadein
from .window import (
    WINDOW_MODE,
    MENU_WINDOW_TYPE,
    WindowAction,
    WindowManager,
    Window,
    Menu,
    MenuItem,
    ExecResult,
    RsltPush,
    RsltPop,
    RsltDiscard,
    RsltContinue,
    RsltReplace,
    WindowInputHandler,
)
