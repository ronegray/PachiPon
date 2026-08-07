"""
エネミーモジュール
"""

from . import EntityBase, BaseSprite, EntityParam, EnemyParam, GuardType
from item import WeaponType
from skill import SkillID


class Enemy(EntityBase):
    def __init__(
        self, param: EntityParam, eparam: EnemyParam, sprite: BaseSprite, id: int = 0
    ):
        self.eparam = eparam  # エネミー専用パラメタ
        super().__init__(param, sprite, id)

    @property
    def hitdice(self) -> int:
        """敵用パラメタ：ダメージ用ダイス"""
        return self.eparam.hitdice

    @property
    def defvalue(self) -> int:
        """敵用パラメタ：防御性能"""
        return self.eparam.defvalue

    @property
    def magpenalty(self) -> int:
        """敵用パラメタ：魔法阻害"""
        return self.eparam.magpenalty

    @property
    def guard_type(self) -> int:
        """敵用パラメタ：防御タイプ"""
        return self.eparam.guardtype

    @property
    def weak_type(self) -> int:
        """敵用パラメタ：魔法弱点"""
        return self.eparam.weaktype

    def calc_guard_rate(self, attack_type: int = -1) -> float:
        """近接ダメージ相性率率計算"""
        try:
            real_attack_type = WeaponType(attack_type)
        except TypeError:
            return 1.0
        weak, same, hard = 0.5, 1.0, 2.0  # 相性倍率
        match real_attack_type:
            case WeaponType.NONE:
                return 1.0
            case WeaponType.CHOP:
                rate_cbs = [same, weak, hard]  # CHOP, BASH, STUB
            case WeaponType.BASH:
                rate_cbs = [hard, same, weak]  # CHOP, BASH, STUB
            case WeaponType.STUB:
                rate_cbs = [weak, hard, same]  # CHOP, BASH, STUB
            case WeaponType.FULL:
                rate_cbs = [hard, hard, hard]  # CHOP, BASH, STUB
        if self.guard_type == GuardType.FULL:
            rate = max([rate / 2 for rate in rate_cbs])
        else:
            rate = rate_cbs[self.guard_type]
        return rate

    def calc_weak_rate(self, skill_id: int = -1) -> float:
        """呪文ダメージ相性率率計算"""
        try:
            real_skill_id = SkillID(skill_id)
        except TypeError:
            return 1.0
        # spell 0x1_1_x_0 のxの値が1~8ある
        spell_type = (real_skill_id >> 4) - 1
        # 0b0000_0000 右端から順にspell種別の弱点bitがon
        is_weak = (self.weak_type >> spell_type) & 0b1
        if is_weak:
            return 2.0
        else:
            return 1.0
