import os


def list_running_uwp_apps() -> str:
    # We filter out all running instances of "RuntimeBroker.exe"
    return (
        "tasklist /apps /fo list /fi 'status eq running' /fi ",
        "'imagename ne RuntimeBroker.exe'",
    )


def get_installed_uwp_apps() -> str:
    return "Get-AppxPackage"


def remove_uwp_app(app_name: str) -> str:
    return f"Get-AppxPackage {app_name} | Remove-AppxPackage"


def register_uwp_app(install_dir: str) -> str:
    return f"Add-AppxPackage -Register {os.path.join(install_dir, 'AppxManifest.xml')}"
