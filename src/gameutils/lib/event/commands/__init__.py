"""event/event_commands/__init__.py
コマンドテーブルの構築
命令追加時はここに1行追加
"""
# from app import AppContext
from .command_context import CommandContext
from ..event_protocol import EventControl
from .evt_cmd_base import EventCommand, generator_type_command

# 以下コマンド生成モジュールとその関数を記述
# 描画命令
from .command_image import _make_image as cmd_image
from .command_popup import _make_popup as cmd_popup

# 即時命令
from .command_bgm import _make_command as cmd_bgm


# COMMAND_TABLE: dict[EventControl, EventCommand] = {
#     EventControl.IMAGE: cmd_image,
#     EventControl.BGM: cmd_bgm,
# }


def build_command_table(ctx: CommandContext) -> dict[EventControl, EventCommand]:
    """依存を注入してコマンドテーブルを構築する"""
    command_table = {
        # 描画命令
        EventControl.IMAGE: cmd_image(ctx),
        EventControl.POPUP: cmd_popup(ctx),
        # 即時命令
        EventControl.BGM: cmd_bgm(ctx),
    }
    return command_table
