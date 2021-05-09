from typing import List, Dict
import subprocess


def get_running_uwp_apps() -> List[Dict[str, str]]:
    cmd_output = subprocess.run(
        'tasklist /apps /fo list /fi "status eq running"', capture_output=True
    )
    cmd_output_list = cmd_output.stdout.decode().replace("\r", "").split("\n")
    cmd_output_list = [
        cmd_output_list[i : i + 4] for i in range(1, len(cmd_output_list), 5)
    ]
    cmd_output_list = [
        {
            key: row[i].split(":")[1].strip()
            for i, key in enumerate(["image_name", "pid", "mem_usage", "pkg_name"])
        }
        for row in cmd_output_list
    ]
    return cmd_output_list
