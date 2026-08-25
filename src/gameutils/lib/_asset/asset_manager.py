"""asset_manager.py
アセットファイルをIDと紐づけて管理する
- 列挙されたアセットIDに対応するファイルの定義
- アセットIDに対応したファイル名の外部提供
"""

from .asset_map import AssetID, ASSETS_PATH


class AssetManager:
    """アセットIDとアセットファイルのマッピング"""

    _asset_map: dict[AssetID, str] = {}
    _app_path: str

    @classmethod
    def get_rootpath(cls, app_path: str) -> None:
        """アプリケーションベースパスの保持"""
        cls._app_path = app_path + "/"

    @classmethod
    def initialize_assetmap(cls) -> None:
        """アセットID辞書とアセットファイルのマッピング"""
        cls._asset_map[AssetID.PYXRES] = f"{ASSETS_PATH}/assets.pyxres"
        # cls._asset_map[AssetID.WINDOW_CHIP] = "gameutils/lib/window/chip_window.bmp"
        # cls._asset_map[AssetID.FONT_BASIC] = f"{ASSETS_PATH}/font/umplus_j10r.bdf"
        # cls._asset_map[AssetID.FONT_LARGE] = f"{ASSETS_PATH}/font/unifont_jp-17.0.04.bdf"
        # cls._asset_map[AssetID.SCRIPT_PATH] = f"{ASSETS_PATH}/script/"
        cls._asset_map[AssetID.IMAGE_CHARA] = f"{ASSETS_PATH}/image/charatest.bmp"
        cls._asset_map[AssetID.IMAGE_SPLASH] = f"{ASSETS_PATH}/image/pyxel_logo_152x64.png"
        cls._asset_map[AssetID.IMAGE_TITLE] = f"{ASSETS_PATH}/image/title.bmp"
        cls._asset_map[AssetID.IMAGE_MAP] = f"{ASSETS_PATH}/image/map.png"
        cls._asset_map[AssetID.DATA_ITEM] = f"{ASSETS_PATH}/data/item_master.json"

    @classmethod
    def get_assetpath(cls, asset_id: AssetID) -> str:
        """アセットIDからアセットファイルを取得"""
        result = cls._asset_map.get(asset_id)
        if result is None:
            result = "No assetfile defined."
        return cls._app_path + result


# AssetManager.initialize_assetmap()
