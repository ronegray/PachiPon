"""
エフェクト用ヘルパーコマンドモジュール
"""

import logging

from typing import Generator, TYPE_CHECKING
import pyxel as px
from const import SoundID, APP_FPS
from item import WeaponType
from skill import SkillID, SkillType
import service_locater as di
from . import DisplayInfo, CommandBaseSequence, SeqSubCmd

if TYPE_CHECKING:
    from entity import EntityBase

# ロギング設定
logger = logging.getLogger(__name__)


class CommonEffectWrapper(CommandBaseSequence):
    """汎用描画エフェクト呼び出しラッパー"""

    def _sequence(self) -> Generator[list, None, None]:
        func = self.kwargs["func"]
        params = self.kwargs.get("params", ())
        if func:
            yield from func(self.display_info, *params)


def efx_diceroll(disp_info: DisplayInfo, dices: int) -> Generator[list[str | int], None, int]:
    """コマンドジェネレータからダイスロールを実行する為のヘルパー関数"""
    effect = di.ref.efxdice

    effect.start(dices)
    yield [SeqSubCmd.SE_SUSTAIN, SoundID.DICE_RESULT]
    if not di.ref.conf.is_cutin_dice:
        effect.skip()
    while effect.is_rolling:
        effect.update()
        disp_info.graphic_command = effect.get_draw_commands()
        yield [SeqSubCmd.WAIT, 0]

    return effect.total


def efx_physical_attack(
    disp_info: DisplayInfo, target: "EntityBase", weapon_type: WeaponType
) -> Generator[list[str | int], None, None]:
    """物理攻撃エフェクト"""
    match weapon_type:
        case WeaponType.NONE | WeaponType.BASH:
            attackse_id = SoundID.BASH
        case WeaponType.CHOP | WeaponType.FULL:
            attackse_id = SoundID.CHOP
        case WeaponType.STUB:
            attackse_id = SoundID.STUB
    effect = di.ref.efxrps
    effect_data = effect.get_efx(weapon_type)

    yield [SeqSubCmd.SE_SUSTAIN, attackse_id]
    yield []
    duration = 0
    efx_index = 0
    img_size = di.ref.efxrps.efx_img_size
    while True:
        efx_frames = effect_data[1][efx_index]
        disp_info.graphic_command = [
            lambda i=efx_index: px.blt(
                target.sprite.x + (target.sprite.w - img_size) // 2,
                target.sprite.y + (target.sprite.h - img_size) // 2,
                effect_data[0],
                i * img_size,
                0,
                img_size,
                img_size,
                colkey=px.COLOR_BLACK,
            )
        ]
        duration += 1
        if duration >= efx_frames:
            efx_index += 1
            if efx_index >= len(effect_data[1]):
                break
            duration = 0
        yield [SeqSubCmd.WAIT, 0]

    disp_info.graphic_command = None
    return


def efx_skill_attack(
    disp_info: DisplayInfo, target: "EntityBase", skill_id: SkillID
) -> Generator[list[str | int], None, None]:
    """スキルエフェクト"""
    skill_def = di.ref.sklrps.get_def(skill_id)
    if skill_def is None:
        raise ValueError(f"スキルIDが未定義です {skill_id}")
    match skill_def.skill_type:
        case SkillType.SACRED:
            se_id = SoundID.CAST_SACRED
        case SkillType.CURSE:
            se_id = SoundID.CAST_CURSE
        case SkillType.FIRE:
            se_id = SoundID.CAST_FIRE
        case SkillType.ICE:
            se_id = SoundID.CAST_ICE
        case SkillType.BOLT:
            se_id = SoundID.CAST_BOLT
        case SkillType.MIND:
            se_id = SoundID.CAST_MIND
        case SkillType.SHOCK:
            se_id = SoundID.CAST_SHOCK
        case SkillType.LIGHT:
            se_id = SoundID.CAST_LIGHT
        case _:
            se_id = SoundID.MAGIC_FAIL
    effect = di.ref.efxrps
    effect_data = effect.get_efx(skill_id)

    yield [SeqSubCmd.SE_SUSTAIN, se_id]
    effect_data = di.ref.efxrps.get_efx(skill_id)

    duration = 0
    efx_index = 0
    img_size = di.ref.efxrps.efx_img_size
    while True:
        efx_frames = effect_data[1][efx_index]
        disp_info.graphic_command = [
            lambda i=efx_index: px.blt(
                target.sprite.x + (target.sprite.w - img_size) // 2,
                target.sprite.y + (target.sprite.h - img_size) // 2,
                effect_data[0],
                i * img_size,
                0,
                img_size,
                img_size,
                colkey=px.COLOR_BLACK,
            )
        ]
        duration += 1
        if duration >= efx_frames:
            efx_index += 1
            if efx_index >= len(effect_data[1]):
                break
            duration = 0
        yield [SeqSubCmd.WAIT, 0]

    disp_info.graphic_command = None
    return


def efx_damage_shake(disp_info: DisplayInfo, target: "EntityBase") -> Generator[list[str | int], None, None]:
    """被ダメージ時の振動"""
    is_player = True if target.chara_id < 10 else False

    # エフェクト音も敵味方で異なる
    if is_player:
        yield [SeqSubCmd.SE_INSTANT, SoundID.DAMAGE_TAKEN]
    else:
        yield [SeqSubCmd.SE_INSTANT, SoundID.DAMAGE_GIVEN]
    tgt_sprite_addr_x = target.sprite.x
    tgt_sprite_addr_y = target.sprite.y
    for i in range(APP_FPS // 4):
        offset_x = px.rndi(-4, 4)
        offset_y = px.rndi(-4, 4)
        if is_player:
            disp_info.graphic_command = [
                lambda x=offset_x, y=offset_y: px.camera(x, y),
            ]
        else:
            target.sprite.x = tgt_sprite_addr_x + offset_x
            target.sprite.y = tgt_sprite_addr_y + offset_y
        yield [SeqSubCmd.WAIT, 0]
    px.camera(0, 0)
    target.sprite.x = tgt_sprite_addr_x
    target.sprite.y = tgt_sprite_addr_y

    disp_info.graphic_command = None
    return


def efx_monster_dead(
    disp_info: DisplayInfo,
    target: "EntityBase",
) -> Generator[list[str | int], None, None]:
    """死亡モンスターグラフィックの消滅処理"""
    yield [SeqSubCmd.SE_SUSTAIN, SoundID.ENEMY_DEATH]
    dither_lvl = 1
    while True:
        disp_info.graphic_command = [
            lambda lvl=dither_lvl: px.dither(lvl),
            lambda tgt=target: tgt.sprite.draw(),
            lambda: px.dither(1),
        ]
        yield [SeqSubCmd.WAIT, 0]
        dither_lvl -= 0.05
        if dither_lvl <= 0:
            break

    disp_info.graphic_command = None
    return


def efx_encount_splash(disp_info: DisplayInfo) -> Generator[list, None, None]:
    """エンカウント時の画面エフェクト"""
    circle_size = 1
    circle_center = (px.width // 2, px.height // 2)
    circle_max = px.sqrt(circle_center[0] ** 2 + circle_center[1] ** 2)

    yield [SeqSubCmd.SE_SUSTAIN, SoundID.ENCOUNT]
    while True:
        disp_info.graphic_command = [
            lambda cs=circle_size, cm=circle_max: px.dither(cs / cm),
            lambda cs=circle_size: px.circ(*circle_center, cs, px.COLOR_BLACK),
            lambda: px.dither(1),
        ]
        if circle_size > circle_max:
            break
        circle_size += 6
        yield [SeqSubCmd.WAIT, 0]

    disp_info.graphic_command = None
    return


def efx_screen_flash(disp_info: DisplayInfo, flash_color: int, flash_frames: int = 1) -> Generator[list, None, None]:
    """画面のフラッシュ"""
    disp_info.graphic_command = [
        lambda: px.dither(0.6),
        lambda: px.rect(0, 0, px.width, px.height, flash_color),
        lambda: px.dither(1),
    ]
    while flash_frames > 0:
        yield [SeqSubCmd.WAIT, 0]
        flash_frames -= 1

    disp_info.graphic_command = None
    return
