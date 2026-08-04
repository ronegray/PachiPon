"""
エンティティパラメタモジュール

エンティティオブジェクトのパラメータ項目と初期値を定義
"""

from dataclasses import dataclass, field
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


class EnemySize(IntEnum):
    """モンスターサイズによる出現数の最大値"""

    S = 6
    M = 4
    L = 2
    XL = 1


# fmt: off
class GuardType(IntEnum):
    """物理攻撃耐性"""

    NONE = -1 # 無
    CHOP = 0 # 斬
    BASH = 1 # 打
    STUB = 2 # 突
    FULL = 3 # 全


class WeakType(IntEnum):
    """魔法弱点"""

    NONE   = 0b0000_0000 # 無
    SACRED = 0b0000_0001 # 破魔
    CURCE  = 0b0000_0010 # 呪毒
    FIRE   = 0b0000_0100 # 火炎
    ICE    = 0b0000_1000 # 氷結
    BOLT   = 0b0001_0000 # 雷電
    MIND   = 0b0010_0000 # 精神
    SHOCK  = 0b0100_0000 # 衝撃
    LIGHT  = 0b1000_0000 # 霊光
    ALL    = 0b1111_1111 # 全


class ActionPattern(IntEnum):
    """行動パターン"""

    ATTACK  = 0
    ESCAPE  = 1
    SKILL   = 2
    SPECIAL = 3
    DEFEND  = 4
# fmt: on


@dataclass
class EnemyParam:
    threat: int = 0
    bodysize: EnemySize = EnemySize.S
    gold: int = 0
    hitdice: int = 1
    defvalue: int = 0
    magpenalty: int = 0
    guardtype: int = 0b0000
    weaktype: int = 0b0000_0000
    action_pattern: list[ActionPattern] = field(default_factory=list)
