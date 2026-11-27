"""
イベントコマンドモジュール
"""

import logging
import sys
from random import choice
from typing import Generator, Callable
import pyxel as px
import service_locater as di
from gameutils.lib import WindowAction, Menu, Window, MENU_WINDOW_TYPE
from const import SoundID
from helper import diceroll, upper_int_spaced, format_leftright
from flag import FlagID
from item import ItemID
from event import Event, EventID, EventType
from field_map import EventPoint
from . import CommandBaseEntity, SeqSubCmd, CommandBaseSequence

# ロギング設定
logger = logging.getLogger(__name__)


class PlayEvent(CommandBaseEntity):
    """イベント用共通クラス"""

    def _sequence(self) -> Generator[list, None, None]:
        """アイテム利用の殻"""
        event_point: EventPoint = self.kwargs["event_point"]
        self.event: Event = event_point.nextevent  # type: ignore
        event_func = getattr(sys.modules[__name__], self.event.event_id.name.lower())  # type: ignore

        if self.event.event_value:
            """メッセージ＋効果の場合は先にメッセージ処理
            効果とメッセージが前後するもの(event_value=0)は効果関数内でメッセージ処理呼び出し"""
            yield from self.play_event_message()

        # イベント個別の処理実行
        yield from event_func(self)

        yield from self.wait_finish()
        return

    def play_event_message(self) -> Generator[list, None, None]:
        """メッセージ処理"""
        for msg in self.event.event_messages:
            yield [msg]

#     # good


def increase_hp(cmd: PlayEvent) -> Generator[list, None, None]:
    """HP回復イベント"""

    yield [SeqSubCmd.SE_INSTANT, SoundID.RECOVER]
    for mem in cmd.ctx.allies:
        recover = diceroll(cmd.event.event_value)
        mem.increase_hp(recover)
        yield [f"{mem.param.name}のＨＰが{recover}回復した"]


def increase_mp(cmd: PlayEvent) -> Generator[list, None, None]:
    """MP回復イベント"""

    yield [SeqSubCmd.SE_INSTANT, SoundID.RECOVER]
    for mem in cmd.ctx.allies:
        recover = diceroll(cmd.event.event_value)
        mem.increase_mp(recover)
        yield [f"{mem.param.name}のＭＰが{recover}回復した"]


def increase_gold(cmd: PlayEvent) -> Generator[list, None, None]:
    """集金イベント"""

    gets = diceroll(cmd.event.event_value)
    yield [SeqSubCmd.SE_INSTANT, SoundID.ITEM_GET]
    di.ref.pt.earn_gold(gets)
    yield [f"パーティは{gets}のお金を手に入れた"]


def increase_food(cmd: PlayEvent) -> Generator[list, None, None]:
    """収穫イベント"""

    gets = diceroll(cmd.event.event_value)
    yield [SeqSubCmd.SE_INSTANT, SoundID.ITEM_GET]
    di.ref.pt.earn_foods(gets)
    yield [f"パーティは{gets}の食料を手に入れた"]


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


def flgevent1_a(self) -> Generator[list, None, None]:
    yield from flag_event_flow(self, FlagID.JADEEYE, ItemID.JADEEYE)


def flgevent1_b(self) -> Generator[list, None, None]:
    yield from flag_event_flow(self, FlagID.CROSS, ItemID.CROSS)


def flgevent1_c(self) -> Generator[list, None, None]:
    yield from flag_event_flow(self, FlagID.CRYSTALROD, ItemID.CRYSTALROD)


def get_potion(cmd: PlayEvent) -> Generator[list, None, None]:
    """薬獲得イベント"""

    yield [SeqSubCmd.SE_INSTANT, SoundID.ITEM_GET]
    item_def = di.ref.pt.get_item(ItemID.HEALPOT)
    yield [f"{item_def.name}を拾った"]


class MeetAlly(CommandBaseSequence):  # 仲間ゲット
    def _sequence(self) -> Generator[list, None, None]:
        event = self.kwargs["event"]
        for msg in event.event_messages:
            yield [msg]

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


def flgevent2_d(self) -> Generator[list, None, None]:
    yield from flag_event_flow(self, FlagID.DRAGONFANG, ItemID.DRAGONFANG, [FlagID.JADEEYE, FlagID.CROSS])


def flgevent2_e(self) -> Generator[list, None, None]:
    yield from flag_event_flow(self, FlagID.TARISMAN, ItemID.TARISMAN, [FlagID.CRYSTALROD, FlagID.CROSS])


def flgevent2_f(self) -> Generator[list, None, None]:
    yield from flag_event_flow(self, FlagID.HOLYSHROUD, ItemID.HOLYSHROUD, [FlagID.CRYSTALROD, FlagID.JADEEYE])


def get_hipotion(cmd: PlayEvent) -> Generator[list, None, None]:
    """高級薬獲得イベント"""

    yield [SeqSubCmd.SE_INSTANT, SoundID.ITEM_GET]
    item_def = di.ref.pt.get_item(ItemID.HIHEALPOT)
    yield [f"{item_def.name}を手に入れた"]


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

    target = choice(di.ref.pt.get_active_member())
    damage = diceroll(cmd.event.event_value)
    yield [SeqSubCmd.SE_INSTANT, SoundID.DAMAGE_TAKEN]
    target.decrease_hp(damage)
    yield [f"{target.param.name}は{damage}のＨＰを失った"]


def decrease_mp(cmd: PlayEvent) -> Generator[list, None, None]:
    """MP消耗イベント"""

    target = choice(di.ref.pt.get_active_member())
    damage = diceroll(cmd.event.event_value)
    yield [SeqSubCmd.SE_INSTANT, SoundID.DAMAGE_TAKEN]
    target.decrease_mp(damage)
    yield [f"{target.param.name}は{damage}のＭＰを失った"]


def decrease_gold(cmd: PlayEvent) -> Generator[list, None, None]:
    """課金(仮)イベント"""

    losts = diceroll(cmd.event.event_value)
    yield [SeqSubCmd.SE_INSTANT, SoundID.ITEM_LOST]
    di.ref.pt.spend_gold(losts)
    yield [f"パーティは{losts}のお金を失った"]


def decrease_food(cmd: PlayEvent) -> Generator[list, None, None]:
    """食品廃棄イベント"""

    losts = diceroll(cmd.event.event_value)
    yield [SeqSubCmd.SE_INSTANT, SoundID.ITEM_LOST]
    di.ref.pt.lost_foods(losts)
    yield [f"パーティは{losts}の食料を失った"]


def lost_bottle(cmd: PlayEvent, item_ids: list[ItemID]) -> Generator[list, None, None]:
    item_def = di.ref.itemrps.get_def(choice(item_ids))
    if di.ref.pl_stack.count(item_def.def_id):
        yield [SeqSubCmd.SE_INSTANT, SoundID.ITEM_LOST]
        yield [f"{item_def.name}を割ってしまった…"]
    else:
        yield ["割れたのは空瓶だったようだ"]


def lost_potion(cmd: PlayEvent) -> Generator[list, None, None]:
    """薬破損イベント"""

    yield from lost_bottle(cmd, [ItemID.HEALPOT, ItemID.MAGICPOT])


def lost_hipotion(cmd: PlayEvent) -> Generator[list, None, None]:
    """高級薬破損イベント"""

    yield from lost_bottle(cmd, [ItemID.HIHEALPOT, ItemID.HIMAGICPOT])


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
        self.event = di.ref.evtrps.get_event(EventType.SAFETY, EventID.GRAIL)  # type: ignore
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

