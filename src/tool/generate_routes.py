import json
import math
import os


def calculate_distance(p1, p2):
    return math.sqrt((p1["x"] - p2["x"]) ** 2 + (p1["y"] - p2["y"]) ** 2)


def calculate_direction(p1, p2):
    # p1 から見た p2 の角度を計算 (ラジアン)
    angle = math.atan2(p2["y"] - p1["y"], p2["x"] - p1["x"])
    degree = math.degrees(angle)

    if -45 <= degree < 45:
        return "right"
    elif 45 <= degree < 135:
        return "down"
    elif degree >= 135 or degree < -135:
        return "left"
    else:  # -135 <= degree < -45
        return "up"


def get_opposite_direction(direction):
    opposites = {"up": "down", "down": "up", "left": "right", "right": "left"}
    return opposites.get(direction)


def generate_routes(data):
    points = data["points"]
    routes = []

    # 各ポイントの各方向スロットが埋まっているかを管理
    # occupied_slots[point_id][direction] = bool
    occupied_slots = {p["id"]: {d: False for d in ["up", "down", "left", "right"]} for p in points}

    # 全ての可能なペアを距離順に並べる
    all_pairs = []
    for i, p1 in enumerate(points):
        for j, p2 in enumerate(points):
            if i >= j:
                continue

            dist = calculate_distance(p1, p2)
            if dist > 115:
                continue
            dir1 = calculate_direction(p1, p2)
            dir2 = calculate_direction(p2, p1)

            all_pairs.append(
                {
                    "p1_id": p1["id"],
                    "p2_id": p2["id"],
                    "dist": dist,
                    "dir1": dir1,
                    "dir2": dir2,
                }
            )

    # 距離の近い順にソート
    all_pairs.sort(key=lambda x: x["dist"])

    route_id_counter = 1
    max_threat = min_threat = 0
    for pair in all_pairs:
        p1_id = pair["p1_id"]
        p2_id = pair["p2_id"]
        dir1 = pair["dir1"]
        dir2 = pair["dir2"]

        # p1のdir1スロットが空いており、かつp2のdir2スロット（逆向き）も空いている場合のみ接続
        if not occupied_slots[p1_id][dir1] and not occupied_slots[p2_id][dir2]:
            # ルートを双方向で作成
            # threat = route_id_counter // 10
            threat = int(p2_id[1:]) // 10  # + route_id_counter//10
            max_threat = max(threat, max_threat)
            min_threat = min(threat, min_threat)

            routes.append(
                {
                    "id": f"r{route_id_counter:03d}",
                    "from": p1_id,
                    "to": p2_id,
                    "cost": 1,
                    "threat": threat,
                    "direction": dir1,
                }
            )
            route_id_counter += 1

            threat = int(p1_id[1:]) // 10  # + route_id_counter//10
            max_threat = max(threat, max_threat)
            min_threat = min(threat, min_threat)

            routes.append(
                {
                    "id": f"r{route_id_counter:03d}",
                    "from": p2_id,
                    "to": p1_id,
                    "cost": 1,
                    "threat": threat,
                    "direction": dir2,
                }
            )
            route_id_counter += 1

            # スロットを埋める
            occupied_slots[p1_id][dir1] = True
            occupied_slots[p2_id][dir2] = True

    print(f"max{max_threat} min{min_threat}")

    return routes


def main():
    path = "../assets/data/map_data.json"
    if not os.path.exists(path):
        print(f"Error: {path} not found.")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(
        f"Cleaning existing routes and re-generating for {len(data['points'])} points with collision avoidance..."
    )
    data["routes"] = generate_routes(data)
    print(f"Generated {len(data['routes'])} routes.")

    # calculate_route_costs.py を実行して route_cost.md を生成
    from calculate_route_costs import calculate_costs

    calculate_costs()

    # route_cost.md からコスト情報を読み込む
    route_costs = {}
    with open("route_cost.md", "r", encoding="utf-8") as f:
        # ヘッダーとセパレーターをスキップ
        next(f)
        next(f)
        for line in f:
            parts = line.strip().split("|")
            if len(parts) >= 5:
                route_id = parts[1].strip()
                cost_str = parts[4].strip()
                try:
                    route_costs[route_id] = (
                        int(float(cost_str)) if "." in cost_str else int(cost_str)
                    )
                except ValueError:
                    print(
                        f"Warning: Could not convert cost '{cost_str}' for route {route_id} to int. Skipping."
                    )

    # map_data.json の routes の cost を更新
    for route in data["routes"]:
        if route["id"] in route_costs:
            route["cost"] = route_costs[route["id"]]
        else:
            print(
                f"Warning: Cost for route {route['id']} not found in route_cost.md. Keeping default cost."
            )

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print("Successfully updated map_data.json")


if __name__ == "__main__":
    main()
