"""
アイテム情報管理モジュール
- マスタ定義ファイルの情報を保持
- 指定したID(EffectDef)のアイテム情報を提供
"""

import logging
from gameutils.base import check_file, read_json
from .skill_protocol import SkillID, SkillDef, SkillType, SkillTargetType
from assets.asset_map import AssetID, AssetMap


# ロギング設定
logger = logging.getLogger(__name__)


class SkillRepository:
    _master_def: dict[SkillID, SkillDef]

    def __init__(self) -> None:
        """JSONファイルを読み込んでアイテム定義を初期化する"""
        path_check = AssetMap.get_assetpath(AssetID.DATA_SKILL)
        json_path = check_file(path_check)
        if json_path:
            json_data = read_json(json_path)
        else:
            errmsg = "スキル定義データファイルが見つかりません"
            logger.critical(errmsg, exc_info=True)
            raise FileNotFoundError(errmsg)

        SkillRepository._master_def = {}
        for type_name, efx_data in json_data.items():
            efx_type = SkillType[type_name]

            for efx_name, details in efx_data.items():
                if hasattr(SkillID, efx_name):
                    # def_id = EffectID[item_name].value
                    def_id = SkillID[efx_name]
                    self._master_def[def_id] = SkillDef(
                        def_id=def_id,
                        name=details.get("name", "Unknown"),
                        skill_type=efx_type,
                        target_type=SkillTargetType[details.get("target_type", "NONE")],
                        price=details.get("price", 0),
                        description=details.get("description", ""),
                        dc=details.get("dc", 0),
                        cost=details.get("cost", 0),
                        effect_func=details.get("effect_func"),
                        effect_value=details.get("effect_value", 0.0),
                        is_percent=details.get("is_percent", False),
                    )
                else:
                    print(
                        f"Warning: EffectID.{efx_name} is not defined in EffectID enum."
                    )

    # def get_def(self, def_id: SkillID) -> SkillDef | None:
    #     """指定されたIDのスキル定義を取得する"""
    #     return self._master_def.get(def_id)

    @classmethod
    def get_def(cls, def_id: SkillID) -> SkillDef | None:
        """指定されたIDのスキル定義を取得する"""
        return cls._master_def.get(def_id)

    # def get_all_definitions(self) -> dict[SkillID, SkillDef]:
    #     """すべてのアイテム定義を取得する"""
    #     return self._master_def
