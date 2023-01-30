# About
**Monitorctl** is the missing piece for switching monitor configurations
for [bspwm](https://github.com/baskerville/bspwm).

Monitorctl allows you to define profiles with different outputs, define the `xrandr`
config for each output, as well what `bspwm` desktops should be assigned to each output.
It also allows you to run a custom script whenever a profile is applied.

# How it works
When switching profiles, `monitorctl` will create a new `bspwm` virtual desktop,
move the existing desktops to the virtual desktop, remove the existing monitors from
`bpswm`, turn off the `xrandr` outputs and then reconfigure all outputs defines on the
profile. As the desktops aren't modified, it will keep all the windows on the same
desktops as before.

# Usage
The easiest way to get start is by defining your profiles and then run
`monitorctl --config <path to profiles.yml> apply-auto` to auto-detect 
a profile and apply it.
For other options, use `monitorctl --help`.

## Example config 
```yaml
# execute the command below when a profile is loaded
# optional field
on_profile_load_cmd: launch_polybar.sh

profiles:
  # profiles entries format
  # <profile name>:
  # - output: <output name> # mandatory
  #   desktop: <list of desktops> # mandatory
  #   resolution: <resolution or 'auto'> # optional, default: auto
  #   rotation: <normal, left or right> # optional, default: normal
  #   <one of: left_of, right_of, above, below>: <output name> # optional, default: None
  single:
    - output: HDMI1
      desktops: [1, 2, 3, 4, 5, 6, 6, 7, 0]
      resolution: 3440x1440
  dual:
    - output: HDMI1
      desktops: [5, 6, 7, 8, 9, 0]
      resolution: 3440x1440
    - output: HDMI2
      desktops: [1, 2, 3, 4]
      resolution: auto
      left_of: HDMI1
      rotation: left
```