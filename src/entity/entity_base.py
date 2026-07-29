"""
エンティティ基底モジュール

エンティティの基本的な機能を提供する
- ID識別
- パラメータ群の保持
- スプライトインスタンスの保持
- スキルインスタンスの保持
"""
import logging
from abc import ABC, abstractmethod
from helper import diceroll
from skill import Skills, SkillDef
from item import WeaponType
from . import EntityParam, BaseSprite


# ロギング設定
logger = logging.getLogger(__name__)


class EntityBase(ABC):
    """エンティティ基底クラス"""

    _critical_threshold: int = 10  # クリティカル判定閾値

    def __init__(self, param: EntityParam, sprite: BaseSprite, id: int = 0):
        self.param: EntityParam = param
        self.sprite: BaseSprite = sprite
        self.id: int = id
        self.skills: Skills = Skills(self.id)
        # ステータスボーナスの表現
        self.multiplier: list[float] = [1.0, 1.0]  # hp,mp倍率
        self.param_bonus: list[int] = [0, 0, 0, 0, 0]  # str,arc,end,spd,lck
        # 状態フラグ・パラメタ
        self.defend_rate: int = 1  # 防御時は2として防御体勢を表現する係数
        self.critical_rate: int = 2  # クリティカルダメージの倍率

    # パラメータ類
    @property
    def max_hp(self) -> int:
        return int(self.param.max_hp * self.multiplier[0])

    @property
    def max_mp(self) -> int:
        return int(self.param.max_mp * self.multiplier[0])

    @property
    def strength(self) -> int:
        return int(self.param.strength + self.param_bonus[0])

    @property
    def arcane(self) -> int:
        return int(self.param.arcane + self.param_bonus[1])

    @property
    def endurance(self) -> int:
        return int(self.param.endurance + self.param_bonus[2])

    @property
    def speed(self) -> int:
        return int(self.param.speed + self.param_bonus[3])

    @property
    def luck(self) -> int:
        return int(self.param.luck + self.param_bonus[4])

    # 装備効果を含めたパラメータから算出する能力値ボーナス
    @property
    def bonus_str(self) -> int:
        return self.strength // 6

    @property
    def bonus_arc(self) -> int:
        return self.arcane // 6

    @property
    def bonus_end(self) -> int:
        return self.endurance // 6

    @property
    def bonus_spd(self) -> int:
        return self.speed // 6

    @property
    def bonus_lck(self) -> int:
        return self.luck // 6

    @property
    def is_alive(self) -> bool:
        """生死判定"""
        return self.param.hp > 0

    @property
    @abstractmethod
    def hitdice(self) -> int:
        """敵味方で異なる為個別に実装"""
        ...

    @property
    @abstractmethod
    def defvalue(self) -> int:
        """敵味方で異なる為個別に実装"""
        ...

    @property
    @abstractmethod
    def magpenalty(self) -> int:
        """敵味方で異なる為個別に実装"""
        ...

    @property
    @abstractmethod
    def guard_type(self) -> int:
        """敵味方で異なる為個別に実装"""
        ...

    @property
    @abstractmethod
    def weak_type(self) -> int:
        """敵味方で異なる為個別に実装"""
        ...

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
        real_val = min(val, self.max_mp - self.param.mp)
        self.param.mp += real_val
        return real_val

    def decrease_mp(self, val: int) -> None:
        """MP減算(外部からの強制)"""
        real_val = min(val, self.param.mp)
        self.param.mp -= real_val

    def use_mp(self, cost: int) -> bool:
        """MP減算(意図した利用)"""
        if self.param.mp < cost:
            return False
        self.param.mp -= cost
        return True

    def check_mp(self, cost: int) -> bool:
        """MP消費可能チェック"""
        return self.param.mp >= cost

    def hitroll_offence(self) -> int:
        """命中ロール：攻撃側"""
        return diceroll(self.bonus_str) + self.bonus_lck

    def hitroll_defence(self) -> int:
        """命中ロール：防御側"""
        return (self.speed + self.bonus_lck) * self.defend_rate

    def get_critical_rate(self, diff: int) -> int:
        """クリティカル判定後、クリティカル倍率を取得"""
        cnt = diff // 6
        while cnt > 0:
            if diceroll(2) > EntityBase._critical_threshold:
                return self.critical_rate
            cnt -= 1
        return 1

    def damageroll_melee(self) -> tuple[int, int]:
        """近接ダメージ計算"""
        return (self.hitdice, diceroll(self.hitdice) + self.bonus_str)

    def suppress_damage_melee(self) -> int:
        """近接ダメージの防御による相殺値"""
        return (self.defvalue) * self.defend_rate

    def castroll(self, dc: int) -> bool:
        """魔法発動ロール"""
        return (diceroll(self.bonus_arc) - (dc + self.magpenalty)) > 0

    def damageroll_skill(self, skill_def: SkillDef) -> int:
        """魔法ダメージ計算（呼び出し）"""
        return self.skills.calc_damage(skill_def)

    def suppress_damage_skill(self) -> int:
        """魔法ダメージの防御による相殺値"""
        return (self.bonus_arc) * self.defend_rate

    def defend(self, sw: bool = True) -> None:
        """防御体勢変更"""
        if sw:
            self.defend_rate = 2
        else:
            self.defend_rate = 1

    def calc_guard_rate(self, attack_type: int = -1) -> float:
        """近接ダメージ相性率率計算 ※エネミー用シグネチャ"""
        return 1.0

    def calc_weak_rate(self, skill_id: int = -1) -> float:
        """呪文ダメージ相性率率計算 ※エネミー用シグネチャ"""
        return 1.0

    def get_weapon_type(self) -> WeaponType:
        """武器種取得　※プレイヤーキャラ用シグネチャ"""
        return WeaponType.NONE

    def gain_parameter(self, target: str) -> None:
        """レベルアップ時のパラメタ上昇　※プレイヤーキャラ用シグネチャ"""
        pass
