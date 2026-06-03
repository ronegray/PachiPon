import pyxel as px
from entity import BaseSprite


class FieldSprite(BaseSprite):
    def __init__(
        self,
        x: int,
        y: int,
        img: int | px.Image,
        u: int = 0,
        v: int = 0,
        w: int = 32,
        h: int = 32,
        colkey: int = px.COLOR_GREEN,
    ):
        super().__init__(x, y, img, u, v, w, h, colkey)
        self.speed = 1
        self._direction = "front"  # 正面向きをデフォルトとする
        self._animation_frame = 0
        self._is_event_point = False
        self._is_moving = False  # 移動中フラグ

        # 各方向のスプライトU, V座標を定義 (32x32pxが8枚、colkeyは親クラスで指定済み)
        self.sprite_uvs = {
            "front": [(0, 0), (32, 0)],  # 正面向き2枚
            "left": [(64, 0), (96, 0)],  # 左向き2枚
            "right": [(128, 0), (160, 0)],  # 右向き2枚
            "back": [(192, 0), (224, 0)],  # 後ろ向き2枚
        }

    def move(self, dx, dy):
        self.x += dx * self.speed
        self.y += dy * self.speed

    def set_direction(self, direction):
        if direction in self.sprite_uvs:
            self._direction = direction

    def set_event_point_status(self, status: bool):
        self._is_event_point = status

    def set_moving_status(self, status: bool):
        self._is_moving = status

    def update(self):
        # # イベントポイント上、または移動中の場合のみアニメーション
        # if self._is_event_point or self._is_moving:
        #     self._animation_frame = (pyxel.frame_count // (60 // 4)) % 2 # pyxel.frame_rate の代わりに60を使用
        # else:
        #     self._animation_frame = 0 # 停止中はアニメーションを停止
        if self._is_moving is False:
            self._direction = "front"
        self._animation_frame = (
            px.frame_count // (60 // 4)
        ) % 2  # pyxel.frame_rate の代わりに60を使用

    def draw(self, x: int | None = None, y: int | None = None):
        draw_x = self.x if x is None else x
        draw_y = self.y if y is None else y

        # 現在の方向とアニメーションフレームに基づいてU, V座標を取得
        u, v = self.sprite_uvs[self._direction][self._animation_frame]

        # img_val = self.img.value if isinstance(self.img, pyxel.Image) else self.img

        if self.colkey is not None:
            px.blt(
                draw_x, draw_y, self.img, u, v, self.w, self.h, self.colkey, scale=0.5
            )
        else:
            px.blt(draw_x, draw_y, self.img, u, v, self.w, self.h, scale=0.5)
