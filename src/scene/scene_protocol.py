"""scene_protocol.py
シーンクラスの利用側とのインタフェース

- シーン遷移時の戻り値の指定パラメータを管理
"""
from typing import Literal

# sceneクラス辞書
SCENE_NAME = Literal[
    "splash",
    "title",
    "newgame",
    "charamake",
    "opening",
    "dataload",
    "config",
    "keyconfig",
    "nameentry",
    "map",
    "mapevent",
    "battlesplash",
    "battle",
    "battlemenu",
    "levelup",
    "shop",
]
