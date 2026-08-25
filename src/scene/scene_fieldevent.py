"""
シーンモジュール：フィールドイベント

シーン：フィールドのサブモジュールとして、
イベントコマンドの実行機能を提供
"""

import logging
import pyxel as px
from const import APP_WIDTH, APP_HEIGHT
from gameutils.lib import Window
import service_locater as di
from . import BaseScene, SceneField

# ロギング設定
logger = logging.getLogger(__name__)


class SceneFieldEvent(BaseScene):
    """イベントシーン"""

    def __init__(self) -> None:
        super().__init__()
        self.situation = "system"

        parent_scene = di.ref.scnmgr.get_now_scene()
        if not isinstance(parent_scene, SceneField):
            errmsg = f"想定外のシーンから呼び出されました：{parent_scene.__class__.__name__}"
            logger.critical(errmsg, exc_info=True)
            raise TypeError(errmsg)

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
        self.eventimage_window = Window("large", *eventimage_pos, *eventimage_size, "once")

        self.load_bgm()

    def load_bgm(self) -> None:
        """シーン切替時のBGMロード"""
        # """暫定処理：BGMロード"""
        # path = check_file("assets/sound/event_slow.txt")
        # if path is not None:
        #     score_data = read_string(path)
        # else:
        #     raise FileNotFoundError("ファイルがない！")
        # px.stop()
        # for i, ch in enumerate(px.channels):
        #     mml = "R"
        #     if i < len(score_data):
        #         mml = score_data[i]
        #     ch.play(mml, loop=True)
        di.ref.sndmgr.request_bgm("event_slow")

    def update(self):
        """更新処理
        - 戦闘終了フラグ時は戦闘報酬コマンド発行
        - 生存エネミーが0の場合に戦闘終了フラグON
        - コマンドスタックがある場合はコマンド処理へ抜ける
          - ない場合は生存PTメンバー分のコマンド生成をループ実行
          - コマンド数が揃ったらエネミー側コマンドと行動順を決定してコマンドスタック追加
        """

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
