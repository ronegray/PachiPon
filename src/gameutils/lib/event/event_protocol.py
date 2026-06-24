"""event_protocol.py
イベント処理定義スクリプトとのインタフェース

- イベント処理に対応する指定パラメータを管理
"""

from enum import IntEnum, StrEnum, auto
# from typing import Literal


# WINDOW_MODE = Literal["once", "wait", "page", "menu"]
# FONT_SIZE_NAME = Literal["small", "basic", "large"]
# MENU_WINDOW_TYPE = Literal["main", "sub"]


class EventControl(StrEnum):
    """イベントで実行する処理を示すリスト"""

    # フレーム待機系コマンド
    POPUP = auto()  # ポップアップメッセージ（メッセージID）
    # WindowManager.push_stack, WindowManager.draw, Window.add_message
    IMAGE = auto()  # 画像描画（画像ファイル名）
    # pyxel.blt, pyxel.dither
    WARP = auto()  # 場面転換（移動先タイルマップID、出現位置X,Y）
    # pyxel.bltm, pyxel.dither, Character.move
    FADE = auto()  # 画面フェードインアウト（フェードタイプ（イン、アウト）、フェード値、フェード時間）
    # pyxel.dither, pyxel.frame_count,
    SHAKE = auto()  # 画面揺れ（揺れの大きさ、揺れの方向（縦、横、ランダム）揺れ時間）
    # pyxel.camera, pyxel.cls
    MOVE = auto()  # キャラクタの移動（対象キャラID、移動先座標X,Y、移動速度）
    # Character.move, Character.direction
    DIR = auto()  # キャラクタの方向転換（対象キャラID、方向）
    # Character.direction
    TALK = auto()  # キャラクタの発言（対象キャラID、メッセージID）
    #
    # 連続実行系コマンド
    BGM = auto()  # BGM再生開始（BGMID）
    SE = auto()  # SE再生開始（SEID）
    QUIET = auto()  # 音声再生全停止
    ITEM = auto()  # アイテムの操作（アイテムID、操作（追加increase、減少decrease））
    FLG_SET = auto()  # フラグの設定（フラグID、設定値（True、False））
    FLG_CHECK = (
        auto()
    )  # フラグの判定とジャンプ（フラグID、判定値（True、False）、ラベル名）
    SELECT = auto()  # 選択肢（[選択肢１，選択肢１の結果実行する処理]...非制限数リスト）
    GOTO = auto()  # 指定ラベルの処理までジャンプする（ラベル名）
    LABEL = auto()  # GOTO、FLG_CHECKでのジャンプ先を示す（ラベル名）
    # ※スクリプトの先頭にLABEL BEGIN、スクリプト末尾はLABEL ENDを記述するのがルール


class EventID(IntEnum):
    """イベントのID"""

    OPENING = auto()
