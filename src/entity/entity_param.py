"""
エンティティパラメタモジュール

エンティティオブジェクトのパラメータ項目と初期値を定義
"""

from dataclasses import dataclass
from enum import IntEnum


@dataclass
class EntityParam:
    name: str
    strength: int
    arcane: int
    endurance: int
    speed: int
    luck: int
    max_hp: int = 0
    max_mp: int = 0
    level: int = 1
    exp: int = 0
    hp: int = 0
    mp: int = 0

    def __post_init__(self):
        """初期化後はHP・MPは最大値に設定"""
        self.hp = self.max_hp
        self.mp = self.max_mp


class GuardType(IntEnum):
    """物理攻撃耐性"""

    NONE = 0b0000  # 無
    CHOP = 0b0001  # 斬
    BASH = 0b0010  # 打
    STUB = 0b0100  # 突
    FULL = 0b1000  # 全


class WeakType(IntEnum):
    """魔法弱点"""

    NONE = 0  # 無
    SACRED = 1  # 破魔
    CURCE = 2  # 呪毒
    FIRE = 3  # 火炎
    ICE = 4  # 氷結
    BOLT = 5  # 雷電
    MIND = 6  # 精神
    SHOCK = 7  # 衝撃
    LIGHT = 8  # 霊光
    ALL = 9  # 全


@dataclass
class EnemyParam(EntityParam):
    threat: int = 0
    gold: int = 0
    hitdice: int = 1
    defvalue: int = 0
    magpenalty: int = 0
    guardtype: GuardType = GuardType.NONE
    weaktype: WeakType = WeakType.ALL
