"""
エフェクト
"""

from enum import IntEnum
from dataclasses import dataclass

# fmt: off
# class EffectCategory(IntEnum):
#     ACTIVE  = 0x1_0_0_0
#     PASSIVE = 0xA_0_0_0

class SkillType(IntEnum):
    """効果の属性"""
    # SPELL = 0x1_1_0_0
    # ENEMY = 0x1_0_0_0
    # ITEMS = 0x0_0_0_0

    ACTIVE  = 0x1_0_0_0
    PASSIVE = 0xA_0_0_0

class SkillID(IntEnum):
    """効果識別子"""
    DUMMY            = 0xF_F_FF # ダミー効果コード

    ### spell 0x1_1_x_0
    # 破魔(sacred)
    SACRED_ARROW     = 0x1_1_1_1 # 単体攻撃
    SANCTUARY        = 0x1_1_1_2 # 範囲攻撃
    HOLY_SMITE       = 0x1_1_1_3 # アンデッド即死
    # 呪毒(curse)
    CURSE_PAIN       = 0x1_1_2_1 # ダイス目ー１
    POISON_CLOUD     = 0x1_1_2_2 # 受けた瞬間以降継続ダメージ
    STATUE_GAZE      = 0x1_1_2_3 # 行動不能
    # 火炎(fire)
    FIRE_BOLT        = 0x1_1_3_1 # 単体攻撃
    BURN_FLOOD       = 0x1_1_3_2 # 範囲攻撃
    INFERNO          = 0x1_1_3_3 # 範囲強攻撃
    # 氷結(ice)
    ICE_NEEDLE       = 0x1_1_4_1 # 単体攻撃
    FROST_CIRCLE     = 0x1_1_4_2 # 範囲攻撃
    BLIZZARD         = 0x1_1_4_3 # 範囲強攻撃
    # 雷電(bolt)
    BOLT_SHOWER      = 0x1_1_5_1 # 範囲攻撃
    THUNDER_PILLER   = 0x1_1_5_2 # 単体強攻撃
    ELECTROMAGNETIC  = 0x1_1_5_3 # 範囲強攻撃
    # 精神(mind)
    SLEEP_SONG       = 0x1_1_6_1 # 範囲催眠
    DISTURB_MIND     = 0x1_1_6_2 # 魔法発動ロールに３のペナルティ
    CHARM_ILLUSION   = 0x1_1_6_3 # 単体魅了
    # 衝撃(shock)
    SHOCK_BULLET     = 0x1_1_7_1 # 単体攻撃
    SONIC_WAVE       = 0x1_1_7_2 # 範囲攻撃
    BLOW_AWAY        = 0x1_1_7_3 # 単体攻撃＋次のイニシアチブが０固定
    # 霊光(light)
    HEALING_HAND     = 0x1_1_8_1 # 単体回復
    CURE_POISON      = 0x1_1_8_2 # 毒の解除
    ANGEL_STAIR      = 0x1_1_8_3 # 範囲回復

    ### item
    # DICE_DAMAGE      = 0x7_0_01
    # BONUS_INITIATIVE = 0x7_0_02
    # DICE_HIT         = 0x7_0_03
    # DICE_ENEMYDAMAGE = 0x7_0_04
    # DICE_ENEMYSPELL  = 0x7_0_05
    ATTACK_BONUS     = 0xA_1_0_1
    SPEED_BONUS      = 0xA_1_0_2
    REDUCE_WEAPON    = 0xA_1_0_3
    REDUCE_SPELL     = 0xA_1_0_4
    DICE_BONUS       = 0xA_1_0_5
    GAIN_MAXHP       = 0xA_2_0_1
    GAIN_MAXMP       = 0xA_2_0_2
    BONUS_STR        = 0xA_2_0_3
    BONUS_ARC        = 0xA_2_0_4
    BONUS_END        = 0xA_2_0_5
    BONUS_SPD        = 0xA_2_0_6
    BONUS_LCK        = 0xA_2_0_7
    HEAL_HP          = 0x1_2_0_1 # 消耗品　HP回復(レベルd6)
    # HIHEALPOT        = 0x7_2_02 # 消耗品　HP回復全快
    HEAL_MP          = 0x1_2_0_2 # 消耗品　MP回復(レベルd6/2※切り上げ)
    # HIMAGICPOT       = 0x7_2_04 # 消耗品　MP回復全快
    TORCHLIGHT       = 0xA_3_0_1 # 消耗品　イベント：ダンジョン時に１消費
    UNLOCK_KEY       = 0xA_3_0_2 # 消耗品　イベント：宝箱時に１消費
    ESCAPE_BATTLE    = 0xA_3_0_3 # 消耗品　使用直後の戦闘発生を回避／現在の戦闘から即座に離脱（敗北扱い）
    REDUCE_NEGATIVE  = 0xA_3_0_4 # 消耗品 次のランダムイベントからマイナス選択肢を１つ減らす
    # CLOVER           = 0x7_2_09 # 消耗品 次のランダムイベントからマイナス選択肢を２つ減らす
    DICE_PLUS        = 0xA_3_0_5 # 消耗品 次に実行されるダイス処理でダイス数を１ふやす
    # HIDICE           = 0x7_2_0B # 消耗品 次に実行されるダイス処理でダイス数を２ふやす
    # RATIONS          = 0x7_2_0C # 消耗品 食糧を10増やす
    # HIRATIONS        = 0x7_2_0D # 消耗品 食糧を50増やす
    FOOD_PLUS        = 0x1_2_0_3

    ### enemy special 0x1_F_0_0
    BREATH           = 0x1_F_0_1 # 炎ブレス
    POWERATTACK      = 0x1_F_0_2 # 強攻撃


class SkillTargetType(IntEnum):
    # NONE    = 0b0000
    # ALLY    = 0b0010
    # ALLIES  = 0b0011
    # ENEMY   = 0b0100
    # ENEMIES = 0b0101
    # ALL     = 0b0110 # ALLIESには自分も含む
    # SELF    = 0b1000
    NONE    = 0b0000 # ターゲット設定不可
    ALLY    = 0b0010 # 味方単体
    ALLIES  = 0b0011 # 味方全体
    ENEMY   = 0b0100 # 敵単体
    ENEMIES = 0b0101 # 敵全体
    ALL     = 0b0111 # 敵味方全体
    SELF    = 0b1000 # 自身のみ
# fmt: on


@dataclass(frozen=True)
class SkillDef:
    """各種効果のパラメタ定義マスタ"""

    def_id: SkillID
    name: str
    skill_type: SkillType
    target_type: SkillTargetType
    price: int = 0
    description: str = ""
    dc: int = 0  # 難易度
    cost: int = 0  # 消費MP
    effect_func: str = ""  # 効果関数コマンド名を記述
    effect_value: float = 0.0
    is_percent: bool = False
