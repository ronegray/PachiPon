"""scene_dictionary.py
シーン辞書
- シーン名リストの定義
- シーン名と該当シーンクラスの対応を管理する辞書定義

"""
from typing import Type
from .scene_protocol import SCENE_NAME

_registry: dict[SCENE_NAME, Type] = {}


def register(name: SCENE_NAME, cls: Type) -> None:
    _registry[name] = cls


def get_scene(name: SCENE_NAME) -> Type:
    return _registry[name]
