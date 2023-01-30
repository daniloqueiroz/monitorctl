from dataclasses import dataclass
from typing import Optional, List

from monitorctl import run


@dataclass
class XRandrOutput:
    name: str
    is_connected: bool
    is_primary: bool = False
    geometry: Optional[str] = None

    def turn_on_output(self, resolution, rotation, relative_position):
        if resolution == "auto":
            params = "--auto"
        else:
            params = f"--mode {resolution}"

        if rotation:
            params += f" --rotate {rotation}"

        if relative_position:
            params += f" --{relative_position.position.name.replace('_', '-')} {relative_position.other_monitor}"

        run(f"xrandr --output {self.name} {params}")
        self.refresh()

    def turn_off_output(self):
        run(f"xrandr --output {self.name} --off")
        self.refresh()

    def refresh(self):
        loaded = XRandrOutput.get_output(self.name)
        self.is_connected = loaded.is_connected
        self.is_primary = loaded.is_primary
        self.geometry = loaded.geometry

    def __str__(self):
        return f"{self.name} " \
               f"{'connected' if self.is_connected else 'disconnected'} " \
               f"{'primary ' if self.is_primary else ''}" \
               f"{self.geometry if self.geometry else ''}"

    @staticmethod
    def list_outputs() -> List["XRandrOutput"]:
        outputs = []
        result = run(f"xrandr -q")
        for line in result:
            if "connected" in line:
                tokens = line.split()
                name = tokens[0]
                is_connected = "disconnected" not in line
                is_primary = "primary" in line
                if is_connected and not tokens[2].startswith("("):
                    geometry = tokens[2] if not is_primary else tokens[3]
                else:
                    geometry = None
                outputs.append(XRandrOutput(
                    name=name,
                    is_connected=is_connected,
                    is_primary=is_primary,
                    geometry=geometry
                ))

        return outputs

    @classmethod
    def get_output(cls, name: str) -> Optional["XRandrOutput"]:
        return next(filter(lambda x: x.name == name, cls.list_outputs()))
