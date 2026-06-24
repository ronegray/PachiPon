from dataclasses import dataclass, field
from command import CommandContext
from scene import SITUATION
from . import Character, Enemy  # , Situation,


@dataclass
class EntityContext(CommandContext):
    """Entityの行うCommandに対応するContext"""

    situation: SITUATION
    actor: Character
    allies: list[Character] = field(default_factory=list)
    enemies: list[Enemy] = field(default_factory=list)
