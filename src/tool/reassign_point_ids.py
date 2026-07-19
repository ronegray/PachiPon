"""reassign_point_ids.py

map_data.json の points 情報を整備するスクリプト。

- p01 を起点(基点)として固定する
- それ以外の全pointを、基点(p01)からの距離が近い順にソートし、
  p02, p03, ... と採番していく（あくまで基点からの距離のみで判定する。
  直前に採番したpointからの距離は見ない）
- 新しいidに合わせて eventId を "ev_<新id>" に更新する
- routes情報は別スクリプトでpoints情報のみを元に再生成されるため、本スクリプトでは触らない
"""

import json
import math
from pathlib import Path

SRC_PATH = Path("../assets/data/map_data.json")
OUT_PATH = Path("../assets/data/map_data.json")


def distance(p1: dict, p2: dict) -> float:
    return math.hypot(p1["x"] - p2["x"], p1["y"] - p2["y"])


def reorder_points_by_distance_from_start(
    points: list[dict], start_id: str = "p01"
) -> list[dict]:
    """start_id(p01)を先頭に固定し、それ以外のpointを
    「基点(p01)からの距離」だけで昇順ソートしたリストを返す。
    """
    start_index = next(i for i, p in enumerate(points) if p["id"] == start_id)
    start_point = points[start_index]

    others = [p for p in points if p["id"] != start_id]
    others.sort(key=lambda p: distance(start_point, p))

    return [start_point] + others


def renumber_and_update_event_id(ordered_points: list[dict]) -> list[dict]:
    """並び替え済みのpointsに新しいid("pXX")を振り直し、
    eventIdを"ev_<新id>"に更新する。
    """
    width = 2 if len(ordered_points) < 100 else len(str(len(ordered_points)))

    id_mapping = {}  # 旧id -> 新id （確認用ログに利用）

    for i, point in enumerate(ordered_points, start=1):
        old_id = point["id"]
        new_id = f"p{i:0{width}d}"
        id_mapping[old_id] = new_id

        point["id"] = new_id
        point["eventId"] = f"ev_{new_id}"

    return id_mapping


def main():
    with open(SRC_PATH, "r", encoding="UTF-8") as f:
        mapdata = json.load(f)

    points = mapdata["points"]

    ordered_points = reorder_points_by_distance_from_start(points, start_id="p01")
    id_mapping = renumber_and_update_event_id(ordered_points)

    mapdata["points"] = ordered_points
    # routesは別スクリプトでpoints情報のみを元に再生成されるため、ここでは変更しない

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="UTF-8") as f:
        json.dump(mapdata, f, indent=4, ensure_ascii=False)

    print("=== id振り直しマッピング (旧id -> 新id) ===")
    for old_id, new_id in id_mapping.items():
        print(f"{old_id} -> {new_id}")

    print(f"\n更新後のファイルを出力しました: {OUT_PATH}")


if __name__ == "__main__":
    main()
