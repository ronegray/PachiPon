"""
入力ライブラリ用インタフェース定義
"""
from typing import Literal, Callable


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
    "other1",
    "other2",
    "LS",
    "RS",
]


type InputHandler = Callable[[INPUT_MODE], bool]


# CONFIG_FILE = "keyconfig.json"
