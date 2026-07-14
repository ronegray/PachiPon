from dataclasses import dataclass, field

# from typing import Callable, TYPE_CHECKING
from command import CommandContext
from scene import SITUATION

from . import EntityBase  # Character, Enemy  # , Situation,

# if TYPE_CHECKING:
#     from command.entity_command import CommandBaseEntity


@dataclass
class EntityContext(CommandContext):
    """Entityの行うCommandに対応するContext"""

    # situation: SITUATION
    # actor: EntityBase
    # allies: list[EntityBase] = field(default_factory=list)
    # targets: list[EntityBase] = field(default_factory=list)
    # target_index: int = 0
    situation: SITUATION
    actor: EntityBase
    target: EntityBase
    allies: list[EntityBase] = field(default_factory=list)
    targets: list[EntityBase] = field(default_factory=list)
    # pending_command: Callable[..., CommandBase] | None = None


# @dataclass
# class CommandPackage:
#     """Command選択結果のメニュー⇔シーン間受け渡し用パッケージ"""
#     selected_action: type[CommandBase] | None = None
#     selected_skill: SkillDef | None = None
#     target_type: TargetType | None = None
