"""command_context.py
イベントコマンドの依存コンテナ関連
- イベントコマンドのプロトコル定義
-
"""

from dataclasses import dataclass
from typing import Protocol


class WindowHandler(Protocol):
    def generate_window(self) -> None:
        ...

    def popup_message(self, msg_id: str) -> None:
        ...

    # def popup_menu(self, menu_id: str) -> None: ...
    def has_stack(self) -> None:
        ...


class SoundHandler(Protocol):
    def play_bgm(self, bgm_id: int) -> None:
        ...

    # def stop_bgm(self) -> None: ...
    # def fadein_bgm(self) -> None: ...
    # def fadeout_bgm(self) -> None: ...
    def play_se(self) -> None:
        ...

    # def stop_se(self) -> None: ...


class CharacterHandler(Protocol):
    def move_character(self, char_id: int, char_dir: int, move_x: int, move_y: int) -> None:
        ...

    def face_character(self, char_id: int, char_dir: int) -> None:
        ...

    def talk_character(self, char_id: int, char_dir: int) -> None:
        ...


class ItemHandler(Protocol):
    def get_item(self, item_id: str, value: int) -> None:
        ...

    def lost_item(self, item_id: str, value: int) -> None:
        ...


class FlagHandler(Protocol):
    def set_flag(self, flag_id: str, value: bool) -> None:
        ...

    def get_flag(self, flag_id: str) -> bool:
        ...


@dataclass
class CommandContext:
    """イベントコマンドが必要とする外部依存の定義
    - ウインドウ操作
      - POPUP = auto() # ポップアップメッセージ（メッセージID）
    - Pyxel標準機能
      - IMAGE = auto() # 画像描画（画像ファイル名）
      - WARP = auto() # 場面転換（移動先タイルマップID、出現位置X,Y）
      - FADE = auto() # 画面フェードインアウト（フェードタイプ（イン、アウト）、フェード値、フェード時間）
      - SHAKE = auto() # 画面揺れ（揺れの大きさ、揺れの方向（縦、横、ランダム）揺れ時間）
    - 音声操作
      - BGM = auto() # BGM再生開始（BGMID）
      - SE = auto() # SE再生開始（SEID）
      - QUIET = auto() # 音声再生全停止
    - キャラ操作
      - MOVE = auto() # キャラクタの移動（対象キャラID、移動先座標X,Y、移動速度）
      - DIR = auto() # キャラクタの方向転換（対象キャラID、方向）
      - TALK = auto() # キャラクタの発言（対象キャラID、メッセージID）
    - アイテム操作
      - ITEM = auto() # アイテムの操作（アイテムID、操作（追加increase、減少decrease））
    - フラグ操作
      - FLG_SET = auto() # フラグの設定（フラグID、設定値（True、False））
      - FLG_CHECK = auto() # フラグの判定とジャンプ（フラグID、判定値（True、False）、ラベル名）
    - 依存なし
      - SELECT = auto() # 選択肢（[選択肢１，選択肢１の結果実行する処理]...非制限数リスト）
      - GOTO = auto() # 指定ラベルの処理までジャンプする（ラベル名）
      - LABEL = auto() # GOTO、FLG_CHECKでのジャンプ先を示す（ラベル名）
    """

    window: WindowHandler
    sound: SoundHandler
    # character: CharacterHandler
    # item: ItemHandler
    # flag: FlagHandler
