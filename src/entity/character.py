"""
キャラクター本体モジュール
"""

# from dataclasses import dataclass  # , field
from gameutils.base import check_file, read_json
from assets.asset_map import AssetMap, AssetID

# import random
# from equipments import
from . import EntityParam, PlayerSprite, Equips  # , PlayerSpriteType, EquipSlot

# from item import ItemState
from skill import SkillID, Skills
# from gameutils.base import check_file, read_json


class Character:
    """ユーザキャラクタークラス"""

    exp_table: list = []

    def __init__(self, param: EntityParam, sprite: PlayerSprite, id: int = 0):
        self.param: EntityParam = param
        self.sprite: PlayerSprite = sprite
        self.id: int = id
        self.equipments: Equips = Equips(self.id)  # Equipmentsを初期化
        self.skills: Skills = Skills(self.id)  # type:ignore

        # 経験値テーブルデータが無い場合は読み込み
        if not Character.exp_table:
            path = check_file(AssetMap.get_assetpath(AssetID.DATA_EXPTABLE))
            if path:
                data = read_json(path)
            else:
                data = [0, 1, 2]
            Character.exp_table = data

    # 装備効果を含めたパラメータ
    @property
    def max_hp(self) -> int:
        return int(self.param.max_hp)

    @property
    def max_mp(self) -> int:
        return int(self.param.max_mp)

    @property
    def next_exp(self) -> int:
        return int(self.exp_table[self.param.level] - self.param.exp)

    @property
    def strength(self) -> int:
        return int(
            self.param.strength + self.equipments.get_adjust_effect(SkillID.BONUS_STR)
        )

    @property
    def arcane(self) -> int:
        return int(
            self.param.arcane + self.equipments.get_adjust_effect(SkillID.BONUS_ARC)
        )

    @property
    def endurance(self) -> int:
        return int(
            self.param.endurance + self.equipments.get_adjust_effect(SkillID.BONUS_END)
        )

    @property
    def speed(self) -> int:
        return int(
            self.param.speed + self.equipments.get_adjust_effect(SkillID.BONUS_SPD)
        )

    @property
    def luck(self) -> int:
        return int(
            self.param.luck + self.equipments.get_adjust_effect(SkillID.BONUS_LCK)
        )

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

    # def gain_exp(self, exp: int):
    #     self.param.exp += exp
    #     # レベルアップ判定ロジックをここに追加

    # def add_exp(self, exp_amount):
    #     self.param.exp += exp_amount
    #     self._check_level_up()

    # def _check_level_up(self):
    #     exp_table_path = check_file("assets/data/exp_table.json", "r")
    #     if not exp_table_path:
    #         print("Error: exp_table.json not found.")
    #         return
    #     exp_table = read_json(exp_table_path)

    #     while (
    #         self.param.level < len(exp_table)
    #         and self.param.exp >= exp_table[self.param.level]
    #     ):
    #         self.param.level += 1
    #         self._apply_level_up_bonus()

    # def _apply_level_up_bonus(self):
    #     # HPとMPがサイコロ1回分上昇
    #     hp_roll = random.randint(1, 6)
    #     mp_roll = random.randint(1, 6)
    #     self.param.hp += hp_roll
    #     self.param.max_hp += hp_roll
    #     self.param.mp += mp_roll
    #     self.param.max_mp += mp_roll

    #     # 筋力、魔力、耐久、速度、幸運の任意の一つを1ポイントアップ
    #     stats = ["strength", "magic", "defense", "speed", "luck"]
    #     chosen_stat = random.choice(stats)
    #     setattr(self.param, chosen_stat, getattr(self.param, chosen_stat) + 1)
