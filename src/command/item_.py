"""
アイテム用ヘルパーコマンドモジュール
"""
# import logging
import sys
from typing import Generator, Callable  # , TYPE_CHECKING, cast
from dataclasses import dataclass, field
from const import SoundID
from helper import upper_int, diceroll
import service_locater as di
from . import SeqSubCmd, CommandBaseAction
from item import ItemDef
# if TYPE_CHECKING:
# from entity import Character
# from item import  StackPool


@dataclass
class item_info_package:
    """アイテム利用時の情報引き渡しパッケージ"""

    command: CommandBaseAction
    item_def: ItemDef
    consume: Callable  # [[], None]
    pre_effects: list[Callable[[], Generator[list, None, None]]] = field(default_factory=list)  # yield を伴う後処理
    after_effects: list[Callable[[], Generator[list, None, None]]] = field(default_factory=list)  # yield を伴う後処理


def use_item(pkg: item_info_package) -> Generator[list, None, None]:
    """アイテム使用共通処理"""
    effect_func = getattr(sys.modules[__name__], pkg.item_def.effect_id)

    yield from effect_func(pkg.command)

    pkg.consume()

    if pkg.after_effects:
        for efx in pkg.after_effects:
            yield from efx()
    return


def potion_hp(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """HP回復アイテム"""

    # ファーストメッセージ
    yield [
        f"{cmd.ctx.actor.param.name}は　{cmd.local_target.param.name}に",
        f"　{cmd.item_def.name} を 使用した",
    ]

    # 回復ロール
    if cmd.item_def.effect_value:
        healing = cmd.local_target.param.max_hp
    else:
        healing = diceroll(cmd.ctx.actor.param.level)

    # 回復量計算
    real_heal = cmd.local_target.increase_hp(healing)
    yield [SeqSubCmd.SE_SUSTAIN, SoundID.RECOVER]
    yield [f"{cmd.local_target.param.name}は {upper_int(real_heal)} のＨＰが　回復した"]


def potion_mp(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """MP回復アイテム"""

    # ファーストメッセージ
    yield [
        f"{cmd.ctx.actor.param.name}は　{cmd.local_target.param.name}に",
        f"　{cmd.item_def.name} を 使用した",
    ]

    # 回復ロール
    if cmd.item_def.effect_value:
        healing = cmd.local_target.param.max_mp
    else:
        healing = diceroll(cmd.ctx.actor.param.level) // 2

    if cmd.ctx.situation == "battle":
        yield [""]

    # run_effectに相当：メッセージ表示後にダメージ適用
    real_heal = cmd.local_target.increase_mp(healing)
    # px.play(self.se_ch, SoundID.RECOVER, resume=True)
    # di.ref.sndmgr.play_se_sustain(SoundID.RECOVER)
    yield [SeqSubCmd.SE_SUSTAIN, SoundID.RECOVER]
    yield [f"{cmd.local_target.param.name}は {upper_int(real_heal)} のＭＰが　回復した"]


# class torchlight(CommandBaseItem):
#     """たいまつ"""


def torchlight(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """たいまつ"""

    # ファーストメッセージ
    yield [f"{cmd.item_def.name} を 使用した", " "]

    # # アイテム消費
    # pl_stack = cast(StackPool, cmd.args[0]["pl_stack"])
    # pl_stack.remove(cmd.item_def.def_id)

    # PT単位効果付与
    di.ref.pt.set_pt_efx(cmd.item_def.effect_id)
    # di.ref.sndmgr.play_se_sustain(SoundID.USEITEM)
    yield [SeqSubCmd.SE_SUSTAIN, SoundID.USEITEM]
    yield [
        "パーティはダンジョン探索が可能になった",
        "ダンジョンのイベントポイントでイベント実行できます",
        f"一度実行すると{cmd.item_def.name}の効果は消失します",
    ]

    # キー待ち
    yield from cmd.wait_finish()


def unlock_key(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """鍵"""

    # ファーストメッセージ
    yield [f"{cmd.item_def.name} を 使用した", " "]

    # # アイテム消費
    # pl_stack = cast(StackPool, cmd.args[0]["pl_stack"])
    # pl_stack.remove(cmd.item_def.def_id)

    return
    # PT単位効果付与
    di.ref.pt.set_pt_efx(cmd.item_def.effect_id)
    # di.ref.sndmgr.play_se_sustain(SoundID.USEITEM)
    yield [SeqSubCmd.SE_SUSTAIN, SoundID.USEITEM]
    yield [
        "パーティはダンジョン探索が可能になった",
        "ダンジョンのイベントポイントでイベント実行できます",
        f"一度実行すると{cmd.item_def.name}の効果は消失します",
    ]

    # キー待ち
    yield from cmd.wait_finish()


# class escape_battle(CommandBaseItem):
#     """戦闘離脱"""


def escape_battle(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """戦闘離脱"""

    # # アイテム消費
    # if cmd._ctx.situation == "battle":
    #     cmd.consume_item()
    # else:
    #     pl_stack = cast(StackPool, cmd.args[0]["pl_stack"])
    #     # pl_stack.remove(item_def.def_id, ItemState.BAG, 1)
    #     pl_stack.remove(cmd.item_def.def_id)

    # PT単位効果付与
    di.ref.pt.set_pt_efx(cmd.item_def.effect_id)
    # di.ref.sndmgr.play_se_sustain(SoundID.USEITEM)
    yield [SeqSubCmd.SE_SUSTAIN, SoundID.USEITEM]
    if cmd.ctx.situation == "battle":
        yield ["ドロン！戦闘から離脱した！"]
        return
    else:
        yield [
            "パーティは次のエンカウント時に",
            f"{cmd.item_def.name}の効果で戦闘を回避します",
            f"一度エンカウントすると{cmd.item_def.name}の効果は消失します",
        ]

    # # run_effectに相当：メッセージ表示後にダメージ適用
    # real_heal = target.increase_mp(healing)
    # # px.play(self.se_ch, SoundID.RECOVER, resume=True)
    # di.ref.sndmgr.play_se_sustain(SoundID.RECOVER)
    # yield [f"{target.param.name}は {upper_int(real_heal)} のＭＰが　回復した"]

    # キー待ち
    yield from cmd.wait_finish()


# class reduce_negative(CommandBaseItem):
#     """マイナス選択肢でダイス振り直し"""


def reduce_negative(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """マイナス選択肢でダイス振り直し"""

    # ファーストメッセージ
    yield [f"{cmd.item_def.name} を 使用した", " "]

    # # アイテム消費
    # pl_stack = cast(StackPool, cmd.args[0]["pl_stack"])
    # pl_stack.remove(cmd.item_def.def_id)

    # PT単位効果付与
    di.ref.pt.set_pt_efx(cmd.item_def.effect_id + str(cmd.item_def.effect_value))
    # di.ref.sndmgr.play_se_sustain(SoundID.USEITEM)
    yield [SeqSubCmd.SE_SUSTAIN, SoundID.USEITEM]
    yield [
        "次に発生するランダムイベントの候補から",
        f"{upper_int(int(cmd.item_def.effect_value))}個のマイナス選択肢を除外します",
        f"一度実行すると{cmd.item_def.name}の効果は消失します",
    ]

    # キー待ち
    yield from cmd.wait_finish()


# class dice_plus(CommandBaseItem):
#     """ダイスロール時のダイスをプラス"""


def dice_plus(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """ダイスロール時のダイスをプラス"""

    # ファーストメッセージ
    yield [f"{cmd.item_def.name} を 使用した", " "]

    # # アイテム消費
    # pl_stack = cast(StackPool, cmd.args[0]["pl_stack"])
    # pl_stack.remove(cmd.item_def.def_id)

    # PT単位効果付与
    di.ref.pt.set_pt_efx(cmd.item_def.effect_id + str(cmd.item_def.effect_value))
    # di.ref.sndmgr.play_se_sustain(SoundID.USEITEM)
    yield [SeqSubCmd.SE_SUSTAIN, SoundID.USEITEM]
    yield [
        "次に行うダイスロール時に、一度だけ",
        f"ダイスを{upper_int(int(cmd.item_def.effect_value))}個追加します",
        f"一度実行すると{cmd.item_def.name}の効果は消失します",
    ]

    # キー待ち
    yield from cmd.wait_finish()


# class food_plus(CommandBaseItem):
#     """食糧を追加"""


def food_plus(cmd: CommandBaseAction) -> Generator[list, None, None]:
    """食糧を追加"""

    # ファーストメッセージ
    yield [f"{cmd.item_def.name} を 使用した", " "]

    # # アイテム消費
    # pl_stack = cast(StackPool, cmd.args[0]["pl_stack"])
    # pl_stack.remove(cmd.item_def.def_id)

    # PT単位効果付与
    val = int(cmd.item_def.effect_value)
    di.ref.pt.earn_foods(val)
    # di.ref.sndmgr.play_se_sustain(SoundID.USEITEM)
    yield [SeqSubCmd.SE_SUSTAIN, SoundID.USEITEM]
    yield [f"食糧が{val}増えた！"]

    # キー待ち
    yield from cmd.wait_finish()
