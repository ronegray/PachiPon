"""file_system.py
ファイル入出力関連

- 形式に応じたファイルの入出力、および対象パスの確認
-- テキスト形式
-- json形式
-- バイナリ形式
"""
from pathlib import Path
from typing import Any
import json


# ファイル存在チェック
def check_file(filepath, chk_mode: str = "r") -> Path | None:
    """ファイル操作前の存在のチェック"""
    # チェックモードの確認
    if chk_mode not in ("r", "w"):
        return None

    # 対象ファイルと親ディレクトリのパスを取得
    path = Path(filepath)
    parent = path.parent

    if chk_mode == "r":  # read時は指定ファイルの有無
        if not path.exists():
            return None
    elif chk_mode == "w":  # write時は出力先の有無
        if not parent.exists():
            return None
        if not parent.is_dir():
            return None

    return path


# テキストファイル
def read_string(filepath: Path) -> list[str]:
    """ファイルを読み込んでデータを返す"""
    with open(filepath, "r", encoding="UTF-8") as f:
        data = f.readlines()
    return data


def write_string(filepath: Path, data: str) -> None:
    """ファイルの書き込み"""
    with open(filepath, "w") as f:
        f.write(data)


# jsonファイル
def read_json(filepath: Path) -> Any:
    """jsonファイルを読み込んでデータを返す"""
    with open(filepath, "r", encoding="UTF-8") as f:
        data = json.load(f)
    return data


def write_json(filepath: Path, data: str | list | tuple | dict) -> None:
    """jsonファイルの書き込み"""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)


# バイナリファイル
def read_bin(filepath: Path) -> bytes:
    """バイナリファイルを読み込んでバイナリデータを返す"""
    with open(filepath, "rb") as f:
        bin_data: bytes = f.read()
    return bin_data


def write_bin(filepath: Path, bin_data: bytes) -> None:
    """バイナリデータのファイル出力"""
    with open(filepath, "wb") as f:
        f.write(bin_data)
