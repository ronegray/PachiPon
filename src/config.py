from dataclasses import dataclass

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


@dataclass
class ApplicationConfig:
    vol_bgm: int = 3
    vol_se: int = 3
    display_size: int = 3
    is_fullscreen: bool = False
    text_speed: int = 2
    is_memory_cursor: bool = False
    is_cutin_dice: bool = True
