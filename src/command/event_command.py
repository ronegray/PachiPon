"""
イベントコマンドモジュール
"""

import logging
import sys
from random import choice
from typing import Generator, Callable  # , cast

# from dataclasses import dataclass, field
import pyxel as px
import service_locater as di
from gameutils.lib import WindowAction, Menu, Window, MENU_WINDOW_TYPE
from const import SoundID
from helper import diceroll, upper_int_spaced, format_leftright

# from helper import diceroll_values
# import service_locater as di
from flag import FlagID
from item import ItemID

# from entity import Party
from event import Event, EventID, EventType
from field_map import EventPoint
from . import CommandBaseEntity, SeqSubCmd, CommandBaseSequence

# ロギング設定
logger = logging.getLogger(__name__)


# class CommandBaseEvent(CommandBaseSequence):
#     """イベントシーン専用コマンドの基底クラス"""

#     # def _wait_finish(self) -> Generator[list, None, None]:
#     #     """イベント終了時のキー待ち処理"""
#     #     self.display_info.target.update_indicator(True)
#     #     while self.display_info.target.update() == WindowAction.CONTINUE:
#     #         yield [SeqSubCmd.WAIT, 0]
#     #     # self.display_info.target.update_indicator(False)
#     #     return


# # #class attack_spell_single(CastSpellBattle):
# #     """単体攻撃魔法"""
# @dataclass
# class event_info_package:
#     """イベント実行時の情報引き渡しパッケージ"""

#     command: CommandBaseSequence
#     event_type: EventType
#     event_id: EventID
#     pre_effects: list[Callable[[], Generator[list, None, None]]] = field(
#         default_factory=list
#     )  # yield を伴う後処理
#     after_effects: list[Callable[[], Generator[list, None, None]]] = field(
#         default_factory=list
#     )  # yield を伴う後処理


# def flow_event(pkg: event_info_package) -> Generator[list, None, None]:
#     """イベント実行共通処理"""
#     effect_func = getattr(sys.modules[__name__], pkg.skill_def.effect_func)

#     yield from effect_func(pkg.command)

#     yield from pkg.command.wait_finish()
#     return


class PlayEvent(CommandBaseEntity):
    """イベント用共通クラス"""

    def _sequence(self) -> Generator[list, None, None]:
        """アイテム利用の殻"""
        # self.item_def: ItemDef = self.kwargs["sel_cmd_dict"]["item_def"]
        # pl_stack: StackPool = self.kwargs["sel_cmd_dict"]["source"]

        # from command.item_ import item_info_package, use_item
        # from command.effect_command import efx_screen_flash

        # yield from flow_event(
        #     event_info_package(
        #         command=self,
        #         item_def=self.item_def,
        #         consume=lambda: pl_stack.remove(self.item_def.def_id),
        #         after_effects=[lambda dsp=self.display_info: efx_screen_flash(dsp, px.COLOR_WHITE)],
        #     )
        # )
        event_point: EventPoint = self.kwargs["event_point"]
        self.event: Event = event_point.nextevent  # type: ignore
        event_func = getattr(sys.modules[__name__], self.event.event_id.name.lower())  # type: ignore
        # event_func = getattr(sys.modules[__name__], "FLGEVENT1_A".lower())

        if self.event.event_value:
            """メッセージ＋効果の場合は先にメッセージ処理
            効果とメッセージが前後するもの(event_value=0)は効果関数内でメッセージ処理呼び出し"""
            # for msg in self.event.event_messages:
            #     yield [msg]
            yield from self.play_event_message()

        # イベント個別の処理実行
        yield from event_func(self)

        yield from self.wait_finish()
        return

    def play_event_message(self) -> Generator[list, None, None]:
        """メッセージ処理"""
        for msg in self.event.event_messages:
            yield [msg]


# class KickEvent(CommandBaseSequence):
#     """フィールドイベント起動処理"""

#     def _sequence(self) -> Generator[list, None, None]:
#         # point = cast(EventPoint, self.args[0])
#         # dices = point.kick_event()
#         # final_value = diceroll_values(dices)
#         # final_value = [1 for _ in range(dices)]
#         current_point: EventPoint = self.kwargs["current_point"]
#         current_point.kick_event()

#         # 固定イベントポイントの場合
#         fixed = current_point.check_fixedevent()
#         if fixed:
#             current_point.rise_event(fixed)
#             return

#         # 算出済ダイス値の取得
#         dices, final_value = current_point.get_event_dice_values()
#         # アイテムボーナス（ダイス数追加）
#         dice_plus = di.ref.pt.pt_dice_plus()
#         dices += dice_plus
#         final_value += [diceroll(1) for _ in range(dice_plus)]

#         effect = di.ref.efxdice
#         roll_frames = 60
#         yield ["何が起こるか", "　おたのしみ！"]
#         effect.start(dices, roll_frames, final_value)
#         if not di.ref.conf.is_cutin_dice:
#             effect.skip()
#             self.display_info.graphic_command = effect.get_draw_commands()
#         while effect.is_rolling:
#             effect.update()
#             self.display_info.graphic_command = effect.get_draw_commands()
#             yield [SeqSubCmd.WAIT, 0]
#         yield [f"出た目は・・・　{effect.total}"]

#         yield from self._wait_finish()

#         # イベントが全てオープンになるまで、同じイベントは再実行されない
#         eventlist = {
#             event_id: event_stat
#             for event_id, event_stat in current_point.event_list.event_stat.items()
#             if event_stat.is_opened is False
#         }
#         # マイナスイベント抑止時
#         if di.ref.pt.get_pt_efx("reduce_negative1") or di.ref.pt.get_pt_efx("reduce_negative2"):
#             negative_list = [
#                 event_id
#                 for event_id in eventlist
#                 if event_id
#                 in (
#                     EventID.DECREASE_HP,  # HP減
#                     EventID.DECREASE_MP,  # MP減
#                     EventID.DECREASE_GOLD,  # おかね減
#                     EventID.DECREASE_FOOD,  # 食糧減
#                     EventID.LOST_POTION,  # 低級消耗品減
#                     EventID.SURPRISE_BATTLE,  # 強制戦闘
#                     EventID.LOST_HIPOTION,  # 高級消耗品減
#                 )
#             ]
#             reduce_negative = di.ref.pt.pt_reduce_negative(negative_list)
#             for event_id in reduce_negative:
#                 eventlist.pop(event_id)
#         # 対象が一つもなくなったら全ランダム
#         if len(eventlist) < 1:
#             eventlist = current_point.event_list.event_stat
#         # 候補内の閾値超えイベントが実際の発生対象
#         # for event_id, event_stat in point.event_list.event_stat.items():
#         for event_id, event_stat in eventlist.items():
#             if effect.total >= event_stat.threshold:
#                 event_stat.is_opened = True
#                 current_point.rise_event(event_id)
#                 break

#     # good


def increase_hp(cmd: PlayEvent) -> Generator[list, None, None]:
    """HP回復イベント"""
    # for msg in cmd.event.event_messages:
    #     yield [msg]

    yield [SeqSubCmd.SE_INSTANT, SoundID.RECOVER]
    for mem in cmd.ctx.allies:
        recover = diceroll(cmd.event.event_value)
        mem.increase_hp(recover)
        yield [f"{mem.param.name}のＨＰが{recover}回復した"]

    # yield from cmd.wait_finish()


# class SAFETY_INCREASE_HP(CommandBaseSequence):
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]
#             # match i:
#             #     case 1:
#             #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
#             #     case 3:
#             #         di.ref.sndmgr.play_se_instant(SoundID.RECOVER)

#         for mem in _cntx.allies:
#             recover = diceroll(event.event_value)
#             mem.increase_hp(recover)
#             yield [f"{mem.param.name}のＨＰが{recover}回復した"]

#         # self.display_info.target.update_indicator(True)
#         # while self.display_info.target.update() == WindowAction.CONTINUE:
#         #     yield [SeqSubCmd.WAIT, 0]
#         # self.display_info.target.update_indicator(False)
#         yield from self.wait_finish()


# class NORMAL_INCREASE_HP(CommandBaseSequence):  # HP増
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


# class GAMBLE_INCREASE_HP(CommandBaseSequence):  # HP増
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


def increase_mp(cmd: PlayEvent) -> Generator[list, None, None]:
    """MP回復イベント"""
    # for msg in cmd.event.event_messages:
    #     yield [msg]

    yield [SeqSubCmd.SE_INSTANT, SoundID.RECOVER]
    for mem in cmd.ctx.allies:
        recover = diceroll(cmd.event.event_value)
        mem.increase_mp(recover)
        yield [f"{mem.param.name}のＭＰが{recover}回復した"]


# class SAFETY_INCREASE_MP(CommandBaseSequence):  # MP増
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]
#             # match i:
#             #     case 1:
#             #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
#             #     case 3:
#             #         di.ref.sndmgr.play_se_instant(SoundID.RECOVER)

#         for mem in _cntx.allies:
#             recover = diceroll(event.event_value)
#             mem.increase_mp(recover)
#             yield [f"{mem.param.name}のＭＰが{recover}回復した"]

#         yield from self.wait_finish()


# class NORMAL_INCREASE_MP(CommandBaseSequence):  # MP増
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


# class GAMBLE_INCREASE_MP(CommandBaseSequence):  # MP増
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


def increase_gold(cmd: PlayEvent) -> Generator[list, None, None]:
    """集金イベント"""

    # for msg in cmd.event.event_messages:
    #     yield [msg]

    gets = diceroll(cmd.event.event_value)
    yield [SeqSubCmd.SE_INSTANT, SoundID.ITEM_GET]
    di.ref.pt.earn_gold(gets)
    yield [f"パーティは{gets}のお金を手に入れた"]


# class SAFETY_INCREASE_GOLD(CommandBaseSequence):  # おかね増
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         party = cast(Party, self.args[2])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]
#             # match i:
#             #     case 3:
#             #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
#             #     case 4:
#             #         di.ref.sndmgr.play_se_instant(SoundID.ITEM_GET)

#         gets = diceroll(event.event_value)
#         party.earn_gold(gets)
#         yield [f"パーティは{gets}のお金を手に入れた"]

#         yield from self.wait_finish()


# class NORMAL_INCREASE_GOLD(CommandBaseSequence):  # おかね増
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


# class GAMBLE_INCREASE_GOLD(CommandBaseSequence):  # おかね増
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


def increase_food(cmd: PlayEvent) -> Generator[list, None, None]:
    """収穫イベント"""

    gets = diceroll(cmd.event.event_value)
    yield [SeqSubCmd.SE_INSTANT, SoundID.ITEM_GET]
    di.ref.pt.earn_foods(gets)
    yield [f"パーティは{gets}の食料を手に入れた"]


# class SAFETY_INCREASE_FOOD(CommandBaseSequence):  # 食糧増
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         party = cast(Party, self.args[2])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]
#             # match i:
#             #     case 2:
#             #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
#             #     case 4:
#             #         di.ref.sndmgr.play_se_instant(SoundID.ITEM_GET)

#         gets = diceroll(event.event_value)
#         party.earn_foods(gets)
#         yield [f"パーティは{gets}の食料を手に入れた"]

#         yield from self.wait_finish()


# class NORMAL_INCREASE_FOOD(CommandBaseSequence):  # 食糧増
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


# class GAMBLE_INCREASE_FOOD(CommandBaseSequence):  # 食糧増
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


def flag_event_flow(
    cmd: PlayEvent, flag: FlagID, item_id: ItemID, requires: list[FlagID] = [], recover_func: Callable | None = None
) -> Generator[list, None, None]:
    """フラグイベント処理フロー"""
    condition = False
    if di.ref.flgmgr.check_all(set(requires)) or not requires:
        condition = True

    if di.ref.flgmgr.is_set(flag):
        if recover_func:
            yield from recover_func(cmd)
        else:
            yield ["もうここには　なにもない"]
    elif condition:
        yield from cmd.play_event_message()

        yield [SeqSubCmd.SE_SUSTAIN, SoundID.FANFALE]
        while di.ref.sndmgr.wait_se_fin() is False:
            pass
        item_def = di.ref.pt.get_item(item_id)
        di.ref.flgmgr.set_flag(flag)
        yield [f"{item_def.name}を手に入れた"]
    else:
        item_def_a = di.ref.itemrps.get_def(ItemID[requires[0].name])
        item_def_b = di.ref.itemrps.get_def(ItemID[requires[1].name])
        yield [f"{item_def_a.name}と{item_def_b.name}を", "手に入れたのち、再び訪れるがよい"]


# class SAFETY_FLGEVENT1_A(CommandBaseSequence):  # フラグイベントStep1

# if di.ref.flgmgr.is_set(FlagID.JADEEYE):
#     yield ["もうここには　なにもない"]
# else:
#     event = cast(Event, self.args[1])
#     for i, msg in enumerate(event.event_messages):
#         yield [msg]
#         # match i:
#         #     case 4:
#         #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
#         #     case 9:
#         #         di.ref.sndmgr.play_se_instant(SoundID.ITEM_GET)

#     pl_item = di.ref.pl_item.create(ItemID.JADEEYE)
#     item_def = di.ref.itemrps.get_def(pl_item[1].ins.param.def_id)
#     di.ref.flgmgr.set_flag(FlagID.JADEEYE)
#     yield [f"{item_def.name}を手に入れた"]  # type: ignore


# yield from self.wait_finish()
def flgevent1_a(self) -> Generator[list, None, None]:
    yield from flag_event_flow(self, FlagID.JADEEYE, ItemID.JADEEYE)


# class SAFETY_FLGEVENT1_B(CommandBaseSequence):  # フラグイベントStep1
#     def _sequence(self) -> Generator[list, None, None]:
#         if di.ref.flgmgr.is_set(FlagID.CROSS):
#             yield ["もうここには　なにもない"]
#         else:
#             event = cast(Event, self.args[1])
#             for i, msg in enumerate(event.event_messages):
#                 yield [msg]
#                 # match i:
#                 #     case 4:
#                 #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
#                 #     case 9:
#                 #         di.ref.sndmgr.play_se_instant(SoundID.ITEM_GET)

#             pl_item = di.ref.pl_item.create(ItemID.CROSS)
#             item_def = di.ref.itemrps.get_def(pl_item[1].ins.param.def_id)
#             di.ref.flgmgr.set_flag(FlagID.CROSS)
#             yield [f"{item_def.name}を手に入れた"]  # type: ignore

#         yield from self.wait_finish()


def flgevent1_b(self) -> Generator[list, None, None]:
    yield from flag_event_flow(self, FlagID.CROSS, ItemID.CROSS)


# class SAFETY_FLGEVENT1_C(CommandBaseSequence):  # フラグイベントStep1
#     def _sequence(self) -> Generator[list, None, None]:
#         if di.ref.flgmgr.is_set(FlagID.CRYSTALROD):
#             yield ["もうここには　なにもない"]
#         else:
#             event = cast(Event, self.args[1])
#             for i, msg in enumerate(event.event_messages):
#                 yield [msg]
#                 # match i:
#                 #     case 4:
#                 #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
#                 #     case 9:
#                 #         di.ref.sndmgr.play_se_instant(SoundID.ITEM_GET)

#             pl_item = di.ref.pl_item.create(ItemID.CRYSTALROD)
#             item_def = di.ref.itemrps.get_def(pl_item[1].ins.param.def_id)
#             di.ref.flgmgr.set_flag(FlagID.CRYSTALROD)
#             yield [f"{item_def.name}を手に入れた"]  # type: ignore

#         yield from self.wait_finish()


def flgevent1_c(self) -> Generator[list, None, None]:
    yield from flag_event_flow(self, FlagID.CRYSTALROD, ItemID.CRYSTALROD)


def get_potion(cmd: PlayEvent) -> Generator[list, None, None]:
    """薬獲得イベント"""

    yield [SeqSubCmd.SE_INSTANT, SoundID.ITEM_GET]
    item_def = di.ref.pt.get_item(ItemID.HEALPOT)
    yield [f"{item_def.name}を拾った"]


# class NORMAL_GET_POTION(CommandBaseSequence):  # 低級消耗品増
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


# class NORMAL_MEET_ALLY(CommandBaseSequence):  # 仲間ゲット
class MeetAlly(CommandBaseSequence):  # 仲間ゲット
    def _sequence(self) -> Generator[list, None, None]:
        # event = cast(Event, self.args[1])
        # ctx = self.
        event = self.kwargs["event"]
        for i, msg in enumerate(event.event_messages):
            yield [msg]
            # match i:
            #     case 6:
            #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)

        # 新キャラクターインスタンス生成
        newbie = di.ref.pt.generate_ptmember()

        # メンバー上限を超える場合は除外メンバーを選択
        if di.ref.pt.add_ptmember(newbie):
            yield ["これから、よろしく！"]
            yield from self.wait_finish()
            return

        yield [
            "見送る場合はキャンセル",
            "交代する場合は離脱キャラを選択",
            "※装備とスキルは継承されます",
        ]

        # 選択メニュー用情報の生成
        self.menu_shape = [1, 2]
        self.allies = di.ref.pt.get_allmember()[1:]
        self.target_list = [
            [
                {
                    "id": mem.param.name,
                    "action": "None",
                    "args": [mem.chara_id],
                }
            ]
            for mem in self.allies
        ]

        # さよならメンバー選択メニュー
        pos_x, pos_y = 128, 136
        menu_width = 104
        menu_select_ally = Menu("basic", pos_x, pos_y, self.menu_shape, self.target_list, menu_width)
        menu_select_ally.cursor_row_offset = 2
        # サブウインドウ生成
        self.build_subwindow()
        self.build_status(newbie, self.windows["main"])
        target_member = self.allies[menu_select_ally.cursor_position[1]]
        self.build_status(target_member, self.windows["sub"])

        # キー待ち時の入力を一回捨てる
        yield [SeqSubCmd.WAIT, 0]

        # スタックに追加せずメニュー動作
        rc = menu_select_ally.update()
        while rc == WindowAction.CONTINUE:
            cursor_y = menu_select_ally.cursor_position[1]
            rc = menu_select_ally.update()
            if cursor_y != menu_select_ally.cursor_position[1]:
                target_member = self.allies[menu_select_ally.cursor_position[1]]
                self.build_status(target_member, self.windows["sub"])

            self.display_info.graphic_command = [
                lambda menu=menu_select_ally: menu.draw(),
                lambda window=self.windows["main"]: window.draw(),
                lambda window=self.windows["main"]: window.draw_message(),
                lambda window=self.windows["sub"]: window.draw(),
                lambda window=self.windows["sub"]: window.draw_message(),
            ]
            yield [SeqSubCmd.WAIT, 0]

        if rc == WindowAction.EXECUTE:
            self.display_info.graphic_command = None
            yield [SeqSubCmd.WAIT, 0]
            yield ["それでは、お元気で・・・"]
            # スキルの継承
            newbie.skills.inherit_skill(target_member.skills.get_learned_skill_id())
            # 装備の継承
            target_member.equipments.inherit_equips(newbie)

            di.ref.pt.remove_ptmember(target_member.chara_id)
            di.ref.pt.add_ptmember(newbie)

        yield from self.wait_finish()

    def build_subwindow(self) -> None:
        # 情報表示ウインドウのサイズ
        param_w, param_h = 128, 136  # ステータス
        padding = 2
        pos_x, pos_y = 0, 0

        self.windows: dict[MENU_WINDOW_TYPE, Window] = {}
        self.windows["main"] = Window("basic", pos_x, pos_y, param_w, param_h, "once")
        self.windows["sub"] = Window(
            "basic", pos_x + self.windows["main"].width + padding, pos_y, param_w, param_h, "once"
        )

    def build_status(self, member, target) -> None:
        """ステータス表示内容の構築（装備含む）"""
        param = member.param

        # メインステータス
        status_lines = f"{param.name}"
        status_lines += f"\nレベル： {upper_int_spaced(param.level, 2)}"
        status_lines += f"\n次まで： {upper_int_spaced(member.next_exp, 1)}"
        status_lines += f"\nＨ　Ｐ： {upper_int_spaced(param.hp, 3)}／{upper_int_spaced(param.max_hp, 3)}"
        status_lines += f"\nＭ　Ｐ： {upper_int_spaced(param.mp, 3)}／{upper_int_spaced(param.max_mp, 3)}"
        status_lines += f"\n筋　力： {
                format_leftright(
                    upper_int_spaced(member.strength, 3),
                    f'（＋{upper_int_spaced(member.bonus_str, 1)}）',
                    18,
                )
            }"
        status_lines += f"\n魔　力： {
            format_leftright(
                upper_int_spaced(member.arcane, 3),
                f'（＋{upper_int_spaced(member.bonus_arc, 1)}）',
                18,
            )
        }"
        status_lines += f"\n耐　久： {
            format_leftright(
                upper_int_spaced(member.endurance, 3),
                f'（＋{upper_int_spaced(member.bonus_end, 1)}）',
                18,
            )
        }"
        status_lines += f"\n速　度： {
            format_leftright(
                upper_int_spaced(member.speed, 3),
                f'（＋{upper_int_spaced(member.bonus_spd, 1)}）',
                18,
            )
        }"
        status_lines += f"\n幸　運： {
            format_leftright(
                upper_int_spaced(member.luck, 3),
                f'（＋{upper_int_spaced(member.bonus_lck, 1)}）',
                18,
            )
        }"

        target.message_list = [status_lines]


# class NORMAL_FLGEVENT2_D(CommandBaseSequence):  # フラグイベントStep2
#     def _sequence(self) -> Generator[list, None, None]:
#         if di.ref.flgmgr.is_set(FlagID.DRAGONFANG):
#             yield ["もうここには　なにもない"]
#         elif di.ref.flgmgr.check_all(set([FlagID.JADEEYE, FlagID.CROSS])):
#             event = cast(Event, self.args[1])
#             for i, msg in enumerate(event.event_messages):
#                 yield [msg]
#                 # match i:
#                 #     case 4:
#                 #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
#                 #     case 9:
#                 #         di.ref.sndmgr.play_se_instant(SoundID.ITEM_GET)

#             pl_item = di.ref.pl_item.create(ItemID.DRAGONFANG)
#             item_def = di.ref.itemrps.get_def(pl_item[1].ins.param.def_id)
#             di.ref.flgmgr.set_flag(FlagID.DRAGONFANG)
#             yield [f"{item_def.name}を手に入れた"]  # type: ignore
#         else:
#             item1 = di.ref.itemrps.get_def(ItemID.JADEEYE)
#             item2 = di.ref.itemrps.get_def(ItemID.CROSS)
#             yield [f"{item1.name}と{item2.name}を手に入れたのち、再び訪れるがよい"]  # type: ignore

#         yield from self.wait_finish()


def flgevent2_d(self) -> Generator[list, None, None]:
    yield from flag_event_flow(self, FlagID.DRAGONFANG, ItemID.DRAGONFANG, [FlagID.JADEEYE, FlagID.CROSS])


# class NORMAL_FLGEVENT2_E(CommandBaseSequence):  # フラグイベントStep2
#     def _sequence(self) -> Generator[list, None, None]:
#         if di.ref.flgmgr.is_set(FlagID.TARISMAN):
#             yield ["もうここには　なにもない"]
#         elif di.ref.flgmgr.check_all(set([FlagID.CRYSTALROD, FlagID.CROSS])):
#             event = cast(Event, self.args[1])
#             for i, msg in enumerate(event.event_messages):
#                 yield [msg]
#                 # match i:
#                 #     case 4:
#                 #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
#                 #     case 9:
#                 #         di.ref.sndmgr.play_se_instant(SoundID.ITEM_GET)

#             pl_item = di.ref.pl_item.create(ItemID.TARISMAN)
#             item_def = di.ref.itemrps.get_def(pl_item[1].ins.param.def_id)
#             di.ref.flgmgr.set_flag(FlagID.TARISMAN)
#             yield [f"{item_def.name}を手に入れた"]  # type: ignore
#         else:
#             item1 = di.ref.itemrps.get_def(ItemID.CRYSTALROD)
#             item2 = di.ref.itemrps.get_def(ItemID.CROSS)
#             yield [f"{item1.name}と{item2.name}を手に入れたのち、再び訪れるがよい"]  # type: ignore

#         yield from self.wait_finish()


def flgevent2_e(self) -> Generator[list, None, None]:
    yield from flag_event_flow(self, FlagID.TARISMAN, ItemID.TARISMAN, [FlagID.CRYSTALROD, FlagID.CROSS])


# class NORMAL_FLGEVENT2_F(CommandBaseSequence):  # フラグイベントStep2
#     def _sequence(self) -> Generator[list, None, None]:
#         if di.ref.flgmgr.is_set(FlagID.HOLYSHROUD):
#             yield ["もうここには　なにもない"]
#         elif di.ref.flgmgr.check_all(set([FlagID.CRYSTALROD, FlagID.JADEEYE])):
#             event = cast(Event, self.args[1])
#             for i, msg in enumerate(event.event_messages):
#                 yield [msg]
#                 # match i:
#                 #     case 4:
#                 #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
#                 #     case 9:
#                 #         di.ref.sndmgr.play_se_instant(SoundID.ITEM_GET)

#             pl_item = di.ref.pl_item.create(ItemID.HOLYSHROUD)
#             item_def = di.ref.itemrps.get_def(pl_item[1].ins.param.def_id)
#             di.ref.flgmgr.set_flag(FlagID.HOLYSHROUD)
#             yield [f"{item_def.name}を手に入れた"]  # type: ignore
#         else:
#             item1 = di.ref.itemrps.get_def(ItemID.CRYSTALROD)
#             item2 = di.ref.itemrps.get_def(ItemID.JADEEYE)
#             yield [f"{item1.name}と{item2.name}を手に入れたのち、再び訪れるがよい"]  # type: ignore

#         yield from self.wait_finish()


def flgevent2_f(self) -> Generator[list, None, None]:
    yield from flag_event_flow(self, FlagID.HOLYSHROUD, ItemID.HOLYSHROUD, [FlagID.CRYSTALROD, FlagID.JADEEYE])


# class GAMBLE_GET_HIPOTION(CommandBaseSequence):  # 高級消耗品増
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


def get_hipotion(cmd: PlayEvent) -> Generator[list, None, None]:
    """高級薬獲得イベント"""

    yield [SeqSubCmd.SE_INSTANT, SoundID.ITEM_GET]
    item_def = di.ref.pt.get_item(ItemID.HIHEALPOT)
    yield [f"{item_def.name}を手に入れた"]


# class GAMBLE_FLGEVENT3_G(CommandBaseSequence):  # フラグイベントStep3
#     def _sequence(self) -> Generator[list, None, None]:
#         if di.ref.flgmgr.is_set(FlagID.SACREDWEAPON):
#             _cntx = self.args[0]
#             yield ["穏やか気配に　満ちた空間だ"]
#             for mem in _cntx.allies:
#                 mem.increase_mp(mem.max_mp)
#             # di.ref.sndmgr.play_se_instant(SoundID.RECOVER)
#             yield [SeqSubCmd.SE_SUSTAIN, SoundID.RECOVER]
#             yield ["全員の魔力が　全快した"]
#         elif di.ref.flgmgr.check_all(set([FlagID.DRAGONFANG, FlagID.TARISMAN])):
#             event = cast(Event, self.args[1])
#             for i, msg in enumerate(event.event_messages):
#                 yield [msg]
#                 # match i:
#                 #     case 4:
#                 #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
#                 #     case 9:
#                 #         di.ref.sndmgr.play_se_instant(SoundID.ITEM_GET)

#             pl_item = di.ref.pl_item.create(ItemID.SACREDWEAPON)
#             item_def = di.ref.itemrps.get_def(pl_item[1].ins.param.def_id)
#             di.ref.flgmgr.set_flag(FlagID.SACREDWEAPON)
#             yield [f"{item_def.name}を手に入れた"]  # type: ignore
#         else:
#             item1 = di.ref.itemrps.get_def(ItemID.DRAGONFANG)
#             item2 = di.ref.itemrps.get_def(ItemID.TARISMAN)
#             yield [f"{item1.name}と{item2.name}を手に入れたのち、再び訪れるがよい"]  # type: ignore

#         yield from self.wait_finish()


def flgevent3_g(cmd) -> Generator[list, None, None]:
    yield from flag_event_flow(
        cmd, FlagID.SACREDWEAPON, ItemID.SACREDWEAPON, [FlagID.DRAGONFANG, FlagID.TARISMAN], sacred_field
    )


def sacred_field(cmd: PlayEvent) -> Generator[list, None, None]:
    yield ["穏やか気配に　満ちた空間だ"]
    yield [SeqSubCmd.SE_SUSTAIN, SoundID.RECOVER]
    for mem in cmd.local_allies:
        mem.increase_mp(mem.max_mp)
    yield ["全員の魔力が　全快した"]


# class GAMBLE_FLGEVENT3_H(CommandBaseSequence):  # フラグイベントStep3
#     def _sequence(self) -> Generator[list, None, None]:
#         if di.ref.flgmgr.is_set(FlagID.HOLYGUARD):
#             _cntx = self.args[0]
#             yield ["厳かな気配に　満ちた空間だ"]
#             for mem in _cntx.allies:
#                 mem.increase_hp(mem.max_hp)
#             # di.ref.sndmgr.play_se_instant(SoundID.RECOVER)
#             yield [SeqSubCmd.SE_SUSTAIN, SoundID.RECOVER]
#             yield ["全員の体力が　全快した"]
#         elif di.ref.flgmgr.check_all(set([FlagID.HOLYSHROUD, FlagID.TARISMAN])):
#             event = cast(Event, self.args[1])
#             for i, msg in enumerate(event.event_messages):
#                 yield [msg]
#                 # match i:
#                 #     case 4:
#                 #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
#                 #     case 9:
#                 #         di.ref.sndmgr.play_se_instant(SoundID.ITEM_GET)

#             pl_item = di.ref.pl_item.create(ItemID.HOLYGUARD)
#             item_def = di.ref.itemrps.get_def(pl_item[1].ins.param.def_id)
#             di.ref.flgmgr.set_flag(FlagID.HOLYGUARD)
#             yield [f"{item_def.name}を手に入れた"]  # type: ignore
#         else:
#             item1 = di.ref.itemrps.get_def(ItemID.HOLYSHROUD)
#             item2 = di.ref.itemrps.get_def(ItemID.TARISMAN)
#             yield [f"{item1.name}と{item2.name}を手に入れたのち、再び訪れるがよい"]  # type: ignore

#         yield from self.wait_finish()


def flgevent3_h(cmd) -> Generator[list, None, None]:
    yield from flag_event_flow(
        cmd, FlagID.HOLYGUARD, ItemID.HOLYGUARD, [FlagID.HOLYSHROUD, FlagID.TARISMAN], holy_field
    )


def holy_field(cmd: PlayEvent) -> Generator[list, None, None]:
    yield ["厳かな気配に　満ちた空間だ"]
    yield [SeqSubCmd.SE_SUSTAIN, SoundID.RECOVER]
    for mem in cmd.local_allies:
        mem.increase_hp(mem.max_hp)
    yield ["全員の体力が　全快した"]


# class SAFETY_GET_JUNK(CommandBaseSequence):  # 最低装備品ゲット
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]
#             # match i:
#             #     case 3:
#             #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
#             #     case 5:
#             #         di.ref.sndmgr.play_se_instant(SoundID.ITEM_GET)

#         item_idx = diceroll(event.event_value) - 1
#         ids = [
#             ItemID.DAGGER,
#             ItemID.MACE,
#             ItemID.JAVELIN,
#             ItemID.CLOTH,
#             ItemID.HPBELT,
#             ItemID.MPBELT,
#         ]
#         get_item_id = ids[item_idx]
#         # di.ref.pl_item.create(get_item_id)
#         # item_def = di.ref.itemrps.get_def(get_item_id)
#         item_def = di.ref.pt.get_item(get_item_id)
#         yield [f"{item_def.name}を手に入れた"]  # type: ignore

#         yield from self.wait_finish()


# class GAMBLE_GET_ARMORY(CommandBaseSequence):  # 装備品ゲット
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


def get_item_flow(cmd: PlayEvent, item_id_list: list[ItemID]) -> Generator[list, None, None]:
    """装備品ランダム獲得イベントフロー"""
    yield from cmd.play_event_message()
    item_idx = diceroll(cmd.event.event_value) - cmd.event.event_value
    get_item_id = item_id_list[item_idx]
    yield [SeqSubCmd.SE_SUSTAIN, SoundID.ITEM_GET]
    item_def = di.ref.pt.get_item(get_item_id)
    yield [f"{item_def.name}を手に入れた"]


def get_armory(cmd: PlayEvent) -> Generator[list, None, None]:
    """装備入手"""
    item_id_list = [
        ItemID.DAGGER,
        ItemID.MAGICSPEAR,
        ItemID.MAGICMACE,
        ItemID.MAGICBLADE,
        ItemID.ENCHANTROBE,
        ItemID.HALFPLATE,
        ItemID.HIATKRING,
        ItemID.HISPDRING,
        ItemID.HIDEFRING,
        ItemID.HIREGRING,
        ItemID.GODDICE,
        ItemID.HIPOWAMULET,
        ItemID.HIARCAMULET,
        ItemID.HICONAMULET,
        ItemID.HISPDAMULET,
        ItemID.HILCKAMULET,
    ]
    yield from get_item_flow(cmd, item_id_list)


def get_junk(cmd: PlayEvent) -> Generator[list, None, None]:
    """ガラクタ入手"""
    item_id_list = [
        ItemID.HPBELT,
        ItemID.DAGGER,
        ItemID.MACE,
        ItemID.JAVELIN,
        ItemID.CLOTH,
        ItemID.MPBELT,
    ]
    yield from get_item_flow(cmd, item_id_list)


##### bad
def decrease_hp(cmd: PlayEvent) -> Generator[list, None, None]:
    """HP消耗イベント"""

    # for mem in cmd.ctx.allies:
    #     recover = diceroll(cmd.event.event_value)
    #     yield [SeqSubCmd.SE_INSTANT, SoundID.RECOVER]
    #     mem.increase_hp(recover)
    #     yield [f"{mem.param.name}のＨＰが{recover}回復した"]
    # target_id = px.rndi(0, len(_cntx.allies) - 1)
    # target = _cntx.allies[target_id]
    target = choice(di.ref.pt.get_active_member())
    damage = diceroll(cmd.event.event_value)
    yield [SeqSubCmd.SE_INSTANT, SoundID.DAMAGE_TAKEN]
    target.decrease_hp(damage)
    yield [f"{target.param.name}は{damage}のＨＰを失った"]


# class SAFETY_DECREASE_HP(CommandBaseSequence):  # HP減
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]
#             # match i:
#             #     case 0:
#             #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_MINUS)
#             #     case 3:
#             #         di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)

#         target_id = px.rndi(0, len(_cntx.allies) - 1)
#         target = _cntx.allies[target_id]
#         damage = diceroll(event.event_value)
#         target.decrease_hp(damage)
#         yield [f"{target.param.name}は{damage}のＨＰを失った"]

#         yield from self.wait_finish()


# class NORMAL_DECREASE_HP(CommandBaseSequence):  # HP減
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


# class GAMBLE_DECREASE_HP(CommandBaseSequence):  # HP減
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


def decrease_mp(cmd: PlayEvent) -> Generator[list, None, None]:
    """MP消耗イベント"""

    target = choice(di.ref.pt.get_active_member())
    damage = diceroll(cmd.event.event_value)
    yield [SeqSubCmd.SE_INSTANT, SoundID.DAMAGE_TAKEN]
    target.decrease_mp(damage)
    yield [f"{target.param.name}は{damage}のＭＰを失った"]


# class SAFETY_DECREASE_MP(CommandBaseSequence):  # MP減
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]
#             # match i:
#             #     case 0:
#             #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_MINUS)
#             #     case 3:
#             #         di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)

#         target_id = px.rndi(0, len(_cntx.allies) - 1)
#         target = _cntx.allies[target_id]
#         damage = diceroll(event.event_value)
#         target.decrease_mp(damage)
#         yield [f"{target.param.name}は{damage}のＭＰを失った"]

#         yield from self.wait_finish()


# class NORMAL_DECREASE_MP(CommandBaseSequence):  # MP減
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


# class GAMBLE_DECREASE_MP(CommandBaseSequence):  # MP減
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


def decrease_gold(cmd: PlayEvent) -> Generator[list, None, None]:
    """課金(仮)イベント"""

    losts = diceroll(cmd.event.event_value)
    yield [SeqSubCmd.SE_INSTANT, SoundID.ITEM_LOST]
    di.ref.pt.spend_gold(losts)
    yield [f"パーティは{losts}のお金を失った"]


# class SAFETY_DECREASE_GOLD(CommandBaseSequence):  # おかね減
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         party = cast(Party, self.args[2])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]
#             # match i:
#             #     case 1:
#             #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_MINUS)
#             #     case 4:
#             #         di.ref.sndmgr.play_se_instant(SoundID.ITEM_LOST)

#         losts = diceroll(event.event_value)
#         party.spend_gold(losts)
#         yield [f"パーティは{losts}のお金を失った"]

#         yield from self.wait_finish()


# class NORMAL_DECREASE_GOLD(CommandBaseSequence):  # おかね減
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


# class GAMBLE_DECREASE_GOLD(CommandBaseSequence):  # おかね減
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


def decrease_food(cmd: PlayEvent) -> Generator[list, None, None]:
    """食品廃棄イベント"""

    losts = diceroll(cmd.event.event_value)
    yield [SeqSubCmd.SE_INSTANT, SoundID.ITEM_LOST]
    di.ref.pt.lost_foods(losts)
    yield [f"パーティは{losts}の食料を失った"]


# class SAFETY_DECREASE_FOOD(CommandBaseSequence):  # 食糧減
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         party = cast(Party, self.args[2])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]
#             # match i:
#             #     case 3:
#             #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_MINUS)
#             #     case 4:
#             #         di.ref.sndmgr.play_se_instant(SoundID.ITEM_LOST)

#         losts = diceroll(event.event_value)
#         party.lost_foods(losts)
#         yield [f"パーティは{losts}の食料を失った"]

#         yield from self.wait_finish()


# class NORMAL_DECREASE_FOOD(CommandBaseSequence):  # 食糧減
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


# class GAMBLE_DECREASE_FOOD(CommandBaseSequence):  # 食糧減
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


def lost_bottle(cmd: PlayEvent, item_ids: list[ItemID]) -> Generator[list, None, None]:
    item_def = di.ref.itemrps.get_def(choice(item_ids))
    if di.ref.pl_stack.count(item_def.def_id):
        yield [SeqSubCmd.SE_INSTANT, SoundID.ITEM_LOST]
        yield [f"{item_def.name}を割ってしまった…"]
    else:
        yield ["割れたのは空瓶だったようだ"]


def lost_potion(cmd: PlayEvent) -> Generator[list, None, None]:
    """薬破損イベント"""

    # item_def = di.ref.itemrps.get_def(choice([ItemID.HEALPOT, ItemID.MAGICPOT]))
    # # if di.ref.pl_stack.count(item_def.def_id):
    # #     yield [SeqSubCmd.SE_INSTANT, SoundID.ITEM_LOST]
    # #     yield [f"{item_def.name}を割ってしまった…"]
    # # else:
    # #     yield ["割れたのは空瓶だったようだ"]
    yield from lost_bottle(cmd, [ItemID.HEALPOT, ItemID.MAGICPOT])


def lost_hipotion(cmd: PlayEvent) -> Generator[list, None, None]:
    """高級薬破損イベント"""

    # item_def = di.ref.itemrps.get_def(choice([ItemID.HIHEALPOT, ItemID.HIMAGICPOT]))
    # if di.ref.pl_stack.count(item_def.def_id):
    #     yield [SeqSubCmd.SE_INSTANT, SoundID.ITEM_LOST]
    #     yield [f"{item_def.name}を割ってしまった…"]
    # else:
    #     yield ["割れたのは空瓶だったようだ"]
    yield from lost_bottle(cmd, [ItemID.HIHEALPOT, ItemID.HIMAGICPOT])


# class NORMAL_LOST_POTION(CommandBaseSequence):  # 低級消耗品減
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


def start_battle(cmd: PlayEvent, enemy_count: int, enemy_id: str, after_event=None) -> Generator[list, None, None]:
    """固定バトルシーン遷移"""
    yield from cmd.wait_finish()
    di.ref.scnmgr.next_scene("fixedbattle", enemy_count, enemy_id, after_event)


def surprise_battle(cmd: PlayEvent) -> Generator[list, None, None]:
    """ランダム戦闘イベント"""
    # エネミーの選定
    threat = cmd.event.event_value
    candidate_list = di.ref.enmrps.get_threat_enemies(threat)
    enemy_id = choice(candidate_list)
    enemy_data = di.ref.enmrps.get_enemy(enemy_id)
    # エネミー出現数の算出
    from_size = min(enemy_data["bodysize"], diceroll(1))
    # 低脅威度で集団に襲われないよう調整
    from_threat = min(from_size, px.ceil(threat / 1.5) + 1)
    enemy_count = from_threat
    yield from start_battle(cmd, enemy_count, enemy_id)


# class SAFETY_SURPRISE_BATTLE(CommandBaseSequence):  # 強制戦闘
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]
#             # match i:
#             #     case 3:
#             #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_MINUS)
#             #     case 5:
#             #         di.ref.sndmgr.play_se_instant(SoundID.ENCOUNT)

#         yield from self.wait_finish()

#         di.ref.scnmgr.next_scene("battlesplash")


# class NORMAL_SURPRISE_BATTLE(CommandBaseSequence):  # 強制戦闘
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1].current_point.nextevent)
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()

#         di.ref.scnmgr.next_scene("fixedbattle", 1, "GOLD_DRAGON_ANCIENT")


# class GAMBLE_SURPRISE_BATTLE(CommandBaseSequence):  # 強制戦闘
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


# class GAMBLE_LOST_HIPOTION(CommandBaseSequence):  # 高級消耗品減
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()

#     # boss


def crown(cmd: PlayEvent) -> Generator[list, None, None]:
    """固定戦闘イベント"""

    yield from cmd.play_event_message()
    yield from start_battle(cmd, 1, "PIT_FIEND", GET_CROWN)


def mirror(cmd: PlayEvent) -> Generator[list, None, None]:
    """固定戦闘イベント"""

    yield from cmd.play_event_message()
    yield from start_battle(cmd, 1, "PIT_FIEND", GET_MIRROR)


def cepter(cmd: PlayEvent) -> Generator[list, None, None]:
    """固定戦闘イベント"""

    yield from cmd.play_event_message()
    yield from start_battle(cmd, 1, "PIT_FIEND", GET_CEPTER)


def grail(cmd: PlayEvent) -> Generator[list, None, None]:
    """固定戦闘イベント"""

    yield from cmd.play_event_message()
    yield from start_battle(cmd, 1, "PIT_FIEND", GET_GRAIL)


def satan(cmd: PlayEvent) -> Generator[list, None, None]:
    """固定戦闘イベント"""

    yield from cmd.play_event_message()
    yield from start_battle(cmd, 1, "PIT_FIEND", DEFEAT_SATAN)


def king(cmd: PlayEvent) -> Generator[list, None, None]:
    """固定戦闘イベント"""

    yield from cmd.play_event_message()
    yield from start_battle(cmd, 1, "PIT_FIEND", SAVE_THE_PLANET)


# class BATTLE_CROWN(CommandBaseSequence):  # 宝冠の守護者　破魔に弱い
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


# class BATTLE_MIRROR(CommandBaseSequence):  # 神鏡の守護者　衝撃に弱い
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


# class BATTLE_CEPTER(CommandBaseSequence):  # 王笏の守護者　精神に弱い
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


# class BATTLE_GRAIL(CommandBaseSequence):  # 聖杯の守護者　呪毒に弱い
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]
#             # match i:
#             #     case 3:
#             #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_MINUS)
#             #     case 5:
#             #         di.ref.sndmgr.play_se_instant(SoundID.ENCOUNT)

#         # self.display_info.target.update_indicator(True)
#         # while self.display_info.target.update() == WindowAction.CONTINUE:
#         #     yield [SeqSubCmd.WAIT, 0]
#         # self.display_info.target.update_indicator(False)
#         yield from self.wait_finish()

#         di.ref.scnmgr.next_scene("fixedbattle", 1, "SCORPION", GET_GRAIL)


def get_artifact(cmd: PlayEvent, flag: FlagID, item_id: ItemID) -> Generator[list, None, None]:
    yield from cmd.play_event_message()
    yield [SeqSubCmd.SE_SUSTAIN, SoundID.FANFALE]
    while di.ref.sndmgr.wait_se_fin() is False:
        pass
    di.ref.flgmgr.set_flag(flag)
    item_def = di.ref.pt.get_item(item_id)
    yield [f"{item_def.name}を手に入れた"]


class GET_CROWN(PlayEvent):
    def _sequence(self) -> Generator[list, None, None]:
        self.event = di.ref.evtrps.get_event(EventType.SAFETY, EventID.CROWN)  # type: ignore
        yield from get_artifact(self, FlagID.CROWN, ItemID.CROWN)


class GET_MIRROR(PlayEvent):
    def _sequence(self) -> Generator[list, None, None]:
        self.event = di.ref.evtrps.get_event(EventType.SAFETY, EventID.MIRROR)  # type: ignore
        yield from get_artifact(self, FlagID.MIRROR, ItemID.MIRROR)


class GET_CEPTER(PlayEvent):
    def _sequence(self) -> Generator[list, None, None]:
        self.event = di.ref.evtrps.get_event(EventType.SAFETY, EventID.CEPTER)  # type: ignore
        yield from get_artifact(self, FlagID.CEPTER, ItemID.CEPTER)


class GET_GRAIL(PlayEvent):
    def _sequence(self) -> Generator[list, None, None]:
        # _cntx = self.args[0]
        # event = di.ref.evtrps.get_event(EventType.SAFETY, EventID.GRAIL)
        # for i, msg in enumerate(event.event_messages):  # type: ignore
        #     yield [msg]
        #     # match i:
        #     #     case 3:
        #     #         di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
        #     #     case 5:
        #     #         di.ref.sndmgr.play_se_instant(SoundID.FANFALE)

        # yield from self.wait_finish()
        self.event = di.ref.evtrps.get_event(EventType.SAFETY, EventID.GRAIL)  # type: ignore
        # yield from self.play_event_message()
        # yield [SeqSubCmd.SE_SUSTAIN, SoundID.FANFALE]
        # item_def = di.ref.pt.get_item(ItemID.GRAIL)
        # yield [f"{item_def.name}を手に入れた"]
        yield from get_artifact(self, FlagID.GRAIL, ItemID.GRAIL)


class DEFEAT_SATAN(PlayEvent):
    def _sequence(self) -> Generator[list, None, None]:
        di.ref.flgmgr.set_flag(FlagID.SLAY_SATAN)

        # トゥルーエンドルート判定
        sacred_check = False
        for mem in di.ref.pt.get_allmember():
            if mem.equipments.check_sacredweapon():
                sacred_check = True
                break
        if sacred_check:
            self.event = di.ref.evtrps.get_event(EventType.SAFETY, EventID.SATAN)  # type: ignore
            di.ref.flgmgr.set_flag(FlagID.BIGBAD)
        else:
            self.event = di.ref.evtrps.get_event(EventType.NORMAL, EventID.SATAN)  # type: ignore

        yield from self.play_event_message()


class SAVE_THE_PLANET(PlayEvent):
    def _sequence(self) -> Generator[list, None, None]:
        di.ref.scnmgr.change_scene("ending")
        yield [SeqSubCmd.WAIT, 0]


# class BATTLE_SATAN(CommandBaseSequence):  # 魔王
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()


# class GAMBLE_KING(CommandBaseSequence):  # 人間の王
#     def _sequence(self) -> Generator[list, None, None]:
#         _cntx = self.args[0]
#         event = cast(Event, self.args[1])
#         for i, msg in enumerate(event.event_messages):
#             yield [msg]

#         yield from self.wait_finish()
