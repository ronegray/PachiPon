"""
sceneパッケージ
基底クラスを継承したsceneクラス群とそれらを定義するリスト
"""
from .scene_protocol import SceneTransition
from .scene_manager import SceneManager  # , scn_mgr
from .scene_dictionary import register, SCENE_NAME
from .scene_base import BaseScene
from .scene_map import SceneMap
from .scene_splash import SceneSplash
from .scene_title import SceneTitle
# from .scene_newgame import SceneNewGame
# from .scene_dataload import SceneDataload
# from .scene_config import SceneConfig
# from .scene_field import SceneField

register("splash", SceneSplash)
register("title", SceneTitle)
register("map", SceneMap)
