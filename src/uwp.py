import os
import re
import subprocess
from functools import lru_cache
from typing import Callable, Dict, List

import psutil

import cmds


def run_powershell_cmd(cmd: Callable[..., str], **kwargs) -> str:
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE

    output = subprocess.run(
        f"powershell {cmd(**kwargs)}",
        capture_output=True,
        startupinfo=startupinfo,
    ).stdout.decode()

    return output


@lru_cache(maxsize=32)
def get_installed_uwp_apps():
    all_installed_uwps = run_powershell_cmd(cmds.get_installed_uwp_apps)
    all_installed_uwps = re.sub("\\r\\n +", " ", all_installed_uwps)

    all_uwps_data = [
        dict(
            [
                list(map(lambda x: x.strip(), elt.split(":", maxsplit=1)))
                for elt in uwp_data.split("\r\n")
            ]
        )
        for uwp_data in all_installed_uwps.strip().split("\r\n\r\n")
    ]

    all_uwps_data_dict = {elt["PackageFullName"]: elt for elt in all_uwps_data}
    return all_uwps_data_dict


def get_running_uwp_apps() -> List[Dict[str, str]]:
    cmd_output = run_powershell_cmd(cmds.list_running_uwp_apps)
    cmd_output_list = cmd_output.replace("\r", "").split("\n")
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

    all_installed_uwp_apps = get_installed_uwp_apps()

    # Get additional data about the running uwp apps
    for uwp_data in cmd_output_list:
        pid = int(uwp_data["pid"])
        proc = psutil.Process(pid)

        installed_uwp_data = all_installed_uwp_apps[uwp_data["pkg_name"]]
        app_name = installed_uwp_data["Name"]

        install_location = installed_uwp_data["InstallLocation"]

        with open(os.path.join(install_location, "AppxManifest.xml"), "r") as f:
            manifest = f.read()
            logo_relative_path = re.search(r"<Logo>(.*?)</Logo>", manifest).group(1)

        uwp_data["executable_path"] = proc.exe()
        uwp_data["app_name"] = app_name
        uwp_data["install_location"] = install_location
        uwp_data["logo_relative_path"] = logo_relative_path

        logos_dir, logo_pattern_name = logo_relative_path.rsplit("\\", maxsplit=1)
        logo_filename = [
            filename
            for filename in os.listdir(os.path.join(install_location, logos_dir))
            if filename.startswith(logo_pattern_name.split(".")[0])
        ][0]
        uwp_data["logo_fullpath"] = os.path.join(
            install_location, logos_dir, logo_filename
        )

    return cmd_output_list
