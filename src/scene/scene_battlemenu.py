"""
シーンモジュール：バトルメニュー

シーン：バトルのサブモジュールとして、
バトルメニューで作成した結果をコマンド化する機能を提供
"""

import logging
from gameutils.lib import WindowAction
import service_locater as di
from . import BaseScene, SceneBattle
import command.entity_command as e_cmd
from menu import MenuBattle

# ロギング設定
logger = logging.getLogger(__name__)


class SceneBattleMenu(BaseScene):
    """バトルシーン"""

    def __init__(self) -> None:
        super().__init__()
        self.situation = "battle"
        parent_scene = di.ref.scnmgr.get_now_scene()
        self.parent_draw = parent_scene.draw
        if not isinstance(parent_scene, SceneBattle):
            errmsg = f"想定外のシーンから呼び出されました：{parent_scene.__class__.__name__}"
            logger.critical(errmsg, exc_info=True)
            raise TypeError(errmsg)
        battle_data = parent_scene.transfer_battledata()
        (
            self.context,
            self.battle_commands,
            self.message_window,
            self.bgimage,
        ) = battle_data
        # キャンセル後の再実行時を考慮して担当キャラの入力済コマンドがあれば削除
        self.battle_commands.pop(self.context.actor.id, None)

        self.command_package = e_cmd.CommandPackage()
        self.wndmgr.push_stack(MenuBattle, self.context, self.command_package)

    def load_bgm(self) -> None:
        """シーン切替時のBGMロード"""
        """暫定処理：BGMロード"""
        pass

    def update(self):
        """更新処理
        - 戦闘終了フラグ時は戦闘報酬コマンド発行
        - 生存エネミーが0の場合に戦闘終了フラグON
        - コマンドスタックがある場合はコマンド処理へ抜ける
          - ない場合は生存PTメンバー分のコマンド生成をループ実行
          - コマンド数が揃ったらエネミー側コマンドと行動順を決定してコマンドスタック追加
        """

        # 基本的にメニューを回す
        # 完了またはキャンセル時の処理は
        is_submenu_open = self.wndmgr.stack_count > 1
        result = self.wndmgr.update()
        # サブメニューオープン時は確定処理を行わない
        if is_submenu_open:
            return
        match result:
            case WindowAction.CLOSE:
                """バトルメニューキャンセル時"""
                if self.context.actor.id > 0:
                    self.battle_commands.pop(self.context.actor.id - 1)
                di.ref.scnmgr.previous_scene(False)
            case WindowAction.NOTHING:
                """バトルメニュー決定完了時"""
                if self.command_package.selected_action is None:
                    errmsg = "コマンドが未定義です"
                    logger.critical(errmsg, exc_info=True)
                    raise TypeError(errmsg)
                cmd = self.command_package.selected_action
                self.battle_commands[self.context.actor.id] = cmd(
                    self.context,
                    self.message_window,
                    self.command_package.selected_args,
                )
                di.ref.scnmgr.previous_scene(False)

    def draw(self):
        """描画処理
        - 背景＝親画面（SceneBattleのdraw関数）
        - バトルメニュー
        """
        # 背景描画
        self.parent_draw()
        self.wndmgr.draw()
