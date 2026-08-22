"""
入力ライブラリ用インタフェース定義
"""

from typing import Literal, get_args, Protocol  # , Callable


# 型指定
INPUT_MODE = Literal["once", "keep", "hold"]
TARGET_DEVICE = Literal["pad", "kbd"]
ACTION_NAME = Literal[
    "up",
    "down",
    "left",
    "right",
    "decide",
    "cancel",
    "action",
    "menu",
    "start",
    "select",
    "LS",
    "RS",
]


def is_action_name(action_name: str) -> bool:
    return action_name in get_args(ACTION_NAME)


# type InputHandler = Callable[[INPUT_MODE], bool]
class InputHandler(Protocol):
    """アクションに対する入力判定関数の型

    mode引数はデフォルト値("once")を持つため、呼び出し側は省略可能。
    Callable[[INPUT_MODE], bool] ではこのデフォルト値を表現できないため、
    __call__にデフォルト引数を持つProtocolとして定義する。
    """

    def __call__(self, mode: INPUT_MODE = "once") -> bool:
        ...


# CONFIG_FILE = "keyconfig.json"
