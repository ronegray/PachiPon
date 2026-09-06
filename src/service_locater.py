"""
サービスロケータモジュール

- ゲーム中で広範に参照されるオブジェクトを管理
"""

from __future__ import annotations
from typing import Any, TYPE_CHECKING
from enum import Enum, auto

# ロギング設定
import logging

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from config import ApplicationConfig
    from command import CommandManager
    from scene import SceneManager
    from event import EventRepository
    from field_map import MapGraph
    from entity import Party, EnemyRepository  # , Character
    from gameutils.base import SoundManager
    from item import ItemRepository, ItemPool, StackPool
    from skill import SkillRepository
    from effect import EffectRepository, DiceRollEffect


class ServiceKey(Enum):
    """DIコンテナ用キー定義"""

    APP_CONFIG = auto()
    ITEM_REPOSITORY = auto()
    SKILL_REPOSITORY = auto()
    ENEMY_REPOSITORY = auto()
    EVENT_REPOSITORY = auto()
    EFFECT_REPOSITORY = auto()

    COMMAND_MANAGER = auto()
    SCENE_MANAGER = auto()
    SOUND_MANAGER = auto()

    PARTY = auto()
    ITEMPOOL = auto()
    STACKPOOL = auto()
    MAPGRAPH = auto()

    DICEROLL_EFFECT = auto()


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
    def conf(self) -> ApplicationConfig:
        return _service_container[ServiceKey.APP_CONFIG]

    @property
    def cmdmgr(self) -> CommandManager:
        return _service_container[ServiceKey.COMMAND_MANAGER]

    @property
    def scnmgr(self) -> SceneManager:
        return _service_container[ServiceKey.SCENE_MANAGER]

    @property
    def evtrps(self) -> EventRepository:
        return _service_container[ServiceKey.EVENT_REPOSITORY]

    @property
    def map(self) -> MapGraph:
        return _service_container[ServiceKey.MAPGRAPH]

    @property
    def efxrps(self) -> EffectRepository:
        return _service_container[ServiceKey.EFFECT_REPOSITORY]

    @property
    def efxdice(self) -> DiceRollEffect:
        return _service_container[ServiceKey.DICEROLL_EFFECT]

    @property
    def sndmgr(self) -> SoundManager:
        return _service_container[ServiceKey.SOUND_MANAGER]

    @property
    def pt(self) -> Party:
        return _service_container[ServiceKey.PARTY]

    @property
    def enmrps(self) -> EnemyRepository:
        return _service_container[ServiceKey.ENEMY_REPOSITORY]

    @property
    def itemrps(self) -> ItemRepository:
        return _service_container[ServiceKey.ITEM_REPOSITORY]

    @property
    def pl_item(self) -> ItemPool:
        return _service_container[ServiceKey.ITEMPOOL]

    @property
    def pl_stack(self) -> StackPool:
        return _service_container[ServiceKey.STACKPOOL]

    @property
    def sklrps(self) -> SkillRepository:
        return _service_container[ServiceKey.SKILL_REPOSITORY]


ref = _Ref()
