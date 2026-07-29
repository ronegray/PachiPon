"""
sceneパッケージ

基底クラスを継承したsceneクラス群とそれらを定義するリスト
個別シーン用モジュールをシーン辞書へ登録
"""

# 管理系モジュール
from .scene_protocol import SCENE_NAME
from .scene_dictionary import register, get_scene, SCENE_NAME
from .scene_base import BaseScene, SITUATION
from .scene_manager import SceneManager

# 個別シーン用モジュール
from .scene_splash import SceneSplash
from .scene_title import SceneTitle
from .scene_charamake import SceneCharaMake
from .scene_newgame import SceneNewGame
from .scene_field import SceneField
from .scene_fieldevent import SceneFieldEvent
from .scene_battlesplash import SceneBattleSplash
from .scene_battle import SceneBattle
from .scene_battlemenu import SceneBattleMenu
from .scene_levelup import SceneLevelup


register("splash", SceneSplash)
register("title", SceneTitle)
register("newgame", SceneNewGame)
register("charamake", SceneCharaMake)
register("map", SceneField)
register("mapevent", SceneFieldEvent)
register("battlesplash", SceneBattleSplash)
register("battle", SceneBattle)
register("battlemenu", SceneBattleMenu)
register("levelup", SceneLevelup)
