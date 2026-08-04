"""
汎用関数モジュール
- ダイスロール実行時の処理定義
- 半角数値の全角化
- 半角数値全角化（幅合わせ版）
"""

import pyxel as px
import unicodedata

UPPER_INT_TABLE = str.maketrans("0123456789", "０１２３４５６７８９")


# def diceroll(dice_num: int) -> int:
#     """指定した数d6を振った結果を取得"""
#     return px.rndi(dice_num, dice_num * 6)


def diceroll(dice_num: int) -> int:
    """指定した数d6を振った結果を取得"""
    return sum(diceroll_values(dice_num))


def diceroll_values(n: int) -> list[int]:
    """nd6 の個々の出目をリストで返す"""
    return [px.rndi(1, 6) for _ in range(n)]


def upper_int(n: int) -> str:
    """数値を全角数字に変換"""
    return str(n).translate(UPPER_INT_TABLE)


def upper_int_format(n: int, w: int) -> str:
    """数値を全角数字に変換し幅w文字空白埋めにした結果を取得"""
    upper_str = upper_int(n)
    return upper_str if len(upper_str) >= w else ("　" * w + upper_str)[-w:]


def format_leftright(left_str: str, right_str: str, str_len: int = 20) -> str:
    """半角スペース数str_lenの範囲で左右文字列を端に詰めた文字列を生成"""

    def calcwidth(text: str) -> int:
        width = 0
        for char in text:
            if unicodedata.east_asian_width(char) in ("F", "W", "A"):
                width += 2
            else:
                width += 1
        return width

    len_lstr = calcwidth(left_str)
    len_rstr = calcwidth(right_str)
    len_padding = str_len - (len_lstr + len_rstr)
    return f"{left_str}{' ' * len_padding}{right_str}"
