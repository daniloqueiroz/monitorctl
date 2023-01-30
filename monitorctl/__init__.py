# SPDX-FileCopyrightText: 2022-present danilo queiroz <dpenna.queiroz@gmail.com>
#
# SPDX-License-Identifier: MIT
import subprocess
from typing import List


def run(cmd_line) -> List[str]:
    if isinstance(cmd_line, str):
        cmd_line = cmd_line.split()
    return subprocess.check_output(cmd_line).decode("utf-8").splitlines()
