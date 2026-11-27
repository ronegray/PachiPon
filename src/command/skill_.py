"""
スキル用ヘルパーコマンドモジュール
"""
import sys
from typing import Generator, Callable
from dataclasses import dataclass, field
from const import SoundID
from entity import Enemy, WeakType, EntityBase
from skill import SkillDef, DebuffType
from helper import upper_int
from .entity_battle_command import CastSpellBattle
from . import SeqSubCmd, CommandBaseAction
from .effect_command import efx_skill_attack


@dataclass
class skill_info_package:
    """スペル利用時の情報引き渡しパッケージ"""

    command: CommandBaseAction
    skill_def: SkillDef
    pre_effects: list[Callable[[], Generator[list, None, None]]] = field(default_factory=list)  # yield を伴う後処理
    after_effects: list[Callable[[], Generator[list, None, None]]] = field(default_factory=list)  # yield を伴う後処理


def use_skill(pkg: skill_info_package) -> Generator[list, None, None]:
    """アイテム使用共通処理"""
    effect_func = getattr(sys.modules[__name__], pkg.skill_def.effect_func)

    yield from effect_func(pkg.command)

    if pkg.after_effects:
        for efx in pkg.after_effects:
            yield from efx()
    return


def cast_spell(self, skill_def: SkillDef) -> Generator[list, None, bool]:
    actor = self.ctx.actor

    # ファーストメッセージ
    yield [f"{actor.param.name}は {skill_def.name} を 詠唱する", "　　・・・・・"]
    yield [""]

    # 戦闘中のＭＰ減少による使用の可否チェック
    if not actor.use_mp(skill_def.cost):
        yield ["しかし　ＭＰが不足している・・・"]
        return False

    # 詠唱ロール
    if self.ctx.situation == "battle" and not actor.castroll(skill_def.dc):
        yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
        yield ["呪文は　失敗に終わった・・・"]
        return False

    return True


def recover_spell(self, actor: EntityBase, skill_def: SkillDef, target: EntityBase) -> Generator[list, None, None]:
    """スペル回復関連共通処理"""
    healing = actor.damageroll_skill(skill_def)

    yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore

    real_heal = target.increase_hp(healing)
    yield [SeqSubCmd.SE_INSTANT, SoundID.RECOVER]
    yield [f"{target.param.name}は {upper_int(real_heal)} のＨＰが　回復した"]


def attack_spell_single(cmd: CastSpellBattle) -> Generator[list, None, None]:
    """単体攻撃魔法"""

    cmd.resolve_singletarget(cmd.local_targets)
    target = cmd.local_target

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    # ダメージロール
    yield from cmd.damage_spell(cmd.ctx.actor, cmd.skill_def, target)


def attack_spell_area(cmd: CastSpellBattle) -> Generator[list, None, None]:
    """全体攻撃魔法"""

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    for target in cmd._check_living_targets():
        # ダメージロール
        yield from cmd.damage_spell(cmd.ctx.actor, cmd.skill_def, target)


def recover_spell_single(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """単体回復呪文"""
    try:
        cmd.resolve_singletarget(cmd.local_allies) # type: ignore
    except AttributeError:
        pass
    target = cmd.local_target

    # スキル共通処理
    result = yield from cast_spell(cmd, cmd.skill_def) # type: ignore
    if result is False:
        return

    # 回復ロール
    yield from recover_spell(cmd, cmd.ctx.actor, cmd.skill_def, target) # type: ignore


def recover_spell_area(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """全体回復呪文"""

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def) # type: ignore
    if result is False:
        return

    # 回復ロール
    for target in cmd.local_allies:
        if target.is_alive:
            yield from cmd.recover_spell(cmd.ctx.actor, cmd.skill_def, target) # type: ignore


def attack_disrupt_undead(cmd: CastSpellBattle) -> Generator[list, None, None]:
    """ターンアンデッド＋ダメージ"""

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    for target in cmd._check_living_targets():
        # ダメージロール
        dmg = yield from cmd.damage_spell(cmd.ctx.actor, cmd.skill_def, target)

        # 混乱時味方にキャストしたらダメージのみで終了
        if isinstance(target, Enemy) and dmg and target.is_alive:
            # 抵抗ロール（アンデッド＝霊光属性弱点の場合のみ）
            if (target.eparam.weaktype & WeakType.LIGHT) >= 1 and target.registroll(
                DebuffType.DISRUPT_UNDEAD, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc
            ) is False:
                target.instant_kill()
                yield [f"{target.param.name}は　灰となって　崩れ落ちた！"]
                continue


def debuff_dice_value(cmd: CastSpellBattle) -> Generator[list, None, None]:
    """デバフ：ダイス値現象"""
    cmd.resolve_singletarget(cmd.local_targets)
    target = cmd.local_target

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    yield from efx_skill_attack(cmd.display_info, target, cmd.skill_def.def_id)
    # 抵抗ロール（弱点属性の場合は必中）
    if (
        target.calc_weak_rate(cmd.skill_def.skill_type) > 1.0
        or target.registroll(DebuffType.REDUCE_DICEVALUE, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc) is False
    ):
        target.activate_debuff(DebuffType.REDUCE_DICEVALUE, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc)
        yield [f"{target.param.name}は　苦痛の呪いを受けた・・・"]
    else:
        yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
        yield [f"{target.param.name}は　効果をはねのけた！"]


def debuff_continual_damage(cmd: CastSpellBattle) -> Generator[list, None, None]:
    """デバフ：継続ダメージ（毒）"""

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    for target in cmd._check_living_targets():
        yield from efx_skill_attack(cmd.display_info, target, cmd.skill_def.def_id)
        # 抵抗ロール（弱点属性の場合は必中）
        if (
            target.calc_weak_rate(cmd.skill_def.skill_type) > 1.0
            or target.registroll(DebuffType.POISON_DAMAGE, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc) is False
        ):
            target.activate_debuff(DebuffType.POISON_DAMAGE, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc)
            yield [f"{target.param.name}は　毒を浴びてしまった・・・"]
        else:
            yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
            yield [f"{target.param.name}は　効果をはねのけた！"]


def debuff_stone_statue(cmd: CastSpellBattle) -> Generator[list, None, None]:
    """デバフ：石化"""

    cmd.resolve_singletarget(cmd.local_targets)
    target = cmd.local_target

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    yield from efx_skill_attack(cmd.display_info, target, cmd.skill_def.def_id)
    # 抵抗ロール（弱点属性の場合は必中）
    if (
        target.calc_weak_rate(cmd.skill_def.skill_type) > 1.0
        or target.registroll(DebuffType.STONE_HOLD, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc) is False
    ):
        target.activate_debuff(DebuffType.STONE_HOLD, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc)
        yield [f"{target.param.name}は　石の像になった・・・"]
    else:
        yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
        yield [f"{target.param.name}は　効果をはねのけた！"]


def debuff_sleep(cmd: CastSpellBattle) -> Generator[list, None, None]:
    """デバフ：睡眠"""

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    for target in cmd._check_living_targets():
        yield from efx_skill_attack(cmd.display_info, target, cmd.skill_def.def_id)
        # 抵抗ロール（弱点属性の場合は必中）
        if (
            target.calc_weak_rate(cmd.skill_def.skill_type) > 1.0
            or target.registroll(DebuffType.FALL_ASLEEP, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc) is False
        ):
            target.activate_debuff(DebuffType.FALL_ASLEEP, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc)
            yield [f"{target.param.name}は　眠りにおちた・・・"]
        else:
            yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
            yield [f"{target.param.name}は　効果をはねのけた！"]


def debuff_cast_penalty(cmd: CastSpellBattle) -> Generator[list, None, None]:
    """デバフ：詠唱妨害"""

    cmd.resolve_singletarget(cmd.local_targets)
    target = cmd.local_target

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    yield from efx_skill_attack(cmd.display_info, target, cmd.skill_def.def_id)
    # 抵抗ロール（弱点属性の場合は必中）
    if (
        target.calc_weak_rate(cmd.skill_def.skill_type) > 1.0
        or target.registroll(DebuffType.DISTURB_MIND, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc) is False
    ):
        target.activate_debuff(DebuffType.DISTURB_MIND, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc)
        yield [f"{target.param.name}は　集中を乱された・・・"]
    else:
        yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
        yield [f"{target.param.name}は　効果をはねのけた！"]


def debuff_charm(cmd: CastSpellBattle) -> Generator[list, None, None]:
    """デバフ：魅了"""

    cmd.resolve_singletarget(cmd.local_targets)
    target = cmd.local_target

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    yield from efx_skill_attack(cmd.display_info, target, cmd.skill_def.def_id)
    # 抵抗ロール（弱点属性の場合は必中）
    if (
        target.calc_weak_rate(cmd.skill_def.skill_type) > 1.0
        or target.registroll(DebuffType.CHARM_PERSON, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc) is False
    ):
        target.activate_debuff(DebuffType.CHARM_PERSON, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc)
        yield [f"{target.param.name}は　魅了された・・・"]
    else:
        yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
        yield [f"{target.param.name}は　効果をはねのけた！"]


def attack_initiative_zero(cmd: CastSpellBattle) -> Generator[list, None, None]:
    """デバフ：イニシアチブ０＋ダメージ"""

    cmd.resolve_singletarget(cmd.local_targets)
    target = cmd.local_target

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    # ダメージロール
    result2 = yield from cmd.damage_spell(cmd.ctx.actor, cmd.skill_def, target)
    if result2:
        # 抵抗ロール（弱点属性の場合は必中）
        if (
            target.calc_weak_rate(cmd.skill_def.skill_type) > 1.0
            or target.registroll(DebuffType.INITIATIVE_ZERO, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc) is False
        ):
            target.activate_debuff(DebuffType.INITIATIVE_ZERO, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc)
            yield [f"{target.param.name}は　吹っ飛ばされた！"]


def dispell_debuff(cmd: CastSpellBattle) -> Generator[list, None, None]:
    """デバフ解除"""

    cmd.resolve_singletarget(cmd.local_allies)
    target = cmd.local_target

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    target.clear_all_debuff()
    yield from efx_skill_attack(cmd.display_info, target, cmd.skill_def.def_id)
    yield [f"{target.param.name}の状態異常は　消え去った！"]
