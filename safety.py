import ctypes
import subprocess


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def create_restore_point() -> tuple[bool, str]:
    """
    Intenta crear un punto de restauración antes de modificar drivers.
    """

    command = r"""
try {
    Checkpoint-Computer `
        -Description "DriverUpdater - Antes de actualizar drivers" `
        -RestorePointType "MODIFY_SETTINGS" `
        -ErrorAction Stop

    Write-Output "OK"
}
catch {
    Write-Output ("ERROR: " + $_.Exception.Message)
    exit 1
}
"""

    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
            startupinfo=startupinfo,
        )

        output = result.stdout.strip()

        if result.returncode == 0 and output == "OK":
            return True, "Punto de restauración creado correctamente."

        error = output or result.stderr.strip()

        return False, (
            "No se pudo crear el punto de restauración: "
            + error
        )

    except Exception as error:
        return False, str(error)