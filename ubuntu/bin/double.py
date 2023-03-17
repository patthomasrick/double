#!/bin/python3

import os
import subprocess
from typing import Set
import re

"""

double.py

Make a "Docker symlink" from all executables in the python-native container in a similar way to the python3 executable.

Like:

docker exec -it python-native python3 $@

"""

CMD_FIND = [
    "find",
    "/usr",
    "/bin",
    "/sbin",
    # "-type",
    # "f",
    "-perm",
    "-u+x",
    "-not",
    "-path",
    "*/lib/*",
]

INTERESTS = {"python*", "pip*", "node", "npm", "yarn", "npx"}

REMOTES = (
    "python-native",
    "node-native",
)


def get_remote_executables(remote: str) -> Set[str]:
    # Get the list of executables in the python-native container
    executables: Set[str] = set()
    cmd = ["docker", "exec", remote, *CMD_FIND]
    output = subprocess.check_output(cmd).decode("utf-8").strip()
    executables.update(output.split("\n"))

    return executables


def get_local_executables() -> Set[str]:
    # Get the list of executables in the local filesystem
    executables: Set[str] = set()
    output = subprocess.check_output(CMD_FIND).decode("utf-8").strip()
    executables.update(output.split("\n"))

    return executables


if __name__ == "__main__":
    for remote_container in REMOTES:
        remote = get_remote_executables(remote_container)
        local = get_local_executables()
        diff = list(remote - local)

        # Sort by length.
        diff.sort(key=len)
        created = set()

        # Create the shell scripts in overrides.
        for executable in diff:
            basename = os.path.basename(executable)
            if basename in created or not re.match(
                f'^{"|".join(INTERESTS)}$', basename
            ):
                continue
            created.add(basename)

            override_name = os.path.join("/overrides", "bin", basename)
            print(f"Creating {override_name} ({executable})")
            with open(override_name, "w") as f:
                f.write(
                    "\n".join(
                        [
                            "#!/bin/bash",
                            f"docker exec -it {remote_container} {executable} $@",
                        ]
                    )
                )
            os.chmod(override_name, 0o755)
