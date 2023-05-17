import click
from click import secho

from monitorctl import app


def _get_profile_or_abort(profile_name: str):
    profile = app.config.find_profile(profile_name)
    if profile is None:
        secho(f"Profile '{profile_name}' not found", fg="red")
        exit(1)
    else:
        return profile


@click.group(name="monitorctl")
@click.option("--config", default="profiles.yml", type=click.Path(exists=True))
def cli(config):
    """
    Monitorctl is a tool to manage bspwm/xrandr monitors profiles
    """
    app.configure(config)


@cli.command()
@click.option("-s", "--show", "show_only", type=click.Choice(["monitors", "profiles", "autoselect"], case_sensitive=False))
def details(show_only):
    """
    Show the current monitors, existing profiles and
    the autoselect profile for the current setup
    """
    if not show_only or show_only == "monitors":
        secho("Current monitors:", fg="blue")
        for mon in app.monitor_status():
            if mon.desktops:
                desktops = " ".join(map(lambda m: m.name, mon.desktops))
            else:
                desktops = "monitor not in bspwm"
            color = "green" if mon.is_connected else "red"
            secho(f" → {mon.name} desktops: {desktops}", fg=color)

    if not show_only or show_only == "profiles":
        secho(f"Profiles list:", fg="blue")
        for profile in app.config.profiles():
            secho(f" → {profile.name}", fg="green")

    if not show_only or show_only == "autoselect":
        secho(f"Auto selected profile based on current status:", fg="blue")
        secho(f" → {app.auto_select_profile()}", fg="green")


@cli.command()
@click.argument('profile_name')
def show(profile_name: str):
    """
    Shows a given profile details
    """
    profile = _get_profile_or_abort(profile_name)
    secho(f"Profile details:", fg="blue")
    secho(profile, fg="green")


@cli.command()
@click.argument('profile_name', required=False)
@click.option('--auto', is_flag=True)
def apply(profile_name: str, auto: bool):
    """
    Applies a profile (if suitable)
    """
    if auto:
        if profile_name:
            secho("Invalid input. Use either 'apply <profile>' or 'apply --auto'")
            exit(1)
        else:
            secho(f"Auto detecting profile", fg="blue")
            profile_name = app.auto_select_profile()

    profile = _get_profile_or_abort(profile_name)
    secho(f"Applying profile '{profile_name}'", fg="blue")
    virtual_mon = app.disable_all_monitors()
    app.configure_profile_monitors(profile, virtual_mon)
    app.notify_profile_loaded(profile_name)
    app.run_profile_loaded_hook()
