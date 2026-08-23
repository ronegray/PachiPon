from dataclasses import dataclass
import pyxel as px

# キー割り当て画面でのコードと表示名の対比
KEYNAME_MAP: dict = {
    px.KEY_ESCAPE: "ＥＳＣ",
    px.KEY_F1: "Ｆ１",
    px.KEY_F2: "Ｆ２",
    px.KEY_F3: "Ｆ３",
    px.KEY_F4: "Ｆ４",
    px.KEY_F5: "Ｆ５",
    px.KEY_F6: "Ｆ６",
    px.KEY_F7: "Ｆ７",
    px.KEY_F8: "Ｆ８",
    px.KEY_F9: "Ｆ９",
    px.KEY_F10: "Ｆ１０",
    px.KEY_F11: "Ｆ１１",
    px.KEY_F12: "Ｆ１２",
    px.KEY_1: "１",
    px.KEY_2: "２",
    px.KEY_3: "３",
    px.KEY_4: "４",
    px.KEY_5: "５",
    px.KEY_6: "６",
    px.KEY_7: "７",
    px.KEY_8: "８",
    px.KEY_9: "９",
    px.KEY_0: "０",
    px.KEY_MINUS: "ー",
    px.KEY_CARET: "＾",
    px.KEY_BACKSPACE: "BS←",
    px.KEY_INSERT: "ＩＮＳ",
    px.KEY_HOME: "ＨＯＭＥ",
    px.KEY_PAGEUP: "PageUp",
    px.KEY_TAB: "ＴＡＢ",
    px.KEY_Q: "Ｑ",
    px.KEY_W: "Ｗ",
    px.KEY_E: "Ｅ",
    px.KEY_R: "Ｒ",
    px.KEY_T: "Ｔ",
    px.KEY_Y: "Ｙ",
    px.KEY_U: "Ｕ",
    px.KEY_I: "Ｉ",
    px.KEY_O: "Ｏ",
    px.KEY_P: "Ｐ",
    px.KEY_AT: "＠",
    px.KEY_LEFTBRACKET: "［",
    px.KEY_RETURN: "Return",
    px.KEY_DELETE: "ＤＥＬ",
    px.KEY_END: "ＥＮＤ",
    px.KEY_PAGEDOWN: "PageDown",
    px.KEY_CAPSLOCK: "ＣＡＰＳ",
    px.KEY_A: "Ａ",
    px.KEY_S: "Ｓ",
    px.KEY_D: "Ｄ",
    px.KEY_F: "Ｆ",
    px.KEY_G: "Ｇ",
    px.KEY_H: "Ｈ",
    px.KEY_J: "Ｊ",
    px.KEY_K: "Ｋ",
    px.KEY_L: "Ｌ",
    px.KEY_SEMICOLON: "；",
    px.KEY_COLON: "：",
    px.KEY_RIGHTBRACKET: "］",
    px.KEY_LSHIFT: "L:SHIFT",
    px.KEY_Z: "Ｚ",
    px.KEY_X: "Ｘ",
    px.KEY_C: "Ｃ",
    px.KEY_V: "Ｖ",
    px.KEY_B: "Ｂ",
    px.KEY_N: "Ｎ",
    px.KEY_M: "Ｍ",
    px.KEY_COMMA: "，",
    px.KEY_PERIOD: "．",
    px.KEY_SLASH: "／",
    px.KEY_BACKSLASH: "￥",
    px.KEY_RSHIFT: "R:SHIFT",
    px.KEY_UP: "↑",
    px.KEY_LCTRL: "L:CTRL",
    px.KEY_LALT: "L:ALT",
    px.KEY_SPACE: "SPACE",
    px.KEY_RALT: "R:ALT",
    px.KEY_MENU: "ＭＥＮＵ",
    px.KEY_RCTRL: "R:CTRL",
    px.KEY_LEFT: "←",
    px.KEY_DOWN: "↓",
    px.KEY_RIGHT: "→",
    px.KEY_KP_DIVIDE: "KP／",
    px.KEY_KP_MULTIPLY: "KP＊",
    px.KEY_KP_MINUS: "KP－",
    px.KEY_KP_7: "KP７",
    px.KEY_KP_8: "KP８",
    px.KEY_KP_9: "KP９",
    px.KEY_KP_PLUS: "KP＋",
    px.KEY_KP_4: "KP４",
    px.KEY_KP_5: "KP５",
    px.KEY_KP_6: "KP６",
    px.KEY_KP_1: "KP１",
    px.KEY_KP_2: "KP２",
    px.KEY_KP_3: "KP３",
    px.KEY_KP_ENTER: "KPEnter",
    px.KEY_KP_0: "KP０",
    px.KEY_KP_PERIOD: "KP．",
    px.GAMEPAD1_BUTTON_A: "Ａ",
    px.GAMEPAD1_BUTTON_B: "Ｂ",
    px.GAMEPAD1_BUTTON_X: "Ｘ",
    px.GAMEPAD1_BUTTON_Y: "Ｙ",
    px.GAMEPAD1_BUTTON_START: "Start",
    px.GAMEPAD1_BUTTON_BACK: "Back",
    px.GAMEPAD1_BUTTON_LEFTSHOULDER: "L:Sholdr",
    px.GAMEPAD1_BUTTON_RIGHTSHOULDER: "R:Sholdr",
}
# menu_structure.jsonから移植
# "MenuVolume": [
#     [{"label": "5", "action": "none", "args": ["最大",1]}],
#     [{"label": "4", "action": "none", "args": ["大きめ", 0.5]}],
#     [{"label": "3", "action": "none", "args": ["標準", 0.25]}],
#     [{"label": "2", "action": "none", "args": ["小さめ", 0.125]}],
#     [{"label": "1", "action": "none", "args": ["極小", 0.0625]}],
#     [{"label": "0", "action": "none", "args": ["無音", 0.0]}]
# ],
# "MenuDispSize": [
#     [{"label": "5", "action": "none", "args": ["最大",7]}],
#     [{"label": "4", "action": "none", "args": ["大きめ", 5]}],
#     [{"label": "3", "action": "none", "args": ["標準", 3]}],
#     [{"label": "2", "action": "none", "args": ["小さめ", 2]}],
#     [{"label": "1", "action": "none", "args": ["極小", 1]}]
# ],
# "MenuTextSpeed": [
#     [{"label": "4", "action": "none", "args": ["キー待ち", 0]}],
#     [{"label": "3", "action": "none", "args": ["遅め", 0.5]}],
#     [{"label": "2", "action": "none", "args": ["標準", 1]}],
#     [{"label": "1", "action": "none", "args": ["速め", 4]}],
#     [{"label": "0", "action": "none", "args": ["待ち無し", 9]}]
# ],
CONF_VOLUME: dict = {
    # 5: {"label": "最大", "action": "none", "args": [5,1]},
    # 4: {"label": "大きめ", "action": "none", "args": [4, 0.5]},
    # 3: {"label": "標準", "action": "none", "args": [3, 0.25]},
    # 2: {"label": "小さめ", "action": "none", "args": [2, 0.125]},
    # 1: {"label": "極小", "action": "none", "args": [1, 0.0625]},
    # 0: {"label": "無音", "action": "none", "args": [0, 0.0]},
    5: {"label": "最大", "action": "none", "args": [5, 1]},
    4: {"label": "大きめ", "action": "none", "args": [4, 0.825]},
    3: {"label": "標準", "action": "none", "args": [3, 0.66]},
    2: {"label": "小さめ", "action": "none", "args": [2, 0.4]},
    1: {"label": "極小", "action": "none", "args": [1, 0.2]},
    0: {"label": "無音", "action": "none", "args": [0, 0.0]},
}


CONF_DISP_SIZE: dict = {
    5: {"label": "最大（１７９２ｐｘ）", "action": "none", "args": [5, 7]},
    4: {"label": " 大 （１２８０ｐｘ）", "action": "none", "args": [4, 5]},
    3: {"label": "標準（　７６８ｐｘ）", "action": "none", "args": [3, 3]},
    2: {"label": " 小 （　５１２ｐｘ）", "action": "none", "args": [2, 2]},
    1: {"label": "極小（　２５６ｐｘ）", "action": "none", "args": [1, 1]},
}


CONF_TEXT_SPEED: dict = {
    4: {"label": "キー待ち", "action": "none", "args": [4, 0]},
    3: {"label": "遅め", "action": "none", "args": [3, 0.5]},
    2: {"label": "標準", "action": "none", "args": [2, 1]},
    1: {"label": "速め", "action": "none", "args": [1, 4]},
    0: {"label": "待ち無し", "action": "none", "args": [0, 9]},
}


ASSIGNABLE_KEY_ACTIONS = {
    "decide": "決定／イベント開始",
    "cancel": "取消／ウインドウ消去",
    "menu": "メニュー表示",
}


KEYCODE_UNASSIGNABLE = [
    px.GAMEPAD1_BUTTON_DPAD_UP,
    px.GAMEPAD1_BUTTON_DPAD_DOWN,
    px.GAMEPAD1_BUTTON_DPAD_LEFT,
    px.GAMEPAD1_BUTTON_DPAD_RIGHT,
    px.GAMEPAD1_AXIS_LEFTX,
    px.GAMEPAD1_AXIS_LEFTY,
    px.GAMEPAD1_AXIS_RIGHTX,
    px.GAMEPAD1_AXIS_RIGHTY,
    px.KEY_UP,
    px.KEY_DOWN,
    px.KEY_LEFT,
    px.KEY_RIGHT,
    px.KEY_W,
    px.KEY_A,
    px.KEY_S,
    px.KEY_D,
]


@dataclass
class ApplicationConfig:
    vol_bgm: int = 3
    vol_se: int = 3
    display_size: int = 3
    is_fullscreen: bool = False
    text_speed: int = 2
    is_memory_cursor: bool = False
    is_cutin_dice: bool = True
