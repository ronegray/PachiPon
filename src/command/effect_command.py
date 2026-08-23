"""
エフェクトコマンドモジュール
"""

import logging

# import pyxel as px
from const import SoundID
from typing import Generator
import service_locater as di
from . import DisplayInfo


# ロギング設定
logger = logging.getLogger(__name__)


def efx_diceroll(
    disp_info: DisplayInfo, dices: int
) -> Generator[list[str | int], None, int]:
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
