"""
エンティティコマンドモジュール
"""

import pyxel as px
from gameutils.lib import Window, WindowAction
from command import CommandBase, CommandPhase, DisplayInfo
from entity import EntityContext
from dice import diceroll


class CommandBaseEntity(CommandBase):
    """エンティティが実行者となるコマンドの基底クラス"""

    def __init__(self, ctx: EntityContext, *args, **kwargs) -> None:
        """初期化：コンテキストの引継"""
        self._ctx: EntityContext = ctx
        self.display_info: DisplayInfo
        self.args = args
        self.kwargs = kwargs
        self.trigger()

    def trigger(self):
        ...


class AttackSpellSingle(CommandBaseEntity):
    def update(self) -> CommandPhase:
        ...

    def draw(self) -> DisplayInfo:
        ...


class RecoverSpellSingle(CommandBaseEntity):
    """単体回復呪文"""

    def trigger(self) -> None:
        self.skill_def = self.args[0]
        self.message_window: Window = Window("basic", 0, 116, 240, 32, "once")
        self.display_info = DisplayInfo(self.message_window)
        # MP残量チェック
        if self._ctx.actor.base_param.mp < self.skill_def.cost:
            self.message_window.set_message(["ＭＰが足りません"])
        else:
            healvalue = diceroll(int(self.skill_def.effect_value))
            self.message_window.set_message([f"ＨＰが{healvalue}回復しました"])
            px.play(3, 63)
        self.phase = CommandPhase.SYN

    def update(self) -> CommandPhase:
        if self.phase == CommandPhase.ACK:
            if self.message_window.update() == WindowAction.DISCARD:
                return CommandPhase.FIN
        else:
            self.phase = CommandPhase.ACK
        return self.phase

    def draw(self) -> DisplayInfo:
        return self.display_info
