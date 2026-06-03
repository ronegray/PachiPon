"""character_param.py
キャラクタのパラメータ項目と初期値を定義
"""
from dataclasses import dataclass


@dataclass
class CharacterParam:
    name: str
    hp: int
    mp: int
    strength: int
    magic: int
    defense: int
    speed: int
    luck: int
    level: int = 1
    exp: int = 0
    max_hp: int = 0
    max_mp: int = 0

    def __post_init__(self):
        self.max_hp = self.hp
        self.max_mp = self.mp
