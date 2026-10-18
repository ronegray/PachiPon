"""scene_protocol.py
シーンクラスの利用側とのインタフェース

- シーン遷移時の戻り値の指定パラメータを管理
"""
from typing import Literal

SITUATION = Literal["field", "battle", "system"]

# sceneクラス辞書
SCENE_NAME = Literal[
    "splash",
    "title",
    "config",
    "keyconfig",
    "dataload",
    "datasave",
    "newgame",
    "nameentry",
    "charamake",
    "opening",
    "map",
    "mapevent",
    "battlesplash",
    "battle",
    "fixedbattle",
    "battlemenu",
    "levelup",
    "shop",
]
