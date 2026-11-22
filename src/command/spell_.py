"""
スキル用ヘルパーコマンドモジュール
"""
from typing import Generator  # , cast, TYPE_CHECKING
from const import SoundID
from entity import Enemy, WeakType
from skill import DebuffType

# from .entity_battle_command import SeqSubCmd
from . import SeqSubCmd, CommandBaseAction
from .effect_command import efx_skill_attack


# #class attack_spell_single(CastSpellBattle):
#     """単体攻撃魔法"""


def attack_spell_single(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """単体攻撃魔法"""
    # self._ctx.actor = self._ctx.self._ctx.actor
    cmd.resolve_singletarget(cmd.local_targets)
    target = cmd.local_target

    # # コマンドパッケージから取得するスキル情報
    # self.skill_def = self.args[0]["skillinfo"]

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    # ダメージロール
    yield from cmd.damage_spell(cmd.ctx.actor, cmd.skill_def, target)


# class attack_spell_area(CastSpellBattle):
"""全体攻撃魔法"""


def attack_spell_area(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """全体攻撃魔法"""
    # self._ctx.actor = self._ctx.self._ctx.actor

    # # コマンドパッケージから取得するスキル情報
    # self.skill_def = self.args[0]["skillinfo"]

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    for target in cmd._check_living_targets():
        # ダメージロール
        yield from cmd.damage_spell(cmd.ctx.actor, cmd.skill_def, target)


# class recover_spell_single(CastSpellBattle):
"""単体回復呪文"""


def recover_spell_single(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """単体回復呪文"""
    # self._ctx.actor = self._ctx.self._ctx.actor
    cmd.resolve_singletarget(cmd.local_allies)
    target = cmd.local_target

    # # コマンドパッケージから取得するスキル情報
    # self.skill_def = self.args[0]["skillinfo"]

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    # 回復ロール
    yield from cmd.recover_spell(cmd.ctx.actor, cmd.skill_def, target)


# class recover_spell_area(CastSpellBattle):
"""全体回復呪文"""


def recover_spell_area(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """全体回復呪文"""
    # self._ctx.actor = self._ctx.self._ctx.actor
    # self._resolve_singletarget(self.allies)

    # # コマンドパッケージから取得するスキル情報
    # self.skill_def = self.args[0]["skillinfo"]

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    # 回復ロール
    for target in cmd.local_allies:
        if target.is_alive:
            yield from cmd.recover_spell(cmd.ctx.actor, cmd.skill_def, target)


# #class attack_disrupt_undead(CastSpellBattle):
def attack_disrupt_undead(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """ターンアンデッド＋ダメージ"""
    # self._ctx.actor = self._ctx.self._ctx.actor

    # # コマンドパッケージから取得するスキル情報
    # self.skill_def = self.args[0]["skillinfo"]

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


# class debuff_dice_value(CastSpellBattle):
def debuff_dice_value(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """デバフ：ダイス値現象"""
    # self._ctx.actor = self._ctx.self._ctx.actor
    cmd.resolve_singletarget(cmd.local_targets)
    target = cmd.local_target

    # # コマンドパッケージから取得するスキル情報
    # self.skill_def = self.args[0]["skillinfo"]

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    yield from efx_skill_attack(cmd.display_info, target, cmd.skill_def.def_id)  # type: ignore
    # 抵抗ロール（弱点属性の場合は必中）
    if (
        target.calc_weak_rate(cmd.skill_def.skill_type) > 1.0
        or target.registroll(
            DebuffType.REDUCE_DICEVALUE, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc
        )
        is False
    ):
        target.activate_debuff(
            DebuffType.REDUCE_DICEVALUE, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc
        )
        yield [f"{target.param.name}は　苦痛の呪いを受けた・・・"]
    else:
        # di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
        yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
        yield [f"{target.param.name}は　効果をはねのけた！"]


# class debuff_continual_damage(CastSpellBattle):
def debuff_continual_damage(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """デバフ：継続ダメージ（毒）"""
    # self._ctx.actor = self._ctx.self._ctx.actor

    # # コマンドパッケージから取得するスキル情報
    # self.skill_def = self.args[0]["skillinfo"]

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    for target in cmd._check_living_targets():
        yield from efx_skill_attack(cmd.display_info, target, cmd.skill_def.def_id)  # type: ignore
        # 抵抗ロール（弱点属性の場合は必中）
        if (
            target.calc_weak_rate(cmd.skill_def.skill_type) > 1.0
            or target.registroll(
                DebuffType.POISON_DAMAGE, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc
            )
            is False
        ):
            target.activate_debuff(
                DebuffType.POISON_DAMAGE, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc
            )
            yield [f"{target.param.name}は　毒を浴びてしまった・・・"]
        else:
            # di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
            yield [f"{target.param.name}は　効果をはねのけた！"]


# class debuff_stone_statue(CastSpellBattle):
def debuff_stone_statue(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """デバフ：石化"""
    # self._ctx.actor = self._ctx.self._ctx.actor
    cmd.resolve_singletarget(cmd.local_targets)
    target = cmd.local_target

    # # コマンドパッケージから取得するスキル情報
    # self.skill_def = self.args[0]["skillinfo"]

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    yield from efx_skill_attack(cmd.display_info, target, cmd.skill_def.def_id)  # type: ignore
    # 抵抗ロール（弱点属性の場合は必中）
    if (
        target.calc_weak_rate(cmd.skill_def.skill_type) > 1.0
        or target.registroll(DebuffType.STONE_HOLD, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc)
        is False
    ):
        target.activate_debuff(DebuffType.STONE_HOLD, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc)
        yield [f"{target.param.name}は　石の像になった・・・"]
    else:
        # di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
        yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
        yield [f"{target.param.name}は　効果をはねのけた！"]


# class debuff_sleep(CastSpellBattle):
def debuff_sleep(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """デバフ：睡眠"""
    # self._ctx.actor = self._ctx.self._ctx.actor

    # # コマンドパッケージから取得するスキル情報
    # self.skill_def = self.args[0]["skillinfo"]

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    for target in cmd._check_living_targets():
        yield from efx_skill_attack(cmd.display_info, target, cmd.skill_def.def_id)  # type: ignore
        # 抵抗ロール（弱点属性の場合は必中）
        if (
            target.calc_weak_rate(cmd.skill_def.skill_type) > 1.0
            or target.registroll(DebuffType.FALL_ASLEEP, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc)
            is False
        ):
            target.activate_debuff(
                DebuffType.FALL_ASLEEP, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc
            )
            yield [f"{target.param.name}は　眠りにおちた・・・"]
        else:
            # di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
            yield [f"{target.param.name}は　効果をはねのけた！"]


# class debuff_cast_penalty(CastSpellBattle):
def debuff_cast_penalty(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """デバフ：詠唱妨害"""
    # self._ctx.actor = self._ctx.self._ctx.actor
    cmd.resolve_singletarget(cmd.local_targets)
    target = cmd.local_target

    # # コマンドパッケージから取得するスキル情報
    # self.skill_def = self.args[0]["skillinfo"]

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    # di.ref.sndmgr.play_se_sustain(SoundID.CAST_MIND)
    yield from efx_skill_attack(cmd.display_info, target, cmd.skill_def.def_id)  # type: ignore
    # 抵抗ロール（弱点属性の場合は必中）
    if (
        target.calc_weak_rate(cmd.skill_def.skill_type) > 1.0
        or target.registroll(DebuffType.DISTURB_MIND, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc)
        is False
    ):
        target.activate_debuff(DebuffType.DISTURB_MIND, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc)
        yield [f"{target.param.name}は　集中を乱された・・・"]
    else:
        # di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
        yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
        yield [f"{target.param.name}は　効果をはねのけた！"]


# class debuff_charm(CastSpellBattle):
def debuff_charm(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """デバフ：魅了"""
    # self._ctx.actor = self._ctx.self._ctx.actor
    cmd.resolve_singletarget(cmd.local_targets)
    target = cmd.local_target

    # # コマンドパッケージから取得するスキル情報
    # self.skill_def = self.args[0]["skillinfo"]

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    # di.ref.sndmgr.play_se_sustain(SoundID.CAST_MIND)
    yield from efx_skill_attack(cmd.display_info, target, cmd.skill_def.def_id)  # type: ignore
    # 抵抗ロール（弱点属性の場合は必中）
    if (
        target.calc_weak_rate(cmd.skill_def.skill_type) > 1.0
        or target.registroll(DebuffType.CHARM_PERSON, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc)
        is False
    ):
        target.activate_debuff(DebuffType.CHARM_PERSON, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc)
        yield [f"{target.param.name}は　魅了された・・・"]
    else:
        # di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
        yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
        yield [f"{target.param.name}は　効果をはねのけた！"]


# class attack_initiative_zero(CastSpellBattle):
def attack_initiative_zero(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """デバフ：イニシアチブ０＋ダメージ"""
    # self._ctx.actor = self._ctx.self._ctx.actor
    cmd.resolve_singletarget(cmd.local_targets)
    target = cmd.local_target

    # # コマンドパッケージから取得するスキル情報
    # self.skill_def = self.args[0]["skillinfo"]

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
            or target.registroll(
                DebuffType.INITIATIVE_ZERO, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc
            )
            is False
        ):
            target.activate_debuff(
                DebuffType.INITIATIVE_ZERO, cmd.skill_def.dc + cmd.ctx.actor.bonus_arc
            )
            yield [f"{target.param.name}は　吹っ飛ばされた！"]


# #class dispell_debuff(CastSpellBattle):
def dispell_debuff(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """デバフ解除"""
    # self._ctx.actor = self._ctx.self._ctx.actor
    cmd.resolve_singletarget(cmd.local_allies)
    target = cmd.local_target

    # # コマンドパッケージから取得するスキル情報
    # self.skill_def = self.args[0]["skillinfo"]

    # スキル共通処理
    result = yield from cmd.cast_spell(cmd.skill_def)
    if result is False:
        return

    target.clear_all_debuff()
    yield from efx_skill_attack(cmd.display_info, target, cmd.skill_def.def_id)  # type: ignore
    yield [f"{target.param.name}の状態異常は　消え去った！"]
