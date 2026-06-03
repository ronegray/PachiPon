"""field_map.py
ノンフィールドマップの定義
- 背景マップの定義
- マップ上のイベントポイントを定義
- イベントポイント間のルートを定義
"""
import pyxel


class Route:
    """イベントポイント間を接続するルートの定義"""

    def __init__(self, route_data):
        self.id = route_data.get("id")
        self.from_id = route_data.get("from")
        self.to_id = route_data.get("to")
        self.cost = route_data.get("cost", 1)
        self.label = route_data.get("label", "")
        self.locked = route_data.get("locked", False)
        self.direction = route_data.get("direction")  # 'up', 'down', 'left', 'right'


class EventPoint:
    """マップ上に定義されるイベント地点"""

    def __init__(self, point_data):
        self.id: int = point_data.get("id")
        self.name: str = point_data.get("name", "")
        self.event_id = point_data.get("eventId")
        self.x = point_data.get("x", 0)
        self.y = point_data.get("y", 0)
        self.routes = []

    def add_route(self, route):
        self.routes.append(route)

    def get_reachable_routes(self):
        return [r for r in self.routes if not r.locked]


class MapGraph:
    """イベントポイントとルートの管理クラス"""

    def __init__(self):
        self.points = {}  # id -> EventPoint

    def load_from_json(self, data):
        # 頂点を登録
        for p_data in data.get("points", []):
            self.points[p_data["id"]] = EventPoint(p_data)

        # 辺を登録
        for r_data in data.get("routes", []):
            route = Route(r_data)
            if route.from_id in self.points:
                self.points[route.from_id].add_route(route)

    def get_point(self, point_id) -> EventPoint | None:
        return self.points.get(point_id)

    def get_connected_node(self, current_node_id, direction):
        point = self.get_point(current_node_id)
        if not point:
            return None

        for route in point.get_reachable_routes():
            if route.direction == direction:
                return route.to_id
        return None

    def draw(self, offset_x: int = 0, offset_y: int = 0):
        # 線（Route）の描画
        for point in self.points.values():
            for route in point.routes:
                target_point = self.get_point(route.to_id)
                if target_point:
                    color = 13 if route.locked else 7
                    pyxel.line(
                        point.x + offset_x,
                        point.y + offset_y,
                        target_point.x + offset_x,
                        target_point.y + offset_y,
                        color,
                    )

        # 点（EventPoint）の描画
        for point in self.points.values():
            pyxel.circ(point.x + offset_x, point.y + offset_y, 2, 7)
            # pyxel.text(point.x + offset_x + 4, point.y + offset_y + 4, point.name, 7)
