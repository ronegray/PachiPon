"""menu_title.py
メニューモジュール：タイトル

"""
from gameutils.lib import Menu, WindowAction
import service_locater as di

# ロギング設定
import logging

logger = logging.getLogger(__name__)


class MenuTitle(Menu):
    def __init__(self):
        menu_pos = (180, 4)
        menu_shape = [1, 3]
        super().__init__("large", *menu_pos, menu_shape, "MenuTitle")

    def exec_menu(self) -> WindowAction:
        """選択メニュー項目の処理を実行"""
        pos_x, pos_y = self.cursor_position
        selected_item = self.menu_items[pos_y][pos_x]
        logger.info(selected_item)

        if selected_item.menu_action is None:
            logger.critical(
                f"メニューアクション関数が定義されていません：{selected_item.item_label}"
            )
            quit()

        logger.info(
            f"選択メニュー実行：{self.menu_items[self.cursor_position[1]][0].item_label}"
        )
        selected_item.menu_action(*selected_item.action_args)

        return WindowAction.DISCARD

    # タイトル画面からの遷移先は、キャンセルでタイトル画面に戻る為にスタック追加として処理
    def to_newgame(self):
        """ニューゲーム画面呼び出し"""
        di.ref.scnmgr.push_stack("map")

    def to_dataload(self):
        """データロード画面呼び出し"""
        di.ref.scnmgr.push_stack("dataload")

    def to_config(self):
        """コンフィグ画面呼び出し"""
        di.ref.scnmgr.push_stack("config")
