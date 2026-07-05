from dataclasses import dataclass, field
from command import CommandContext
from scene import SITUATION
from . import EntityBase  # Character, Enemy  # , Situation,


@dataclass
class EntityContext(CommandContext):
    """Entityの行うCommandに対応するContext"""

    situation: SITUATION
    actor: EntityBase
    allies: list[EntityBase] = field(default_factory=list)
    targets: list[EntityBase] = field(default_factory=list)
    target_index: int = 0
    #     target_id: int = 0
    # pending_command: type[CommandBase] | None = None
