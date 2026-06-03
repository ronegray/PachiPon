"""base_sprite.py
スプライトイメージの表示モジュール
"""
import pyxel as px


class BaseSprite:
    def __init__(
        self,
        x: int,
        y: int,
        img: int | px.Image,
        u: int,
        v: int,
        w: int,
        h: int,
        colkey: int = px.COLOR_BLACK,
    ):
        self.x = x
        self.y = y
        self.img = img
        self.u = u
        self.v = v
        self.w = w
        self.h = h
        self.colkey = colkey

    def draw(self, x: int | None = None, y: int | None = None):
        draw_x = self.x if x is None else x
        draw_y = self.y if y is None else y
        px.blt(draw_x, draw_y, self.img, self.u, self.v, self.w, self.h, self.colkey)
