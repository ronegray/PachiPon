"""
エネミー情報管理モジュール
- マスタ定義ファイルの情報を保持
- 指定したIDの情報を提供
"""

import logging
from gameutils.base import check_file, read_json
from assets.asset_map import AssetID, AssetMap
from . import GuardType, WeakType, ActionPattern, EnemySize

# ロギング設定
logger = logging.getLogger(__name__)


class EnemyRepository:
    # _master_def: dict[int, list[dict]]
    _master_def: dict
    _threat_group: dict[int, list[str]]

    def __init__(self) -> None:
        """JSONファイルを読み込んでアイテム定義を初期化する"""
        path_check = AssetMap.get_assetpath(AssetID.DATA_ENEMY)
        json_path = check_file(path_check)
        if json_path:
            json_data = read_json(json_path)
        else:
            errmsg = "アイテム定義データファイルが見つかりません"
            logger.critical(errmsg, exc_info=True)
            raise FileNotFoundError(errmsg)

        EnemyRepository._master_def = {}
        EnemyRepository._threat_group = {}
        # for sthreat, data in enumerate(json_data):
        #     threat = int(sthreat)
        #     enemy_list = []
        #     for params in data:
        #         enemy_list.append(
        #             {
        #                 "name": params.get("name", "Unknown"),
        #                 "strength": params.get("strength", 3),
        #                 "arcane": params.get("arcane", 3),
        #                 "endurance": params.get("endurance", 3),
        #                 "speed": params.get("speed", 3),
        #                 "luck": params.get("luck", 3),
        #                 "level": params.get("level", 1),
        #                 "exp": params.get("exp", 3),
        #                 "threat": threat,
        #                 "gold": params.get("gold", 3),
        #                 "bodysize": getattr(EnemySize, params.get("bodysize", "S")),
        #                 "hitdice": params.get("hitdice", 3),
        #                 "defvalue": params.get("defvalue", 3),
        #                 "magpenalty": params.get("magpenalty", 3),
        #                 "guardtype": getattr(GuardType, params.get("guardtype", "NONE")),
        #                 "weaktype": getattr(WeakType, params.get("weaktype", "NONE")),
        #                 "action_pattern": [
        #                     getattr(ActionPattern, str(action).upper())
        #                     for action in params.get("action_pattern", [])
        #                 ],
        #                 "skills": [],
        #             }
        #         )
        #     EnemyRepository._master_def[threat] = enemy_list
        threat_base = 0
        threat_list = []
        for key, params in json_data.items():
            threat = params.get("threat", 0)
            if threat != threat_base:
                EnemyRepository._threat_group[threat_base] = threat_list
                threat_base = threat
                threat_list = []
            EnemyRepository._master_def[key] = {
                "threat": threat,
                "name": params.get("name", "Unknown"),
                "strength": params.get("strength", 3),
                "arcane": params.get("arcane", 3),
                "endurance": params.get("endurance", 3),
                "speed": params.get("speed", 3),
                "luck": params.get("luck", 3),
                "level": params.get("level", 1),
                "exp": params.get("exp", 1),
                "gold": params.get("gold", 0),
                "bodysize": getattr(EnemySize, params.get("bodysize", "S")),
                "hitdice": params.get("hitdice", 1),
                "defvalue": params.get("defvalue", 0),
                "magpenalty": params.get("magpenalty", 0),
                "guardtype": getattr(GuardType, params.get("guardtype", "NONE")),
                "weaktype": getattr(WeakType, params.get("weaktype", "NONE")),
                "action_pattern": [
                    getattr(ActionPattern, str(action).upper())
                    for action in params.get("action_pattern", [])
                ],
                "skills": params.get("skills", []),
            }
            threat_list.append(key)

    def get_enemy(self, enemy_id: str) -> dict:
        """指定されたIDのモンスターデータを取得"""
        if not EnemyRepository._master_def[enemy_id]:
            errmsg = f"指定されたエネミーは定義されていません：ID={enemy_id}"
            logger.critical(errmsg, exc_info=True)
            raise IndexError(errmsg)
        return EnemyRepository._master_def[enemy_id]

    # def get_threat_enemies(self, threat: int) -> list[dict]:
    def get_threat_enemies(self, threat: int) -> list[str]:
        """指定された脅威度のモンスターリストを取得"""
        if not EnemyRepository._threat_group[threat]:
            errmsg = f"指定された脅威度のエネミーは定義されていません：脅威度={threat}"
            logger.critical(errmsg, exc_info=True)
            raise IndexError(errmsg)
        # return EnemyRepository._master_def[threat]
        return EnemyRepository._threat_group[threat]
