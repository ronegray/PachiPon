"""entity_param.py
エンティティオブジェクトのパラメータ項目と初期値を定義
"""

from dataclasses import dataclass


@dataclass
class EntityParam:
    name: str
    strength: int
    arcane: int
    endurance: int
    speed: int
    luck: int
    level: int = 1
    exp: int = 0
    max_hp: int = 0
    max_mp: int = 0
    hp: int = 0
    mp: int = 0

    def __post_init__(self):
        """初期化後はHP・MPは最大値に設定"""
        self.hp = self.max_hp
        self.mp = self.max_mp
