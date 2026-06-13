from enum import IntEnum, auto


class EffectType(IntEnum):
    SPELL = auto()
    ITEM = auto()
    ENEMY = auto()


class EffectID(IntEnum):
    ### spell
    # 破魔(sacred)
    SACRED_ARROW = auto()  # 単体攻撃
    SANCTUARY = auto()  # 範囲攻撃
    HOLY_SMITE = auto()  # アンデッド即死
    # 呪毒(curse)
    CURSE_PAIN = auto()  # ダイス目ー１
    POISON_CLOUD = auto()  # 受けた瞬間以降継続ダメージ
    STATUE_GAZE = auto()  # 行動不能
    # 火炎(fire)
    FIRE_BOLT = auto()  # 単体攻撃
    BURN_FLOOD = auto()  # 範囲攻撃
    INFERNO = auto()  # 範囲強攻撃
    # 氷結(ice)
    ICE_NEEDLE = auto()  # 単体攻撃
    FROST_CIRCLE = auto()  # 範囲攻撃
    BLIZZARD = auto()  # 範囲強攻撃
    # 雷電(bolt)
    BOLT_SHOWER = auto()  # 範囲攻撃
    THUNDER_PILLER = auto()  # 単体強攻撃
    ELECTROMAGNETIC = auto()  # 範囲強攻撃
    # 精神(mind)
    SLEEP_SONG = auto()  # 範囲催眠
    DISTURB_MIND = auto()  # 魔法発動ロールに３のペナルティ
    CHARM_ILLUSION = auto()  # 単体魅了
    # 衝撃(shock)
    SHOCK_BULLET = auto()  # 単体攻撃
    SONIC_WAVE = auto()  # 範囲攻撃
    BLOW_AWAY = auto()  # 単体攻撃＋次のイニシアチブが０固定
    # 霊光(light)
    HEAL = auto()  # 単体回復
    CURE_POISON = auto()  # 毒の解除
    ANGEL_STAIR = auto()  # 範囲回復

    ### item
    DICE_DAMAGE = auto()
    BONUS_INITIATIVE = auto()
    DICE_HIT = auto()
    DICE_ENEMYDAMAGE = auto()
    DICE_ENEMYSPELL = auto()
    DICE_ALL = auto()
    BONUS_MAXHP = auto()
    BONUS_MAXMP = auto()
    BONUS_STR = auto()
    BONUS_ARC = auto()
    BONUS_END = auto()
    BONUS_SPD = auto()
    BONUS_LCK = auto()
    HEALPOT = auto()  # 消耗品　HP回復(レベルd6)
    HIHEALPOT = auto()  # 消耗品　HP回復全快
    MAGICPOT = auto()  # 消耗品　MP回復(レベルd6/2※切り上げ)
    HIMAGICPOT = auto()  # 消耗品　MP回復全快
    TORCH = auto()  # 消耗品　イベント：ダンジョン時に１消費
    KEY = auto()  # 消耗品　イベント：宝箱時に１消費
    SMOKE = (
        auto()
    )  # 消耗品　使用直後の戦闘発生を回避／現在の戦闘から即座に離脱（敗北扱い）
    HORSESHOE = auto()  # 消耗品 次のランダムイベントからマイナス選択肢を１つ減らす
    CLOVER = auto()  # 消耗品 次のランダムイベントからマイナス選択肢を２つ減らす
    DICE = auto()  # 消耗品 次に実行されるダイス処理でダイス数を１ふやす
    HIDICE = auto()  # 消耗品 次に実行されるダイス処理でダイス数を２ふやす
    RATIONS = auto()  # 消耗品 食糧を10増やす
    HIRATIONS = auto()  # 消耗品 食糧を50増やす
