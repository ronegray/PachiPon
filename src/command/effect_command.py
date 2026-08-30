"""
エフェクトコマンドモジュール
"""

import logging

from typing import Generator
import pyxel as px
from const import SoundID
from item import WeaponType
from entity import EntityBase
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
    di.ref.sndmgr.play_se_sustain(SoundID.DICE_ROLL)
    if not di.ref.conf.is_cutin_dice:
        effect.skip()
        disp_info.graphic_command = effect.get_draw_commands()
    while effect.is_rolling:
        effect.update()
        disp_info.graphic_command = effect.get_draw_commands()
        yield ["wait", "0"]
    disp_info.graphic_command = None
    # effect = None
    return effect.total


def efx_physical_attack(
    disp_info: DisplayInfo, target: EntityBase, weapon_type: WeaponType
) -> Generator[list[str | int], None, None]:
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
    while True:
        efx_frames = effect_data[1][efx_index]
        disp_info.graphic_command = [
            lambda: px.blt(
                target.sprite.x + 8,
                target.sprite.y + 8,
                effect_data[0],
                efx_index * di.ref.efxrps._efx_size,
                0,
                di.ref.efxrps._efx_size,
                di.ref.efxrps._efx_size,
                colkey=px.COLOR_BLACK,
            )
        ]
        duration += 1
        if duration >= efx_frames:
            efx_index += 1
            if efx_index >= len(effect_data[1]):
                break
            duration = 0
        logger.debug(weapon_type, duration, efx_index)
        yield ["wait", "0"]

    disp_info.graphic_command = None
    return
