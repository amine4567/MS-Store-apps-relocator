from typing import List, Dict
import subprocess
import os
import time
import re
from functools import lru_cache

import psutil


@lru_cache(maxsize=32)
def get_installed_uwp_apps():
    all_installed_uwps = subprocess.run(
        "powershell Get-AppxPackage",
        capture_output=True,
    ).stdout.decode()
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


class UWPAppManifest:
    def __init__(self, pkg_name: str):
        self._manifest_str = subprocess.run(
            f"powershell (Get-AppxPackageManifest -Package {pkg_name}).OuterXml",
            capture_output=True,
        ).stdout.decode()

    def get_name(self) -> str:
        return re.search(r'<Identity Name="(.*?)"', self._manifest_str).group(1)

    def get_logo_location(self) -> str:
        return re.search(r"<Logo>(.*?)</Logo>", self._manifest_str).group(1)


def get_running_uwp_apps() -> List[Dict[str, str]]:
    t1 = time.time()
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

    t2 = time.time()
    print(f"get_running_uwp_apps took {t2-t1} seconds")
    return cmd_output_list
