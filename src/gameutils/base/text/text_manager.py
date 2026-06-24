"""
テキスト処理管理マネージャ

- 指定フォントサイズに対応するフォントファイルの定義
- 影付きテキスト描画関数
"""

from dataclasses import dataclass
import pyxel as px
from ...libconfig import ResourcePath
from . import FONT_SIZE_NAME


@dataclass
class FontData:
    """フォント名とフォントオブジェクトの対応付け"""

    name: FONT_SIZE_NAME  # サイズ名
    font: px.Font | None  # フォントオブジェクト
    height: int = 6  # フォントの高さ


class FontManager:
    """フォント管理クラス"""

    _fontdata: dict[FONT_SIZE_NAME, FontData] = {}

    @classmethod
    def initialize(cls):
        """フォント情報を設定(BDFフォントの場合はフォントファイルのSIZEを取得)"""
        font_file_name: dict[FONT_SIZE_NAME, str] = {
            "small": "default",
            "basic": ResourcePath.FONT_BASIC,
            "large": ResourcePath.FONT_LARGE,
        }
        for size_name, file_name in font_file_name.items():
            if size_name == "small":
                cls._fontdata[size_name] = FontData(size_name, None, 4)
                continue

            if file_name.endswith(".bdf"):
                with open(file_name, mode="r", encoding="utf-8") as f:
                    data = f.readline()
                    while data.find("SIZE") == -1:
                        data = f.readline()
                tmpdata = FontData(
                    size_name,
                    px.Font(file_name),
                    int(data.split(" ")[1]),
                )
                cls._fontdata[size_name] = tmpdata
            else:
                match size_name:
                    case "basic":
                        cls._fontdata[size_name].height = 9
                    case "large":
                        cls._fontdata[size_name].height = 13

    @classmethod
    def get_fontdata(cls, size_name: FONT_SIZE_NAME) -> FontData:
        """フォント"""
        return cls._fontdata[size_name]


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
