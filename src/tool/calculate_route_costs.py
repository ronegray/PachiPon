import json
import math


def calculate_costs():
    json_path = "../assets/data/map_data.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    points = {p["id"]: (p["x"], p["y"]) for p in data["points"]}
    routes = data["routes"]

    results = []
    results.append("| route_id | from | to | distance (px) |")
    results.append("| --- | --- | --- | --- |")

    for route in routes:
        p1 = points.get(route["from"])
        p2 = points.get(route["to"])
        if p1 and p2:
            tmpdist = math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
            dist = math.ceil(tmpdist / 56)
            results.append(
                f"| {route['id']} | {route['from']} | {route['to']} | {dist} |"
            )
        else:
            results.append(
                f"| {route['id']} | {route['from']} | {route['to']} | Error: Point not found |"
            )

    with open("route_cost.md", "w", encoding="utf-8") as f:
        f.write("\n".join(results))


if __name__ == "__main__":
    calculate_costs()
