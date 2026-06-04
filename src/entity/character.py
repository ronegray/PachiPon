"""chacacter.py
キャラクター本体モジュール
"""
from dataclasses import dataclass, field
import random
from .equipments import EquipSlot, Equips
from . import CharacterParam
from . import PlayerSprite
from gameutils.base import check_file, read_json


@dataclass
class Character:
    """キャラクターデータ
    - キャラクターに関するデータ・状態の管理
    - 振る舞いに関するメソッドは持たせない"""

    param: CharacterParam
    sprite: PlayerSprite  # スプライト
    id: int = 0
    equipments: Equips = field(init=False)  # Equipmentsクラスをコンポジション

    def __post_init__(self):
        self.equipments = Equips(_owner_character_id=self.id)  # Equipmentsを初期化

    def update(self):
        self.sprite.update()

    def draw(self, screen_x: int, screen_y: int):
        self.sprite.draw(screen_x, screen_y)

    def get_name(self):
        return self.param.name

    def get_hp(self):
        return self.param.hp

    def get_mp(self):
        return self.param.mp

    def take_damage(self, damage: int):
        self.param.hp -= damage
        if self.param.hp < 0:
            self.param.hp = 0

    def is_alive(self) -> bool:
        return self.param.hp > 0

    def gain_exp(self, exp: int):
        self.param.exp += exp
        # レベルアップ判定ロジックをここに追加

    def get_attack_power(self) -> int:
        # 装備品による攻撃力補正をここに加える
        base_atk = self.param.strength  # strength をベースにする
        weapon_def = self.equipments.get_itemdef(EquipSlot.WEAPON)
        if weapon_def:
            base_atk += weapon_def.atk
        # 装飾品からの攻撃力補正
        acc1 = self.equipments.get_itemdef(EquipSlot.ACCESSORY_1)
        if acc1:
            base_atk += acc1.atk
        acc2 = self.equipments.get_itemdef(EquipSlot.ACCESSORY_2)
        if acc2:
            base_atk += acc2.atk
        return base_atk

    def get_defense_power(self) -> int:
        # 装備品による防御力補正をここに加える
        base_dfn = self.param.defense  # defense をベースにする
        guarder_def = self.equipments.get_itemdef(EquipSlot.GUARDER)
        if guarder_def:
            base_dfn += guarder_def.dfn
        # 装飾品からの防御力補正
        acc1 = self.equipments.get_itemdef(EquipSlot.ACCESSORY_1)
        if acc1:
            base_dfn += acc1.dfn
        acc2 = self.equipments.get_itemdef(EquipSlot.ACCESSORY_2)
        if acc2:
            base_dfn += acc2.dfn
        return base_dfn

    def heal_hp(self, amount):
        self.param.hp += amount
        if self.param.hp > self.param.max_hp:
            self.param.hp = self.param.max_hp

    def use_mp(self, amount):
        self.param.mp -= amount
        if self.param.mp < 0:
            self.param.mp = 0

    def restore_mp(self, amount):
        self.param.mp += amount
        if self.param.mp > self.param.max_mp:
            self.param.mp = self.param.max_mp

    def add_exp(self, exp_amount):
        self.param.exp += exp_amount
        self._check_level_up()

    def _check_level_up(self):
        exp_table_path = check_file("assets/data/exp_table.json", "r")
        if not exp_table_path:
            print("Error: exp_table.json not found.")
            return
        exp_table = read_json(exp_table_path)

        while (
            self.param.level < len(exp_table)
            and self.param.exp >= exp_table[self.param.level]
        ):
            self.param.level += 1
            self._apply_level_up_bonus()

    def _apply_level_up_bonus(self):
        # HPとMPがサイコロ1回分上昇
        hp_roll = random.randint(1, 6)
        mp_roll = random.randint(1, 6)
        self.param.hp += hp_roll
        self.param.max_hp += hp_roll
        self.param.mp += mp_roll
        self.param.max_mp += mp_roll

        # 筋力、魔力、耐久、速度、幸運の任意の一つを1ポイントアップ
        stats = ["strength", "magic", "defense", "speed", "luck"]
        chosen_stat = random.choice(stats)
        setattr(self.param, chosen_stat, getattr(self.param, chosen_stat) + 1)
