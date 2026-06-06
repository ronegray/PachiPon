import pyxel as px
from .scene_base import BaseScene

# from field_map import MapGraph
from gameutils.base import is_pressed

from menu import MenuField

# from event_manager import EventManager
from gameutils.base.file.file_system import check_file, read_string

import service_locater as di
# from service_locater import ref as di


class SceneField(BaseScene):
    def __init__(self):
        super().__init__()
        # self.game_map = MapGraph()
        # map_path = check_file("assets/data/map_data.json", "r")
        # if map_path:
        #     self.game_map.load_mapdata(read_json(map_path))

        # self.map_image = pyxel.Image.from_image("assets/image/map.png")
        # self.map_image_width = self.map_image.width
        # self.map_image_height = self.map_image.height

        self.current_node = "p17"  # 初期位置
        self.last_visited_node = "p17"
        # self.event_manager = EventManager()

        # キャラクターは main.py で初期化され、サービスロケータに登録されている
        # self.player_character = di.ref.hero
        self.field_chara = di.ref.pt._field_sprite

        # start_point = self.game_map.get_point(self.current_node)
        # if start_point:
        #     # プレイヤー座標はワールドマップ上の絶対座標
        #     # self.player_character.set_position(start_point.x, start_point.y)
        #     di.ref.hero.set_position(start_point.x, start_point.y)

        # カメラオフセット
        self.camera_x = 0
        self.camera_y = 0

        self.event_flags = {node_id: True for node_id in di.ref.map.points.keys()}

        """暫定処理：BGMロード"""
        path = check_file("assets/sound/field.txt")
        if path is not None:
            score_data = read_string(path)
        else:
            raise FileNotFoundError("ファイルがない！")
        for i, mml in enumerate(score_data):
            px.sounds[i].mml(mml)
            px.musics[0].set([0], [1])
            px.stop()
            px.playm(0, loop=True)

    def update(self):
        # メニューキー判定
        if is_pressed("other1"):
            if self.wndmgr.has_stack:
                self.wndmgr.pop_stack()
            else:
                self.wndmgr.push_stack(MenuField)
            return

        # WindowManagerにスタックがある場合はメニュー操作を優先
        if self.wndmgr.has_stack:
            self.wndmgr.update()
            return

        # 移動中は何もしない
        # if self.field_chara.is_moving:
        # self.field_chara.set_event_point_status(False)
        # self.field_chara.update()
        # return
        if di.ref.pt._pt_is_moving:
            # di.ref.pt.set_event_point_status(False)
            di.ref.pt.update()
            return

        # 通常のフィールド操作
        old_node = self.current_node

        # ACTION_NAME 型に準拠させるための固定リスト
        actions = ["up", "down", "left", "right"]
        for d in actions:
            if is_pressed(d):  # type: ignore
                next_node_id = di.ref.map.get_connected_node(self.current_node, d)
                if next_node_id:
                    self.current_node = next_node_id
                    # プレイヤーの向きを設定
                    direction_map = {
                        "up": "back",
                        "down": "front",
                        "left": "left",
                        "right": "right",
                    }
                    # self.field_chara.set_direction(direction_map[d])
                    di.ref.pt.set_sprite_direction(direction_map[d])

                    # 移動開始
                    # target_point = di.ref.map.get_point(next_node)
                    # if target_point:
                    #     # self.field_chara.move_to(target_point.x, target_point.y)
                    #     di.ref.pt.move_to(target_point.id)
                    di.ref.pt.move_to(next_node_id)
                    # break
                    return

        if old_node != self.current_node:
            self.event_flags[self.current_node] = True
            self.last_visited_node = old_node

        # イベント発生判定
        is_event_point = self.event_flags.get(self.current_node, False)
        # self.field_chara.set_event_point_status(is_event_point)
        di.ref.pt.set_event_point_status(is_event_point)

        if is_pressed("decide") and is_event_point:
            # self.event_manager.trigger_event(self.current_node, self.event_flags)
            self.event_flags[self.current_node] = False

        # キャラクターのスプライトを更新（非移動時もアニメーション等のために必要）
        self.field_chara.update()

        # カメラオフセットの計算 (プレイヤーを画面中央に固定)
        # self.camera_x = px.width // 2 - self.field_chara.sprite.x
        # self.camera_y = px.height // 2 - self.field_chara.sprite.y
        self.camera_x = px.width // 2 - di.ref.pt._field_sprite.x
        self.camera_y = px.height // 2 - di.ref.pt._field_sprite.y

        # カメラのクランプ (ワールドマップの端が画面外に出ないように調整)
        self.camera_x = max(px.width - di.ref.map.map_img_width, min(0, self.camera_x))
        self.camera_y = max(
            px.height - di.ref.map.map_img_height, min(0, self.camera_y)
        )

    def draw(self):
        # プレイヤーキャラのワールド座標を取得
        # # px_ = self.field_chara.sprite.x
        # # py_ = self.field_chara.sprite.y
        # px_ = di.ref.pt._field_sprite.x
        # py_ = di.ref.pt._field_sprite.y
        wx, wy = di.ref.pt.get_pt_world_address()

        # カメラオフセットを計算 (プレイヤーが画面中央に来るように)
        # ox = px.width // 2 - px_
        # oy = px.height // 2 - py_
        ox = px.width // 2 - wx
        oy = px.height // 2 - wy

        # # マップ背景の描画 (ワールド座標 (0,0) を ox, oy に描画)
        # pyxel.blt(
        #     ox, oy, di.ref.map.map_img, 0, 0,
        #     di.ref.map.map_img_width, di.ref.map.map_img_height
        # )

        # マップ上のノードと線の描画 (オフセット適用)
        di.ref.map.draw(ox, oy)

        # イベント発生可能フラグの表示 (デバッグ用)
        for node_id, point in di.ref.map.points.items():
            if self.event_flags.get(node_id, False):
                px.text(point.x + ox + 5, point.y + oy + 5, "E", 8)  # 黄色で表示

        # プレイヤーキャラの描画 (常に画面中央)
        # self.field_chara.draw(128 - 16, 128 - 16)
        di.ref.pt.draw(px.width // 2, px.height // 2)

        # WindowManagerの描画（メニュー等）
        self.wndmgr.draw()
