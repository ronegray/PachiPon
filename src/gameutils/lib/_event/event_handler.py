"""event/event_handler.py
イベント制御モジュール

update サイクル:
    - 待機命令のジェネレータを1ステップ進める
    - 完了したら次の命令へ（即時命令は同フレーム内チェーン実行）
    - コマンドの描画状態は _current_draw / _current_state で管理
draw サイクル:
    - _current_draw を呼ぶだけ（状態変更なし）
"""

# from __future__ import annotations
from typing import Callable, TYPE_CHECKING

# from app import AppContext
from .event_protocol import EventControl
from .script_handler import ScriptHandler

# from .commands import EventCommand, build_command_table
from .commands import build_command_table, generator_type_command

# from ..file import check_file, read_string
# from ..asset import AssetID, AssetManager
from ...libconfig import ResourcePath
from ...base import check_file, read_string  # , AssetID, AssetManager

# from manager import flg
if TYPE_CHECKING:
    from .commands import EventCommand
    # from .wrapper_window import WindowManagerImpl

# # ジェネレータ型エイリアス（戻り値なし）
# _generator_type_command = Generator[None, None, None]

from .commands.command_context import CommandContext, WindowHandler


class EventManager:
    # # _event_scripts: list[str] = [] # 読み込んだイベントスクリプトのコマンドリスト
    # # _label_index: dict[str, int] = {} # ラベル名とコマンドリストの位置対応付け
    # _script: ScriptHandler|None = None # 解析済のイベントスクリプトとラベル位置辞書
    # _current_cmd: _generator_type_command|None = None # 現在の処理対象のイベントコマンド
    # _current_cmd_draw: Callable|None = None # 現在の処理対象のイベントコマンドの描画関数
    # _is_running: bool = False # イベントコマンド実行中（複数フレームで処理するコマンド用）
    # _command_table:dict = {}

    # # _command_stack: list = [] # 複数処理の一括実行用
    # # is_waiting: bool = False # 待機中フラグ
    # # currentstep = None # 処理実行ジェネレータ用

    _ctx: CommandContext  # |None = None
    _command_table: dict[EventControl, EventCommand] = {}
    _script: ScriptHandler | None = None  # 解析済のイベントスクリプトとラベル位置辞書
    _current_cmd: generator_type_command | None = None  # 現在の処理対象のイベントコマンド
    _current_cmd_draw: Callable | None = None  # 現在の処理対象のイベントコマンドの描画関数
    _current_state: dict | None = None
    _is_running: bool = False  # イベントコマンド実行中（複数フレームで処理するコマンド用）
    MAX_INSTANT_CHAIN = 1000  # 無限ループ検出用上限
    _script_path: str

    def __init__(self, ctx: CommandContext) -> None:
        self._ctx = ctx
        self._script_path = ResourcePath.SCRIPT_PATH
        self._command_table = build_command_table(ctx)

        self._init_state()

    def initialize_command_table(self, ctx: CommandContext) -> None:
        self._ctx = ctx
        self._command_table = build_command_table(ctx)

    def _init_state(self) -> None:
        """クラス変数初期化処理"""
        # self._script_path = AssetManager.get_assetpath(AssetID.SCRIPT_PATH)
        # self._script_path = ResourcePath.SCRIPT_PATH
        self._script = None
        self._current_cmd = None
        self._current_cmd_draw = None
        self._current_state = None
        self._is_running = False
        # self._event_scripts = [] # 読み込んだイベントスクリプト
        # self._command_stack = [] # 複数処理の一括実行用
        # self.is_waiting = False # 待機中フラグ
        # self.currentstep = None # 処理実行ジェネレータ用

    def load_event(self, event_id: int, wndmgr: WindowHandler) -> None:
        """イベントスクリプトの読み込みとスクリプトコマンドリストおよびラベルインデックスの作成"""
        self._wndmgr = wndmgr
        # 状態初期化
        self._init_state()
        # スクリプト読み込み
        filename = f"{self._script_path}/evt{event_id}.scr"
        path = check_file(filename)
        if path is None:
            raise FileNotFoundError(f"スクリプトファイルが見つかりません：{filename}")
        script_texts = read_string(path)
        # スクリプト情報をハンドラに渡して整備
        self._script = ScriptHandler(script_texts)

    def update_event(self) -> bool:
        """イベント更新処理"""
        # イベントコマンド実行中はジェネレータを進める
        if self._is_running:
            assert self._current_cmd is not None, "実行コマンドが未定義です"
            try:
                next(self._current_cmd)
            except StopIteration:
                self._is_running = False
                self._current_cmd = None
            return True

        # イベントスクリプトを読み進める（draw不要の単一フレーム処理は連続で実行する）
        assert self._script is not None, "イベントスクリプトハンドラが未定義です"
        chain_count = 0
        while not self._script.is_finished:
            if chain_count > self.MAX_INSTANT_CHAIN:
                raise RuntimeError(f"即時命令チェーンの上限({self.MAX_INSTANT_CHAIN})を越えました")
            chain_count += 1

            next_command_line = self._script.get_next_command()
            if next_command_line is None:
                # 次のコマンドがない＝スクリプト終端に到達時は終了処理
                # self._finish_event()
                break
            else:
                # 命令をパースする
                self._current_cmd = self._parse_command(next_command_line)
                if self._current_cmd is None:
                    # 即時実行命令の場合は続けてスクリプト読み込み
                    continue
                # コマンドが定義された場合は実行中フラグを立てて読み出しフレームで初回実行
                try:
                    self._is_running = True
                    next(self._current_cmd)
                except StopIteration:
                    pass
                return True

        # 全ての処理を抜けた場合は完了
        self._finish_event()
        return False

    def draw_event(self) -> None:
        """イベント描画処理"""
        if self._current_cmd_draw is not None:
            self._current_cmd_draw()

    def _parse_command(self, command_line: str) -> generator_type_command | None:
        """イベント命令を解析して結果を戻す
        - 単一フレーム処理の場合はNone（処理はパース時に即時実行）
        - 複数フレーム処理の場合はコマンドジェネレータ
        """
        parts = command_line.split()
        # if not parts:
        #     return None
        command = (
            parts[0].lower()
        )  # StrEnum.auto()の小文字に合わせる（スクリプト側の書き方に左右うされないメリットもあり
        args = parts[1:]

        # 制御命令の処理
        match command:
            case EventControl.LABEL:
                return None  # ラベルは読み飛ばす

            case EventControl.GOTO:
                self._script.goto_label(args[0])  # type: ignore
                return None

            case EventControl.FLG_CHECK:
                flag_id, value, label = args[0:2]
                if self._ctx.flag.get_flag(flag_id) == (value == "True"):
                    self._script.goto_label(label)  # type: ignore
                return None

        try:
            command_key = EventControl(command)
        except ValueError:
            raise ValueError(f"不明なイベント制御コマンド：{command}")
        # entry: EventCommand|None = COMMAND_TABLE.get(EventControl(command))
        entry = self._command_table.get(command_key)
        assert entry is not None, f"イベント制御コマンドが定義されていません：{command}"

        params: dict = {"wndmgr": self._wndmgr}
        self._current_state = params

        if entry.is_instant:
            entry.runner(*args, params)
            self._current_draw = None
            self._current_state = None
            return None  # 即時命令なのでNoneを返す

        self._current_cmd_draw = lambda: entry.drawer(params) if entry.drawer else None
        return entry.runner(*args, params)

        # match command:
        #     # ---- 即時命令 -------------------------------------------- #
        #     case EventControl.LABEL:
        #         return None  # ラベルは読み飛ばす

        #     case EventControl.GOTO:
        #         self._script.goto_label(args[0])
        #         return None

        #     # case EventControl.FLG_SET:
        #     #     flag_id, value = args[0], args[1]
        #     #     flg.set(flag_id, value == "True")
        #     #     return None

        #     # case EventControl.FLG_CHECK:
        #     #     flag_id, value, label = args[0], args[1], args[2]
        #     #     if flg.get(flag_id) == (value == "True"):
        #     #         self._script.goto(label)
        #     #     return None

        #     case EventControl.BGM:
        #         px.playm(int(args[0]))
        #         return None

        #     case EventControl.SE:
        #         px.play(3, int(args[0]))  # ch=3 を SE 用チャンネルとして使用
        #         return None

        #     # case EventControl.QUIET:
        #     #     px.stop()
        #     #     return None

        #     # case EventControl.DIR:
        #     #     # TODO: キャラクタ方向転換処理を呼ぶ
        #     #     return None

        #     # case EventControl.ITEM:
        #     #     # TODO: アイテム操作処理を呼ぶ
        #     #     return None

        #     # ---- 待機命令 -------------------------------------------- #
        #     case EventControl.IMAGE:
        #         imginfo = {"img": None, "x": 0, "y": 0}
        #         self._current_cmd_draw = lambda: self._draw_image(imginfo)  # draw関数を同時に割り当て
        #         filename = str(args[0])
        #         return self._cmd_image(filename, imginfo)

        #     # case EventControl.MOVE:
        #     #     char_id, dx, dy, speed = int(args[0]), int(args[1]), int(args[2]), int(args[3])
        #     #     return self._cmd_move(char_id, dx, dy, speed)

        #     case EventControl.POPUP:
        #         msginfo = {"msg_id": args[0]}
        #         self._current_cmd_draw = lambda: self._draw_popup(msginfo)
        #         return self._cmd_popup(msg_id)

        #     # case EventControl.FADE:
        #     #     fade_type, target, duration = args[0], int(args[1]), int(args[2])
        #     #     return self._cmd_fade(fade_type, target, duration)

        #     # case EventControl.SHAKE:
        #     #     strength, direction, duration = int(args[0]), args[1], int(args[2])
        #     #     return self._cmd_shake(strength, direction, duration)

        #     # case EventControl.WARP:
        #     #     map_id, x, y = int(args[0]), int(args[1]), int(args[2])
        #     #     return self._cmd_warp(map_id, x, y)

        #     # case EventControl.TALK:
        #     #     char_id, msg_id = int(args[0]), args[1]
        #     #     return self._cmd_talk(char_id, msg_id)

        #     # case EventControl.SELECT:
        #     #     return self._cmd_select(args)

        #     case _:
        #         raise ValueError(f"未知のコマンド: '{command}'")

    # @classmethod
    # def _cmd_image(self, filename:str, imginfo: dict) -> _generator_type_command:
    #     """
    #     画像表示準備・制御コマンド
    #     """
    #     icnt = 0
    #     imginfo["img"] = px.Image.from_image(filename)
    #     imginfo["x"] = (px.width-imginfo["img"].width)//2
    #     imginfo["y"] = (px.height-imginfo["img"].height)//2
    #     while icnt < 120:
    #         yield
    #         icnt += 1
    #     return

    # @classmethod
    # def _draw_image(self, imginfo: dict) -> None:
    #     """
    #     画像表示コマンド
    #     """
    #     if imginfo["img"] is None:
    #         return
    #     px.cls(0)
    #     px.blt(imginfo["x"], imginfo["y"], imginfo["img"],
    #            0,0,imginfo["img"].width,imginfo["img"].height)

    # @classmethod
    # def _cmd_popup(self, msg_id: str) -> _generator_type_command:
    #     """
    #     ポップアップメッセージ表示。
    #     決定キー（Z / RETURN）が押されるまで待機する。
    #     """
    #     self._draw_state["popup"] = {"msg_id": msg_id, "visible": True}
    #     # 決定キー入力を待つ（同フレームの誤検知を防ぐために1フレーム必ず待つ）
    #     yield
    #     while not (pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_RETURN)):
    #         yield
    #     del self._draw_state["popup"]

    # @staticmethod
    # def execute_event():
    #     """イベント処理実行"""
    #     if True:
    #         yield True
    #     return False

    def _finish_event(self) -> None:
        """イベント終了時のリセット処理"""
        self._init_state()
