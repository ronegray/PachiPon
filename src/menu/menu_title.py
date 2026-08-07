"""menu_title.py
メニューモジュール：タイトル
"""

import logging
import pyxel as px
from gameutils.lib import (
    Menu,
    WindowAction,
    ExecResult,
    RsltContinue,
)
import service_locater as di

# ロギング設定
logger = logging.getLogger(__name__)


class MenuTitle(Menu):
    def __init__(self):
        menu_pos = (157, 4)
        menu_shape = [1, 3]
        super().__init__("large", *menu_pos, menu_shape, "MenuTitle")

    def key_check(self) -> WindowAction:
        """キー入力の確認と応答"""
        if self.move_cursor():
            # pass
            px.play(self.se_ch, self.ui_se["CURSOR_VERTICAL"], resume=True)
        elif self.inputkey.decide():
            px.play(self.se_ch, self.ui_se["DECIDE"], resume=True)
            return WindowAction.EXECUTE
        return WindowAction.CONTINUE

    def exec_menu(self) -> ExecResult:
        """選択メニュー項目の処理を実行"""
        pos_x, pos_y = self.cursor_position
        selected_item = self.menu_items[pos_y][pos_x]
        logger.info(selected_item)

        if selected_item.menu_action is None:
            errmsg = f"メニューアクション関数が定義されていません：{selected_item.item_label}"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)

        logger.info(
            f"選択メニュー実行：{self.menu_items[self.cursor_position[1]][0].item_label}"
        )
        selected_item.menu_action(*selected_item.action_args)

        return RsltContinue()

    # タイトル画面からの遷移先は、キャンセルでタイトル画面に戻る為にスタック追加として処理
    def to_newgame(self):
        """ニューゲーム画面呼び出し"""
        di.ref.scnmgr.next_scene("newgame")

    def to_dataload(self):
        """データロード画面呼び出し"""
        di.ref.scnmgr.next_scene("dataload")

    def to_config(self):
        """コンフィグ画面呼び出し"""
        di.ref.scnmgr.next_scene("config")
