from collections import namedtuple
from typing import Optional, Generator

import yaml

from monitorctl import run
from monitorctl.bspc import BspMonitor
from monitorctl.profile import Profile, Position, ProfileMonitor, RelativePosition
from monitorctl.xrandr import XRandrOutput

config = None


class Config:
    def __init__(self, raw_config, config_file):
        self._raw_config = raw_config
        self._config_file = config_file

    def on_profile_load_cmd(self) -> Optional[str]:
        return self._raw_config.get("on_profile_load_cmd")

    def find_profile(self, profile_name) -> Optional[Profile]:
        try:
            return next(filter(lambda x: x.name == profile_name, self.profiles()))
        except StopIteration:
            return None

    def profiles(self) -> Generator[Profile, None, None]:
        if "profiles" not in self._raw_config:
            raise KeyError(f"No profiles section defined in {self._config_file}")

        profiles_section = self._raw_config["profiles"]
        for name, raw_monitors in profiles_section.items():
            monitors = []

            for config in raw_monitors:
                data = {}

                if "output" in config:
                    data["output"] = config["output"]
                else:
                    raise KeyError(f"Profile {name} contains an unnamed monitor")

                if "desktops" in config:
                    data["desktops"] = config["desktops"]
                else:
                    raise KeyError(f"Profile {name} contains a monitor with no desktops.")

                if "resolution" in config:
                    data["resolution"] = config["resolution"]

                if "rotation" in config:
                    data["rotation"] = config["rotation"]

                for pos in Position:
                    if pos.name in config:
                        if "position" not in data:
                            data["position"] = RelativePosition(pos, config[pos.name])
                        else:
                            raise KeyError(f"Profile {name} defines a monitor with multiple positions.")

                # Add ProfileMonitor to list of monitors
                monitors.append(ProfileMonitor(**data))

            yield Profile(name, monitors)


def configure(config_file):
    global config
    with open(config_file) as config_yaml:
        raw_config = yaml.safe_load(config_yaml.read())
        config = Config(raw_config, config_file)


MonStatus = namedtuple('MonStatus', ["name", "is_connected", "desktops"])


def monitor_status() -> Generator[MonStatus, None, None]:
    xrandr_status = XRandrOutput.list_outputs()
    bspc_status = {x.name: x for x in BspMonitor.load_all()}
    for x in xrandr_status:
        desktops = bspc_status[x.name].desktops if x.name in bspc_status else None
        yield MonStatus(x.name, x.is_connected, desktops)


def disable_all_monitors() -> BspMonitor:
    """
    To disable all monitors we need to:
    1. Create a virtual monitor in bspwm
    1. Move all desktops to virtual monitor
    2. Remove monitors from BSPWM
    3. Turn off monitors in xrandr

    This function returns the virtual monitor
    """
    # create temporary dummy monitor
    dummy_mon = BspMonitor.add_monitor("DUMMY", "800x600+0+0")

    # move desktops to dummy monitor
    for bspc_mon in BspMonitor.load_all():
        if bspc_mon.id != dummy_mon.id:
            dummy_desktop = bspc_mon.add_desktop("DUMMY")
            for desktop in bspc_mon.desktops:
                if desktop.id is not dummy_desktop.id:
                    dummy_mon.move_desktop_here(desktop)
            bspc_mon.remove()

    # Turn off all outputs
    for output in XRandrOutput.list_outputs():
        output.turn_off_output()
    return dummy_mon


def configure_profile_monitors(profile: Profile, virtual_mon: BspMonitor):
    xrandr_outputs_by_name = dict(
        map(lambda x: (x.name, x), XRandrOutput.list_outputs())
    )
    desktops_by_name = dict(map(lambda x: (x.name, x), virtual_mon.desktops))

    # configure each monitor defined in the profile
    for profile_monitor in profile.monitors:
        # configure xrandr monitor
        output = xrandr_outputs_by_name[profile_monitor.output]
        output.turn_on_output(
            profile_monitor.resolution,
            profile_monitor.rotation,
            profile_monitor.position,
        )

        # configure bspwm monitor
        bsp_monitor = BspMonitor.load(output.name)
        if bsp_monitor.id is None:
            # monitor not present in bspwm
            bsp_monitor = BspMonitor.add_monitor(output.name, output.geometry)

        # move desktops to monitor
        for desktop_name in profile_monitor.desktops:
            if desktop_name in desktops_by_name:
                # desktop already exists, move to monitor
                bsp_monitor.move_desktop_here(desktops_by_name[desktop_name])
            else:
                bsp_monitor.add_desktop(desktop_name)

        # remove any desktop that isn't define in the profile
        for desktop in bsp_monitor.desktops:
            if desktop.name not in profile_monitor.desktops:
                bsp_monitor.remove_desktop(desktop)

    # Remove any monitor that isn't part of the profile
    profile_monitor_names = set(map(lambda m: m.output, profile.monitors))
    for monitor in BspMonitor.load_all():
        if monitor.name not in profile_monitor_names:
            monitor.remove()


def notify_profile_loaded(profile_name: str):
    msg = f"Profile '{profile_name}\' loaded"
    run(["notify-send", "--urgency=normal", "--app-name=monitorctl", msg])


def run_profile_loaded_hook():
    cmd = config.on_profile_load_cmd()
    if cmd:
        run(cmd, disown=True)


def auto_select_profile() -> str:
    selected_profile = None
    monitors_match_count = -1

    connected_monitors = set(
        map(lambda x: x.name, filter(lambda x: x.is_connected, XRandrOutput.list_outputs()))
    )

    for profile in config.profiles():
        matches = 0
        for mon in profile.monitors:
            if mon.output in connected_monitors:
                matches += 1
            else:
                break
        else:
            if matches > monitors_match_count:
                monitors_match_count = matches
                selected_profile = profile.name

    return selected_profile

