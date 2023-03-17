#!/bin/python3

import argparse
import os
import re
import subprocess
from typing import List, Optional, Set

"""

double.py

Make a "Docker symlink" from all executables in the python-native container in a similar way to the python3 executable.

Like:

docker exec -it python-native python3 $@

"""

SEARCH_DIRS = (
    "/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin".split(
        ":"
    )
)

INTERESTS = {"python", "pip", "conda", "node", "npm", "yarn", "npx"}

REMOTES = (
    "python-native",
    "node-native",
)


def get_remote_path(remote: str) -> List[str]:
    return (
        subprocess.check_output(["docker", "exec", remote, "bash", "-c", "echo $PATH"])
        .decode("utf-8")
        .strip()
        .split(":")
    )


def get_local_path() -> List[str]:
    return os.environ["PATH"].split(":")


def find_cmd(remote: Optional[str] = None) -> List[str]:
    return [
        "find",
        *(get_remote_path(remote) if remote else get_local_path()),
        "-maxdepth",
        "1",
        "-executable",
    ]


def get_remote_executables(remote: str) -> Set[str]:
    # Get the list of executables in the python-native container
    executables: Set[str] = set()
    cmd = ["docker", "exec", remote, *find_cmd(remote)]
    output = subprocess.check_output(cmd).decode("utf-8").strip()
    executables.update(output.split("\n"))

    return executables


def get_local_executables() -> Set[str]:
    # Get the list of executables in the local filesystem
    executables: Set[str] = set()
    output = subprocess.check_output(find_cmd()).decode("utf-8").strip()
    executables.update(output.split("\n"))

    return executables


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    # Ignore interests
    parser.add_argument("--ignore-interests", action="store_true", default=False)
    # Custom interests
    parser.add_argument("-i", "--interest", action="append", default=[])
    # Custom search path
    parser.add_argument("-p", "--path", action="append", default=[])

    # Get args.
    args = parser.parse_args()
    search_dirs = SEARCH_DIRS
    if args.ignore_interests:
        INTERESTS = set()
    if args.interest:
        INTERESTS.update(set(args.interest))
    if args.path:
        search_dirs = args.path

    created = set()
    for remote_container in REMOTES:
        remote = get_remote_executables(remote_container)
        local = get_local_executables()
        diff = list(remote - local)

        # Sort by length.
        diff.sort(key=len)

        # Create the shell scripts in overrides.
        for executable in diff:
            basename = os.path.basename(executable)
            if basename in created or not re.match(f'{"|".join(INTERESTS)}', basename):
                continue
            created.add(basename)

            override_name = os.path.join("/overrides", "bin", basename)
            print(f"Creating {basename} {override_name} ({executable})")
            with open(override_name, "w") as f:
                cwd = os.getcwd()
                f.write(
                    "\n".join(
                        [
                            "#!/bin/bash",
                            f'docker exec -it {remote_container} bash -c "cd {cwd} && {executable} $@"',
                        ]
                    )
                )
            os.chmod(override_name, 0o755)
