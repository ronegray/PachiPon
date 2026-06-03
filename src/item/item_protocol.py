# item_pool.py

from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import Optional


# アイテム属性（スタック可否の分岐に使う）
class ItemTag(IntEnum):
    WEAPON = auto()  # 武器：インスタンス管理
    GUARDER = auto()  # 防具：インスタンス管理
    ACCESSORY = auto()  # 装飾：インスタンス管理
    CONSUME = auto()  # 消耗品：スタック管理
    KEY_ITEM = auto()  # 重要品：インスタンス管理


# def_idの一覧
class ItemID(IntEnum):
    DAGGER = auto()  # 武器
    SHORTSWORD = auto()  # 武器
    LONGSWORD = auto()  # 武器
    CLAYMORE = auto()  # 武器
    FIREBLADE = auto()  # 武器
    SACREDSWORD = auto()  # 武器
    CLOTH = auto()  # 防具
    LEATHER = auto()  # 防具
    CHAIN = auto()  # 防具
    HALFPLATE = auto()  # 防具
    FULLPLATE = auto()  # 防具
    HOLYARMOR = auto()  # 防具
    ATKRING = auto()  # アクセ　ダメージ＋１
    DEFRING = auto()  # アクセ　ダメージ減少＋１
    HPBELT = auto()  # アクセ　HP2倍
    MPBELT = auto()  # アクセ　MP2倍
    CHEATDICE = auto()  # アクセ　ダイス目＋１
    POWAMULET = auto()  # アクセ　筋力＋１
    ARCAMULET = auto()  # アクセ　魔力＋１
    CONAMULET = auto()  # アクセ　耐久＋１
    SPDAMULET = auto()  # アクセ　速度＋１
    LCKAMULET = auto()  # アクセ　幸運＋１
    CIRCLET = auto()  # アクセ　MP消費減少
    HEALPOT = auto()  # 消耗品　HPMAXの半分回復
    MAGICPOT = auto()  # 消耗品　MPMAXの半分回復
    TORCH = auto()  # 消耗品　ダンジョン進入時に１消費


# アイテム定義（マスターデータ）
@dataclass(frozen=True)
class ItemDef:
    def_id: int  # 種類を表すID (ItemID の値)
    name: str
    tag: ItemTag
    stackable: bool
    price: int = 0
    description: str = ""
    # 装備品用
    atk: int = 0
    dfn: int = 0
    spd: int = 0
    # 消耗品用
    effect_type: Optional[str] = None
    effect_value: int = 0
    is_percent: bool = False


# --- インスタンス管理（装備品など） ---
class Owner(IntEnum):
    BAG = -1
    FREE = -9


# アイテムの状態をまとめたデータクラス
@dataclass
class ItemState:
    equipped: bool = False
    durability: int = 100


@dataclass
class ItemInstance:
    instance_id: int  # 固有ID
    def_id: int  # 定義ID
    owner_id: int  # 所持者ID
    state: ItemState = field(default_factory=ItemState)
