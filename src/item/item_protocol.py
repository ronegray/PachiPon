"""item_protocol.py
アイテム関連のID定義モジュール
"""

from dataclasses import dataclass  # , field
from enum import IntEnum  # , auto
# from typing import Optional
# from typing import Callable


# fmt: off
class ItemType(IntEnum):
    """アイテムの属性"""
    # WEAPON   = 0x00_00 # 武器：インスタンス管理
    # GUARDER  = 0x07_00 # 防具：インスタンス管理
    # ORNAMENT = 0x0B_00 # 装飾：インスタンス管理
    # CONSUME  = 0x10_00 # 消耗品：スタック管理
    # KEY_ITEM = 0x0F_00 # 重要品：インスタンス管理
    WEAPON   = 0x00 # 武器：インスタンス管理
    GUARDER  = 0x07 # 防具：インスタンス管理
    ORNAMENT = 0x0B # 装飾：インスタンス管理
    CONSUME  = 0x10 # 消耗品：スタック管理
    KEY_ITEM = 0x0F # 重要品：インスタンス管理


class WeaponType(IntEnum):
    """武器種別"""

    NONE = 0x00_0 # 無
    CHOP = 0x00_1 # 斬
    BASH = 0x00_2 # 打
    STUB = 0x00_4 # 突
    FULL = 0x00_7 # 全


class GuarderType(IntEnum):
    """防具種別"""

    FREE = 0x07_0_0  # 魔法制約なし
    GEIS = 0x07_1_0  # 魔法制約あり


class OrnamentGrade(IntEnum):
    """装飾品のグレード"""

    COMMON = 0x0B_0_0
    LEGEND = 0x0B_1_0


class ConsumeGrade(IntEnum):
    """消耗品のグレード"""

    COMMON = 0x10_0_0
    LEGEND = 0x10_1_0


class ItemID(IntEnum):
    """アイテム識別子"""
    DUMMY        = 0xFF_F_F  # ダミーアイテムコード

    # キーアイテム
    CROWN        = 0x0F_0_1  # ラスボス対策 # 魔法ロールを下げる
    MIRROR       = 0x0F_0_2  # ラスボス対策 # 特殊攻撃を封じる
    CEPTER       = 0x0F_0_3  # ラスボス対策 # 攻撃ロールを下げる
    GRAIL        = 0x0F_0_4  # ラスボス対策 # HP自動回復を封じる
    JADEEYE      = 0x0F_0_5  # イベントA A+B = D
    CROSS        = 0x0F_0_6  # イベントB B+C = E
    CRYSTALROD   = 0x0F_0_7  # イベントC C+A = F
    DRAGONFANG   = 0x0F_0_8  # イベントD D+E 武器
    TARISMAN     = 0x0F_0_9  # イベントE
    HOLYSHROUD   = 0x0F_0_A  # イベントF E+F 防具
    # 武器：斬
    DAGGER       = 0x00_1_1
    SHORTSWORD   = 0x00_1_2
    LONGSWORD    = 0x00_1_3
    CLAYMORE     = 0x00_1_4
    MAGICBLADE   = 0x00_1_5
    # 武器：打
    MACE         = 0x00_2_1
    FLAIL        = 0x00_2_2
    MORNINGSTAR  = 0x00_2_3
    WARHAMMER    = 0x00_2_4
    MAGICMACE    = 0x00_2_5
    # 武器：突
    JAVELIN      = 0x00_4_1
    SPEAR        = 0x00_4_2
    PIKE         = 0x00_4_3
    LANCE        = 0x00_4_4
    MAGICSPEAR   = 0x00_4_5
    # 最強武器
    SACREDWEAPON = 0x00_7_9
    # 防具 カテゴリ_魔法制約ペナ有無_アイテム識別子
    # ※魔法制約ペナ有無は論理情報で実際にはItemDef.magpenaltyを使用する
    CLOTH        = 0x07_0_1  # 魔法制約0
    LEATHER      = 0x07_1_2  # 魔法制約-1
    CHAIN        = 0x07_1_3  # 魔法制約-2
    ENCHANTROBE  = 0x07_0_4  # 魔法制約0
    HALFPLATE    = 0x07_1_5  # 魔法制約-4
    FULLPLATE    = 0x07_1_6  # 魔法制約-8
    # 最強防具
    HOLYGUARD    = 0x07_1_9  # 魔法制約-3
    # アクセサリ（効果の高い方が優先で重複はしない）
    # アイテムそのものの識別子であり、効果識別子とはItemDef.effect_idで紐付け
    ATKRING      = 0x0B_0_1  # アクセ　物理ダメージダイス＋１
    SPDRING      = 0x0B_0_2  # アクセ　イニシアチブボーナス＋１、命中ロールダイス＋１
    DEFRING      = 0x0B_0_3  # アクセ　相手のダメージダイスー１
    REGRING      = 0x0B_0_4  # アクセ　相手の魔法発動／効果ダイスー１
    HIATKRING    = 0x0B_1_1  # アクセ　物理ダメージダイス＋３
    HISPDRING    = 0x0B_1_2  # アクセ　イニシアチブボーナス＋３、命中ロールダイス＋３
    HIDEFRING    = 0x0B_1_3  # アクセ　相手のダメージダイスー３
    HIREGRING    = 0x0B_1_4  # アクセ　相手の魔法発動／効果ダイスー３
    HPBELT       = 0x0B_0_5  # アクセ　最大HP1.5倍
    MPBELT       = 0x0B_0_6  # アクセ　最大MP1.5倍
    HIHPBELT     = 0x0B_1_5  # アクセ　最大HP3倍
    HIMPBELT     = 0x0B_1_6  # アクセ　最大MP3倍
    CHEATDICE    = 0x0B_0_7  # アクセ　全ダイス目＋１
    GODDICE      = 0x0B_1_7  # アクセ　全ダイス目＋３
    POWAMULET    = 0x0B_0_8  # アクセ　筋力＋３
    ARCAMULET    = 0x0B_0_9  # アクセ　魔力＋３
    CONAMULET    = 0x0B_0_A  # アクセ　耐久＋３
    SPDAMULET    = 0x0B_0_B  # アクセ　速度＋３
    LCKAMULET    = 0x0B_0_C  # アクセ　幸運＋３
    HIPOWAMULET  = 0x0B_1_8  # アクセ　筋力＋６
    HIARCAMULET  = 0x0B_1_9  # アクセ　魔力＋６
    HICONAMULET  = 0x0B_1_A  # アクセ　耐久＋６
    HISPDAMULET  = 0x0B_1_B  # アクセ　速度＋６
    HILCKAMULET  = 0x0B_1_C  # アクセ　幸運＋６
    # CIRCLET      = 0x0B_0_D # アクセ　MP消費減少25％ #検討中
    # HICIRCLET    = 0x0B_1_D # アクセ　MP消費減少50％ #検討中
    # 消耗品 # カテゴリ_高級品_効果ID
    HEALPOT      = 0x10_0_1  # 消耗品　HP回復(レベルd6)
    HIHEALPOT    = 0x10_1_1  # 消耗品　HP回復全快
    MAGICPOT     = 0x10_0_2  # 消耗品　MP回復(レベルd6/2※切り上げ)
    HIMAGICPOT   = 0x10_1_2  # 消耗品　MP回復全快
    TORCH        = 0x10_0_3  # 消耗品　イベント：ダンジョン時に１消費
    KEY          = 0x10_0_4  # 消耗品　イベント：宝箱時に１消費
    SMOKE        = 0x10_0_5  # 消耗品　使用直後の戦闘発生を回避／現在の戦闘から即座に離脱（敗北扱い）
    HORSESHOE    = 0x10_0_6  # 消耗品 次のランダムイベントからマイナス選択肢を１つ減らす
    CLOVER       = 0x10_1_6  # 消耗品 次のランダムイベントからマイナス選択肢を２つ減らす
    DICE         = 0x10_0_7  # 消耗品 次に実行されるダイス処理でダイス数を１ふやす
    HIDICE       = 0x10_1_7  # 消耗品 次に実行されるダイス処理でダイス数を２ふやす
    RATIONS      = 0x10_0_8  # 消耗品 食糧を10増やす
    HIRATIONS    = 0x10_1_8  # 消耗品 食糧を50増やす

class ItemTargetType(IntEnum):
    NONE    = 0b0000 # ターゲット設定不可
    ALLY    = 0b0010 # 味方単体
    ALLIES  = 0b0011 # 味方全体
    ENEMY   = 0b0100 # 敵単体
    ENEMIES = 0b0101 # 敵全体
    ALL     = 0b0111 # 敵味方全体
    SELF    = 0b1000 # 自身のみ

class ItemRank(IntEnum):
    JUNK   = 0
    NORMAL = 1
    RARE   = 2
    LEGEND = 3
# fmt: on


@dataclass(frozen=True)
class ItemDef:
    """アイテムパラメタ定義マスタ"""

    def_id: ItemID  # 種類を表すID (ItemID の値)
    name: str
    item_type: ItemType
    target_type: ItemTargetType
    stackable: bool
    rank: ItemRank
    price: int = 0
    description: str = ""
    # 装備品
    hitdice: int = 0
    defvalue: int = 0
    magpenalty: int = 0
    # アクセ・消耗品用
    effect_id: str = ""  # EffectIDと連携
    effect_value: float = 0.0
    is_percent: bool = False

    @property
    def expect_damage(self) -> int:
        """ダメージ期待値"""
        if self.item_type != ItemType.WEAPON:
            return 0
        dice_min = 1
        dice_max = 6
        return (self.hitdice * (dice_min + dice_max)) // 2 + 1


# --- インスタンス管理（装備品など） ---
class ItemState(IntEnum):
    """アイテム状態"""

    BAG = 9  # 共有バッグ
    FREE = -1  # 所属無し（生成直後やモンスタードロップ等）
    HERO = 0  # 主人公の装備品
    MEM1 = 1  # 仲間１の装備品
    MEM2 = 2  # 仲間２の装備品


# # アイテムの状態をまとめたデータクラス
# @dataclass
# class ItemState:
#     equipped: bool = False
#     durability: int = 100


# @dataclass
# class UniqueIdentifyItem:
#     """アイテム個体識別情報"""

#     instance_id: int  # 固有ID
#     def_id: ItemID  # 定義ID
#     state: ItemState  # 所持者ID
#     # state: ItemState = field(default_factory=ItemState)


@dataclass
class ItemInstance:
    param: ItemDef
    enchant: int = 1


@dataclass
class PoolEntry:
    ins: ItemInstance
    stat: ItemState


# 装備スロット用独自型
type PooledItem = tuple[int, PoolEntry]
