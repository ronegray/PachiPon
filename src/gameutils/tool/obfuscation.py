"""obfuscation.py
画像・json等データファイルの難読化及び復元

- bmp画像、jsonファイルを読み込んで難読化バイナリファイルに変換して保存
  - zip圧縮後のハッシュ値を先頭に付与したバイナリファイルに変換
  - bmp画像の場合、pyxel.Imageオブジェクトに復帰させる為画像サイズを埋め込み
- 変換したファイルの読み出しと復元
- jsonファイルの一括変換
"""
from pathlib import Path
from hashlib import sha256
from gzip import compress, decompress
from struct import pack, unpack
from pyxel import Image
from ..base import check_file, read_json, read_bin, write_bin


def _data_writer(data: bytes, filepath: Path, suffix_name: str = ".bin") -> bool:
    """元データにハッシュ値を付与した難読化データ生成と書き込み"""
    compressed = compress(data)
    hash_value = sha256(compressed).digest()

    writepath = check_file(filepath.with_suffix(suffix_name), "w")
    if not writepath:
        return False

    write_bin(writepath, hash_value + compressed)
    return True


def convert_json(filename: str | Path) -> bool:
    """jsonファイルにハッシュを付けてgzip保存する"""
    filepath = check_file(filename, "r")
    if not filepath:
        return False

    data = read_json(filepath)
    return _data_writer(data, filepath, ".jcd")  # json converted data
    # compressed = compress(data)
    # hash_value = sha256(compressed).digest()
    # writepath = check_file(path.with_suffix(".jbn"), "w")
    # if not writepath:
    #     return False
    # write_bin(writepath, hash_value + compressed)


def convert_bmp(filename: str | Path) -> bool:
    """指定された画像ファイルに画像サイズとハッシュを付けてgzip保存する"""
    # ファイル存在チェック
    filepath = check_file(filename, "r")
    if not filepath:
        return False

    # 1. いったん普通にBMPを読み込む
    img = Image.from_image(str(filename))
    # 2. Pyxelのメモリから「純粋なピクセルデータ」をbytesとして取り出す
    pixel_data = img.data_ptr()
    raw_pixel_data = bytes(pixel_data)
    # 3. 展開時に利用する画像サイズ情報を付与してピクセルデータを圧縮する
    "※※※!HHに<（エンディアン指定）が必要ではないか！？"
    sizeheader = pack("!HH", img.width, img.height)
    # compressed = compress(sizeheader + raw_pixel_data)
    # # 4. ハッシュ計算
    # hash_value = sha256(compressed).digest()
    # # 5. データファイルの出力
    # writepath = check_file(filepath.with_suffix(".bdt"), "w")
    # if not writepath:
    #     return False
    # write_bin(writepath, hash_value + compressed)

    # return True
    return _data_writer(
        sizeheader + raw_pixel_data, filepath, ".bcd"
    )  # bmp converted data


def _data_reader(filepath: Path):
    """難読化データを読み込みハッシュ値チェックして元データを返却"""
    # データファイル読込
    bin_data = read_bin(filepath)
    # ハッシュデータと分離
    hash_value = bin_data[:32]  # SHA-256ハッシュ（32バイト）
    compressed = bin_data[32:]
    # ハッシュチェック
    if sha256(compressed).digest() != hash_value:  # ハッシュ不一致
        return None

    # 復元処理
    return decompress(compressed)


# def load_dat_bmp(filename: str) -> Image | None:
def restore_bmp(filename: str | Path) -> Image | None:
    """変換済ビットマップファイルを読み込んでImageオブジェクトを生成"""
    # ファイル存在チェック
    filepath = check_file(filename, "r")
    if not filepath:
        return None

    # # データファイル読込
    # bin_data = read_bin(filepath)
    # # ハッシュデータと分離
    # hash_value = bin_data[:32]  # SHA-256ハッシュ（32バイト）
    # compressed = bin_data[32:]
    # # ハッシュチェック
    # if sha256(compressed).digest() != hash_value:  # ハッシュ一致
    #     return None

    # # 復元処理
    # decompressed = decompress(compressed)
    decompressed = _data_reader(filepath)
    if decompressed is None:
        return None
    sizeheader = decompressed[:4]
    raw_pixel_data = decompressed[4:]
    img_width, img_height = unpack("!HH", sizeheader)

    pixel_image = Image(img_width, img_height)
    pixel_data = pixel_image.data_ptr()
    pixel_data[:] = raw_pixel_data

    return pixel_image


def restore_json(filename: str | Path):
    """変換済ビットマップファイルを読み込んでjsonオブジェクトを生成"""
    # ファイル存在チェック
    filepath = check_file(filename, "r")
    if not filepath:
        return None
    return _data_reader(filepath)


# 暗号圧縮
if __name__ == "__main__":
    # px.init(120, 120, title="common")

    dir_path = Path.cwd()
    for json_fullpath in dir_path.rglob("*.json"):
        print(json_fullpath)

    [convert_json(json_fullpath) for json_fullpath in dir_path.rglob("*.json")]

    # px.text(0, 0, "encrypt finished. ", px.COLOR_WHITE)
    # px.text(0, 10, "press ESC key", px.COLOR_WHITE)
    # px.show()
    print("encrypt finished. ")
