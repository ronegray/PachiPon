"""
システムコマンドモジュール
"""

import logging
from typing import Generator  # , cast
import pyxel as px
import service_locater as di
from gameutils.lib import WindowAction
from const import SoundID, FOOD_UNITS
# from helper import diceroll

# from helper import diceroll_values
# import service_locater as di
# from entity import Party
# from event import Event
from field_map import PointPlaceType  # , EventPoint,
from item import ItemState
from . import CommandBaseSequence

# ロギング設定
logger = logging.getLogger(__name__)


class CommandBaseSystem(CommandBaseSequence):
    """システムに対するユーザ操作を表すコマンドの基底クラス"""

    pass


class ShopPurchase(CommandBaseSystem):
    """ショップ購入対応（スタック／インスタンス共用）"""

    def _sequence(self) -> Generator[list[str], None, None]:
        pt = self.args[0]
        item_def = self.args[1]
        func_add_pool = self.args[2]

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
            di.ref.sndmgr.play_se_instant(SoundID.SHOP_BUY)
            yield [buy_message]  # type: ignore

            # 購入処理
            pt.spend_gold(item_def.price)
            func_add_pool(item_def.def_id, ItemState.BAG)

        else:
            match eventpoint.point_type:
                case PointPlaceType.CAPITAL_CITY:
                    not_enough_message = "お客様\n当店の割引券をお持ちなのですか？"
                case PointPlaceType.TOWN:
                    not_enough_message = "ちょっと待ちなよ\nあんたの手持ちじゃ足りねえみてえだぜ"
                case PointPlaceType.VILLAGE:
                    not_enough_message = "どれどれ、ひぃふぅみぃ・・・\nこれじゃ売ってやれんのう"
            yield [not_enough_message]  # type: ignore

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        # self.display_info.target.update_indicator(False)

        match eventpoint.point_type:
            case PointPlaceType.CAPITAL_CITY:
                next_message = "他に御入用は　ございますか？"
            case PointPlaceType.TOWN:
                next_message = "他にもなんか　買ってくかい？"
            case PointPlaceType.VILLAGE:
                next_message = "そっちのもどうじゃろか？"
        yield [next_message]  # type: ignore


class PurchaseFoods(CommandBaseSystem):
    """ショップ購入対応（食料品）"""

    def _sequence(self) -> Generator[list[str], None, None]:
        pt = self.args[0]
        price = self.args[1]

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
            # px.play(self.se_ch, SoundID.SHOP_BUY, resume=True)
            di.ref.sndmgr.play_se_instant(SoundID.SHOP_BUY)
            yield [buy_message]  # type: ignore

            # 購入処理
            pt.spend_gold(price)
            pt.earn_foods(price * FOOD_UNITS)

        else:
            match eventpoint.point_type:
                case PointPlaceType.CAPITAL_CITY:
                    not_enough_message = "お客様\n当店の割引券をお持ちなのですか？"
                case PointPlaceType.TOWN:
                    not_enough_message = "ちょっと待ちなよ\nあんたの手持ちじゃ足りねえみてえだぜ"
                case PointPlaceType.VILLAGE:
                    not_enough_message = "どれどれ、ひぃふぅみぃ・・・\nこれじゃ売ってやれんのう"
            yield [not_enough_message]  # type: ignore

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        # self.display_info.target.update_indicator(False)

        match eventpoint.point_type:
            case PointPlaceType.CAPITAL_CITY:
                next_message = "他に御入用は　ございますか？"
            case PointPlaceType.TOWN:
                next_message = "他にもなんか　買ってくかい？"
            case PointPlaceType.VILLAGE:
                next_message = "そっちのもどうじゃろか？"
        yield [next_message]  # type: ignore


class SellEquip(CommandBaseSystem):
    """装備下取り"""

    def _sequence(self) -> Generator[list[str], None, None]:
        pt = self.args[0]
        item_iid, item_def, sellprice = self.args[1]
        pool_item = self.args[2]

        eventpoint = pt.get_current_point()
        # 所持金チェック
        match eventpoint.point_type:
            case PointPlaceType.CAPITAL_CITY:
                sell_message = "それでは、こちらお受け取りください"
            case PointPlaceType.TOWN:
                sell_message = "んじゃこいつだ！確かめてくんな！"
            case PointPlaceType.VILLAGE:
                sell_message = "足りるかの・・・おお、あったあった"
        # px.play(self.se_ch, SoundID.SHOP_BUY, resume=True)
        di.ref.sndmgr.play_se_instant(SoundID.SHOP_BUY)
        yield [sell_message]  # type: ignore

        # 売却処理
        pt.earn_gold(sellprice)
        pool_item.destroy(item_iid)
        print(f"sell={item_iid}")

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        # self.display_info.target.update_indicator(False)

        match eventpoint.point_type:
            case PointPlaceType.CAPITAL_CITY:
                next_message = "よいお取引に感謝いたします"
            case PointPlaceType.TOWN:
                next_message = "またいいもん持ってきてくれよ！"
            case PointPlaceType.VILLAGE:
                next_message = "さて、いくらで売れるかの・・・"
        self.display_info.target.update_indicator(True)
        yield [next_message]  # type: ignore
        # self.display_info.target.update_indicator(False)


class BattleStartEffect(CommandBaseSystem):
    """戦闘開始エフェクト"""

    def _sequence(self) -> Generator[list[str], None, None]:
        circle_size = 1
        circle_center = (px.width // 2, px.height // 2)
        circle_max = px.sqrt(circle_center[0] ** 2 + circle_center[1] ** 2)

        while circle_size < circle_max:
            self.display_info.graphic_command = [
                lambda: px.dither(circle_size / circle_max),
                lambda: px.circ(*circle_center, circle_size, px.COLOR_BLACK),
                lambda: px.dither(1),
            ]
            circle_size += 6
            yield [self.WAIT, "0"]
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
        # px.play(self.se_ch, SoundID.TURN_DAMAGE, resume=True)
        di.ref.sndmgr.play_se_instant(SoundID.TURN_DAMAGE)
        yield [self.WAIT, "0"]
