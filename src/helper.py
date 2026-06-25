"""
汎用関数モジュール
- ダイスロール実行時の処理定義
- 半角数値の全角化
- 半角数値全角化（幅合わせ版）
"""

import pyxel as px
from const import UPPER_INT_TABLE


def diceroll(dice_num: int) -> int:
    """指定した数d6を振った結果を取得"""
    return px.rndi(dice_num, dice_num * 6)


def upper_int(n: int) -> str:
    """数値を全角数字に変換"""
    return str(n).translate(UPPER_INT_TABLE)


def upper_int_format(n: int, w: int) -> str:
    """数値を全角数字に変換し幅w文字空白埋めにした結果を取得"""
    upper_str = upper_int(n)
    return upper_str if len(upper_str) >= w else ("　" * w + upper_str)[-w:]
