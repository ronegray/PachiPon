"""
エフェクトコマンドモジュール
"""

import logging

from typing import Generator
import pyxel as px
from const import SoundID, APP_FPS
from item import WeaponType
from skill import SkillID, SkillType
from entity import EntityBase, Enemy
import service_locater as di
from . import DisplayInfo


# ロギング設定
logger = logging.getLogger(__name__)


def efx_diceroll(disp_info: DisplayInfo, dices: int) -> Generator[list[str | int], None, int]:
    """コマンドジェネレータからダイスロールを実行する為のヘルパー関数"""
    # effect = DiceRollEffect()
    # effect.load_diceimage()
    effect = di.ref.efxdice
    effect.start(dices)
    # se_ch = 3
    # px.play(se_ch, SoundID.DICE_ROLL, resume=True)
    di.ref.sndmgr.play_se_sustain(SoundID.DICE_RESULT)
    if not di.ref.conf.is_cutin_dice:
        effect.skip()
        # disp_info.graphic_command = effect.get_draw_commands()
    while effect.is_rolling:
        effect.update()
        disp_info.graphic_command = effect.get_draw_commands()
        yield ["wait", "0"]
    # disp_info.graphic_command = None # ダイス結果を残せるようにコマンド初期化をOFF
    # effect = None
    return effect.total


def efx_physical_attack(
    disp_info: DisplayInfo, target: EntityBase, weapon_type: WeaponType
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

    di.ref.sndmgr.play_se_sustain(attackse_id)
    # offset = 0
    # # while not di.ref.sndmgr.wait_se_fin():
    #     disp_info.graphic_command = [lambda: px.rect(target.sprite.x+offset,target.sprite.y+offset,4,4,px.COLOR_RED)]
    #     offset+=4
    #     yield ["wait", 0]
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
        # logger.debug(f"{weapon_type} {duration} {efx_index}")
        yield ["wait", "0"]

    disp_info.graphic_command = None
    return


def efx_skill_attack(
    disp_info: DisplayInfo, target: EntityBase, skill_id: SkillID
) -> Generator[list[str | int], None, None]:
    """毒ダメージエフェクト"""
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

    di.ref.sndmgr.play_se_sustain(se_id)
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
        # logger.debug(f"{weapon_type} {duration} {efx_index}")
        yield ["wait", "0"]

    disp_info.graphic_command = None
    return


def efx_damage_shake(
    disp_info: DisplayInfo, target: EntityBase
) -> Generator[list[str | int], None, None]:
    """被ダメージ時の振動"""
    # エフェクト音も敵味方で異なる
    if isinstance(target, Enemy):
        di.ref.sndmgr.play_se_sustain(SoundID.DAMAGE_GIVEN)
    else:
        di.ref.sndmgr.play_se_sustain(SoundID.DAMAGE_TAKEN)
    tgt_sprite_addr_x = target.sprite.x
    tgt_sprite_addr_y = target.sprite.y
    for i in range(APP_FPS // 4):
        offset_x = px.rndi(-4, 4)
        offset_y = px.rndi(-4, 4)
        if isinstance(target, Enemy):
            target.sprite.x = tgt_sprite_addr_x + offset_x
            target.sprite.y = tgt_sprite_addr_y + offset_y
        else:
            disp_info.graphic_command = [
                lambda x=offset_x, y=offset_y: px.camera(x, y),
                lambda: px.camera(0, 0),
            ]
        yield ["wait", "0"]
    px.camera(0, 0)
    target.sprite.x = tgt_sprite_addr_x
    target.sprite.y = tgt_sprite_addr_y


def efx_monster_dead(
    disp_info: DisplayInfo, target: Enemy
) -> Generator[list[str | int], None, None]:
    """死亡モンスターグラフィックの消滅処理"""
    di.ref.sndmgr.play_se_sustain(SoundID.ENEMY_DEATH)
    dither_lvl = 1
    while True:
        disp_info.graphic_command = [
            lambda lvl=dither_lvl: px.dither(lvl),
            lambda tgt=target: tgt.sprite.draw(),
            lambda: px.dither(1),
        ]
        yield ["wait", "0"]
        dither_lvl -= 0.05
        if dither_lvl <= 0:
            break

    disp_info.graphic_command = None
    return
