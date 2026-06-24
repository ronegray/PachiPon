"""encryptjson.py
難読化jsonファイルの生成

- zip圧縮後のハッシュ値を先頭に付与したバイナリファイルに変換
- 直接実行時は再帰的にjsonを探して一括実行
"""

# import pyxel as px
from gzip import compress
from pathlib import Path
from hashlib import sha256
from ..base import check_file, read_json, write_bin


def encrypt_json(filename):
    """jsonファイルの難読化／圧縮"""
    path = check_file(filename, "r")
    if not path:
        return

    data = read_json(path)
    compressed = compress(data)
    hash_value = sha256(compressed).digest()
    writepath = check_file(path.with_suffix(".jbn"), "w")
    if not writepath:
        return False
    write_bin(writepath, hash_value + compressed)


# 暗号圧縮
if __name__ == "__main__":
    # px.init(120, 120, title="common")

    dir_path = Path.cwd()
    for json_fullpath in dir_path.rglob("*.json"):
        print(json_fullpath)

    [encrypt_json(json_fullpath) for json_fullpath in dir_path.rglob("*.json")]

    # px.text(0, 0, "encrypt finished. ", px.COLOR_WHITE)
    # px.text(0, 10, "press ESC key", px.COLOR_WHITE)
    # px.show()
    print("encrypt finished. ")
