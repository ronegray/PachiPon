"""command_save.py

SystemCommand系の具象例。実行者(Entity)を持たず、対象（セーブ先）のみを持つ
Contextの形を示す。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from command._command_protocol import CommandState, DisplayInfo, Phase, wait_for_confirm


class SaveTarget(Protocol):
    """セーブ先を表す最小の契約。実プロジェクトではセーブデータを
    json/pickle等でファイルへ書き出すクラスがこれを満たす。
    """

    def write(self) -> None:
        ...


@dataclass(frozen=True, slots=True)
class SystemContext:
    """実行者を持たないContext。対象（システムリソース）のみを運ぶ。"""

    target: SaveTarget


class CommandSave:
    """セーブコマンド（System系）。"""

    def __init__(self, ctx: SystemContext) -> None:
        self._ctx = ctx
        self._state = CommandState(phase=Phase.PENDING)

    # --- CommandSystemProtocol の要求 ---------------------------------------
    @property
    def target(self) -> SaveTarget:
        return self._ctx.target

    # --- CommandProtocol の要求 ---------------------------------------------
    def update(self) -> CommandState:
        if self._state.phase is Phase.PENDING:
            self._apply_effect()
            self._state.phase = Phase.AWAITING_ACK
        elif self._state.phase is Phase.AWAITING_ACK:
            if wait_for_confirm():
                self._state.phase = Phase.DONE

        return self._state

    def draw(self) -> DisplayInfo | None:
        return self._state.display_info

    # --- 内部処理 -------------------------------------------------------
    def _apply_effect(self) -> None:
        """初回updateでのみ呼ばれる。旧コードでMenuYesNoが`exec()`を
        個別に呼んでいた処理は、ここに統合されている。
        CommandCastSpellと全く同じ『初回updateで実処理→確認待ちへ』
        という形を取っており、CommandManager側からは区別がつかない。
        """
        self._ctx.target.write()
        self._state.display_info = DisplayInfo(message="セーブしました")
