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
def status():
    """
    Show the current monitors and desktops
    """
    secho("Current monitors:", fg="blue")
    for mon in app.monitor_status():
        if mon.desktops:
            desktops = " ".join(map(lambda m: m.name, mon.desktops))
        else:
            desktops = "monitor not in bspwm"
        color = "green" if mon.is_connected else "red"
        secho(f" → {mon.name} desktops: {desktops}", fg=color)


@cli.command()
def list_profiles():
    """
    List the available profiles
    """
    secho(f"Profiles list:", fg="blue")
    for profile in app.config.profiles():
        secho(f" → {profile.name}", fg="green")
    secho(f"Auto selected profile based on current status: {app.auto_select_profile()}", fg="blue")


@cli.command()
@click.argument('profile_name')
def show_profile(profile_name: str):
    """
    Shows a given profile details
    """
    profile = _get_profile_or_abort(profile_name)
    secho(f"Profile details:", fg="blue")
    secho(profile, fg="green")


@cli.command()
@click.argument('profile_name')
def apply_profile(profile_name: str):
    """
    Applies a profile (if suitable)
    """
    # find profile
    profile = _get_profile_or_abort(profile_name)
    secho(f"Applying profile '{profile_name}'", fg="blue")

    virtual_mon = app.disable_all_monitors()
    app.configure_profile_monitors(profile, virtual_mon)
    app.notify_profile_loaded(profile_name)
    app.run_profile_loaded_hook()


@cli.command()
@click.pass_context
def apply_auto(ctx):
    """
    Auto-detect best profile to use and apply it
    """
    secho(f"Auto detecting profile", fg="blue")
    ctx.invoke(apply_profile, profile_name=app.auto_select_profile())
