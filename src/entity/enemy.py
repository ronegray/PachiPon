"""
エネミーモジュール
"""
from . import BaseSprite, EntityParam
from skill import Skills


class Enemy:
    def __init__(self, param: EntityParam, sprite: BaseSprite, id: int = 0):
        self.param: EntityParam = param
        self.sprite: BaseSprite = sprite
        self.id: int = id
        self.skills: Skills = Skills(self.id)

    # 装備効果を含めたパラメータ
    @property
    def max_hp(self) -> int:
        return int(self.param.max_hp)

    @property
    def max_mp(self) -> int:
        return int(self.param.max_mp)

    # 装備効果を含めたパラメータから算出する能力値ボーナス
    @property
    def bonus_str(self) -> int:
        return self.param.strength // 6

    @property
    def bonus_arc(self) -> int:
        return self.param.arcane // 6

    @property
    def bonus_end(self) -> int:
        return self.param.endurance // 6

    @property
    def bonus_spd(self) -> int:
        return self.param.speed // 6

    @property
    def bonus_lck(self) -> int:
        return self.param.luck // 6

    def increase_hp(self, val: int) -> int:
        """HP加算"""
        real_val = min(val, self.max_hp - self.param.hp)
        self.param.hp += real_val
        return real_val

    def decrease_hp(self, val: int) -> None:
        """HP減算"""
        real_val = min(val, self.param.hp)
        self.param.hp -= real_val

    def increase_mp(self, val: int) -> int:
        """MP加算"""
        real_val = max(val, self.max_mp - self.param.mp)
        self.param.mp += real_val
        return real_val

    def decrease_mp(self, val: int) -> None:
        """MP減算"""
        real_val = min(val, self.param.mp)
        self.param.mp -= real_val

    def use_mp(self, cost: int) -> bool:
        """MP減算"""
        if self.param.mp < cost:
            return False
        self.param.mp -= cost
        return True

    def is_alive(self) -> bool:
        return self.param.hp > 0
