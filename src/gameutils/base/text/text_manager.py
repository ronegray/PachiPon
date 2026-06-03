from dataclasses import dataclass
import pyxel as px

# from ...base import AssetID, AssetManager
from ...libconfig import ResourcePath
from .text_protocol import FONT_SIZE_NAME


@dataclass
class FontData:
    """フォント名とフォントオブジェクトの対応付け"""

    name: FONT_SIZE_NAME  # サイズ名
    font: px.Font | None  # フォントオブジェクト
    height: int = 6  # フォントの高さ


class FontManager:
    """フォント管理クラス"""

    _fontdata: dict[FONT_SIZE_NAME, FontData] = {}

    # def __init__(self):
    @classmethod
    def initialize(cls):
        """フォント情報を設定(BDFフォントの場合はフォントファイルのSIZEを取得)"""
        font_file_name: dict[FONT_SIZE_NAME, str] = {
            "small": "default",
            # # "basic": "umplus_j10r.bdf",
            # # "large": "unifont_jp-17.0.04.bdf",
            # "basic": AssetManager.get_assetpath(AssetID.FONT_BASIC),
            # "large": AssetManager.get_assetpath(AssetID.FONT_LARGE),
            "basic": ResourcePath.FONT_BASIC,
            "large": ResourcePath.FONT_LARGE,
        }
        for size_name, file_name in font_file_name.items():
            # self.fontdata[size_name].name = size_name
            # self.fontdata[size_name].font = px.Font(f"assets/font/{file_name}")
            if size_name == "small":
                cls._fontdata[size_name] = FontData(size_name, None, 4)
                continue

            if file_name.endswith(".bdf"):
                # print(os.getcwd())
                # with open(f"assets/font/{file_name}", mode="r", encoding="utf-8") as f:
                with open(file_name, mode="r", encoding="utf-8") as f:
                    data = f.readline()
                    while data.find("SIZE") == -1:
                        data = f.readline()
                    # self.font_heights[size_name] = int(data.split(" ")[1])
                    # self.fontdata[size_name].height = int(data.split(" ")[1])
                tmpdata = FontData(
                    size_name,
                    # px.Font(f"assets/font/{file_name}"),
                    px.Font(file_name),
                    int(data.split(" ")[1]),
                )
                cls._fontdata[size_name] = tmpdata
            else:
                match size_name:
                    # case "small":
                    #     cls._fontdata[size_name].height = 4
                    case "basic":
                        cls._fontdata[size_name].height = 9
                    case "large":
                        cls._fontdata[size_name].height = 13

    @classmethod
    def get_fontdata(cls, size_name: FONT_SIZE_NAME) -> FontData:
        """フォント"""
        return cls._fontdata[size_name]


# # フォント管理クラスは静的クラスとして初期化
# FontHandler.initialize()


def shadowed_text(
    x: float,
    y: float,
    s: str,
    col: int,
    font: px.Font | None = None,
    shadow_col: int = px.COLOR_BLACK,
) -> None:
    """影付き文字の描画"""
    px.text(x + 1, y + 1, s, shadow_col, font)  # 影文字の描画
    px.text(x, y, s, col, font)  # 影文字の描画
