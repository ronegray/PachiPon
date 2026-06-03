from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import Optional, Dict
import random

from . import CharacterParam
from . import PlayerSprite
from item.item_protocol import ItemInstance, ItemTag, ItemDef, Owner

# import pyxel
from gameutils.base import check_file, read_json
# from service_locater import ServiceLocator

# import service_locater
from item.item_manager import ItemManager


class EquipmentSlot(IntEnum):
    WEAPON = auto()  # 武器
    GUARDER = auto()  # 防具
    ACCESSORY_1 = auto()  # 装飾品1
    ACCESSORY_2 = auto()  # 装飾品2
    CONSUME_1 = auto()  # 消耗品1
    CONSUME_2 = auto()  # 消耗品2


@dataclass
class Equipments:
    _owner_character_id: int

    def __post_init__(self):
        # ItemManagerをサービスロケータから取得
        # ItemManager はクラスメソッドしか持たないのでインスタンス化不要
        pass

    _equipped_items: Dict[EquipmentSlot, Optional[ItemInstance]] = field(
        default_factory=lambda: {
            EquipmentSlot.WEAPON: None,
            EquipmentSlot.GUARDER: None,
            EquipmentSlot.ACCESSORY_1: None,
            EquipmentSlot.ACCESSORY_2: None,
            EquipmentSlot.CONSUME_1: None,
            EquipmentSlot.CONSUME_2: None,
        }
    )
    _cached_itemdefs: Dict[EquipmentSlot, Optional[ItemDef]] = field(
        default_factory=lambda: {
            EquipmentSlot.WEAPON: None,
            EquipmentSlot.GUARDER: None,
            EquipmentSlot.ACCESSORY_1: None,
            EquipmentSlot.ACCESSORY_2: None,
            EquipmentSlot.CONSUME_1: None,
            EquipmentSlot.CONSUME_2: None,
        }
    )

    def _get_slot_from_item_tag(self, item_tag: ItemTag) -> Optional[EquipmentSlot]:
        # 武器、防具、装飾品は専用スロットに装備
        if item_tag == ItemTag.WEAPON:
            return EquipmentSlot.WEAPON
        if item_tag == ItemTag.GUARDER:
            return EquipmentSlot.GUARDER
        if item_tag == ItemTag.ACCESSORY:
            if self._equipped_items[EquipmentSlot.ACCESSORY_1] is None:
                return EquipmentSlot.ACCESSORY_1
            else:
                return EquipmentSlot.ACCESSORY_2
        # 消耗品は空いているスロットに装備（優先度: CONSUME_1 -> CONSUME_2）
        if item_tag == ItemTag.CONSUME:
            if self._equipped_items[EquipmentSlot.CONSUME_1] is None:
                return EquipmentSlot.CONSUME_1
            else:
                return EquipmentSlot.CONSUME_2
        return None

    def equip_on(self, item_instance: ItemInstance) -> Optional[ItemInstance]:
        item_def = ItemManager.get_def(item_instance.def_id)
        if not item_def:
            return None

        slot = self._get_slot_from_item_tag(item_def.tag)
        if slot is None:
            return None  # 装備できないアイテム

        # 既にそのスロットに装備品がある場合は、それを外して返す
        unequipped_item = None
        if self._equipped_items[slot] is not None:
            unequipped_item = self.equip_off(slot)  # 既存の装備を外す

        # 新しいアイテムを装備
        self._equipped_items[slot] = item_instance
        item_instance.owner_id = self._owner_character_id
        item_instance.state.equipped = True
        self._cached_itemdefs[slot] = item_def  # キャッシュを更新
        return unequipped_item

    def equip_off(self, slot: EquipmentSlot) -> Optional[ItemInstance]:
        item_instance = self._equipped_items[slot]
        if item_instance is not None:
            item_instance.owner_id = Owner.BAG.value  # バッグに戻す
            item_instance.state.equipped = False
            self._equipped_items[slot] = None
            self._cached_itemdefs[slot] = None  # キャッシュをクリア
        return item_instance

    def get_itemdef(self, slot: EquipmentSlot) -> Optional[ItemDef]:
        item_instance = self._equipped_items[slot]
        if item_instance is None:  # 装備されていない場合はNoneを返す
            return None

        if self._cached_itemdefs[slot] is None:
            # キャッシュがなければItemManagerから取得してキャッシュする
            item_def = ItemManager.get_def(item_instance.def_id)
            self._cached_itemdefs[slot] = item_def
        return self._cached_itemdefs[slot]


@dataclass
class Character:
    param: CharacterParam
    sprite: PlayerSprite  # スプライト
    id: int = 0
    equipments: Equipments = field(init=False)  # Equipmentsクラスをコンポジション

    is_moving: bool = False  # 移動中フラグ
    target_x: int = 0  # 目標X座標
    target_y: int = 0  # 目標Y座標
    move_speed: float = 1.5  # 移動速度（ピクセル/フレーム）
    _current_x: float = 0.0  # 内部的な正確なX座標
    _current_y: float = 0.0  # 内部的な正確なY座標

    def __post_init__(self):
        # param 内に座標データがあるか確認が必要だが、以前のコードに基づき x, y があると想定
        # ただし CharacterParam の定義を見ると x, y はない。
        # Character 自体が x, y を持つべきか、param に追加すべきか。
        # 以前の character.py の実装では self.param.x を参照していた。
        # とりあえずエラー回避のためにスプライトの初期座標を使う。
        self._current_x = float(self.sprite.x)
        self._current_y = float(self.sprite.y)
        self.equipments = Equipments(_owner_character_id=self.id)  # Equipmentsを初期化

    def update(self):
        if self.is_moving:
            self._update_movement()
        self.sprite.set_moving_status(self.is_moving)
        self.sprite.update()

    def draw(self, screen_x: int, screen_y: int):
        self.sprite.draw(screen_x, screen_y)

    def set_direction(self, direction: str):
        self.sprite.set_direction(direction)

    def set_event_point_status(self, status: bool):
        self.sprite.set_event_point_status(status)

    def set_position(self, x, y):
        self.sprite.x = self._current_x = x
        self.sprite.y = self._current_y = y
        self.target_x = x
        self.target_y = y
        self.is_moving = False

    def move_to(self, target_x: int, target_y: int):
        self.target_x = target_x
        self.target_y = target_y
        self.is_moving = True

    def _update_movement(self):
        dx = self.target_x - self._current_x
        dy = self.target_y - self._current_y

        distance = (dx**2 + dy**2) ** 0.5

        if distance < self.move_speed:
            self._current_x = float(self.target_x)
            self._current_y = float(self.target_y)
            # self.param.x = self.target_x # param に x, y はない
            # self.param.y = self.target_y
            self.is_moving = False
        else:
            # 移動方向を正規化
            if distance > 0:
                direction_x = dx / distance
                direction_y = dy / distance
            else:
                direction_x = 0
                direction_y = 0

            self._current_x += direction_x * self.move_speed
            self._current_y += direction_y * self.move_speed

            # self.param.x = int(round(self._current_x))
            # self.param.y = int(round(self._current_y))

        self.sprite.x = int(round(self._current_x))
        self.sprite.y = int(round(self._current_y))

    def get_position(self):
        return self.sprite.x, self.sprite.y

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
        weapon_def = self.equipments.get_itemdef(EquipmentSlot.WEAPON)
        if weapon_def:
            base_atk += weapon_def.atk
        # 装飾品からの攻撃力補正
        acc1 = self.equipments.get_itemdef(EquipmentSlot.ACCESSORY_1)
        if acc1:
            base_atk += acc1.atk
        acc2 = self.equipments.get_itemdef(EquipmentSlot.ACCESSORY_2)
        if acc2:
            base_atk += acc2.atk
        return base_atk

    def get_defense_power(self) -> int:
        # 装備品による防御力補正をここに加える
        base_dfn = self.param.defense  # defense をベースにする
        guarder_def = self.equipments.get_itemdef(EquipmentSlot.GUARDER)
        if guarder_def:
            base_dfn += guarder_def.dfn
        # 装飾品からの防御力補正
        acc1 = self.equipments.get_itemdef(EquipmentSlot.ACCESSORY_1)
        if acc1:
            base_dfn += acc1.dfn
        acc2 = self.equipments.get_itemdef(EquipmentSlot.ACCESSORY_2)
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
