"""script_handler.py
イベントスクリプト制御モジュール

- スクリプト全体をステップ単位にパース
- 次ステップのスクリプトコマンド行を提供
- ラベル名とステップ位置の対応インデックス作成
- ラベル名のステップ位置への移動処理
"""

from .event_protocol import EventControl


class ScriptHandler:
    """
    イベントスクリプトのラッパー。
    カーソルとラベル索引を保持し、行単位で命令を供給する。

    スクリプト書式（1行1命令）:
        # コメント行（先頭 # は無視）
        MOVE 0 -5 0 2       # char_id=0 を左5タイル・速度2で移動
        POPUP msg_001       # ポップアップ表示
        LABEL loop_start    # ジャンプ先ラベル定義
        FLG_CHECK flag_a True loop_start  # フラグ判定→ジャンプ
        GOTO loop_start     # 無条件ジャンプ
    """

    def __init__(self, script_texts: str) -> None:
        # 行単位に分割、コメント・空行を除去
        self._event_scripts = [
            nimonic.strip()
            for nimonic in script_texts.splitlines()
            if nimonic.strip() and not nimonic.strip().startswith("#")
        ]
        # ラベルインデックスの作成
        self._cursor_pos: int = 0
        self._label_index: dict[str, int] = self._build_label_index()

    def _build_label_index(self) -> dict[str, int]:
        """LABEL命令を全行スキャンしてラベル索引を構築する"""
        label_index: dict[str, int] = {}
        for i, commandline in enumerate(self._event_scripts):
            command = commandline.split()
            if command and command[0].lower() == EventControl.LABEL:
                if len(command) < 2:
                    raise SyntaxError(f"LABEL 命令に名前がありません: 行：{i}")
                label_name = command[1]
                if label_name in label_index:
                    raise SyntaxError(f"ラベル名が重複しています: 行：{i}/{label_name}")
                label_index[label_name] = i
        return label_index

    @property
    def is_finished(self) -> bool:
        """スクリプトの終了行まで読んだかどうか"""
        return self._cursor_pos >= len(self._event_scripts)

    def get_next_command(self) -> str | None:
        """カーソル位置を一つ進めて次のスクリプトコマンド行を返す"""
        self._cursor_pos += 1
        if self.is_finished:
            return None
        command_line = self._event_scripts[self._cursor_pos]
        return command_line

    def goto_label(self, label: str) -> None:
        """カーソルを指定ラベルの位置に移動させる"""
        if label not in self._label_index:
            raise KeyError(f"未定義のラベル: '{label}'")
        self._cursor_pos = self._label_index[label]
