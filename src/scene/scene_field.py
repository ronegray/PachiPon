"""
シーンモジュール：フィールド

- フィールド画面の表示
- フィールド画面メニューの呼び出し
  - 呼び出しメニューに応じたコマンドの生成
"""

import logging
import pyxel as px
import service_locater as di
from const import FIELD_MESSAGE_HEIGHT
from gameutils.base import is_pressed, check_file, read_string
from gameutils.lib import Window, WindowAction

# from command import CommandContext
from field_map import EventPoint
from entity import EntityContext
import command.entity_command as e_cmd
from menu import MenuField
from . import BaseScene

# ロギング設定
logger = logging.getLogger(__name__)


class SceneField(BaseScene):
    def __init__(self):
        super().__init__()
        self.situation = "field"
        # フィールドメッセージウインドウの生成
        x_offset = 4
        message_pos = (x_offset, px.height // 2 - (FIELD_MESSAGE_HEIGHT // 2))
        message_size = (px.width - (x_offset * 2), FIELD_MESSAGE_HEIGHT)
        self.message_window = Window("basic", *message_pos, *message_size, "once", 0)
        evinfo_pos = (0, 0)
        evinfo_size = (96, 104)
        self.eventpoint_info_window = Window("basic", *evinfo_pos, *evinfo_size, "once")
        self.eventpoint_info_window.update_row_max(8)

        # コンテキスト
        self.ctx: EntityContext

        # 位置情報
        # current_point = di.ref.pt.get_current_point()
        # startpoint_id = current_point.id
        # self.current_node_id: str = startpoint_id
        self.current_point: EventPoint = di.ref.pt.get_current_point()
        self.last_visited_node: str = self.current_point.id
        self.next_node: str = ""
        # self.eventpoint_info_window.add_message(self.current_point.name)
        # for key, val in self.current_point.get_eventpoint_info().items():
        #     self.eventpoint_info_window.add_message(f"{val["name"]}  {val["threshold"]}")
        self.update_eventpoint_info()

        # キャラクターは main.py で初期化され、サービスロケータに登録されている
        self.field_chara = di.ref.pt._field_sprite

        # カメラオフセット
        self.camera_x = 0
        self.camera_y = 0

        # self.event_flags = {node_id: True for node_id in di.ref.map.points.keys()}

        self.load_bgm()

    def update_eventpoint_info(self):
        """イベントポイントウインドウの内容更新"""
        self.eventpoint_info_window.clear_message()
        self.eventpoint_info_window.add_message(self.current_point.name)
        logger.debug(self.current_point)
        logger.debug(self.current_point.get_eventpoint_info())
        for _, val in self.current_point.get_eventpoint_info().items():
            self.eventpoint_info_window.add_message(
                f"{val["name"]}  {val["threshold"]}"
            )
        logger.debug(self.eventpoint_info_window.message_list)
        return

    def load_bgm(self) -> None:
        """暫定処理：BGMロード"""
        path = check_file("assets/sound/field.txt")
        if path is not None:
            score_data = read_string(path)
        else:
            raise FileNotFoundError("ファイルがない！")
        for i, mml in enumerate(score_data):
            px.sounds[i].mml(mml)
            px.musics[0].set([0], [1], [2], [3])
            px.stop()
            px.playm(0, loop=True)

    def update(self):
        """フィールド関連オブジェクト群の更新処理"""
        # コマンド実行中は更新処理停止
        if not di.ref.cmdmgr.is_empty:
            return

        # WindowManagerにスタックがある場合はメニュー操作を優先
        if self.wndmgr.has_stack:
            if self.wndmgr.update() == WindowAction.DISCARD:
                if self.command_package.selected_action is None:
                    return
                cmd = self.command_package.selected_action
                di.ref.cmdmgr.push_command(
                    cmd(
                        self.ctx,
                        self.message_window,
                        self.command_package.selected_args,
                    )
                )
            return

        # 準備状態でないイベントポイントのみ更新
        [
            lambda: point.update()
            for point in di.ref.map.points.values()
            if point.is_ready is False
        ]

        # 移動中は何もしない
        if di.ref.pt._pt_is_moving:
            di.ref.pt.update()
            # 移動中→移動完了への状態変化時に、前ポイントのイベント回復＆現在地修正
            # -> イベント回復はイベントポイントの更新処理へ移動
            # 移動終了時は地点情報を更新
            if di.ref.pt._pt_is_moving is False:
                self.next_node = ""
                self.current_point = di.ref.pt.get_current_point()
                self.update_eventpoint_info()
                self.last_visited_node = self.current_point.id
                # self.eventpoint_info_window.set_message([f"{di.ref.pt._current_point.event_list}"])
            return

        # メニューキー判定
        if is_pressed("other1"):
            if self.wndmgr.has_stack:
                self.wndmgr.pop_stack()
            else:
                self.ctx = self.build_context()
                self.command_package = e_cmd.CommandPackage()
                self.wndmgr.push_stack(
                    MenuField,
                    self.ctx,
                    self.command_package,
                    di.ref.pl_item,
                    di.ref.pl_stack,
                )
            return

        # ACTION_NAME 型に準拠させるための固定リスト
        actions = ["up", "down", "left", "right"]
        for d in actions:
            if is_pressed(d):  # type: ignore
                # to_route = di.ref.map.get_route(self.current_node_id, d)
                to_route = di.ref.map.get_route(self.current_point.id, d)
                if to_route:
                    self.next_node = to_route.to_id
                    # プレイヤーの向きを設定
                    direction_map = {
                        "up": "back",
                        "down": "front",
                        "left": "left",
                        "right": "right",
                    }
                    di.ref.pt.set_sprite_direction(direction_map[d])

                    # 移動開始
                    di.ref.pt.set_current_route(to_route)
                    di.ref.pt.move_route(to_route)
                    return

        # イベント発生判定
        # is_event_point = self.event_flags.get(self.current_node_id, False)
        # # self.field_chara.set_event_point_status(is_event_point)
        # di.ref.pt.set_event_point_status(is_event_point)

        # if is_pressed("decide") and is_event_point:
        #     self.event_flags[self.current_node_id] = False
        # current_point = di.ref.pt.get_current_point()?
        if is_pressed("decide") and self.current_point.is_ready:
            self.current_point

        # キャラクターのスプライトを更新（非移動時もアニメーション等のために必要）
        self.field_chara.update()

        # カメラオフセットの計算 (プレイヤーを画面中央に固定)
        self.camera_x = px.width // 2 - di.ref.pt._field_sprite.x
        self.camera_y = px.height // 2 - di.ref.pt._field_sprite.y

        # カメラのクランプ (ワールドマップの端が画面外に出ないように調整)
        self.camera_x = max(px.width - di.ref.map.map_img_width, min(0, self.camera_x))
        self.camera_y = max(
            px.height - di.ref.map.map_img_height, min(0, self.camera_y)
        )

    def draw(self):
        # プレイヤーキャラのワールド座標を取得
        wx, wy = di.ref.pt.get_pt_world_address()

        # カメラオフセットを計算 (プレイヤーが画面中央に来るように)
        ox = px.width // 2 - wx
        oy = px.height // 2 - wy

        # マップ描画（地図・ノード・ルート　オフセット適用)
        di.ref.map.draw(ox, oy)
        # イベントポイント情報表示（移動中は非表示）
        if not di.ref.pt._pt_is_moving:
            self.eventpoint_info_window.draw()
            self.eventpoint_info_window.draw_message()

        # プレイヤーキャラの描画 (常に画面中央)
        di.ref.pt.draw(px.width, px.height)

        # WindowManagerの描画（メニュー等）
        self.wndmgr.draw()

    def build_context(self) -> EntityContext:
        """エンティティコマンド用コンテキスト生成"""
        ctx = EntityContext(
            situation=self.situation,
            actor=di.ref.pt.get_member(0),
            target=di.ref.pt.get_member(0),
            allies=list(di.ref.pt.get_allmember()),
            targets=list(di.ref.pt.get_allmember()),
        )
        return ctx
