import pyxel as px
from entity import BaseSprite
from const import APP_FPS


class FieldSprite(BaseSprite):
    def __init__(
        self,
        x: int,
        y: int,
        img: int | px.Image,
        u: int = 0,
        v: int = 0,
        w: int = 16,
        h: int = 16,
        colkey: int = px.COLOR_GREEN,
    ):
        super().__init__(x, y, img, u, v, w, h, colkey)
        self.speed = 1
        self._direction = "front"  # 正面向きをデフォルトとする
        self._animation_frame = 0
        self._is_moving = False  # 移動中フラグ

        # 各方向のスプライトU, V座標を定義 (32x32pxが8枚、colkeyは親クラスで指定済み)
        self.sprite_uvs = {
            "front": [(0, 0), (16, 0)],  # 正面向き2枚
            "left": [(32, 0), (48, 0)],  # 左向き2枚
            "right": [(64, 0), (80, 0)],  # 右向き2枚
            "back": [(96, 0), (112, 0)],  # 後ろ向き2枚
        }

    def set_direction(self, direction):
        if direction in self.sprite_uvs:
            self._direction = direction

    def update(self):
        # 停止中＝イベントポイント待機中は正面向き
        if self._is_moving is False:
            self._direction = "front"
        self._animation_frame = (px.frame_count // (APP_FPS // 2)) % 2  # FPSの半分で切替

    def draw(self, x: int | None = None, y: int | None = None):
        width_offset = self.w // 2
        height_offset = self.h // 2
        draw_x = (self.x if x is None else x) - width_offset
        draw_y = (self.y if y is None else y) - height_offset

        # 現在の方向とアニメーションフレームに基づいてU, V座標を取得
        u, v = self.sprite_uvs[self._direction][self._animation_frame]
        px.blt(draw_x, draw_y, self.img, u, v, self.w, self.h, self.colkey)
