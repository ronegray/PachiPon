"""
システムコマンドモジュール
CommandProtocol
└CommandBaseSequenceを継承する、最も基礎的な構成のコマンド
"""

import logging
from typing import Generator  # , cast
import pyxel as px
import service_locater as di

from gameutils.base import is_pressed

# from gameutils.lib import WindowAction
from const import SoundID, FOOD_UNITS, APP_FPS
# from helper import diceroll

# from helper import diceroll_values
# import service_locater as di
# from entity import Party
# from event import Event
from field_map import PointPlaceType  # , EventPoint,
from item import ItemState
from . import CommandBaseSequence, SeqSubCmd, effect_command as efx_cmd

# ロギング設定
logger = logging.getLogger(__name__)


class CommonFieldMessage(CommandBaseSequence):
    """汎用メッセージ表示処理"""

    def _sequence(self) -> Generator[list, None, None]:
        # message_list = self.args[0]
        # for msg in message_list:
        for msg in self.kwargs["msg_list"]:
            yield [msg]

        yield from self._wait_finish()


class PartyDefeated(CommandBaseSequence):
    """パーティー全滅時処理"""

    def _sequence(self) -> Generator[list, None, None]:
        # フェード用背景画像コピー
        bg: px.Image = self.kwargs["bgimage"]
        w, h = px.width, px.height
        fade_bgimage = px.Image(w, h)
        fade_bgimage.blt(0, 0, bg, 0, 0, w, h)
        # 背景&BGMフェード
        i = 1
        di.ref.sndmgr.stop_music_fadeout(APP_FPS * 5)
        while True:
            self.display_info.graphic_command = [
                lambda alpha=i: bg.dither(alpha),
                lambda: bg.cls(0),
                lambda: bg.blt(0, 0, fade_bgimage, 0, 0, px.width, px.height),
            ]
            i -= 0.015
            if i < 0:
                if di.ref.sndmgr.get_fade_state():
                    # 全滅後のエネミー行動キャンセルの為、データクリア
                    # self.args[1].clear()
                    self.kwargs["enemies"].clear()
                    break
            yield [SeqSubCmd.WAIT, 0]
        # 全滅BGM再生
        di.ref.sndmgr.request_bgm("defeat")
        messages = [
            ["やられたョ！", "　　♰ 全員　死亡 ♰ "],
            [SeqSubCmd.WAIT, 3],
            ["", "・・・慌てる事はありません"],
            [SeqSubCmd.WAIT, 2],
            ["", "あなたに再び立ち上がり、戦う力を与えましょう"],
            [SeqSubCmd.WAIT, 2],
            ["", "啓示を得た者がそこを訪れ、王城へと連れ帰ってくれます"],
            [SeqSubCmd.WAIT, 2],
            ["", "彼の地でゆっくり傷を癒やすとよいでしょう"],
            [""],
            [""],
            [""],
            [SeqSubCmd.WAIT, 2],
            ["これだけの業を振るったのです"],
            [SeqSubCmd.WAIT, 3],
            ["", "少しの供物を頂いておきますよ？"],
        ]
        for msg in messages:
            if is_pressed("cancel"):
                break
            yield msg

        # お供え物
        # di.ref.sndmgr.play_se_instant(SoundID.ITEM_LOST)
        yield [SeqSubCmd.SE_INSTANT, SoundID.ITEM_LOST]
        offering_foods = di.ref.pt._pt_foods // 2
        di.ref.pt.lost_foods(offering_foods)
        offering_golds = int(di.ref.pt._pt_golds * 0.1)
        di.ref.pt.spend_gold(offering_golds)

        # イベントポイントの待機化
        penalty_turns = max(1, int(di.ref.pt.average_level // 10))
        di.ref.map.defeated_penalty(penalty_turns)

        yield from self._wait_finish()

        # スタート地点へ戻る
        di.ref.pt.set_current_point("p01")
        di.ref.pt._pt_is_moving = False
        di.ref.pt.set_current_route()
        di.ref.pt._field_sprite._is_moving = False

        di.ref.scnmgr.change_scene("map")

        return


class ShopPurchase(CommandBaseSequence):
    """ショップ購入対応（スタック／インスタンス共用）"""

    def _sequence(self) -> Generator[list, None, None]:
        # pt = self.args[0]
        # item_def = self.args[1]
        # func_add_pool = self.args[2]
        pt = self.kwargs["party"]
        item_def = self.kwargs["item_def"]
        func_add_pool = self.kwargs["func_add_pool"]

        eventpoint = pt.get_current_point()
        # pt._pt_golds = 99999
        # 所持金チェック
        if pt._pt_golds >= item_def.price:
            match eventpoint.point_type:
                case PointPlaceType.CAPITAL_CITY:
                    buy_message = "お買い上げ　誠にありがとうございます"
                case PointPlaceType.TOWN:
                    buy_message = "よし売った！ありがとよ！"
                case PointPlaceType.VILLAGE:
                    buy_message = "どうもおおきにのう～"
            # px.play(self.se_ch, SoundID.SHOP_BUY, resume=True)
            # di.ref.sndmgr.play_se_instant(SoundID.SHOP_BUY)
            yield [SeqSubCmd.SE_INSTANT, SoundID.SHOP_BUY]
            yield [buy_message]  # type: ignore

            # 購入処理
            pt.spend_gold(item_def.price)
            func_add_pool(item_def.def_id, ItemState.BAG)

        else:
            match eventpoint.point_type:
                case PointPlaceType.CAPITAL_CITY:
                    not_enough_message = "当店では値引交渉はお受けしておりません"
                case PointPlaceType.TOWN:
                    not_enough_message = "あんたの手持ちじゃ足りねえみてえだぜ"
                case PointPlaceType.VILLAGE:
                    not_enough_message = "どれどれ・・・これじゃ売ってやれんのう"
            yield [not_enough_message]  # type: ignore

        # self.display_info.target.update_indicator(True)
        # while self.display_info.target.update() == WindowAction.CONTINUE:
        #     yield [SeqSubCmd.WAIT, 0]
        # # self.display_info.target.update_indicator(False)
        yield from self._wait_finish()

        match eventpoint.point_type:
            case PointPlaceType.CAPITAL_CITY:
                next_message = "他に御入用は　ございますか？"
            case PointPlaceType.TOWN:
                next_message = "他にもなんか　買ってくかい？"
            case PointPlaceType.VILLAGE:
                next_message = "そっちのもどうじゃろか？"
        yield [next_message]  # type: ignore
        yield from self._wait_finish()


class PurchaseFoods(CommandBaseSequence):
    """ショップ購入対応（食料品）"""

    def _sequence(self) -> Generator[list, None, None]:
        # pt = self.args[0]
        # price = self.args[1]
        pt = self.kwargs["party"]
        price = self.kwargs["price"]

        eventpoint = pt.get_current_point()
        # 所持金チェック
        if pt._pt_golds >= price:
            match eventpoint.point_type:
                case PointPlaceType.CAPITAL_CITY:
                    buy_message = "最高級シェフの手になる自慢の一品でございます"
                case PointPlaceType.TOWN:
                    buy_message = "うちのを食ったら他のは食えねえぜ！"
                case PointPlaceType.VILLAGE:
                    buy_message = "ばあさんの手作りじゃぞい"
            # # px.play(self.se_ch, SoundID.SHOP_BUY, resume=True)
            # di.ref.sndmgr.play_se_instant(SoundID.SHOP_BUY)
            yield [SeqSubCmd.SE_INSTANT, SoundID.SHOP_BUY]
            yield [buy_message]  # type: ignore

            # 購入処理
            pt.spend_gold(price)
            pt.earn_foods(price * FOOD_UNITS)

        else:
            match eventpoint.point_type:
                case PointPlaceType.CAPITAL_CITY:
                    not_enough_message = "当店では値引交渉はお受けしておりません"
                case PointPlaceType.TOWN:
                    not_enough_message = "あんたの手持ちじゃ足りねえみてえだぜ"
                case PointPlaceType.VILLAGE:
                    not_enough_message = "どれどれ・・・これじゃ売ってやれんのう"
            yield [not_enough_message]  # type: ignore

        # self.display_info.target.update_indicator(True)
        # while self.display_info.target.update() == WindowAction.CONTINUE:
        #     yield [SeqSubCmd.WAIT, 0]
        # # self.display_info.target.update_indicator(False)
        yield from self._wait_finish()

        match eventpoint.point_type:
            case PointPlaceType.CAPITAL_CITY:
                next_message = "他に御入用は　ございますか？"
            case PointPlaceType.TOWN:
                next_message = "他にもなんか　買ってくかい？"
            case PointPlaceType.VILLAGE:
                next_message = "そっちのもどうじゃろか？"
        yield [next_message]  # type: ignore
        yield from self._wait_finish()


class SellEquip(CommandBaseSequence):
    """装備下取り"""

    def _sequence(self) -> Generator[list, None, None]:
        # pt = self.args[0]
        # item_iid, item_def, sellprice = self.args[1]
        # pool_item = self.args[2]
        pt = self.kwargs["party"]
        item_iid, _, sellprice = self.kwargs["item_info"]
        pool_item = self.kwargs["pool_item"]

        eventpoint = pt.get_current_point()
        # 所持金チェック
        match eventpoint.point_type:
            case PointPlaceType.CAPITAL_CITY:
                sell_message = "それでは、こちらお受け取りください"
            case PointPlaceType.TOWN:
                sell_message = "んじゃこいつだ！確かめてくんな！"
            case PointPlaceType.VILLAGE:
                sell_message = "足りるかの・・・おお、あったあった"
        # # px.play(self.se_ch, SoundID.SHOP_BUY, resume=True)
        # di.ref.sndmgr.play_se_instant(SoundID.SHOP_BUY)
        yield [SeqSubCmd.SE_INSTANT, SoundID.SHOP_BUY]
        yield [sell_message]  # type: ignore

        # 売却処理
        pt.earn_gold(sellprice)
        pool_item.destroy(item_iid)
        logger.debug(f"sell={item_iid}")

        # # self.display_info.target.update_indicator(True)
        # # while self.display_info.target.update() == WindowAction.CONTINUE:
        # #     yield [SeqSubCmd.WAIT, 0]
        # # # self.display_info.target.update_indicator(False)
        # yield from self._wait_finish()

        match eventpoint.point_type:
            case PointPlaceType.CAPITAL_CITY:
                next_message = "よいお取引に感謝いたします"
            case PointPlaceType.TOWN:
                next_message = "またいいもん持ってきてくれよ！"
            case PointPlaceType.VILLAGE:
                next_message = "さて、いくらで売れるかの・・・"
        # self.display_info.target.update_indicator(True)
        yield ["", next_message]  # type: ignore
        # self.display_info.target.update_indicator(False)
        yield from self._wait_finish()


# class BattleStartEffect(CommandBaseSequence):
#     """戦闘開始エフェクト"""

#     def _sequence(self) -> Generator[list, None, None]:
#         circle_size = 1
#         circle_center = (px.width // 2, px.height // 2)
#         circle_max = px.sqrt(circle_center[0] ** 2 + circle_center[1] ** 2)

#         while circle_size < circle_max:
#             self.display_info.graphic_command = [
#                 lambda: px.dither(circle_size / circle_max),
#                 lambda: px.circ(*circle_center, circle_size, px.COLOR_BLACK),
#                 lambda: px.dither(1),
#             ]
#             circle_size += 6
#             yield [SeqSubCmd.WAIT, 0]
#         return


class FoodShortageMessage(CommandBaseSequence):
    """フードが消費量に満たない場合の警告"""

    def _sequence(self) -> Generator[list, None, None]:
        yield ["食糧が　足りなくなった"]
        yield [
            "ターン経過毎に ＨＰとＭＰが５％ずつ",
            "減少してしまう・・・",
        ]
        # while self.display_info.target.update() == WindowAction.CONTINUE:
        #     yield [SeqSubCmd.WAIT, 0]
        yield from self._wait_finish()


class FoodShortageEffect(CommandBaseSequence):
    """フードが消費量に満たない場合の画面エフェクト"""

    def _sequence(self) -> Generator[list, None, None]:
        # self.display_info.graphic_command = [
        #     lambda: px.dither(0.5),
        #     lambda: px.rect(0, 0, px.width, px.height, px.COLOR_RED),
        #     lambda: px.dither(1),
        # ]
        # # # px.play(self.se_ch, SoundID.TURN_DAMAGE, resume=True)
        # # di.ref.sndmgr.play_se_instant(SoundID.TURN_DAMAGE)
        # # yield [SeqSubCmd.WAIT, 0]
        # yield [SeqSubCmd.SE_SUSTAIN, SoundID.TURN_DAMAGE]

        yield [SeqSubCmd.SE_SUSTAIN, SoundID.TURN_DAMAGE]
        yield from efx_cmd.efx_screen_flash(self.display_info, px.COLOR_RED)
        yield from efx_cmd.efx_damage_shake(self.display_info, di.ref.pt.get_member())
        # yield from efx_cmd.efx_screen_flash(self.display_info, px.COLOR_RED)
