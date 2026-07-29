"""
キャラクター本体モジュール
"""

# from dataclasses import dataclass  # , field
from gameutils.base import check_file, read_json
from assets.asset_map import AssetMap, AssetID
from item import PooledItem, WeaponType

# import random
# from equipments import
from . import (
    EntityBase,
    EntityParam,
    PlayerSprite,
    Equips,
    EquipSlot,
)  # , PlayerSpriteType, EquipSlot

from item import ItemType
from skill import SkillID  # , Skills

# from gameutils.base import check_file, read_json
import service_locater as di


class Character(EntityBase):
    """ユーザキャラクタークラス"""

    exp_table: list = []

    def __init__(self, param: EntityParam, sprite: PlayerSprite, id: int = 0):
        # self.param: EntityParam = param
        # self.sprite: PlayerSprite = sprite
        # self.id: int = id
        super().__init__(param, sprite, id)
        self.equipments: Equips = Equips(self.id)  # Equipmentsを初期化
        # self.skills: Skills = Skills(self.id)  # type:ignore

        # 経験値テーブルデータが無い場合は読み込み
        if not Character.exp_table:
            path = check_file(AssetMap.get_assetpath(AssetID.DATA_EXPTABLE))
            if path:
                data = read_json(path)
            else:
                data = [0, 1, 2]
            Character.exp_table = data

    def update_bonus(self) -> None:
        self.multiplier = [
            max(1, self.equipments.get_adjust_effect(SkillID.GAIN_MAXHP)),
            max(1, self.equipments.get_adjust_effect(SkillID.GAIN_MAXMP)),
        ]
        self.param_bonus = [
            int(self.equipments.get_adjust_effect(SkillID.BONUS_STR)),
            int(self.equipments.get_adjust_effect(SkillID.BONUS_ARC)),
            int(self.equipments.get_adjust_effect(SkillID.BONUS_END)),
            int(self.equipments.get_adjust_effect(SkillID.BONUS_SPD)),
            int(self.equipments.get_adjust_effect(SkillID.BONUS_LCK)),
        ]

    @property
    def next_exp(self) -> int:
        return int(self.exp_table[self.param.level] - self.param.exp)

    # @property
    # def strength(self) -> int:
    #     return int(
    #         self.param.strength + self.equipments.get_adjust_effect(SkillID.BONUS_STR)
    #     )

    # @property
    # def arcane(self) -> int:
    #     return int(
    #         self.param.arcane + self.equipments.get_adjust_effect(SkillID.BONUS_ARC)
    #     )

    # @property
    # def endurance(self) -> int:
    #     return int(
    #         self.param.endurance + self.equipments.get_adjust_effect(SkillID.BONUS_END)
    #     )

    # @property
    # def speed(self) -> int:
    #     return int(
    #         self.param.speed + self.equipments.get_adjust_effect(SkillID.BONUS_SPD)
    #     )

    # @property
    # def luck(self) -> int:
    #     return int(
    #         self.param.luck + self.equipments.get_adjust_effect(SkillID.BONUS_LCK)
    #     )

    def get_equip(self, slot: EquipSlot) -> PooledItem | None:
        """装備中のアイテムを取得"""
        return self.equipments.get_slot(slot)

    def get_weapon_type(self) -> WeaponType:
        item = self.get_equip(EquipSlot.WEAPON)
        if item is None:
            return WeaponType.NONE
        else:
            weapon_type = (item[1].ins.param.def_id >> 4) & 0xF
            return WeaponType(weapon_type)

    @property
    def hitdice(self) -> int:
        """武器のダイス値を取得"""
        item = self.get_equip(EquipSlot.WEAPON)
        if item is None:
            return 1
        else:
            return item[1].ins.param.hitdice

    @property
    def defvalue(self) -> int:
        """防具の防御値を取得"""
        # item = self.equipments.get_slot(EquipSlot.GUARDER)
        item = self.get_equip(EquipSlot.GUARDER)
        if item is None:
            return 0
        else:
            return item[1].ins.param.defvalue

    @property
    def magpenalty(self) -> int:
        """防具のペナルティ値を取得"""
        # item = self.equipments.get_slot(EquipSlot.GUARDER)
        item = self.get_equip(EquipSlot.GUARDER)
        if item is None:
            return 0
        else:
            return item[1].ins.param.magpenalty

    @property
    def guard_type(self) -> int:
        """防御タイプによる減衰はプレイヤーには無し"""
        return 0b0000

    @property
    def weak_type(self) -> int:
        """プレイヤーには魔法弱点無し"""
        return 0b0000_0000

    def gain_exp(self, exp: int):
        """expの加算"""
        self.param.exp += exp

    def check_levelup(self) -> int:
        """レベルアップ判定ロジック"""
        up_count = 0
        for nextexp in self.exp_table[self.param.level :]:
            if self.param.exp >= nextexp:
                up_count += 1
            else:
                break
        return up_count

    def gain_parameter(self, target: str) -> None:
        """指定されたパラメタを加算"""
        val = getattr(self.param, target)
        if val is None:
            raise ValueError
        setattr(self.param, target, val + 1)

    def equip_default(self) -> None:
        """キャラ作成時のデフォルト装備を設定"""
        pooled = di.ref.pl_item.get_by_type(ItemType.WEAPON)
        pl_item = [(key, val) for key, val in pooled.items()]
        self.equipments.equip_on_pool(EquipSlot.WEAPON, pl_item[0])
        pooled = di.ref.pl_item.get_by_type(ItemType.GUARDER)
        pl_item = [(key, val) for key, val in pooled.items()]
        self.equipments.equip_on_pool(EquipSlot.GUARDER, pl_item[0])
