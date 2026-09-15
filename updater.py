

import json
import subprocess
import time

from scanner import get_device_by_instance_id, normalize_version


def run_powershell(command: str) -> str:
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
            command,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        creationflags=subprocess.CREATE_NO_WINDOW,
        startupinfo=startupinfo,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
            or "PowerShell devolvió un error."
        )

    return result.stdout.strip()


def parse_json(output):
    if not output:
        return None

    return json.loads(output)


def search_update(update_id):
    if not update_id:
        raise ValueError(
            "UpdateID no válido."
        )

    safe_id = update_id.replace(
        "'",
        "''"
    )

    command = """
$ErrorActionPreference = 'Stop'

$session = New-Object -ComObject Microsoft.Update.Session
$searcher = $session.CreateUpdateSearcher()

$result = $searcher.Search(
    "IsInstalled=0 and IsHidden=0 and Type='Driver'"
)

foreach ($update in $result.Updates) {

    if ($update.Identity.UpdateID -eq '__UPDATE_ID__') {

        [PSCustomObject]@{
            Title = $update.Title
            UpdateID = $update.Identity.UpdateID
            DriverManufacturer = $update.DriverManufacturer
            DriverProvider = $update.DriverProvider
            DriverVersion = $update.DriverVerVersion
            DriverDate = $update.DriverVerDate
            DriverClass = $update.DriverClass
        } | ConvertTo-Json -Depth 5

        break
    }
}
"""

    command = command.replace(
        "__UPDATE_ID__",
        safe_id
    )

    return parse_json(
        run_powershell(command)
    )


def download_update(update_id):
    safe_id = update_id.replace(
        "'",
        "''"
    )

    command = """
$ErrorActionPreference = 'Stop'

$session = New-Object -ComObject Microsoft.Update.Session
$searcher = $session.CreateUpdateSearcher()

$result = $searcher.Search(
    "IsInstalled=0 and IsHidden=0 and Type='Driver'"
)

$collection = New-Object -ComObject Microsoft.Update.UpdateColl

foreach ($update in $result.Updates) {

    if ($update.Identity.UpdateID -eq '__UPDATE_ID__') {
        [void]$collection.Add($update)
        break
    }
}

if ($collection.Count -eq 0) {
    throw "No se encontró la actualización seleccionada."
}

$downloader = $session.CreateUpdateDownloader()
$downloader.Updates = $collection

$downloadResult = $downloader.Download()

[PSCustomObject]@{
    ResultCode = [int]$downloadResult.ResultCode
    HResult = $downloadResult.HResult
    UpdatesDownloaded = [int]$downloadResult.UpdatesDownloaded
} | ConvertTo-Json -Depth 5
"""

    command = command.replace(
        "__UPDATE_ID__",
        safe_id
    )

    data = parse_json(
        run_powershell(command)
    )

    if data is None:
        return {
            "success": False,
            "error": "No se obtuvo resultado de descarga.",
        }

    result_code = int(
        data.get("ResultCode", -1)
    )

    success = result_code in (
        2,
        3,
    )

    data["success"] = success

    if not success:
        data["error"] = (
            "Windows Update no completó "
            "correctamente la descarga."
        )

    return data


def install_update(update_id):
    safe_id = update_id.replace(
        "'",
        "''"
    )

    command = """
$ErrorActionPreference = 'Stop'

$session = New-Object -ComObject Microsoft.Update.Session
$searcher = $session.CreateUpdateSearcher()

$result = $searcher.Search(
    "IsInstalled=0 and IsHidden=0 and Type='Driver'"
)

$collection = New-Object -ComObject Microsoft.Update.UpdateColl

foreach ($update in $result.Updates) {

    if ($update.Identity.UpdateID -eq '__UPDATE_ID__') {
        [void]$collection.Add($update)
        break
    }
}

if ($collection.Count -eq 0) {
    throw "No se encontró la actualización seleccionada."
}

$installer = $session.CreateUpdateInstaller()
$installer.Updates = $collection

$installResult = $installer.Install()

$individual = @()

for ($i = 0; $i -lt $installResult.ResultCode.Count; $i++) {

    $individual += [PSCustomObject]@{
        Index = $i
        ResultCode = [int]$installResult.ResultCode.Item($i)
        HResult = $installResult.HResult
    }
}

[PSCustomObject]@{
    OverallResultCode = [int]$installResult.ResultCode
    HResult = $installResult.HResult
    RebootRequired = [bool]$installResult.RebootRequired
    IndividualResults = $individual
} | ConvertTo-Json -Depth 7
"""

    command = command.replace(
        "__UPDATE_ID__",
        safe_id
    )

    data = parse_json(
        run_powershell(command)
    )

    if data is None:
        return {
            "success": False,
            "error": "No se obtuvo resultado de instalación.",
        }

    result_code = int(
        data.get(
            "OverallResultCode",
            -1
        )
    )

    success = result_code in (
        2,
        3,
    )

    data["success"] = success

    if not success:
        data["error"] = (
            "Windows Update no confirmó "
            "una instalación correcta."
        )

    return data


def verify_device(
    instance_id,
    expected_version=None
):
    if not instance_id:
        return {
            "status": "NO_INSTANCE_ID",
            "success": False,
            "device_error": True,
            "error": (
                "No se recibió el InstanceId "
                "del dispositivo."
            ),
        }

    last_device = None

    for _ in range(3):

        try:
            last_device = get_device_by_instance_id(
                instance_id
            )

            if last_device:
                break

        except Exception:
            pass

        time.sleep(2)

    if not last_device:
        return {
            "status": "DEVICE_NOT_FOUND",
            "success": False,
            "device_error": True,
            "error": (
                "No se pudo localizar el dispositivo "
                "después de la instalación."
            ),
        }

    status = str(
        last_device.get("Status") or ""
    ).upper()

    problem_code = last_device.get(
        "ProblemCode"
    )

    try:
        problem_code = (
            int(problem_code)
            if problem_code is not None
            else 0
        )

    except (
        ValueError,
        TypeError
    ):
        problem_code = 0

    device_error = (
        status != "OK"
        or problem_code != 0
    )

    installed_version = last_device.get(
        "DriverVersion"
    )

    version_ok = True

    if expected_version and installed_version:

        version_ok = (
            normalize_version(
                installed_version
            )
            >= normalize_version(
                expected_version
            )
        )

    elif expected_version and not installed_version:
        version_ok = False

    if not installed_version:
        version_ok = False

    if device_error:
        verification_status = (
            "DEVICE_ERROR"
        )

    elif not version_ok:
        verification_status = (
            "VERSION_NOT_UPDATED"
        )

    else:
        verification_status = "OK"

    return {
        "status": verification_status,
        "success": (
            verification_status == "OK"
        ),
        "device_error": device_error,
        "status_value": status,
        "problem_code": problem_code,
        "version_ok": version_ok,
        "driver_version": installed_version,
        "device": last_device,
    }


def update_driver(
    update_id,
    create_restore=True,
    instance_id=None,
    expected_version=None,
):
    result = {
        "success": False,
        "update_id": update_id,
        "reboot_required": False,
        "before": {},
        "after": {},
        "restore_point": {},
        "download": {},
        "installation": {},
        "verification": {},
    }

    try:

        # -------------------------------------------------
        # ESTADO ANTES DE LA INSTALACIÓN
        # -------------------------------------------------

        if instance_id:

            result["before"] = (
                get_device_by_instance_id(
                    instance_id
                )
                or {}
            )

        # -------------------------------------------------
        # COMPROBAR QUE LA ACTUALIZACIÓN SIGUE DISPONIBLE
        # -------------------------------------------------

        update = search_update(
            update_id
        )

        if not update:

            result["error"] = (
                "La actualización seleccionada "
                "ya no está disponible."
            )

            return result

        result["update"] = update

        # -------------------------------------------------
        # PUNTO DE RESTAURACIÓN
        # -------------------------------------------------

        if create_restore:

            from safety import create_restore_point

            restore_ok, restore_message = (
                create_restore_point()
            )

            result["restore_point"] = {
                "success": restore_ok,
                "message": restore_message,
            }

            if not restore_ok:

                result["error"] = (
                    "No se pudo crear el punto "
                    "de restauración. "
                    "La instalación fue bloqueada "
                    "por seguridad."
                )

                return result

        # -------------------------------------------------
        # DESCARGA
        # -------------------------------------------------

        result["download"] = download_update(
            update_id
        )

        if not result["download"].get(
            "success"
        ):

            result["error"] = (
                "La descarga del controlador falló."
            )

            return result

        # -------------------------------------------------
        # INSTALACIÓN
        # -------------------------------------------------

        result["installation"] = install_update(
            update_id
        )

        result["reboot_required"] = bool(
            result["installation"].get(
                "RebootRequired",
                False
            )
        )

        if not result["installation"].get(
            "success"
        ):

            result["error"] = (
                "La instalación del controlador falló."
            )

            return result

        # -------------------------------------------------
        # VERIFICACIÓN
        # -------------------------------------------------

        time.sleep(2)

        if instance_id:

            verification = verify_device(
                instance_id,
                expected_version
            )

            # Si Windows indica que necesita reinicio,
            # no declaramos fallo solo porque la versión
            # todavía no se haya reflejado.
            if result["reboot_required"]:

                if verification.get(
                    "status"
                ) == "DEVICE_ERROR":

                    verification["status"] = (
                        "DEVICE_ERROR"
                    )

                    verification["success"] = False

                else:

                    verification["status"] = (
                        "PENDING_REBOOT"
                    )

                    verification["success"] = True

            result["verification"] = verification

            result["after"] = (
                verification.get("device")
                or get_device_by_instance_id(
                    instance_id
                )
                or {}
            )

            if verification.get(
                "status"
            ) == "DEVICE_ERROR":

                result["success"] = False

                result["error"] = (
                    "La instalación terminó, "
                    "pero el dispositivo presenta "
                    "un error."
                )

                return result

            if result["reboot_required"]:

                result["success"] = True

            else:

                result["success"] = bool(
                    verification.get(
                        "success"
                    )
                )

        else:

            result["verification"] = {
                "status": "NOT_AVAILABLE",
                "success": False,
                "device_error": False,
                "error": (
                    "No se recibió InstanceId "
                    "para verificar el dispositivo."
                ),
            }

            result["success"] = True

        return result

    except Exception as exc:

        result["success"] = False
        result["error"] = str(exc)

        return result

