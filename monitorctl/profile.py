from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional


class Position(Enum):
    right_of = auto()
    left_of = auto()
    above = auto()
    below = auto()


@dataclass
class RelativePosition:
    position: Position
    other_monitor: str

    def __str__(self):
        return f"{self.position.name} {self.other_monitor}"


@dataclass
class ProfileMonitor:
    output: str
    desktops: List[str]
    resolution: str = auto
    rotation: str = "normal"
    position: Optional[RelativePosition] = None

    def __post_init__(self):
        # make sure all desktops are treated as strings
        self.desktops = list(map(str, self.desktops))

    def __str__(self):
        return f"""
  - {self.output}: {self.rotation} {self.resolution} {self.position if self.position is not None else ""}
    bspwm desktops: {" ".join(self.desktops)}"""


@dataclass
class Profile:
    name: str
    monitors: List[ProfileMonitor]

    def __str__(self):
        monitors = "".join(map(lambda x: str(x), self.monitors))
        return f"{self.name}:{monitors}"
