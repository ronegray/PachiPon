"""
エネミー情報管理モジュール
- マスタ定義ファイルの情報を保持
- 指定したIDの情報を提供
"""
import logging
from gameutils.base import check_file, read_json
from assets.asset_map import AssetID, AssetMap
from . import GuardType, WeakType, EnemyParam

# ロギング設定
logger = logging.getLogger(__name__)


class EnemyManager:
    _master_def: dict[int, list[EnemyParam]]

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

        EnemyManager._master_def = {}
        for sthreat, data in enumerate(json_data):
            threat = int(sthreat)
            enemy_list = []
            for params in data:
                enemy_list.append(
                    EnemyParam(
                        name=params.get("name", "Unknown"),
                        strength=params.get("strength", 3),
                        arcane=params.get("arcane", 3),
                        endurance=params.get("endurance", 3),
                        speed=params.get("speed", 3),
                        luck=params.get("luck", 3),
                        exp=params.get("exp", 3),
                        threat=threat,
                        gold=params.get("gold", 3),
                        hitdice=params.get("hitdice", 3),
                        defvalue=params.get("defvalue", 3),
                        magpenalty=params.get("magpenalty", 3),
                        guardtype=getattr(GuardType, params.get("guardtype", "NONE")),
                        weaktype=getattr(WeakType, params.get("weaktype", "NONE")),
                    )
                )
            EnemyManager._master_def[threat] = enemy_list

    def get_threat_enemies(self, threat: int) -> list[EnemyParam]:
        """指定された脅威度のモンスターリストを取得"""
        if not EnemyManager._master_def[threat]:
            errmsg = f"指定された脅威度のエネミーは定義されていません：脅威度={threat}"
            logger.critical(errmsg, exc_info=True)
            raise IndexError(errmsg)
        return EnemyManager._master_def[threat]
