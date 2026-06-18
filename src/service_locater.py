"""service_locater.py
サービスロケータモジュール
- シーンマネージャやユーザキャラ等のゲーム中で広範に参照されるオブジェクトを管理
"""
from __future__ import annotations
from typing import Any, TYPE_CHECKING
from enum import Enum, auto

# ロギング設定
import logging

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from scene import SceneManager
    from field_map import MapGraph
    from entity import Party, Character
    from gameutils.lib import SoundManager

    # from character import Character
    from item import ItemManager, ItemPool, StackPool


class ServiceKey(Enum):
    """DIコンテナ用キー定義"""

    SCENE_MANAGER = auto()
    MAPGRAPH = auto()
    SOUND_MANAGER = auto()
    ITEM_MANAGER = auto()
    MEMBER1 = auto()
    MEMBER2 = auto()
    MEMBER3 = auto()
    ITEMPOOL = auto()
    STACKPOOL = auto()
    PARTY = auto()
    HERO = auto()


# サービスコンテナ
_service_container: dict[ServiceKey, Any] = {}


def register(key: ServiceKey, instance: Any) -> None:
    """キーおよび対応インスタンスをコンテナに登録"""
    if _service_container.get(key):
        logger.warning(f"キーとインスタンスは登録済です:{key, type(instance)}")
    _service_container[key] = instance
    logger.info(f"サービス登録:{key.name, type(instance)}")


def show() -> dict:
    """登録済サービスコンテナ情報を参照"""
    logger.info(_service_container)
    return _service_container


# 型アクセサクラス
class _Ref:
    @property
    def scnmgr(self) -> SceneManager:
        return _service_container[ServiceKey.SCENE_MANAGER]

    @property
    def map(self) -> MapGraph:
        return _service_container[ServiceKey.MAPGRAPH]

    @property
    def sndmgr(self) -> SoundManager:
        return _service_container[ServiceKey.SOUND_MANAGER]

    @property
    def pt(self) -> Party:
        return _service_container[ServiceKey.PARTY]

    @property
    def hero(self) -> Character:
        return _service_container[ServiceKey.HERO]

    @property
    def mem1(self) -> Character:
        return _service_container[ServiceKey.MEMBER1]

    @property
    def mem2(self) -> Character:
        return _service_container[ServiceKey.MEMBER2]

    @property
    def itemmgr(self) -> ItemManager:
        return _service_container[ServiceKey.ITEM_MANAGER]

    @property
    def pl_item(self) -> ItemPool:
        return _service_container[ServiceKey.ITEMPOOL]

    @property
    def pl_stack(self) -> StackPool:
        return _service_container[ServiceKey.STACKPOOL]

    # @property
    # def cfgmgr(self) -> ConfigManager:
    #     return _di_container[DIKey.CFGMGR]


ref = _Ref()
