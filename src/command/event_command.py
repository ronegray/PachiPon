"""
イベントコマンドモジュール
"""

import logging
from typing import Generator, cast
import pyxel as px
import service_locater as di
from gameutils.lib import WindowAction, Menu, Window, MENU_WINDOW_TYPE
from const import SoundID
from helper import diceroll, upper_int_spaced, format_leftright

# from helper import diceroll_values
# import service_locater as di
from item import ItemID
from entity import Party
from event import Event, EventID
from field_map import EventPoint
from . import CommandBaseSequence

# ロギング設定
logger = logging.getLogger(__name__)


class CommandBaseEvent(CommandBaseSequence):
    """イベントシーン専用コマンドの基底クラス"""

    def _wait_finish(self) -> Generator[list[str], None, None]:
        """イベント終了時のキー待ち処理"""
        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)
        return


class KickEvent(CommandBaseEvent):
    """フィールドイベント起動処理"""

    def _sequence(self) -> Generator[list[str], None, None]:
        point = cast(EventPoint, self.args[0])
        # dices = point.kick_event()
        # final_value = diceroll_values(dices)
        # final_value = [1 for _ in range(dices)]
        point.kick_event()

        # 固定イベントポイントの場合
        fixed = point.check_fixedevent()
        if fixed:
            point.rise_event(fixed)
            return

        # 算出済ダイス値の取得
        dices, final_value = point.get_event_dice_values()
        # アイテムボーナス（ダイス数追加）
        dice_plus = di.ref.pt.pt_dice_plus()
        dices += dice_plus
        final_value += [diceroll(1) for _ in range(dice_plus)]

        effect = di.ref.efxdice
        roll_frames = 60
        yield ["何が起こるか", "　おたのしみ！"]
        effect.start(dices, roll_frames, final_value)
        if not di.ref.conf.is_cutin_dice:
            effect.skip()
            self.display_info.graphic_command = effect.get_draw_commands()
        while effect.is_rolling:
            effect.update()
            self.display_info.graphic_command = effect.get_draw_commands()
            yield ["wait", "0"]
        yield [f"出た目は・・・　{effect.total}"]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)

        # イベントが全てオープンになるまで、同じイベントは再実行されない
        eventlist = {
            event_id: event_stat
            for event_id, event_stat in point.event_list.event_stat.items()
            if event_stat.is_opened is False
        }
        # マイナスイベント抑止時
        if di.ref.pt.get_pt_efx("reduce_negative1") or di.ref.pt.get_pt_efx("reduce_negative2"):
            negative_list = [
                event_id
                for event_id in eventlist
                if event_id
                in (
                    EventID.DECREASE_HP,  # HP減
                    EventID.DECREASE_MP,  # MP減
                    EventID.DECREASE_GOLD,  # おかね減
                    EventID.DECREASE_FOOD,  # 食糧減
                    EventID.LOST_POTION,  # 低級消耗品減
                    EventID.SURPRISE_BATTLE,  # 強制戦闘
                    EventID.LOST_HIPOTION,  # 高級消耗品減
                )
            ]
            reduce_negative = di.ref.pt.pt_reduce_negative(negative_list)
            for event_id in reduce_negative:
                eventlist.pop(event_id)
        # 対象が一つもなくなったら全ランダム
        if len(eventlist) < 1:
            eventlist = point.event_list.event_stat
        # 候補内の閾値超えイベントが実際の発生対象
        # for event_id, event_stat in point.event_list.event_stat.items():
        for event_id, event_stat in eventlist.items():
            if effect.total >= event_stat.threshold:
                event_stat.is_opened = True
                point.rise_event(event_id)
                break

    # good


class SAFETY_INCREASE_HP(CommandBaseEvent):
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]
            match i:
                case 1:
                    di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
                case 3:
                    di.ref.sndmgr.play_se_instant(SoundID.RECOVER)

        for mem in _cntx.allies:
            recover = diceroll(event.event_value)
            mem.increase_hp(recover)
            yield [f"{mem.param.name}のＨＰが{recover}回復した"]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class NORMAL_INCREASE_HP(CommandBaseEvent):  # HP増
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class GAMBLE_INCREASE_HP(CommandBaseEvent):  # HP増
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class SAFETY_INCREASE_MP(CommandBaseEvent):  # MP増
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]
            match i:
                case 1:
                    di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
                case 3:
                    di.ref.sndmgr.play_se_instant(SoundID.RECOVER)

        for mem in _cntx.allies:
            recover = diceroll(event.event_value)
            mem.increase_mp(recover)
            yield [f"{mem.param.name}のＭＰが{recover}回復した"]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class NORMAL_INCREASE_MP(CommandBaseEvent):  # MP増
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class GAMBLE_INCREASE_MP(CommandBaseEvent):  # MP増
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class SAFETY_INCREASE_GOLD(CommandBaseEvent):  # おかね増
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        party = cast(Party, self.args[2])
        for i, msg in enumerate(event.event_messages):
            yield [msg]
            match i:
                case 3:
                    di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
                case 4:
                    di.ref.sndmgr.play_se_instant(SoundID.ITEM_GET)

        gets = diceroll(event.event_value)
        party.earn_gold(gets)
        yield [f"パーティは{gets}のお金を手に入れた"]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class NORMAL_INCREASE_GOLD(CommandBaseEvent):  # おかね増
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class GAMBLE_INCREASE_GOLD(CommandBaseEvent):  # おかね増
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class SAFETY_INCREASE_FOOD(CommandBaseEvent):  # 食糧増
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        party = cast(Party, self.args[2])
        for i, msg in enumerate(event.event_messages):
            yield [msg]
            match i:
                case 2:
                    di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
                case 4:
                    di.ref.sndmgr.play_se_instant(SoundID.ITEM_GET)

        gets = diceroll(event.event_value)
        party.earn_foods(gets)
        yield [f"パーティは{gets}の食料を手に入れた"]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class NORMAL_INCREASE_FOOD(CommandBaseEvent):  # 食糧増
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class GAMBLE_INCREASE_FOOD(CommandBaseEvent):  # 食糧増
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class SAFETY_FLGEVENT1_A(CommandBaseEvent):  # フラグイベントStep1
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]
            match i:
                case 4:
                    di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
                case 9:
                    di.ref.sndmgr.play_se_instant(SoundID.ITEM_GET)

        pl_item = di.ref.pl_item.create(ItemID.JADEEYE)
        item_def = di.ref.itemrps.get_def(pl_item[1].ins.param.def_id)
        yield [f"{item_def.name}を手に入れた"]  # type: ignore

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class SAFETY_FLGEVENT1_B(CommandBaseEvent):  # フラグイベントStep1
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]
            match i:
                case 4:
                    di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
                case 9:
                    di.ref.sndmgr.play_se_instant(SoundID.ITEM_GET)

        pl_item = di.ref.pl_item.create(ItemID.CROSS)
        item_def = di.ref.itemrps.get_def(pl_item[1].ins.param.def_id)
        yield [f"{item_def.name}を手に入れた"]  # type: ignore

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class SAFETY_FLGEVENT1_C(CommandBaseEvent):  # フラグイベントStep1
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]
            match i:
                case 4:
                    di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
                case 9:
                    di.ref.sndmgr.play_se_instant(SoundID.ITEM_GET)

        pl_item = di.ref.pl_item.create(ItemID.CRYSTALROD)
        item_def = di.ref.itemrps.get_def(pl_item[1].ins.param.def_id)
        yield [f"{item_def.name}を手に入れた"]  # type: ignore

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class NORMAL_GET_POTION(CommandBaseEvent):  # 低級消耗品増
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class NORMAL_MEET_ALLY(CommandBaseEvent):  # 仲間ゲット
    def _sequence(self) -> Generator[list[str], None, None]:
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]
            match i:
                case 6:
                    di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)

        # 新キャラクターインスタンス生成
        newbie = di.ref.pt.generate_ptmember()

        # メンバー上限を超える場合は除外メンバーを選択
        if di.ref.pt.add_ptmember(newbie):
            yield ["これから、よろしく！"]
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
        menu_select_ally = Menu(
            "basic", pos_x, pos_y, self.menu_shape, self.target_list, menu_width
        )
        menu_select_ally.cursor_row_offset = 2
        # サブウインドウ生成
        self.build_subwindow()
        self.build_status(newbie, self.windows["main"])
        target_member = self.allies[menu_select_ally.cursor_position[1]]
        self.build_status(target_member, self.windows["sub"])

        # キー待ち時の入力を一回捨てる
        yield [self.WAIT, "0"]

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
            yield [self.WAIT, "0"]

        if rc == WindowAction.EXECUTE:
            self.display_info.graphic_command = None
            yield [self.WAIT, "0"]
            yield ["それでは、お元気で・・・"]
            # スキルの継承
            newbie.skills.inherit_skill(target_member.skills.get_learned_skill_id())
            # 装備の継承
            target_member.equipments.inherit_equips(newbie)

            di.ref.pt.remove_ptmember(target_member.chara_id)
            di.ref.pt.add_ptmember(newbie)

        yield from self._wait_finish()

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
        status_lines += (
            f"\nＨ　Ｐ： {upper_int_spaced(param.hp, 3)}／{upper_int_spaced(param.max_hp, 3)}"
        )
        status_lines += (
            f"\nＭ　Ｐ： {upper_int_spaced(param.mp, 3)}／{upper_int_spaced(param.max_mp, 3)}"
        )
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


class NORMAL_FLGEVENT2_D(CommandBaseEvent):  # フラグイベントStep2
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class NORMAL_FLGEVENT2_E(CommandBaseEvent):  # フラグイベントStep2
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class NORMAL_FLGEVENT2_F(CommandBaseEvent):  # フラグイベントStep2
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class GAMBLE_GET_HIPOTION(CommandBaseEvent):  # 高級消耗品増
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class GAMBLE_FLGEVENT3_G(CommandBaseEvent):  # フラグイベントStep3
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class GAMBLE_FLGEVENT3_H(CommandBaseEvent):  # フラグイベントStep3
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class SAFETY_GET_JUNK(CommandBaseEvent):  # 最低装備品ゲット
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]
            match i:
                case 3:
                    di.ref.sndmgr.play_se_instant(SoundID.EVENT_PLUS)
                case 5:
                    di.ref.sndmgr.play_se_instant(SoundID.ITEM_GET)

        item_idx = diceroll(event.event_value) - 1
        ids = [
            ItemID.DAGGER,
            ItemID.MACE,
            ItemID.JAVELIN,
            ItemID.CLOTH,
            ItemID.HPBELT,
            ItemID.MPBELT,
        ]
        get_item_id = ids[item_idx]
        di.ref.pl_item.create(get_item_id)
        item_def = di.ref.itemrps.get_def(get_item_id)
        yield [f"{item_def.name}を手に入れた"]  # type: ignore

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class GAMBLE_GET_ARMORY(CommandBaseEvent):  # 装備品ゲット
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)

    # bad


class SAFETY_DECREASE_HP(CommandBaseEvent):  # HP減
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]
            match i:
                case 0:
                    di.ref.sndmgr.play_se_instant(SoundID.EVENT_MINUS)
                case 3:
                    di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)

        target_id = px.rndi(0, len(_cntx.allies) - 1)
        target = _cntx.allies[target_id]
        damage = diceroll(event.event_value)
        target.decrease_hp(damage)
        yield [f"{target.param.name}は{damage}のＨＰを失った"]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class NORMAL_DECREASE_HP(CommandBaseEvent):  # HP減
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class GAMBLE_DECREASE_HP(CommandBaseEvent):  # HP減
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class SAFETY_DECREASE_MP(CommandBaseEvent):  # MP減
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]
            match i:
                case 0:
                    di.ref.sndmgr.play_se_instant(SoundID.EVENT_MINUS)
                case 3:
                    di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)

        target_id = px.rndi(0, len(_cntx.allies) - 1)
        target = _cntx.allies[target_id]
        damage = diceroll(event.event_value)
        target.decrease_mp(damage)
        yield [f"{target.param.name}は{damage}のＭＰを失った"]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class NORMAL_DECREASE_MP(CommandBaseEvent):  # MP減
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class GAMBLE_DECREASE_MP(CommandBaseEvent):  # MP減
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class SAFETY_DECREASE_GOLD(CommandBaseEvent):  # おかね減
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        party = cast(Party, self.args[2])
        for i, msg in enumerate(event.event_messages):
            yield [msg]
            match i:
                case 1:
                    di.ref.sndmgr.play_se_instant(SoundID.EVENT_MINUS)
                case 4:
                    di.ref.sndmgr.play_se_instant(SoundID.ITEM_LOST)

        losts = diceroll(event.event_value)
        party.spend_gold(losts)
        yield [f"パーティは{losts}のお金を失った"]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class NORMAL_DECREASE_GOLD(CommandBaseEvent):  # おかね減
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class GAMBLE_DECREASE_GOLD(CommandBaseEvent):  # おかね減
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class SAFETY_DECREASE_FOOD(CommandBaseEvent):  # 食糧減
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        party = cast(Party, self.args[2])
        for i, msg in enumerate(event.event_messages):
            yield [msg]
            match i:
                case 3:
                    di.ref.sndmgr.play_se_instant(SoundID.EVENT_MINUS)
                case 4:
                    di.ref.sndmgr.play_se_instant(SoundID.ITEM_LOST)

        losts = diceroll(event.event_value)
        party.lost_foods(losts)
        yield [f"パーティは{losts}の食料を失った"]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class NORMAL_DECREASE_FOOD(CommandBaseEvent):  # 食糧減
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class GAMBLE_DECREASE_FOOD(CommandBaseEvent):  # 食糧減
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class NORMAL_LOST_POTION(CommandBaseEvent):  # 低級消耗品減
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class SAFETY_SURPRISE_BATTLE(CommandBaseEvent):  # 強制戦闘
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]
            match i:
                case 3:
                    di.ref.sndmgr.play_se_instant(SoundID.EVENT_MINUS)
                case 5:
                    di.ref.sndmgr.play_se_instant(SoundID.ENCOUNT)

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)

        di.ref.scnmgr.next_scene("battlesplash")


class NORMAL_SURPRISE_BATTLE(CommandBaseEvent):  # 強制戦闘
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1].current_point.nextevent)
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        yield from self._wait_finish()

        di.ref.scnmgr.next_scene("fixedbattle", 1, "GOLD_DRAGON_ANCIENT")


class GAMBLE_SURPRISE_BATTLE(CommandBaseEvent):  # 強制戦闘
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class GAMBLE_LOST_HIPOTION(CommandBaseEvent):  # 高級消耗品減
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)

    # boss


class BATTLE_CROWN(CommandBaseEvent):  # 宝冠の守護者　破魔に弱い
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class BATTLE_MIRROR(CommandBaseEvent):  # 神鏡の守護者　衝撃に弱い
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class BATTLE_CEPTER(CommandBaseEvent):  # 王笏の守護者　精神に弱い
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class BATTLE_GRAIL(CommandBaseEvent):  # 聖杯の守護者　呪毒に弱い
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]
            match i:
                case 3:
                    di.ref.sndmgr.play_se_instant(SoundID.EVENT_MINUS)
                case 5:
                    di.ref.sndmgr.play_se_instant(SoundID.ENCOUNT)

        # self.display_info.target.update_indicator(True)
        # while self.display_info.target.update() == WindowAction.CONTINUE:
        #     yield [self.WAIT, "0"]
        # self.display_info.target.update_indicator(False)
        yield from self._wait_finish()

        di.ref.scnmgr.next_scene("fixedbattle", 1, "GOLD_DRAGON_ANCIENT")


class BATTLE_SATAN(CommandBaseEvent):  # 魔王
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class GAMBLE_KING(CommandBaseEvent):  # 人間の王
    def _sequence(self) -> Generator[list[str], None, None]:
        _cntx = self.args[0]
        event = cast(Event, self.args[1])
        for i, msg in enumerate(event.event_messages):
            yield [msg]

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)
