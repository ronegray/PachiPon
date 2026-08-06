"""
シーンモジュール：フィールドイベント

シーン：フィールドのサブモジュールとして、
イベントコマンドの実行機能を提供
"""

import logging
import pyxel as px
from const import APP_WIDTH, APP_HEIGHT
from gameutils.lib import Window  # , WindowAction, WindowInputHandler
import service_locater as di
from gameutils.base import check_file, read_string  # is_pressed,
from . import BaseScene, SceneField
# import command.entity_command as e_cmd
# from menu import MenuBattle

# ロギング設定
logger = logging.getLogger(__name__)


class SceneFieldEvent(BaseScene):
    """イベントシーン"""

    def __init__(self) -> None:
        super().__init__()
        self.situation = "system"

        parent_scene = di.ref.scnmgr.get_now_scene()
        if not isinstance(parent_scene, SceneField):
            errmsg = (
                f"想定外のシーンから呼び出されました：{parent_scene.__class__.__name__}"
            )
            logger.critical(errmsg, exc_info=True)
            raise TypeError(errmsg)

        # # 背景用に直前画面のスクリーンポインタからイメージ生成
        # self.bgimage: px.Image = px.Image(px.width, px.height)
        # bgpointer = self.bgimage.data_ptr()
        # bgpointer[:] = px.screen.data_ptr()

        # イベントメッセージウインドウの生成
        self.message_window = Window(
            "large", 4, APP_HEIGHT // 2 - 4, APP_WIDTH - 8, APP_HEIGHT // 2, "once"
        )
        self.message_window.update_row_max(6)

        # フィールドシーンからイベント情報を取得
        ctx, evtcmd = parent_scene.transfer_eventdata()
        cmd = evtcmd(
            self.message_window,
            ctx,
            parent_scene.current_point.nextevent.event_type,  # type: ignore
            parent_scene.current_point.nextevent.event_value,  # type: ignore
        )
        di.ref.cmdmgr.push_command(cmd)
        parent_scene.current_point.flush_event()

        # イベント画像の取得
        self.eventimage: px.Image = px.Image.from_image("assets/image/event01.bmp")
        eventimage_pos = (APP_WIDTH // 2 - self.eventimage.width // 2, 0)
        eventimage_size = (self.eventimage.width, self.eventimage.height)
        self.eventimage_window = Window(
            "large", *eventimage_pos, *eventimage_size, "once"
        )

        self.load_bgm()

    def load_bgm(self) -> None:
        """シーン切替時のBGMロード"""
        """暫定処理：BGMロード"""
        path = check_file("assets/sound/event_slow.txt")
        if path is not None:
            score_data = read_string(path)
        else:
            raise FileNotFoundError("ファイルがない！")
        # for i, mml in enumerate(score_data):
        #     px.sounds[i].mml(mml)
        #     px.musics[0].set([0], [1], [2], [3])
        #     px.stop()
        #     px.playm(0, loop=True)
        px.stop()
        for i, ch in enumerate(px.channels):
            mml = "R"
            if i < len(score_data):
                mml = score_data[i]
            ch.play(mml, loop=True)

    def update(self):
        """更新処理
        - 戦闘終了フラグ時は戦闘報酬コマンド発行
        - 生存エネミーが0の場合に戦闘終了フラグON
        - コマンドスタックがある場合はコマンド処理へ抜ける
          - ない場合は生存PTメンバー分のコマンド生成をループ実行
          - コマンド数が揃ったらエネミー側コマンドと行動順を決定してコマンドスタック追加
        """

        # # 基本的にメニューを回す
        # # 完了またはキャンセル時の処理は
        # is_submenu_open = self.wndmgr.stack_count > 1
        # result = self.wndmgr.update()
        # # サブメニューオープン時は確定処理を行わない
        # if is_submenu_open:
        #     return
        # match result:
        #     # case WindowAction.NOTHING:
        #     #     pass
        #     case WindowAction.CLOSE:
        #         """バトルメニューキャンセル時"""
        #         if self.context.actor.id > 0:
        #             self.battle_commands.pop(self.context.actor.id - 1)
        #         di.ref.scnmgr.previous_scene(False)
        #     case WindowAction.NOTHING:
        #         """バトルメニュー決定完了時"""
        #         if self.command_package.selected_action is None:
        #             errmsg = "コマンドが未定義です"
        #             logger.critical(errmsg, exc_info=True)
        #             raise TypeError(errmsg)
        #         cmd = self.command_package.selected_action
        #         self.battle_commands[self.context.actor.id] = cmd(
        #             self.context,
        #             self.message_window,
        #             self.command_package.selected_args,
        #         )
        #         di.ref.scnmgr.previous_scene(False)
        if di.ref.cmdmgr.is_empty:
            di.ref.scnmgr.previous_scene()

    def draw(self):
        """描画処理
        ※イベントメッセージはコマンドで描画"""
        # 背景画像描画
        # プレイヤーキャラのワールド座標を取得
        wx, wy = di.ref.pt.get_pt_world_address()

        # カメラオフセットを計算 (プレイヤーが画面中央に来るように)
        ox = px.width // 2 - wx
        oy = px.height // 2 - wy

        # マップ描画（地図・ノード・ルート　オフセット適用)
        di.ref.map.draw(ox, oy)

        # イベント画像の枠
        px.blt(
            self.eventimage_window.x,
            self.eventimage_window.y,
            self.eventimage,
            0,
            0,
            self.eventimage.width,
            self.eventimage.height,
        )
        # イベント画像本体
        px.blt(
            self.eventimage_window.x,
            self.eventimage_window.y,
            self.eventimage_window.window_image,
            0,
            0,
            self.eventimage_window.width,
            self.eventimage_window.height,
            px.COLOR_NAVY,
        )
