"""asset_map.py
アセットファイルをIDと紐づけて管理する
- 列挙されたアセットIDに対応するファイルの定義
- アセットIDに対応したファイル名の外部提供
"""
from enum import IntEnum, auto
from pathlib import Path


class AssetID(IntEnum):
    PYXRES = auto()
    SYSCONFIG = auto()
    KEYCONFIG = auto()
    IMAGE_CHARA = auto()
    IMAGE_SPLASH = auto()
    IMAGE_TITLE = auto()
    IMAGE_LOGO = auto()
    IMAGE_MAP = auto()
    DATA_LETTER = auto()
    DATA_ITEM = auto()
    DATA_MAP = auto()


class AssetMap:
    """アセットIDとアセットファイルのマッピング"""

    _asset_map: dict[AssetID, str] = {}
    # _app_path: str

    _asset_path: str = ""

    @classmethod
    def _set_assetpath(cls) -> None:
        """アセットパスの定義"""
        asset_dir: str = "assets"
        app_root_path = Path(__file__)
        for parent_path in Path(__file__).resolve().parents:
            if (parent_path / "main.py").exists():
                app_root_path = parent_path
                break
        cls._asset_path = str(app_root_path) + "\\" + asset_dir

    @classmethod
    def initialize_assetmap(cls) -> None:
        """アセットID辞書とアセットファイルのマッピング"""
        # アセットファイルパスの定義
        cls._set_assetpath()
        # アセットファイルの定義
        cls._asset_map[AssetID.PYXRES] = f"{cls._asset_path}/assets.pyxres"
        cls._asset_map[AssetID.SYSCONFIG] = "systemconfig.json"
        cls._asset_map[AssetID.KEYCONFIG] = "keyconfig.json"
        cls._asset_map[AssetID.IMAGE_CHARA] = f"{cls._asset_path}/image/charatest.bmp"
        cls._asset_map[
            AssetID.IMAGE_SPLASH
        ] = f"{cls._asset_path}/image/pyxel_logo_76x32.png"
        cls._asset_map[AssetID.IMAGE_TITLE] = f"{cls._asset_path}/image/title.bmp"
        cls._asset_map[AssetID.IMAGE_LOGO] = f"{cls._asset_path}/image/pp_logo.bmp"
        cls._asset_map[AssetID.IMAGE_MAP] = f"{cls._asset_path}/image/map.png"
        cls._asset_map[AssetID.DATA_LETTER] = f"{cls._asset_path}/data/item_master.json"
        cls._asset_map[AssetID.DATA_ITEM] = f"{cls._asset_path}/data/item_master.json"
        cls._asset_map[AssetID.DATA_MAP] = f"{cls._asset_path}/data/map_data.json"

    @classmethod
    def get_assetpath(cls, asset_id: AssetID) -> str:
        """アセットIDからアセットファイルを取得"""
        result = cls._asset_map.get(asset_id)
        if result is None:
            result = "No assetfile defined."
        # return (cls._asset_path + result)
        return result
