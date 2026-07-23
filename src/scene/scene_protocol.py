"""scene_protocol.py
シーンクラスの利用側とのインタフェース

- シーン遷移時の戻り値の指定パラメータを管理
"""

# from enum import Enum, auto
from typing import Literal


# sceneクラス辞書
SCENE_NAME = Literal[
    "splash",
    "title",
    "newgame",
    # "ngplus",
    "dataload",
    "config",
    "keyconfig",
    # "saveconfig",
    "nameentry",
    # "town",
    # "field",
    # "dungeon",
    "map",
    "mapevent",
    "battlesplash",
    "battle",
    "battlemenu",
    # "craft",
    # "rest",
]


# class SceneTransition(Enum):
#     """画面遷移時の応答リスト"""
#     FORWARD = auto()  # 次画面（スタック追加）
#     PREVIOUS = auto()  # 前画面（最新スタック削除）
#     REPLACE = auto()  # 別画面（スタッククリア＆別画面スタック追加）
