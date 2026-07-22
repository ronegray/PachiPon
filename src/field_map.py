"""
ノンフィールドマップの定義

- 背景マップの定義
- マップ上のイベントポイントを定義
- イベントポイント間のルートを定義
"""

import logging
from typing import Literal
import pyxel as px
from assets.asset_map import AssetID, AssetMap
from gameutils.base import check_file, read_json
import service_locater as di
from event import EventList, EventType, EventStat, Event, EventID


# ルート方向指定子
ROUTE_DIR = Literal["up", "down", "left", "right"]


# ロギング設定
logger = logging.getLogger(__name__)


class Route:
    """イベントポイント間を接続するルートの定義"""

    def __init__(self, route_data: dict) -> None:
        """Routeオブジェクト定義"""
        tmp_id = route_data.get("id")
        tmp_from = route_data.get("from")
        tmp_to = route_data.get("to")
        tmp_dir = route_data.get("direction")  # 'up','down','left','right'
        if (
            (tmp_id is None)
            or (tmp_from is None)
            or (tmp_to is None)
            or (tmp_dir is None)
        ):
            errmsg = "必須項目(ID/from/to/direction)のいずれかが未定義です"
            logger.critical(errmsg, exc_info=True)
            raise TypeError(errmsg)
        self.id: str = tmp_id
        self.from_id: str = tmp_from
        self.to_id: str = tmp_to
        self.cost: int = route_data.get("cost", 1)
        self.threat: int = route_data.get("threat", 0)
        self.label: str = route_data.get("label", "")
        self.locked: bool = route_data.get("locked", False)
        self.direction: ROUTE_DIR = tmp_dir


class EventPoint:
    """マップ上に定義されるイベント地点"""

    ready_timer: dict[str, int] = {"NORMAL": 3, "SAFETY": 1, "GAMBLE": 9, "BATTLE": 1}

    def __init__(self, point_data: dict, event_dict: dict) -> None:
        """EventPointオブジェクト定義"""
        tmp_id = point_data.get("id")
        if tmp_id is None:
            errmsg = "イベントポイントIDが未定義です"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)
        tmp_evid = point_data.get("eventId")
        if tmp_evid is None:
            errmsg = "イベントIDが未定義です"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)

        self.id: str = tmp_id
        self.name: str = point_data.get("name", "Unknown")
        self.event_id: str = tmp_evid
        self.event_type: EventType = EventType[
            event_dict.get("eventpoint_type", "NORMAL")
        ]
        self.is_ready: bool = True
        self.ready_count: int = 0
        self.x: int = point_data.get("x", 0)
        self.y: int = point_data.get("y", 0)
        self.routes: list[Route] = []
        self.nextevent: Event | None = None

        # イベントポイントのイベント状態を定義
        self.event_list: EventList
        is_first = True
        for key, ev_def in event_dict["event_stat"].items():
            if is_first:
                self.event_list = EventList(
                    self.event_id,
                    self.event_type,
                    {EventID[key]: EventStat(ev_def["threshold"])},
                )
                is_first = False
            else:
                self.event_list.event_stat[EventID[key]] = EventStat(
                    ev_def["threshold"]
                )
        pass

    def add_route(self, route: Route) -> None:
        """イベントポイントにルートを結合"""
        self.routes.append(route)

    def get_reachable_routes(self) -> list[Route]:
        """非ロック状態のルートを取得"""
        return [r for r in self.routes if not r.locked]

    def get_eventpoint_info(self) -> dict:
        """イベントポイントの情報を文字列化して取得"""
        result_dict = {}
        for event_id, event_stat in self.event_list.event_stat.items():
            if event_stat.threshold > 0:
                if event_stat.is_opened:
                    logger.debug(self.event_list.eventpoint_type, event_id)  # type: ignore
                    event_def = di.ref.evtrps.get_event(
                        self.event_list.eventpoint_type, event_id
                    )
                    name = event_def.event_name  # type: ignore
                else:
                    name = "？？？？？？？？"
                result_dict[event_id] = {
                    "name": name,
                    "threshold": event_stat.threshold,
                }

        return result_dict

    def kick_event(self) -> int:
        """イベント開始準備
        - ポイントのイベント準備状態を更新
        - イベントタイプから発生イベント決定用ダイス値を取得
        """
        # イベントポイントの準備状態を変更
        self.is_ready = False
        # イベントタイプからカウンタ兼ダイス数を取得
        cnt = EventPoint.ready_timer[self.event_type.name]
        self.ready_count = cnt
        return cnt

    def rise_event(self, evt_id: EventID) -> None:
        """実行イベント定義"""
        self.nextevent = di.ref.evtrps.get_event(self.event_type, evt_id)

    def flush_event(self) -> None:
        """実行イベント定義のクリア"""
        self.nextevent = None

    def update(self):
        """イベント準備状態の更新"""
        self.ready_count = max(0, self.ready_count - 1)
        if self.ready_count == 0:
            self.is_ready = True

    def draw(self, offset_x: float = 0, offset_y: float = 0):
        """イベントポイント情報の描画"""
        px_COLOR_0x00FF00 = 27
        # px.circ(self.x + offset_x, self.y + offset_y, 2, px_COLOR_0x00FF00)
        pointcolor = px_COLOR_0x00FF00 if self.is_ready else px.COLOR_RED
        px.circ(self.x + offset_x, self.y + offset_y, 2, pointcolor)
        px.circb(self.x + offset_x, self.y + offset_y, 2, px.COLOR_WHITE)
        # px.text(
        #     self.x + offset_x + 4,
        #     self.y + offset_y + 4,
        #     self.name,
        #     px.COLOR_WHITE,
        # )


class MapGraph:
    """マップ情報（イベントポイント、ルート、画像）の管理クラス"""

    _instance = None  # シングルトンインスタンスの器
    points: dict[str, EventPoint]

    def __new__(cls) -> "MapGraph":
        """シングルトンインスタンス管理"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """マップの初期化"""
        # マップ構造はマップ画像から生成する為両者をセットで管理
        self.map_img: px.Image  # マップ画像はpyxelパレットロード後に読み込む
        self.map_img_width: int = 0
        self.map_img_height: int = 0
        # マップ構造データのロードと構築
        self.points = {}  # id -> EventPoint
        self.load_mapdata()

    def load_mapimage(self) -> None:
        """マップ画像データの遅延ロード（pyxpalロード後に実行）"""
        self.map_img = px.Image.from_image(AssetMap.get_assetpath(AssetID.IMAGE_MAP))
        self.map_img_width = self.map_img.width
        self.map_img_height = self.map_img.height

    def load_mapdata(self) -> None:
        """map_data.jsonのデータからイベントポイントを登録"""
        map_path = check_file(AssetMap.get_assetpath(AssetID.DATA_MAP), "r")
        if map_path:
            data: dict = read_json(map_path)
        else:
            errmsg = "マップ構造データファイルが見つかりません"
            logger.critical(errmsg, exc_info=True)
            raise FileNotFoundError(errmsg)

        ev_path = check_file(AssetMap.get_assetpath(AssetID.DATA_EVENTPOINT), "r")
        if ev_path:
            evdata: dict = read_json(ev_path)
        else:
            errmsg = "ポイント別イベント構成ファイルが見つかりません"
            logger.critical(errmsg, exc_info=True)
            raise FileNotFoundError(errmsg)

        # 頂点を登録
        for point in data.get("points", []):
            event_def = evdata[point["eventId"]]
            self.points[point["id"]] = EventPoint(point, event_def)

        # 辺を登録
        for r_data in data.get("routes", []):
            route = Route(r_data)
            if route.from_id in self.points:
                self.points[route.from_id].add_route(route)

    def get_point(self, point_id: str) -> EventPoint | None:
        """指定IDのイベントポイントオブジェクトを取得"""
        return self.points.get(point_id)

    def get_route(
        self, current_node_id: str, direction: ROUTE_DIR | str
    ) -> Route | None:
        """現地点から選択した方向へのルート情報を取得"""
        point = self.get_point(current_node_id)
        if not point:
            return None

        for route in point.get_reachable_routes():
            if route.direction == direction:
                return route
        return None

    def get_connected_node(
        self, current_node_id: str, direction: ROUTE_DIR | str
    ) -> str | None:
        """現地点から移動可能なイベントポイントを取得"""
        point = self.get_point(current_node_id)
        if not point:
            return None

        for route in point.get_reachable_routes():
            if route.direction == direction:
                return route.to_id
        return None

    def draw(self, offset_x: float = 0, offset_y: float = 0):
        """マップデータ（画像・イベントポイント・ルート）の描画"""
        # マップ背景の描画 (ワールド座標 (0,0) を ox, oy に描画)
        px.blt(
            offset_x,
            offset_y,
            self.map_img,
            0,
            0,
            self.map_img_width,
            self.map_img_height,
        )

        # 線（Route）の描画
        draw_target_points = []
        for point in self.points.values():
            # 描画範囲にあるポイントに対してのみ描画処理を実行
            if (
                offset_x <= point.x <= self.map_img_width
                and offset_y <= point.y <= self.map_img_height
            ):
                # 線（Route）の描画
                for route in point.routes:
                    target_point = self.get_point(route.to_id)
                    if target_point:
                        color = px.COLOR_GRAY if route.locked else px.COLOR_WHITE
                        px.line(
                            point.x + offset_x,
                            point.y + offset_y,
                            target_point.x + offset_x,
                            target_point.y + offset_y,
                            color,
                        )
                # 描画対象ポイントの確保
                # 次ポイントのroute描画でポイントが上書きされるのを防ぐ
                draw_target_points.append(point)

        # 点（EventPoint）の描画
        for point in draw_target_points:
            point.draw(offset_x, offset_y)
