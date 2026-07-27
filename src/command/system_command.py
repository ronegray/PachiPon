"""
システムコマンドモジュール
"""
import logging

# from abc import abstractmethod
from typing import Generator, cast
import pyxel as px
from gameutils.lib import WindowAction  # , Window,
from field_map import EventPoint
from const import SoundID

# from const import COMMAND_STEPWAIT_FRAME
# from . import CommandBase, CommandPhase, DisplayInfo
import service_locater as di
from . import CommandBaseSequence

# ロギング設定
logger = logging.getLogger(__name__)


class CommandBaseSystem(CommandBaseSequence):
    """システムに対するユーザ操作を表すコマンドの基底クラス"""

    pass
    # WAIT = "wait"  # 待機を示すリターンコマンド

    # def __init__(self, wnd: Window, *args, **kwargs) -> None:
    #     """初期化：コンテキストの引継"""
    #     self.display_info: DisplayInfo = DisplayInfo(wnd)
    #     self.step_wait = COMMAND_STEPWAIT_FRAME  # メッセージ待ち間隔
    #     self.se_no = 0  # サウンドエフェクトの番号
    #     self.args = args
    #     self.kwargs = kwargs
    #     self.phase = CommandPhase.SYN

    # @abstractmethod
    # def _sequence(self) -> Generator[list[str], None, None]:
    #     ...
    #     # """サブクラスが実装すべき処理シーケンス"""

    # def update(self) -> CommandPhase:
    #     match self.phase:
    #         case CommandPhase.SYN:
    #             self.display_info.target.message_list.clear()
    #             self._gen = self._sequence()
    #             self._advance()
    #             self.phase = CommandPhase.ACK
    #         case CommandPhase.ACK:
    #             if (
    #                 self.display_info.target.update() == WindowAction.DISCARD
    #                 or self.step_wait < 0
    #             ):
    #                 self._advance()
    #             self.step_wait -= 1
    #     return self.phase

    # def _advance(self):
    #     try:
    #         result = next(self._gen)
    #         if result:
    #             if result[0] == self.WAIT:
    #                 self.step_wait = int(result[1]) * COMMAND_STEPWAIT_FRAME
    #             else:
    #                 self.display_info.message = result
    #                 self.display_info.is_change = True
    #                 self.step_wait = COMMAND_STEPWAIT_FRAME
    #         else:
    #             self.step_wait = 0
    #     except StopIteration:
    #         self.phase = CommandPhase.FIN

    # def draw(self) -> DisplayInfo:
    #     """コマンド描画情報送信"""
    #     return self.display_info


class BattleStartEffect(CommandBaseSystem):
    """戦闘開始エフェクト"""

    def _sequence(self) -> Generator[list[str], None, None]:
        circle_size = 1
        circle_center = (px.width // 2, px.height // 2)
        circle_max = px.sqrt(circle_center[0] ** 2 + circle_center[1] ** 2)

        while circle_size < circle_max:
            # px.dither(circle_size / circle_max)

            self.display_info.graphic_command = [
                lambda: px.dither(circle_size / circle_max),
                # lambda: px.dither(0.1),
                lambda: px.circ(*circle_center, circle_size, px.COLOR_BLACK),
                lambda: px.dither(1),
            ]
            # px.dither(1)
            circle_size += 6
            yield [self.WAIT, "0"]

        # # ここで勝利SEとBGMロード
        # len_fanfale = "1"
        # yield ["敵との戦闘に　勝利した！！"]
        # yield [""]
        # yield [self.WAIT, len_fanfale]  # 勝利SEの長さを文字で返す

        # # お金
        # reward_gold = sum([enemy.eparam.gold for enemy in enemy_list])
        # pt.earn_gold(reward_gold)
        # yield [f"パーティーは　{reward_gold}ゴールド　の儲け"]

        # # 経験値はメンバー人数割りで死亡者も全員獲得
        # reward_exp = sum([enemy.param.exp for enemy in enemy_list])
        # num = pt.get_member_count()
        # for member in pt.get_allmember():
        #     getexp = px.ceil(reward_exp / num)
        #     member.gain_exp(getexp)
        #     yield [f"{member.param.name}は　経験値{getexp}　を稼いだ！"]

        return


class FoodShortageMessage(CommandBaseSystem):
    """フードが消費量に満たない場合の警告"""

    def _sequence(self) -> Generator[list[str], None, None]:
        yield [
            "食糧が　足りなくなった",
            "ターン経過毎に ＨＰとＭＰが５％ずつ",
            "減少してしまう・・・",
        ]
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]


class FoodShortageEffect(CommandBaseSystem):
    """フードが消費量に満たない場合の画面エフェクト"""

    def _sequence(self) -> Generator[list[str], None, None]:
        self.display_info.graphic_command = [
            lambda: px.dither(0.5),
            lambda: px.rect(0, 0, px.width, px.height, px.COLOR_RED),
            lambda: px.dither(1),
        ]
        px.play(self.se_ch, SoundID.TURN_DAMAGE, resume=True)
        yield [self.WAIT, "0"]


class KickEvent(CommandBaseSystem):
    """フィールドイベント起動処理"""

    def _sequence(self) -> Generator[list[str], None, None]:
        point = cast(EventPoint, self.args[0])
        dices = point.kick_event()
        # effect = DiceRollEffect()
        # effect.load_diceimage()
        effect = di.ref.efxdice
        roll_frames = 60
        effect.start(dices, roll_frames)
        yield ["何が起こるか", "　おたのしみ！"]
        px.play(self.se_ch, SoundID.DICE_ROLL, resume=True)
        while effect.is_rolling:
            effect.update()
            self.display_info.graphic_command = effect.get_draw_commands()
            yield ["wait", "0"]
        yield [f"出た目は・・・　{effect.total}"]
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        for event_id, event_stat in point.event_list.event_stat.items():
            if effect.total >= event_stat.threshold:
                event_stat.is_opened = True
                point.rise_event(event_id)
                break

    # good


class SAFETY_INCREASE_HP(CommandBaseSystem):
    def _sequence(self) -> Generator[list[str], None, None]:
        # event_type = self.args[0]
        # event_value = self.args[1]

        yield ["HP回復イベント"]
        yield ["なんか"]
        yield ["メッセージが"]
        yield ["流れたあとに"]
        px.play(self.se_ch, SoundID.EVENT_PLUS, resume=True)
        yield ["なんか"]
        yield ["効果が"]
        px.play(self.se_ch, SoundID.RECOVER, resume=True)
        yield ["発生する感じ"]

        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]


class NORMAL_INCREASE_HP(CommandBaseSystem):  # HP増
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class GAMBLE_INCREASE_HP(CommandBaseSystem):  # HP増
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class SAFETY_INCREASE_MP(CommandBaseSystem):  # MP増
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class NORMAL_INCREASE_MP(CommandBaseSystem):  # MP増
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class GAMBLE_INCREASE_MP(CommandBaseSystem):  # MP増
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class SAFETY_INCREASE_GOLD(CommandBaseSystem):  # おかね増
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class NORMAL_INCREASE_GOLD(CommandBaseSystem):  # おかね増
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class GAMBLE_INCREASE_GOLD(CommandBaseSystem):  # おかね増
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class SAFETY_INCREASE_FOOD(CommandBaseSystem):  # 食糧増
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class NORMAL_INCREASE_FOOD(CommandBaseSystem):  # 食糧増
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class GAMBLE_INCREASE_FOOD(CommandBaseSystem):  # 食糧増
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class SAFETY_FLGEVENT1_A(CommandBaseSystem):  # フラグイベントStep1
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class SAFETY_FLGEVENT1_B(CommandBaseSystem):  # フラグイベントStep1
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class SAFETY_FLGEVENT1_C(CommandBaseSystem):  # フラグイベントStep1
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class NORMAL_GET_POTION(CommandBaseSystem):  # 低級消耗品増
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class NORMAL_MEET_ALLY(CommandBaseSystem):  # 仲間ゲット
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class NORMAL_FLGEVENT2_D(CommandBaseSystem):  # フラグイベントStep2
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class NORMAL_FLGEVENT2_E(CommandBaseSystem):  # フラグイベントStep2
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class NORMAL_FLGEVENT2_F(CommandBaseSystem):  # フラグイベントStep2
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class GAMBLE_GET_HIPOTION(CommandBaseSystem):  # 高級消耗品増
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class GAMBLE_FLGEVENT3_G(CommandBaseSystem):  # フラグイベントStep3
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class GAMBLE_FLGEVENT3_H(CommandBaseSystem):  # フラグイベントStep3
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class SAFETY_GET_JUNK(CommandBaseSystem):  # 最低装備品ゲット
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class GAMBLE_GET_ARMORY(CommandBaseSystem):  # 装備品ゲット
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]

    # bad


class SAFETY_DECREASE_HP(CommandBaseSystem):  # HP減
    def _sequence(self) -> Generator[list[str], None, None]:
        # event_type = self.args[0]
        # event_value = self.args[1]

        yield ["HP回復イベント"]
        yield ["なんか"]
        yield ["メッセージが"]
        yield ["流れたあとに"]
        px.play(self.se_ch, SoundID.EVENT_MINUS, resume=True)
        yield ["なんか"]
        yield ["効果が"]
        px.play(self.se_ch, SoundID.MP_DECREASE, resume=True)
        yield ["発生する感じ"]

        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]


class NORMAL_DECREASE_HP(CommandBaseSystem):  # HP減
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class GAMBLE_DECREASE_HP(CommandBaseSystem):  # HP減
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class SAFETY_DECREASE_MP(CommandBaseSystem):  # MP減
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class NORMAL_DECREASE_MP(CommandBaseSystem):  # MP減
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class GAMBLE_DECREASE_MP(CommandBaseSystem):  # MP減
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class SAFETY_DECREASE_GOLD(CommandBaseSystem):  # おかね減
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class NORMAL_DECREASE_GOLD(CommandBaseSystem):  # おかね減
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class GAMBLE_DECREASE_GOLD(CommandBaseSystem):  # おかね減
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class SAFETY_DECREASE_FOOD(CommandBaseSystem):  # 食糧減
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class NORMAL_DECREASE_FOOD(CommandBaseSystem):  # 食糧減
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class GAMBLE_DECREASE_FOOD(CommandBaseSystem):  # 食糧減
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class NORMAL_LOST_POTION(CommandBaseSystem):  # 低級消耗品減
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class SAFETY_SURPRISE_BATTLE(CommandBaseSystem):  # 強制戦闘
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class NORMAL_SURPRISE_BATTLE(CommandBaseSystem):  # 強制戦闘
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class GAMBLE_SURPRISE_BATTLE(CommandBaseSystem):  # 強制戦闘
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class GAMBLE_LOST_HIPOTION(CommandBaseSystem):  # 高級消耗品減
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]

    # boss


class BATTLE_CROWN(CommandBaseSystem):  # 宝冠の守護者　破魔に弱い
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class BATTLE_MIRROR(CommandBaseSystem):  # 神鏡の守護者　衝撃に弱い
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class BATTLE_CEPTER(CommandBaseSystem):  # 王笏の守護者　精神に弱い
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class BATTLE_GRAIL(CommandBaseSystem):  # 聖杯の守護者　呪毒に弱い
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class BATTLE_SATAN(CommandBaseSystem):  # 魔王
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]


class GAMBLE_KING(CommandBaseSystem):  # 人間の王
    def _sequence(self) -> Generator[list[str], None, None]:
        yield [""]
