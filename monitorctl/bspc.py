import json
from dataclasses import dataclass, field
from functools import reduce
from subprocess import CalledProcessError
from typing import Optional, Set

from monitorctl import run


@dataclass
class BspID:
    name: str
    id: Optional[str] = None

    def __str__(self):
        return f"{self.name} ({self.id or 'NoID'})"

    def __hash__(self):
        return self.id.__hash__() if self.id else self.name.__hash__()


@dataclass
class BspMonitor(BspID):
    desktops: Set[BspID] = field(default_factory=list)

    @property
    def exists_in_bspwm(self):
        return self.id is not None

    def add_desktop(self, desktop_name) -> BspID:
        prev_desktops = self.desktops
        run(f"bspc monitor {self.id} --add-desktops {desktop_name}")
        self.refresh()
        diff = self.desktops - prev_desktops
        if 0 > len(diff) > 1:
            raise Exception(f"Unable to add desktop {desktop_name}")
        else:
            return diff.pop()

    def move_desktop_here(self, desktop: BspID):
        run(f"bspc desktop {desktop.id} --to-monitor {self.id}")
        self.refresh()

    def remove_desktop(self, desktop: BspID):
        run(f"bspc desktop {desktop.id} --remove")
        self.refresh()

    def remove(self):
        run(f"bspc monitor {self.id} --remove")
        self.desktops = set()
        self.id = None

    def refresh(self):
        try:
            raw = json.loads(run(f"bspc query --tree --monitor {self.name}")[0])
        except CalledProcessError:
            pass
        else:
            self.id = raw["id"]
            desktops = set()
            for desktop in raw["desktops"]:
                desktop = BspID(desktop["name"], desktop["id"])
                desktops.add(desktop)
            self.desktops = desktops

    def __hash__(self):
        return reduce(lambda x, y: x+y, map(hash, self.desktops))

    @staticmethod
    def load(name: str) -> "BspMonitor":
        mon = BspMonitor(name)
        mon.refresh()
        return mon

    @staticmethod
    def load_all() -> Set["BspMonitor"]:
        result = set()
        monitor_names = run("bspc query --monitors --names")
        for name in monitor_names:
            monitor = BspMonitor(name=name)
            monitor.refresh()
            result.add(monitor)
        return result

    @staticmethod
    def add_monitor(name: str, geometry: str) -> "BspMonitor":
        run(f"bspc wm --add-monitor {name} {geometry}")
        return BspMonitor.load(name)
