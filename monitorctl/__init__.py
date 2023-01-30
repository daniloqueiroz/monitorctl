# SPDX-FileCopyrightText: 2022-present danilo queiroz <dpenna.queiroz@gmail.com>
#
# SPDX-License-Identifier: MIT
import os
import subprocess
from typing import List, Optional


def run(cmd_line, disown=False) -> Optional[List[str]]:
    """
    Runs the given command as a subprocess. The command can be a list
    of strings or a string. If it's a string, it'll be splitted into
    a list of string.

    If `disown is False` (default), this function will wait the
    command to be completed and return it's std output as a list
    of strings/lines.
    If `disown is True` this function will fire and forget the
    given command, running it in a shell and redirecting its std
    and err outputs to `os.devnull`. In this case the return value
    is `None`
    """
    if isinstance(cmd_line, str):
        cmd_line = cmd_line.split()

    if disown:
        with open(os.devnull, 'w') as f:
            subprocess.Popen(cmd_line, shell=True, stdout=f, stderr=f)
    else:
        return subprocess.check_output(cmd_line).decode("utf-8").splitlines()
