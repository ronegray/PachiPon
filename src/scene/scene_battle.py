import pyxel as px
import service_locater as di
from gameutils.base import is_pressed, check_file, read_string
from .scene_base import BaseScene

"""
from menu import MenuBattle
"""


class SceneBattle(BaseScene):
    def __init__(self):
        super().__init__()

        """
        戦闘メニューの構築
        メッセージウインドウ定義
        ルート情報呼び出し
        脅威度別モンスターリストからモンスターID選択
        モンスターデータ呼び出し＆配列定義

        """

        """暫定処理：BGMロード"""
        path = check_file("assets/sound/battle.txt")
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
        if is_pressed("decide"):
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
            di.ref.scnmgr.previous_scene()
        # # # メニューキー判定
        # # if is_pressed("other1"):
        # #     if self.wndmgr.has_stack:
        # #         self.wndmgr.pop_stack()
        # #     else:
        # #         self.wndmgr.push_stack(MenuField)
        # #     return

        # # WindowManagerにスタックがある場合はメニュー操作を優先
        # if self.wndmgr.has_stack:
        #     self.wndmgr.update()
        #     return

        # # 移動中は何もしない
        # # if self.field_chara.is_moving:
        # # self.field_chara.set_event_point_status(False)
        # # self.field_chara.update()
        # # return
        # if di.ref.pt._pt_is_moving:
        #     # di.ref.pt.set_event_point_status(False)
        #     di.ref.pt.update()
        #     # 移動中→移動完了への状態変化時に、前ポイントのイベント回復＆現在地修正
        #     if di.ref.pt._pt_is_moving is False:
        #         self.event_flags[self.current_node] = True
        #         self.last_visited_node = self.current_node = self.next_node
        #     return

        # # メニューキー判定
        # if is_pressed("other1"):
        #     if self.wndmgr.has_stack:
        #         self.wndmgr.pop_stack()
        #     else:
        #         self.wndmgr.push_stack(MenuField)
        #     return

        # # 通常のフィールド操作
        # # old_node = self.current_node

        # # ACTION_NAME 型に準拠させるための固定リスト
        # actions = ["up", "down", "left", "right"]
        # # for d in actions:
        # #     if is_pressed(d):  # type: ignore
        # #         next_node_id = di.ref.map.get_connected_node(self.current_node, d)
        # #         if next_node_id:
        # #             self.current_node = next_node_id
        # #             # プレイヤーの向きを設定
        # #             direction_map = {
        # #                 "up": "back",
        # #                 "down": "front",
        # #                 "left": "left",
        # #                 "right": "right",
        # #             }
        # #             # self.field_chara.set_direction(direction_map[d])
        # #             di.ref.pt.set_sprite_direction(direction_map[d])

        # #             # 移動開始
        # #             # target_point = di.ref.map.get_point(next_node)
        # #             # if target_point:
        # #             #     # self.field_chara.move_to(target_point.x, target_point.y)
        # #             #     di.ref.pt.move_to(target_point.id)
        # #             di.ref.pt.move_to(next_node_id)
        # #             # break
        # #             return
        # for d in actions:
        #     if is_pressed(d):  # type: ignore
        #         # next_node_id = di.ref.map.get_connected_node(self.current_node, d)
        #         to_route = di.ref.map.get_route(self.current_node, d)
        #         # if next_node_id:
        #         if to_route:
        #             # self.current_node = next_node_id
        #             self.next_node = to_route.to_id
        #             # プレイヤーの向きを設定
        #             direction_map = {
        #                 "up": "back",
        #                 "down": "front",
        #                 "left": "left",
        #                 "right": "right",
        #             }
        #             di.ref.pt.set_sprite_direction(direction_map[d])

        #             # 移動開始
        #             # di.ref.pt.move_to(next_node_id)
        #             # di.ref.pt.move_to(self.next_node)
        #             di.ref.pt.move_route(to_route)
        #             return

        # # if old_node != self.current_node:
        # #     self.event_flags[self.current_node] = True
        # #     self.last_visited_node = old_node

        # # # イベント発生判定
        # # is_event_point = self.event_flags.get(self.current_node, False)
        # # # self.field_chara.set_event_point_status(is_event_point)
        # # di.ref.pt.set_event_point_status(is_event_point)

        # # if is_pressed("decide") and is_event_point:
        # #     # self.event_manager.trigger_event(self.current_node, self.event_flags)
        # #     self.event_flags[self.current_node] = False

        # # # キャラクターのスプライトを更新（非移動時もアニメーション等のために必要）
        # # self.field_chara.update()

        # # カメラオフセットの計算 (プレイヤーを画面中央に固定)
        # # self.camera_x = px.width // 2 - self.field_chara.sprite.x
        # # self.camera_y = px.height // 2 - self.field_chara.sprite.y
        # self.camera_x = px.width // 2 - di.ref.pt._field_sprite.x
        # self.camera_y = px.height // 2 - di.ref.pt._field_sprite.y

        # # カメラのクランプ (ワールドマップの端が画面外に出ないように調整)
        # self.camera_x = max(px.width - di.ref.map.map_img_width, min(0, self.camera_x))
        # self.camera_y = max(
        #     px.height - di.ref.map.map_img_height, min(0, self.camera_y)
        # )

    def draw(self):
        pass
        # # プレイヤーキャラのワールド座標を取得
        # # # px_ = self.field_chara.sprite.x
        # # # py_ = self.field_chara.sprite.y
        # # px_ = di.ref.pt._field_sprite.x
        # # py_ = di.ref.pt._field_sprite.y
        # wx, wy = di.ref.pt.get_pt_world_address()

        # # カメラオフセットを計算 (プレイヤーが画面中央に来るように)
        # # ox = px.width // 2 - px_
        # # oy = px.height // 2 - py_
        # ox = px.width // 2 - wx
        # oy = px.height // 2 - wy

        # # # マップ背景の描画 (ワールド座標 (0,0) を ox, oy に描画)
        # # pyxel.blt(
        # #     ox, oy, di.ref.map.map_img, 0, 0,
        # #     di.ref.map.map_img_width, di.ref.map.map_img_height
        # # )

        # # マップ上のノードと線の描画 (オフセット適用)
        # di.ref.map.draw(ox, oy)

        # # # イベント発生可能フラグの表示 (デバッグ用)
        # # for node_id, point in di.ref.map.points.items():
        # #     if self.event_flags.get(node_id, False):
        # #         px.text(point.x + ox + 5, point.y + oy + 5, "E", 8)  # 黄色で表示

        # # プレイヤーキャラの描画 (常に画面中央)
        # # self.field_chara.draw(128 - 16, 128 - 16)
        # di.ref.pt.draw(px.width // 2, px.height // 2)

        # # WindowManagerの描画（メニュー等）
        # self.wndmgr.draw()
