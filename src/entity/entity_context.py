from dataclasses import dataclass, field
from command import CommandContext
from scene import SITUATION
from . import EntityBase


@dataclass
class EntityContext(CommandContext):
    """Entityの行うCommandに対応するContext"""

    situation: SITUATION
    actor: EntityBase
    target: EntityBase
    allies: list[EntityBase] = field(default_factory=list)
    targets: list[EntityBase] = field(default_factory=list)
