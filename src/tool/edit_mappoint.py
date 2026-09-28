# pylint: skip-file
# ruff: noqa
import sys, os, re, math, shutil  # noqa E401 E402
from datetime import datetime  # noqa E401 E402

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")  # noqa E401 E402
import pyxel as px  # noqa E401 E402
from gameutils.base import check_file, read_json, write_json  # noqa E401 E402

MAP_DATA_PATH = "../assets/data/map_data.json"
EVENTPOINTS_PATH = "../assets/data/eventpoints.json"

CIRCLE_RADIUS = 6  # 既存ポイントの円描画半径（クリック・ドラッグ判定にも使用）
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
ENTER_KEY = getattr(px, "KEY_RETURN", None)  # メインキーボードのEnter
KP_ENTER_KEY = getattr(px, "KEY_KP_ENTER", None)  # テンキーのEnter

# ---------------------------------------------------------------------------
# event_stat編集で選択可能なEventID / eventpoint_typeの一覧
# 規約で定義済のものだけを選択肢とするため、可能であれば実際のゲームコードから
# importして使用する。実装側の本来のモジュール名は"event"だが、念のため
# "event_protocol"（過去に共有いただいたファイル）も試し、
# どちらもimportできない場合のみ同じ内容のハードコード一覧を使う。
# ---------------------------------------------------------------------------
EVENT_ID_NAMES = [
    "INCREASE_HP",
    "INCREASE_MP",
    "INCREASE_GOLD",
    "INCREASE_FOOD",
    "FLGEVENT1_A",
    "FLGEVENT1_B",
    "FLGEVENT1_C",
    "GET_POTION",
    "MEET_ALLY",
    "FLGEVENT2_D",
    "FLGEVENT2_E",
    "FLGEVENT2_F",
    "GET_HIPOTION",
    "FLGEVENT3_G",
    "FLGEVENT3_H",
    "GET_JUNK",
    "GET_ARMORY",
    "DECREASE_HP",
    "DECREASE_MP",
    "DECREASE_GOLD",
    "DECREASE_FOOD",
    "LOST_POTION",
    "SURPRISE_BATTLE",
    "LOST_HIPOTION",
    "CROWN",
    "MIRROR",
    "CEPTER",
    "GRAIL",
    "SATAN",
    "KING",
]
EVENT_TYPES = ["NORMAL", "SAFETY", "GAMBLE", "BATTLE"]

try:
    from event import EventID, EventType  # ゲーム本体が実際にimportしているモジュール名
except Exception:
    try:
        from event_protocol import (
            EventID,
            EventType,
        )  # 予備: 別名で配置されている場合 # type ignore
    except Exception:
        EventID = None
        EventType = None

if EventID is not None:
    EVENT_ID_NAMES = [e.name for e in EventID]
if EventType is not None:
    EVENT_TYPES = [t.name for t in EventType]

# ---------------------------------------------------------------------------
# point_type編集で選択可能な場所タイプの一覧
# field_map.PointPlaceTypeで定義済（UNKNOWNはエラー時のフォールバック値のため選択肢から除外）
# ---------------------------------------------------------------------------
POINT_TYPE_NAMES = [
    "VILLAGE",
    "TOWN",
    "CAPITAL_CITY",
    "PORT",
    "THOROUGHFARE",
    "LAKE",
    "DUNGEON",
    "REST_AREA",
    "TEMPLE",
    "FRONTIER",
    "RUINS",
    "FOREST",
    "MOUNTAIN",
]

try:
    from field_map import PointPlaceType

    POINT_TYPE_NAMES = [t.name for t in PointPlaceType if t.name != "UNKNOWN"]
except Exception:
    pass  # field_map.pyがimportできない場合は上記のハードコード一覧を使う


EVENT_STAT_SLOT_COUNT = 6  # 1つのeventpointに登録するevent_statの総数（固定）

# 定義数マトリクス表示用のレイアウト定数
# 軸ラベルはEventID/EventTypeの実際のname(識別子文字列)をそのまま欠落なく表示するため、
# 実際の名前の最大文字数から必要な幅を計算しておく(pyxel標準フォントは1文字4px)
MATRIX_LABEL_COL_WIDTH = max(len(n) for n in EVENT_ID_NAMES) * 4 + 4
MATRIX_TYPE_COL_WIDTH = max(len(t) for t in EVENT_TYPES) * 4 + 6
MATRIX_ROW_HEIGHT = 8


def _wrap_key_list(keys, max_chars=46, max_lines=4):
    """event_statのキー一覧を、ダイアログ幅に収まるよう複数行へ整形する"""
    if not keys:
        return []

    lines = []
    current = ""
    for k in keys:
        piece = k if not current else ", " + k
        if current and len(current) + len(piece) > max_chars:
            lines.append(current)
            current = k
        else:
            current += piece
    if current:
        lines.append(current)

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1] + " ..."
    return lines


class InputField:
    """ダイアログ内の1行テキスト入力欄"""

    def __init__(self, x, y, w, h, label, value="", numeric_only=False):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.label = label
        self.value = value
        self.active = False
        self.numeric_only = numeric_only  # Trueの場合は数字キーのみ受け付ける

    def contains(self, mx, my):
        return self.x <= mx <= self.x + self.w and self.y <= my <= self.y + self.h

    def handle_key(self):
        if not self.active:
            return

        shift = SHIFT_KEY is not None and px.btn(SHIFT_KEY)
        for key, (lower_c, upper_c) in CHAR_KEYMAP.items():
            if self.numeric_only and not lower_c.isdigit():
                continue
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


class ConfirmDialog:
    """メッセージ＋OK/Cancelのみの汎用確認ダイアログ(ポイント削除確認などに使う)"""

    def __init__(self, screen_w, screen_h, message_lines):
        self.message_lines = message_lines
        line_h = 10

        content_w = max((len(line) for line in message_lines), default=0) * 4
        w = max(160, content_w + 20)
        h = 20 + len(message_lines) * line_h + 26

        self.x = (screen_w - w) // 2
        self.y = (screen_h - h) // 2
        self.w, self.h = w, h

        btn_y = self.y + h - 22
        self.btn_ok = Button(self.x + 10, btn_y, 70, 14, "OK", px.COLOR_DARK_BLUE)
        self.btn_cancel = Button(self.x + w - 80, btn_y, 70, 14, "Cancel", px.COLOR_RED)

    def draw(self):
        px.rect(self.x, self.y, self.w, self.h, px.COLOR_BLACK)
        px.rectb(self.x, self.y, self.w, self.h, px.COLOR_WHITE)
        for i, line in enumerate(self.message_lines):
            px.text(self.x + 10, self.y + 10 + i * 10, line, px.COLOR_WHITE)
        self.btn_ok.draw()
        self.btn_cancel.draw()


class PointDialog:
    """ポイント追加・編集用の入力ダイアログ"""

    def __init__(
        self,
        screen_w,
        screen_h,
        mode,
        eventpoints,
        point=None,
        pending_xy=None,
        pending_id=None,
        default_event_key="",
    ):
        self.mode = mode  # "add" または "edit"
        self.point = point  # 編集対象のポイント(dict)。追加時はNone
        self.pending_xy = pending_xy  # 追加時のクリック座標 (x, y)
        self.pending_id = pending_id  # 追加時に採番される予定のid
        self.eventpoints = eventpoints or {}

        w, h = 240, 180
        self.x = (screen_w - w) // 2
        self.y = (screen_h - h) // 2
        self.w, self.h = w, h

        init_type = point["point_type"] if point else POINT_TYPE_NAMES[0]
        if init_type not in POINT_TYPE_NAMES:
            # 旧データ等でPOINT_TYPE_NAMESに無い値だった場合の保険
            print(
                f"警告: 未知のpoint_type '{init_type}' のため '{POINT_TYPE_NAMES[0]}' として表示します"
            )
            init_type = POINT_TYPE_NAMES[0]
        init_name = point["name"] if point else ""
        init_event_key = point["event_key"] if point else default_event_key

        # --- point_type: 固定語彙(POINT_TYPE_NAMES)から選ぶ<>セレクタ ---
        self.point_type_value = init_type
        point_type_y = self.y + 22
        self.point_type_prev_btn = Button(self.x + 10, point_type_y, 16, 12, "<", px.COLOR_GRAY)
        self.point_type_next_btn = Button(self.x + w - 26, point_type_y, 16, 12, ">", px.COLOR_GRAY)
        self._point_type_label_y = point_type_y

        # --- name: 自由入力 ---
        self.field_name = InputField(self.x + 10, self.y + 50, w - 20, 12, "name", init_name)

        # --- event_key: 自由入力 + 既存テンプレートを<>で巡回できるセレクタ ---
        event_y = self.y + 78
        self.event_key_prev_btn = Button(self.x + 10, event_y, 14, 12, "<", px.COLOR_GRAY)
        self.event_key_next_btn = Button(self.x + w - 24, event_y, 14, 12, ">", px.COLOR_GRAY)
        self.field_event = InputField(self.x + 28, event_y, w - 66, 12, "", init_event_key)
        self._event_label_y = event_y

        self.field_name.active = True

        self.stats_label_y = self.y + 98
        self.stats_content_y = self.y + 108
        self.stats_line_height = 9

        self.btn_edit_stats = Button(
            self.x + w - 80, self.stats_label_y - 2, 70, 12, "Edit", px.COLOR_GRAY
        )

        btn_y = self.y + h - 24
        self.btn_ok = Button(self.x + 10, btn_y, 70, 14, "OK", px.COLOR_DARK_BLUE)
        self.btn_cancel = Button(self.x + w - 80, btn_y, 70, 14, "Cancel", px.COLOR_RED)

    def fields(self):
        return (self.field_name, self.field_event)

    def _cycle_point_type(self, step):
        idx = (
            POINT_TYPE_NAMES.index(self.point_type_value)
            if self.point_type_value in POINT_TYPE_NAMES
            else 0
        )
        self.point_type_value = POINT_TYPE_NAMES[(idx + step) % len(POINT_TYPE_NAMES)]

    def _cycle_event_key(self, step):
        """既存のeventpoints.jsonのキーを順に巡回してevent_keyへセットする
        (新規キーを入力したい場合はテキストとして直接編集すればよい)
        """
        keys = sorted(self.eventpoints.keys())
        if not keys:
            return
        current = self.field_event.value
        if current in keys:
            idx = (keys.index(current) + step) % len(keys)
        else:
            idx = 0 if step > 0 else len(keys) - 1
        self.field_event.value = keys[idx]

    def update(self):
        for f in self.fields():
            f.handle_key()

        if px.btnp(px.MOUSE_BUTTON_LEFT):
            mx, my = px.mouse_x, px.mouse_y

            if self.point_type_prev_btn.contains(mx, my):
                self._cycle_point_type(-1)
                return
            if self.point_type_next_btn.contains(mx, my):
                self._cycle_point_type(1)
                return
            if self.event_key_prev_btn.contains(mx, my):
                self._cycle_event_key(-1)
                return
            if self.event_key_next_btn.contains(mx, my):
                self._cycle_event_key(1)
                return

            # 入力欄がクリックされたらそちらへフォーカスを切り替える
            for f in self.fields():
                if f.contains(mx, my):
                    for other in self.fields():
                        other.active = False
                    f.active = True
                    break

    def _event_stat_lines(self):
        """現在のevent_key入力内容に対応するevent_statのキー一覧を整形して返す"""
        event_data = self.eventpoints.get(self.field_event.value)
        if event_data is None:
            return ["(該当するeventデータがありません)"]

        keys = list(event_data.get("event_stat", {}).keys())
        lines = _wrap_key_list(keys)
        return lines if lines else ["(event_statが空です)"]

    def draw(self):
        px.rect(self.x, self.y, self.w, self.h, px.COLOR_BLACK)
        px.rectb(self.x, self.y, self.w, self.h, px.COLOR_WHITE)
        title = "Edit Point" if self.mode == "edit" else "Add Point"
        px.text(self.x + 10, self.y + 6, title, px.COLOR_WHITE)

        # point_type セレクタ
        px.text(self.x + 10, self._point_type_label_y - 8, "point_type", px.COLOR_WHITE)
        self.point_type_prev_btn.draw()
        self.point_type_next_btn.draw()
        type_text_x = self.x + (self.w - len(self.point_type_value) * 4) // 2
        px.text(type_text_x, self._point_type_label_y + 3, self.point_type_value, px.COLOR_WHITE)

        # name
        self.field_name.draw()

        # event_key セレクタ + 自由入力欄
        px.text(
            self.x + 10,
            self._event_label_y - 8,
            "event_key (< > で既存テンプレートを巡回)",
            px.COLOR_WHITE,
        )
        self.event_key_prev_btn.draw()
        self.event_key_next_btn.draw()
        self.field_event.draw()

        px.text(self.x + 10, self.stats_label_y, "Event Stats:", px.COLOR_WHITE)
        self.btn_edit_stats.draw()
        for i, line in enumerate(self._event_stat_lines()):
            px.text(
                self.x + 10, self.stats_content_y + i * self.stats_line_height, line, px.COLOR_GRAY
            )

        self.btn_ok.draw()
        self.btn_cancel.draw()


class EventStatDialog:
    """eventpoints.jsonの1エントリ(eventpoint_type + event_stat)を編集するダイアログ

    - EventIDは規約(EVENT_ID_NAMES)で定義済のものだけを選択可能
    - 同じEventIDが複数のスロットに重複しないよう、選択肢を巡回する際に排除する
    - スロット数は常にEVENT_STAT_SLOT_COUNT(6)固定とすることで、
      「合計登録数が6イベント」という条件を構造的に満たす
    """

    def __init__(self, screen_w, screen_h, event_key, eventpoints):
        self.event_key = event_key
        existing = eventpoints.get(event_key)

        self.eventpoint_type = existing["eventpoint_type"] if existing else EVENT_TYPES[0]

        existing_stat = existing["event_stat"] if existing else {}
        names = [n for n in existing_stat.keys() if n in EVENT_ID_NAMES][:EVENT_STAT_SLOT_COUNT]
        thresholds = [str(existing_stat[n].get("threshold", 0)) for n in names]

        # 6件に満たない場合は、まだ使われていないEventIDで埋める
        used = set(names)
        for candidate in EVENT_ID_NAMES:
            if len(names) >= EVENT_STAT_SLOT_COUNT:
                break
            if candidate not in used:
                names.append(candidate)
                thresholds.append("0")
                used.add(candidate)

        self.slot_names = names  # 長さ EVENT_STAT_SLOT_COUNT の EventID名リスト

        w, h = 260, 200
        self.x = (screen_w - w) // 2
        self.y = (screen_h - h) // 2
        self.w, self.h = w, h

        self.type_prev_btn = Button(self.x + 10, self.y + 24, 16, 12, "<", px.COLOR_GRAY)
        self.type_next_btn = Button(self.x + 140, self.y + 24, 16, 12, ">", px.COLOR_GRAY)

        self.slot_prev_buttons = []
        self.slot_next_buttons = []
        self.slot_thresholds = []

        row_base_y = self.y + 44
        row_h = 20
        for i in range(EVENT_STAT_SLOT_COUNT):
            ry = row_base_y + i * row_h
            self.slot_prev_buttons.append(Button(self.x + 10, ry, 14, 12, "<", px.COLOR_GRAY))
            self.slot_next_buttons.append(Button(self.x + 96, ry, 14, 12, ">", px.COLOR_GRAY))
            self.slot_thresholds.append(
                InputField(self.x + 136, ry, 50, 12, "", thresholds[i], numeric_only=True)
            )

        btn_y = self.y + h - 22
        self.btn_ok = Button(self.x + 10, btn_y, 70, 14, "OK", px.COLOR_DARK_BLUE)
        self.btn_cancel = Button(self.x + w - 80, btn_y, 70, 14, "Cancel", px.COLOR_RED)

    def _cycle_type(self, step):
        idx = EVENT_TYPES.index(self.eventpoint_type) if self.eventpoint_type in EVENT_TYPES else 0
        self.eventpoint_type = EVENT_TYPES[(idx + step) % len(EVENT_TYPES)]

    def _cycle_slot(self, slot_index, step):
        """slot_index番目のEventIDを、他のスロットと重複しない範囲で前後に切り替える"""
        used_elsewhere = {n for j, n in enumerate(self.slot_names) if j != slot_index}
        current = self.slot_names[slot_index]
        pos = EVENT_ID_NAMES.index(current) if current in EVENT_ID_NAMES else 0
        n = len(EVENT_ID_NAMES)
        for k in range(1, n + 1):
            candidate = EVENT_ID_NAMES[(pos + step * k) % n]
            if candidate not in used_elsewhere:
                self.slot_names[slot_index] = candidate
                return

    def update(self):
        for f in self.slot_thresholds:
            f.handle_key()

        if px.btnp(px.MOUSE_BUTTON_LEFT):
            mx, my = px.mouse_x, px.mouse_y

            if self.type_prev_btn.contains(mx, my):
                self._cycle_type(-1)
                return
            if self.type_next_btn.contains(mx, my):
                self._cycle_type(1)
                return

            for i in range(EVENT_STAT_SLOT_COUNT):
                if self.slot_prev_buttons[i].contains(mx, my):
                    self._cycle_slot(i, -1)
                    return
                if self.slot_next_buttons[i].contains(mx, my):
                    self._cycle_slot(i, 1)
                    return
                if self.slot_thresholds[i].contains(mx, my):
                    for f in self.slot_thresholds:
                        f.active = False
                    self.slot_thresholds[i].active = True
                    return

    def draw(self):
        px.rect(self.x, self.y, self.w, self.h, px.COLOR_BLACK)
        px.rectb(self.x, self.y, self.w, self.h, px.COLOR_WHITE)
        px.text(self.x + 10, self.y + 6, f"Event Stats: {self.event_key}", px.COLOR_WHITE)

        self.type_prev_btn.draw()
        self.type_next_btn.draw()
        px.text(self.x + 32, self.y + 27, f"Type: {self.eventpoint_type}", px.COLOR_WHITE)

        row_base_y = self.y + 44
        row_h = 20
        for i in range(EVENT_STAT_SLOT_COUNT):
            ry = row_base_y + i * row_h
            self.slot_prev_buttons[i].draw()
            self.slot_next_buttons[i].draw()
            px.text(self.x + 28, ry + 3, self.slot_names[i], px.COLOR_WHITE)
            px.text(self.x + 116, ry + 3, "TH", px.COLOR_GRAY)
            self.slot_thresholds[i].draw()

        self.btn_ok.draw()
        self.btn_cancel.draw()


class App:
    def __init__(self):
        self.pointcolors = {
            "SAFETY": (px.COLOR_WHITE, px.COLOR_RED),
            "NORMAL": (px.COLOR_GREEN, px.COLOR_WHITE),
            "GAMBLE": (px.COLOR_YELLOW, px.COLOR_GREEN),
            "BATTLE": (px.COLOR_RED, px.COLOR_YELLOW),
        }
        self.datapath = check_file(MAP_DATA_PATH)
        mapdata = read_json(self.datapath)
        self.points = mapdata["points"]
        self.routes = mapdata["routes"]

        self.eventpoints = self._load_eventpoints()

        sizing: px.Image = px.Image.from_image("../assets/image/map.bmp")
        # quit_key=KEY_NONEでESCキーによる終了(pyxelのデフォルト挙動)を無効化。
        # 誤ってESCを押しても編集中データを失わないようにするため、
        # アプリを閉じる手段はウィンドウの×のみとする。
        px.init(sizing.width, sizing.height, display_scale=2, quit_key=px.KEY_NONE)
        px.load("../assets/assets.pyxres")
        # パレット読み込みしてから画像ロード
        self.mapimage: px.Image = px.Image.from_image("../assets/image/map.bmp")
        px.mouse(True)

        self.mode = "normal"  # "normal" / "dialog" / "event_dialog" / "confirm_delete_point"
        self.dialog = None  # PointDialog インスタンス
        self.event_dialog = None  # EventStatDialog インスタンス

        # Shift+左クリックによるポイント削除確認用の状態
        self.confirm_dialog = None  # ConfirmDialog インスタンス
        self.pending_delete_point = None  # 削除確認中のポイント(dict)

        # Ctrl+ドラッグによるroute作成・削除用の状態
        self.dragging = False
        self.drag_mode = None  # "create"（route作成） または "delete"（route削除）
        self.drag_start_point = None

        px.run(self.update, self.draw)

    # ------------------------------------------------------------------
    # event_stat定義ファイルの読み込み（存在しない場合は空データで継続する）
    # ------------------------------------------------------------------
    def _load_eventpoints(self):
        self.eventpoints_path = check_file(EVENTPOINTS_PATH)
        if self.eventpoints_path is None:
            print(f"警告: {EVENTPOINTS_PATH} が見つかりません。Event Statsは表示されません。")
            return {}
        return read_json(self.eventpoints_path)

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
    # route ID採番: 既存の "rXXX" 形式idの最大値+1を新しいidとする
    # ------------------------------------------------------------------
    def _route_id_num(self, route_id):
        """ "rXXX"形式のidから数値部分を取り出す。形式に合わない場合はNone"""
        m = re.match(r"r(\d+)$", route_id)
        return int(m.group(1)) if m else None

    def _format_route_id(self, num):
        width = 3 if num < 1000 else len(str(num))
        return f"r{num:0{width}d}"

    def _generate_next_route_id(self):
        nums = [n for r in self.routes if (n := self._route_id_num(r["id"])) is not None]
        next_num = (max(nums) + 1) if nums else 1
        return self._format_route_id(next_num)

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
            self.dialog = PointDialog(px.width, px.height, "edit", self.eventpoints, point=nearest)
            self.mode = "dialog"
            return

        if nearest is not None and dist <= NEAR_THRESHOLD:
            # 円の外だが中心から30px以内 → 追加しない
            print("距離が近すぎる")
            return

        # どのポイントからも十分離れている → 新規追加ダイアログを表示
        new_id = self._generate_new_id()
        # event_keyは「新規に採番」ではなく「既存テンプレートから選ぶ」運用に変わったため、
        # 既存テンプレートがあればその先頭(ソート順)をデフォルト値として提案する
        existing_keys = sorted(self.eventpoints.keys())
        default_event_key = existing_keys[0] if existing_keys else ""
        self.dialog = PointDialog(
            px.width,
            px.height,
            "add",
            self.eventpoints,
            pending_xy=(mx, my),
            pending_id=new_id,
            default_event_key=default_event_key,
        )
        self.mode = "dialog"

    def _confirm_dialog(self):
        d = self.dialog
        point_type = d.point_type_value
        name = d.field_name.value.strip()
        event_key = d.field_event.value.strip()

        if d.mode == "edit":
            # x, yは変更せず、point_type・name・event_keyのみ更新する
            d.point["point_type"] = point_type
            d.point["name"] = name
            d.point["event_key"] = event_key
        else:
            new_id = d.pending_id or self._generate_new_id()
            x, y = d.pending_xy
            new_point = {
                "id": new_id,
                "point_type": point_type,
                "name": name,
                "event_key": event_key,
                "x": x,
                "y": y,
            }
            self.points.append(new_point)

        self.dialog = None
        self.mode = "normal"

    def _cancel_dialog(self):
        self.dialog = None
        self.mode = "normal"

    # ------------------------------------------------------------------
    # ポイント削除(Shift+左クリック → 確認ダイアログ)
    # ------------------------------------------------------------------
    def _try_start_delete_point(self, mx, my):
        nearest, dist = self._find_nearest_point(mx, my)
        if nearest is None or dist > CIRCLE_RADIUS:
            return  # ポイントの無い場所でのShift+クリックは無視

        connected_routes = [
            r for r in self.routes if r["from"] == nearest["id"] or r["to"] == nearest["id"]
        ]
        if connected_routes:
            print(
                f"削除できません: {nearest['id']}に接続されたrouteが{len(connected_routes)}件残っています。"
                "先にroute(Ctrl+右ドラッグ)を削除してください"
            )
            return

        self.pending_delete_point = nearest
        self.confirm_dialog = ConfirmDialog(
            px.width,
            px.height,
            [f"ポイント {nearest['id']} を削除しますか？", nearest.get("name", "")],
        )
        self.mode = "confirm_delete_point"

    def _confirm_delete_point(self):
        point = self.pending_delete_point
        if point in self.points:
            self.points.remove(point)
            print(f"ポイントを削除しました: {point['id']}")

        self.pending_delete_point = None
        self.confirm_dialog = None
        self.mode = "normal"

    def _cancel_delete_point(self):
        self.pending_delete_point = None
        self.confirm_dialog = None
        self.mode = "normal"

    # ------------------------------------------------------------------
    # Event Stats編集ダイアログ(EventStatDialog)の開始・確定・キャンセル
    # ------------------------------------------------------------------
    def _open_event_stat_dialog(self):
        event_key = self.dialog.field_event.value.strip()
        if not event_key:
            print("event_keyが未入力のため、Event Statsを編集できません")
            return
        self.event_dialog = EventStatDialog(px.width, px.height, event_key, self.eventpoints)
        self.mode = "event_dialog"

    def _confirm_event_dialog(self):
        ed = self.event_dialog

        event_stat = {}
        for name, field in zip(ed.slot_names, ed.slot_thresholds):
            raw = field.value.strip()
            threshold = int(raw) if raw.isdigit() else 0
            event_stat[name] = {"threshold": threshold}

        self.eventpoints[ed.event_key] = {
            "eventpoint_type": ed.eventpoint_type,
            "event_stat": event_stat,
        }
        print(f"eventpoints情報を更新しました(未保存): {ed.event_key}")

        self.event_dialog = None
        self.mode = "dialog"  # 呼び出し元のポイント編集ダイアログへ戻る

    def _cancel_event_dialog(self):
        self.event_dialog = None
        self.mode = "dialog"

    # ------------------------------------------------------------------
    # 2点間のなす方向を上下左右の4方向(扇形90°)に分類する
    # 画面座標系(yは下方向が正)を前提とする
    # ------------------------------------------------------------------
    def _calc_direction(self, from_point, to_point):
        dx = to_point["x"] - from_point["x"]
        dy = to_point["y"] - from_point["y"]
        angle = math.degrees(math.atan2(dy, dx)) % 360

        if 45 <= angle < 135:
            return "down"
        elif 135 <= angle < 225:
            return "left"
        elif 225 <= angle < 315:
            return "up"
        else:
            return "right"

    def _has_direction_conflict(self, point_id, direction):
        """point_idを起点とするrouteの中に、指定方向と同じdirectionを持つものが
        既に存在するかを判定する。

        ゲーム中の移動ロジックは上下左右の4方向にしか対応しておらず、
        同じ起点から同じ方向に2つ以上の移動先が定義されると
        どちらを移動先とすべきか判定できなくなるため（コアロジックのため変更不可）、
        route作成前に必ずこのチェックを行う。
        """
        return any(r["from"] == point_id and r["direction"] == direction for r in self.routes)

    def _try_create_route(self, from_point, to_point):
        from_id = from_point["id"]
        to_id = to_point["id"]

        # 既に(from,to)のセットを行き・帰りどちらかの向きで保有していれば何もしない
        exists = any(
            (r["from"] == from_id and r["to"] == to_id)
            or (r["from"] == to_id and r["to"] == from_id)
            for r in self.routes
        )
        if exists:
            print(f"route情報は既に存在するため作成しません: {from_id} - {to_id}")
            return

        forward_direction = self._calc_direction(from_point, to_point)
        backward_direction = self._calc_direction(to_point, from_point)

        # 起点(from_id)側に、これから作ろうとしている方向(forward_direction)と
        # 同じ方向のrouteが既にある場合は作成しない
        if self._has_direction_conflict(from_id, forward_direction):
            print(
                f"route作成をスキップしました: {from_id}には既に{forward_direction}方向の"
                "routeが定義されているため、新しいrouteを作成できません"
            )
            return

        # 復路側の起点(to_id)についても同様にチェックする
        if self._has_direction_conflict(to_id, backward_direction):
            print(
                f"route作成をスキップしました: {to_id}には既に{backward_direction}方向の"
                "routeが定義されているため、新しいrouteを作成できません"
            )
            return

        forward_id = self._generate_next_route_id()
        self.routes.append(
            {
                "id": forward_id,
                "from": from_id,
                "to": to_id,
                "cost": 1,
                "threat": 0,
                "direction": forward_direction,
            }
        )

        # 復路(to -> from)をセットで作成する
        backward_id = self._generate_next_route_id()
        self.routes.append(
            {
                "id": backward_id,
                "from": to_id,
                "to": from_id,
                "cost": 1,
                "threat": 0,
                "direction": backward_direction,
            }
        )

        print(
            f"route情報を作成しました: {forward_id}({from_id}->{to_id}), {backward_id}({to_id}->{from_id})"
        )

    # ------------------------------------------------------------------
    # 2点間の往路・復路routeを検索する
    # ------------------------------------------------------------------
    def _find_route_pair(self, id_a, id_b):
        forward = next((r for r in self.routes if r["from"] == id_a and r["to"] == id_b), None)
        backward = next((r for r in self.routes if r["from"] == id_b and r["to"] == id_a), None)
        return forward, backward

    def _try_delete_route(self, point_a, point_b):
        id_a, id_b = point_a["id"], point_b["id"]
        forward, backward = self._find_route_pair(id_a, id_b)

        if forward is None and backward is None:
            print(f"route情報が存在しないため削除しません: {id_a} - {id_b}")
            return

        removed_ids = []
        for route in (forward, backward):
            if route is not None:
                removed_ids.append(route["id"])
                self.routes.remove(route)

        print(f"route情報を削除しました: {', '.join(removed_ids)} ({id_a} <-> {id_b})")
        self._fill_route_id_gaps(removed_ids)

    def _fill_route_id_gaps(self, freed_ids):
        """削除によって空いたid番号に、現在の末尾(番号が一番大きい)のrouteを
        詰め直し、id番号に欠番が出ないようにする。
        他のデータからidを参照される想定がないため、単純な振り直しでよい。
        """
        freed_nums = sorted(
            n for n in (self._route_id_num(rid) for rid in freed_ids) if n is not None
        )

        for freed_num in freed_nums:
            if not self.routes:
                break
            tail_route = max(self.routes, key=lambda r: self._route_id_num(r["id"]) or -1)
            tail_num = self._route_id_num(tail_route["id"])
            if tail_num is None or tail_num <= freed_num:
                # 空いた番号より大きいidが残っていない(既に末尾) → 詰め直し不要
                continue
            old_id = tail_route["id"]
            new_id = self._format_route_id(freed_num)
            tail_route["id"] = new_id
            print(f"route idを振り直しました: {old_id} -> {new_id}")

    def _backup_file(self, path):
        """保存前に、指定ファイルを "<ファイル名>.YYYYMMDD_HHMMSS" という名前でコピーしておく"""
        if path is None or not path.exists():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.with_name(f"{path.name}.{timestamp}")
        shutil.copy2(path, backup_path)
        print(f"バックアップを作成しました: {backup_path.name}")

    def _save(self):
        self._backup_file(self.datapath)
        write_json(self.datapath, {"points": self.points, "routes": self.routes})
        saved_files = ["map_data.json"]

        if self.eventpoints_path is not None:
            self._backup_file(self.eventpoints_path)
            write_json(self.eventpoints_path, self.eventpoints)
            saved_files.append("eventpoints.json")

        print(f"保存しました: {', '.join(saved_files)}")

    # ------------------------------------------------------------------
    # 現在の状態を俯瞰するための表示機能
    # ------------------------------------------------------------------
    def _draw_flag_markers(self, point):
        """event_keyがflgで始まるポイントの右上に、キー名末尾の文字を表示する"""
        event_key = point.get("event_key", "")
        if not event_key.lower().startswith("flg"):
            return
        flag_char = event_key[-1].upper()
        px.text(
            point["x"] + CIRCLE_RADIUS - 2,
            point["y"] - CIRCLE_RADIUS - 7,
            flag_char,
            px.COLOR_YELLOW,
        )

    def _build_point_type_counts(self):
        """マップ上の各ポイントを、実際に解決されるeventpoint_type別に集計する
        (テンプレート定義数ではなく、マップポイント自体の数)
        """
        counts = {t: 0 for t in EVENT_TYPES}
        for p in self.points:
            entry = self.eventpoints.get(p.get("event_key"))
            if entry and entry.get("eventpoint_type") in counts:
                counts[entry["eventpoint_type"]] += 1
        return counts

    def _build_event_definition_counts(self):
        """EventID x EventType の出現数を集計する

        eventpoints.jsonは複数pointから共有される「テンプレート」なので、
        テンプレート自体を1回ずつ数えるのではなく、map_data.json側の各pointが
        実際にそのテンプレートを参照している回数ぶんだけ加重して数える。
        これにより、複数pointから参照されるテンプレートは参照された回数分カウントされ、
        逆にどのpointからも参照されていないテンプレート(あれば)は計上されない。
        """
        counts = {name: {t: 0 for t in EVENT_TYPES} for name in EVENT_ID_NAMES}
        for p in self.points:
            entry = self.eventpoints.get(p.get("event_key"))
            if entry is None:
                continue
            etype = entry.get("eventpoint_type")
            if etype not in EVENT_TYPES:
                continue
            for event_id in entry.get("event_stat", {}).keys():
                if event_id in counts:
                    counts[event_id][etype] += 1
        return counts

    def _draw_event_definition_matrix(self):
        """描画領域右上に、EventID(縦軸) x EventType(横軸)の定義数マトリクスを表示する
        軸のラベルはEventID/EventTypeのenumメンバー名(name)をそのまま欠落なく表示する
        """
        col_w = MATRIX_TYPE_COL_WIDTH
        row_h = MATRIX_ROW_HEIGHT
        label_w = MATRIX_LABEL_COL_WIDTH
        header_rows = 2  # 1行目:実ポイント数, 2行目:EventType名

        total_w = label_w + col_w * len(EVENT_TYPES)
        total_h = row_h * (header_rows + len(EVENT_ID_NAMES))

        mx = px.width - total_w - 4
        my = 4

        px.rect(mx, my, total_w, total_h, px.COLOR_BLACK)
        px.rectb(mx, my, total_w, total_h, px.COLOR_WHITE)

        point_counts = self._build_point_type_counts()
        definition_counts = self._build_event_definition_counts()

        # ヘッダー: 各タイプの実ポイント数 / EventType名
        for ci, etype in enumerate(EVENT_TYPES):
            cx = mx + label_w + ci * col_w
            count_text = str(point_counts.get(etype, 0))
            px.text(
                cx + max(0, (col_w - len(count_text) * 4)) // 2, my + 1, count_text, px.COLOR_WHITE
            )
            px.text(
                cx + max(0, (col_w - len(etype) * 4)) // 2, my + 1 + row_h, etype, px.COLOR_YELLOW
            )

        # 各行: EventID名 + タイプ別定義数
        for ri, name in enumerate(EVENT_ID_NAMES):
            ry = my + header_rows * row_h + ri * row_h
            px.text(mx + 2, ry + 1, name, px.COLOR_YELLOW)

            for ci, etype in enumerate(EVENT_TYPES):
                cx = mx + label_w + ci * col_w
                cnt = definition_counts[name][etype]
                text = str(cnt) if cnt else "-"
                color = px.COLOR_WHITE if cnt else px.COLOR_GRAY
                px.text(cx + max(0, (col_w - len(text) * 4)) // 2, ry + 1, text, color)

    # ------------------------------------------------------------------
    def update(self):
        if self.mode == "confirm_delete_point":
            if px.btnp(px.MOUSE_BUTTON_LEFT):
                mx, my = px.mouse_x, px.mouse_y
                if self.confirm_dialog.btn_ok.contains(mx, my):
                    self._confirm_delete_point()
                elif self.confirm_dialog.btn_cancel.contains(mx, my):
                    self._cancel_delete_point()
                return

            enter_pressed = (ENTER_KEY is not None and px.btnp(ENTER_KEY)) or (
                KP_ENTER_KEY is not None and px.btnp(KP_ENTER_KEY)
            )
            if enter_pressed:
                self._confirm_delete_point()
            return

        if self.mode == "event_dialog":
            self.event_dialog.update()

            if px.btnp(px.MOUSE_BUTTON_LEFT):
                mx, my = px.mouse_x, px.mouse_y
                if self.event_dialog.btn_ok.contains(mx, my):
                    self._confirm_event_dialog()
                elif self.event_dialog.btn_cancel.contains(mx, my):
                    self._cancel_event_dialog()
            return

        if self.mode == "dialog":
            self.dialog.update()

            if px.btnp(px.MOUSE_BUTTON_LEFT):
                mx, my = px.mouse_x, px.mouse_y
                if self.dialog.btn_ok.contains(mx, my):
                    self._confirm_dialog()
                elif self.dialog.btn_cancel.contains(mx, my):
                    self._cancel_dialog()
                elif self.dialog.btn_edit_stats.contains(mx, my):
                    self._open_event_stat_dialog()
            return

        ctrl_held = CTRL_KEY is not None and px.btn(CTRL_KEY)

        if ctrl_held:
            # Ctrl+S でmap_data.jsonを保存
            if SAVE_KEY is not None and px.btnp(SAVE_KEY):
                self._save()

            # Ctrl+マウス左ドラッグでroute作成を開始
            if px.btnp(px.MOUSE_BUTTON_LEFT) and not self.dragging:
                nearest, dist = self._find_nearest_point(px.mouse_x, px.mouse_y)
                if nearest is not None and dist <= CIRCLE_RADIUS:
                    self.dragging = True
                    self.drag_mode = "create"
                    self.drag_start_point = nearest

            # Ctrl+マウス右ドラッグでroute削除を開始
            if px.btnp(px.MOUSE_BUTTON_RIGHT) and not self.dragging:
                nearest, dist = self._find_nearest_point(px.mouse_x, px.mouse_y)
                if nearest is not None and dist <= CIRCLE_RADIUS:
                    self.dragging = True
                    self.drag_mode = "delete"
                    self.drag_start_point = nearest

            # 左ボタンを離した → route作成を確定
            if self.dragging and self.drag_mode == "create" and px.btnr(px.MOUSE_BUTTON_LEFT):
                nearest, dist = self._find_nearest_point(px.mouse_x, px.mouse_y)
                if (
                    nearest is not None
                    and dist <= CIRCLE_RADIUS
                    and nearest["id"] != self.drag_start_point["id"]
                ):
                    self._try_create_route(self.drag_start_point, nearest)
                self._reset_drag()

            # 右ボタンを離した → route削除を確定
            if self.dragging and self.drag_mode == "delete" and px.btnr(px.MOUSE_BUTTON_RIGHT):
                nearest, dist = self._find_nearest_point(px.mouse_x, px.mouse_y)
                if (
                    nearest is not None
                    and dist <= CIRCLE_RADIUS
                    and nearest["id"] != self.drag_start_point["id"]
                ):
                    self._try_delete_route(self.drag_start_point, nearest)
                self._reset_drag()
            return

        # Ctrlが離されたら、進行中のドラッグはキャンセルする
        if self.dragging:
            self._reset_drag()

        # Shift+左クリックでポイント削除確認を開始
        if SHIFT_KEY is not None and px.btn(SHIFT_KEY) and px.btnp(px.MOUSE_BUTTON_LEFT):
            self._try_start_delete_point(px.mouse_x, px.mouse_y)
            return

        # 通常モード（ダイアログ非表示・Ctrl/Shift非押下時）
        if px.btnp(px.MOUSE_BUTTON_LEFT):
            self._handle_map_click(px.mouse_x, px.mouse_y)
            return

    def _reset_drag(self):
        self.dragging = False
        self.drag_mode = None
        self.drag_start_point = None

    def draw(self):
        px.blt(0, 0, self.mapimage, 0, 0, self.mapimage.width, self.mapimage.height)

        for route in self.routes:
            from_addr = [
                (point["x"], point["y"]) for point in self.points if point["id"] == route["from"]
            ]
            to_addr = [
                (point["x"], point["y"]) for point in self.points if point["id"] == route["to"]
            ]
            # ロック状態に関わらず全てのrouteを表示する。
            # 色分けはfield_map.pyのMapGraph.draw()と同じ配色(ロック中はグレー)に合わせている
            line_color = px.COLOR_GRAY if route.get("locked", False) else px.COLOR_WHITE
            px.line(*from_addr[0], *to_addr[0], line_color)

        for point in self.points:
            cols = self.pointcolors[self.eventpoints[point["event_key"]]["eventpoint_type"]]
            px.circ(point["x"], point["y"], CIRCLE_RADIUS, cols[0])
            px.text(point["x"] - 4, point["y"] - 2, point["id"], cols[1])
            self._draw_flag_markers(point)

        if self.dragging and self.drag_start_point is not None:
            sx, sy = self.drag_start_point["x"], self.drag_start_point["y"]
            mx, my = px.mouse_x, px.mouse_y
            line_color = px.COLOR_YELLOW if self.drag_mode == "create" else px.COLOR_RED
            px.line(sx, sy, mx, my, line_color)

            target, dist = self._find_nearest_point(mx, my)
            if (
                target is not None
                and dist <= CIRCLE_RADIUS
                and target["id"] != self.drag_start_point["id"]
            ):
                if self.drag_mode == "create":
                    px.circb(target["x"], target["y"], CIRCLE_RADIUS + 3, px.COLOR_LIME)
                else:
                    forward, backward = self._find_route_pair(
                        self.drag_start_point["id"], target["id"]
                    )
                    if forward is not None or backward is not None:
                        px.circb(target["x"], target["y"], CIRCLE_RADIUS + 3, px.COLOR_RED)

        if px.btn(px.MOUSE_BUTTON_RIGHT) and self.dragging is False:
            px.blt(0, 0, self.mapimage, 0, 0, self.mapimage.width, self.mapimage.height)

        # 右上の定義数マトリクスは、素の地図を覗いている間も見えたままにしたいので
        # 上のpeek処理より後で描画する
        self._draw_event_definition_matrix()

        # PointDialog表示中(Event Stats編集ダイアログを開いている間も含む)は
        # 背面にPointDialogを残したまま、その上にEventStatDialogを重ねて描画する
        if self.dialog is not None:
            self.dialog.draw()
        if self.event_dialog is not None:
            self.event_dialog.draw()
        if self.confirm_dialog is not None:
            self.confirm_dialog.draw()


App()
