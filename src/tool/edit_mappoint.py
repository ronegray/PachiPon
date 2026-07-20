import sys
import os
import re
import pyxel as px

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
if os.path.dirname(os.path.abspath(__file__)) + "/.." in sys.path:
    from gameutils.base import check_file, read_json, write_json

CIRCLE_RADIUS = 6  # 既存ポイントの円描画半径（クリック判定にも使用）
NEAR_THRESHOLD = 30  # これより近い場合は「近すぎる」として新規追加を拒否する距離

# ---------------------------------------------------------------------------
# ダイアログでのテキスト入力用: pyxelのキー定数と入力文字の対応表を作成
# ---------------------------------------------------------------------------
CHAR_KEYMAP = {}
for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    key = getattr(px, f"KEY_{c}", None)
    if key is not None:
        CHAR_KEYMAP[key] = (c.lower(), c)
for n in "0123456789":
    key = getattr(px, f"KEY_{n}", None)
    if key is not None:
        CHAR_KEYMAP[key] = (n, n)

_EXTRA_KEYMAP = {
    "KEY_SPACE": (" ", " "),
    "KEY_MINUS": ("-", "_"),
    "KEY_APOSTROPHE": ("'", '"'),
    "KEY_COMMA": (",", "<"),
    "KEY_PERIOD": (".", ">"),
    "KEY_SLASH": ("/", "?"),
}
for _name, _chars in _EXTRA_KEYMAP.items():
    _key = getattr(px, _name, None)
    if _key is not None:
        CHAR_KEYMAP[_key] = _chars

BACKSPACE_KEY = getattr(px, "KEY_BACKSPACE", None)
SHIFT_KEY = getattr(px, "KEY_SHIFT", None)  # 左右どちらのShiftでも反応する統合キー
CTRL_KEY = getattr(px, "KEY_CTRL", None)  # 左右どちらのCtrlでも反応する統合キー
SAVE_KEY = getattr(px, "KEY_S", None)


class InputField:
    """ダイアログ内の1行テキスト入力欄"""

    def __init__(self, x, y, w, h, label, value=""):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.label = label
        self.value = value
        self.active = False

    def contains(self, mx, my):
        return self.x <= mx <= self.x + self.w and self.y <= my <= self.y + self.h

    def handle_key(self):
        if not self.active:
            return

        shift = SHIFT_KEY is not None and px.btn(SHIFT_KEY)
        for key, (lower_c, upper_c) in CHAR_KEYMAP.items():
            if px.btnp(key, 12, 3):
                self.value += upper_c if shift else lower_c

        if BACKSPACE_KEY is not None and px.btnp(BACKSPACE_KEY, 12, 3):
            self.value = self.value[:-1]

    def draw(self):
        px.text(self.x, self.y - 8, self.label, px.COLOR_WHITE)
        border_color = px.COLOR_YELLOW if self.active else px.COLOR_GRAY
        px.rect(self.x, self.y, self.w, self.h, px.COLOR_NAVY)
        px.rectb(self.x, self.y, self.w, self.h, border_color)
        px.text(self.x + 3, self.y + 3, self.value, px.COLOR_WHITE)


class Button:
    def __init__(self, x, y, w, h, label, color):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.label = label
        self.color = color

    def contains(self, mx, my):
        return self.x <= mx <= self.x + self.w and self.y <= my <= self.y + self.h

    def draw(self):
        px.rect(self.x, self.y, self.w, self.h, self.color)
        px.rectb(self.x, self.y, self.w, self.h, px.COLOR_WHITE)
        tx = self.x + (self.w - len(self.label) * 4) // 2
        ty = self.y + (self.h - 6) // 2
        px.text(tx, ty, self.label, px.COLOR_WHITE)


class PointDialog:
    """ポイント追加・編集用の入力ダイアログ"""

    def __init__(self, screen_w, screen_h, mode, point=None, pending_xy=None):
        self.mode = mode  # "add" または "edit"
        self.point = point  # 編集対象のポイント(dict)。追加時はNone
        self.pending_xy = pending_xy  # 追加時のクリック座標 (x, y)

        w, h = 200, 90
        self.x = (screen_w - w) // 2
        self.y = (screen_h - h) // 2
        self.w, self.h = w, h

        init_type = point["point_type"] if point else ""
        init_name = point["name"] if point else ""

        self.field_type = InputField(
            self.x + 10, self.y + 22, w - 20, 12, "point_type", init_type
        )
        self.field_name = InputField(
            self.x + 10, self.y + 52, w - 20, 12, "name", init_name
        )
        self.field_type.active = True

        self.btn_ok = Button(
            self.x + 10, self.y + h - 18, 70, 14, "OK", px.COLOR_DARK_BLUE
        )
        self.btn_cancel = Button(
            self.x + w - 80, self.y + h - 18, 70, 14, "Cancel", px.COLOR_RED
        )

    def fields(self):
        return (self.field_type, self.field_name)

    def update(self):
        for f in self.fields():
            f.handle_key()

        if px.btnp(px.MOUSE_BUTTON_LEFT):
            mx, my = px.mouse_x, px.mouse_y
            # 入力欄がクリックされたらそちらへフォーカスを切り替える
            for f in self.fields():
                if f.contains(mx, my):
                    for other in self.fields():
                        other.active = False
                    f.active = True
                    break

    def draw(self):
        px.rect(self.x, self.y, self.w, self.h, px.COLOR_BLACK)
        px.rectb(self.x, self.y, self.w, self.h, px.COLOR_WHITE)
        title = "Edit Point" if self.mode == "edit" else "Add Point"
        px.text(self.x + 10, self.y + 6, title, px.COLOR_WHITE)
        for f in self.fields():
            f.draw()
        self.btn_ok.draw()
        self.btn_cancel.draw()


class App:
    def __init__(self):
        self.datapath = check_file("../assets/data/map_data.json")
        mapdata = read_json(self.datapath)
        self.points = mapdata["points"]
        self.routes = mapdata["routes"]

        sizing: px.Image = px.Image.from_image("../assets/image/map.bmp")
        px.init(sizing.width, sizing.height, display_scale=2)
        px.load("../assets/assets.pyxres")
        # パレット読み込みしてから画像ロード
        self.mapimage: px.Image = px.Image.from_image("../assets/image/map.bmp")
        px.mouse(True)

        self.mode = "normal"  # "normal" または "dialog"
        self.dialog = None  # PointDialog インスタンス

        px.run(self.update, self.draw)

    # ------------------------------------------------------------------
    # ID採番: 既存の "pXX" 形式idの最大値+1を新しいidとする
    # ------------------------------------------------------------------
    def _generate_new_id(self):
        nums = []
        for p in self.points:
            m = re.match(r"p(\d+)$", p["id"])
            if m:
                nums.append(int(m.group(1)))
        next_num = (max(nums) + 1) if nums else 1
        width = 2 if next_num < 100 else len(str(next_num))
        return f"p{next_num:0{width}d}"

    # ------------------------------------------------------------------
    # クリック位置に最も近い既存ポイントとその距離を求める
    # ------------------------------------------------------------------
    def _find_nearest_point(self, mx, my):
        nearest = None
        nearest_dist = None
        for p in self.points:
            d = ((p["x"] - mx) ** 2 + (p["y"] - my) ** 2) ** 0.5
            if nearest_dist is None or d < nearest_dist:
                nearest = p
                nearest_dist = d
        return nearest, nearest_dist

    def _handle_map_click(self, mx, my):
        nearest, dist = self._find_nearest_point(mx, my)

        if nearest is not None and dist <= CIRCLE_RADIUS:
            # 既存ポイントの円の範囲内 → 編集ダイアログを表示
            self.dialog = PointDialog(px.width, px.height, "edit", point=nearest)
            self.mode = "dialog"
            return

        if nearest is not None and dist <= NEAR_THRESHOLD:
            # 円の外だが中心から30px以内 → 追加しない
            print("距離が近すぎる")
            return

        # どのポイントからも十分離れている → 新規追加ダイアログを表示
        self.dialog = PointDialog(px.width, px.height, "add", pending_xy=(mx, my))
        self.mode = "dialog"

    def _confirm_dialog(self):
        d = self.dialog
        point_type = d.field_type.value.strip()
        name = d.field_name.value.strip()

        if d.mode == "edit":
            # x, yは変更せず、point_typeとnameのみ更新する
            d.point["point_type"] = point_type
            d.point["name"] = name
        else:
            new_id = self._generate_new_id()
            x, y = d.pending_xy
            new_point = {
                "id": new_id,
                "point_type": point_type,
                "name": name,
                "eventId": f"ev_{new_id}",
                "x": x,
                "y": y,
            }
            self.points.append(new_point)

        self.dialog = None
        self.mode = "normal"

    def _cancel_dialog(self):
        self.dialog = None
        self.mode = "normal"

    def _save(self):
        write_json(self.datapath, {"points": self.points, "routes": self.routes})
        print("map_data.json を保存しました")

    # ------------------------------------------------------------------
    def update(self):
        if self.mode == "dialog":
            self.dialog.update()

            if px.btnp(px.MOUSE_BUTTON_LEFT):
                mx, my = px.mouse_x, px.mouse_y
                if self.dialog.btn_ok.contains(mx, my):
                    self._confirm_dialog()
                elif self.dialog.btn_cancel.contains(mx, my):
                    self._cancel_dialog()
            return

        # 通常モード（ダイアログ非表示中）
        if px.btnp(px.MOUSE_BUTTON_LEFT):
            self._handle_map_click(px.mouse_x, px.mouse_y)
            return

        # Ctrl+S でmap_data.jsonを保存（ダイアログ表示中は無効）
        if CTRL_KEY is not None and SAVE_KEY is not None:
            if px.btn(CTRL_KEY) and px.btnp(SAVE_KEY):
                self._save()

    def draw(self):
        px.blt(0, 0, self.mapimage, 0, 0, self.mapimage.width, self.mapimage.height)

        for route in self.routes:
            from_addr = [
                (point["x"], point["y"])
                for point in self.points
                if point["id"] == route["from"]
            ]
            to_addr = [
                (point["x"], point["y"])
                for point in self.points
                if point["id"] == route["to"]
            ]
            if not route.get("locked", False):
                px.line(*from_addr[0], *to_addr[0], px.COLOR_WHITE)

        for point in self.points:
            px.circ(point["x"], point["y"], CIRCLE_RADIUS, px.COLOR_WHITE)
            px.text(point["x"] - 4, point["y"] - 2, point["id"], px.COLOR_RED)

        if px.btn(px.MOUSE_BUTTON_RIGHT):
            px.blt(0, 0, self.mapimage, 0, 0, self.mapimage.width, self.mapimage.height)

        if self.mode == "dialog":
            self.dialog.draw()


App()
