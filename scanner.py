import json
import platform
import subprocess


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
        timeout=180,
        creationflags=subprocess.CREATE_NO_WINDOW,
        startupinfo=startupinfo,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
            or "PowerShell devolvió un error."
        )

    return result.stdout.strip()


def normalize_version(version):
    if not version:
        return ()

    parts = []

    for part in str(version).strip().split("."):
        digits = "".join(
            ch for ch in part if ch.isdigit()
        )

        parts.append(
            int(digits) if digits else 0
        )

    return tuple(parts)


def version_is_newer_or_equal(installed, available):
    if not available:
        return True

    if not installed:
        return False

    a = normalize_version(installed)
    b = normalize_version(available)

    length = max(len(a), len(b))

    a += (0,) * (length - len(a))
    b += (0,) * (length - len(b))

    return a >= b


def get_system_info():
    commands = {
        "computer": r"""
Get-CimInstance Win32_ComputerSystem |
    Select-Object Manufacturer, Model |
    ConvertTo-Json -Compress
""",

        "os": r"""
Get-CimInstance Win32_OperatingSystem |
    Select-Object Caption, BuildNumber, Version |
    ConvertTo-Json -Compress
""",

        "bios": r"""
Get-CimInstance Win32_BIOS |
    Select-Object SMBIOSBIOSVersion, ReleaseDate |
    ConvertTo-Json -Compress
"""
    }

    info = {}

    try:
        computer_output = run_powershell(
            commands["computer"]
        )

        if computer_output:
            computer = json.loads(
                computer_output
            )

            info["Manufacturer"] = (
                computer.get("Manufacturer")
            )

            info["Model"] = (
                computer.get("Model")
            )

    except Exception:
        pass

    try:
        os_output = run_powershell(
            commands["os"]
        )

        if os_output:
            operating_system = json.loads(
                os_output
            )

            info["WindowsVersion"] = (
                operating_system.get("Caption")
            )

            info["WindowsBuild"] = (
                operating_system.get("BuildNumber")
            )

            info["WindowsVersionNumber"] = (
                operating_system.get("Version")
            )

    except Exception:
        pass

    try:
        bios_output = run_powershell(
            commands["bios"]
        )

        if bios_output:
            bios = json.loads(
                bios_output
            )

            info["BIOSVersion"] = (
                bios.get("SMBIOSBIOSVersion")
            )

            info["BIOSDate"] = (
                bios.get("ReleaseDate")
            )

    except Exception:
        pass

    return info
    


def get_devices():
    command = r"""
$ErrorActionPreference = 'Stop'

$pnpDevices = Get-PnpDevice -ErrorAction SilentlyContinue

$drivers = @{}

Get-CimInstance Win32_PnPSignedDriver |
    ForEach-Object {
        if ($_.DeviceID) {
            $drivers[$_.DeviceID] = $_
        }
    }

$devices = foreach ($device in $pnpDevices) {

    $driver = $drivers[$device.InstanceId]

    $hardwareIds = @()

    if ($driver -and $driver.HardWareID) {
        $hardwareIds = @($driver.HardWareID)
    }

    [PSCustomObject]@{
        DeviceName = if ($driver) {
            $driver.DeviceName
        } else {
            $device.FriendlyName
        }

        FriendlyName = $device.FriendlyName

        DeviceID = $device.InstanceId

        Class = $device.Class

        Status = $device.Status

        ProblemCode = $device.ProblemCode

        Manufacturer = if ($driver) {
            $driver.Manufacturer
        } else {
            $device.Manufacturer
        }

        DriverProviderName = if ($driver) {
            $driver.DriverProviderName
        } else {
            $null
        }

        DriverVersion = if ($driver) {
            $driver.DriverVersion
        } else {
            $null
        }

        DriverDate = if ($driver) {
            $driver.DriverDate
        } else {
            $null
        }

        InfName = if ($driver) {
            $driver.InfName
        } else {
            $null
        }

        DriverDescription = if ($driver) {
            $driver.DriverDescription
        } else {
            $null
        }

        IsSigned = if ($driver) {
            $driver.IsSigned
        } else {
            $null
        }

        HardwareIds = $hardwareIds
    }
}

$devices | ConvertTo-Json -Depth 7
"""

    output = run_powershell(command)

    if not output:
        return []

    data = json.loads(output)

    if isinstance(data, dict):
        return [data]

    return data


def get_device_by_instance_id(instance_id):
    if not instance_id:
        return None

    safe_id = instance_id.replace(
        "'",
        "''"
    )

    command = """
$ErrorActionPreference = 'Stop'

$device = Get-PnpDevice `
    -InstanceId '__INSTANCE_ID__' `
    -ErrorAction SilentlyContinue

$driver = Get-CimInstance Win32_PnPSignedDriver |
    Where-Object {
        $_.DeviceID -eq '__INSTANCE_ID__'
    } |
    Select-Object -First 1

if ($device -or $driver) {

    $hardwareIds = @()

    if ($driver -and $driver.HardWareID) {
        $hardwareIds = @($driver.HardWareID)
    }

    [PSCustomObject]@{

        DeviceName = if ($driver) {
            $driver.DeviceName
        } else {
            $device.FriendlyName
        }

        FriendlyName = $device.FriendlyName

        DeviceID = '__INSTANCE_ID__'

        Class = $device.Class

        Status = $device.Status

        ProblemCode = $device.ProblemCode

        Manufacturer = if ($driver) {
            $driver.Manufacturer
        } else {
            $device.Manufacturer
        }

        DriverProviderName = if ($driver) {
            $driver.DriverProviderName
        } else {
            $null
        }

        DriverVersion = if ($driver) {
            $driver.DriverVersion
        } else {
            $null
        }

        DriverDate = if ($driver) {
            $driver.DriverDate
        } else {
            $null
        }

        InfName = if ($driver) {
            $driver.InfName
        } else {
            $null
        }

        IsSigned = if ($driver) {
            $driver.IsSigned
        } else {
            $null
        }

        HardwareIds = $hardwareIds

    } | ConvertTo-Json -Depth 7
}
"""

    command = command.replace(
        "__INSTANCE_ID__",
        safe_id
    )

    output = run_powershell(command)

    if not output:
        return None

    return json.loads(output)


def get_windows_update_drivers():
    command = r"""
$ErrorActionPreference = 'Stop'

$session = New-Object `
    -ComObject Microsoft.Update.Session

$searcher = $session.CreateUpdateSearcher()

$result = $searcher.Search(
    "IsInstalled=0 and IsHidden=0 and Type='Driver'"
)

$updates = foreach ($update in $result.Updates) {

    [PSCustomObject]@{
        Title = $update.Title
        UpdateID = $update.Identity.UpdateID
        DriverClass = $update.DriverClass
        HardwareIds = @($update.DriverHardwareID)
        Manufacturer = $update.DriverManufacturer
        Provider = $update.DriverProvider
        DriverVersion = $update.DriverVerVersion
        DriverDate = $update.DriverVerDate
        KB = @($update.KBArticleIDs)
    }
}

$updates | ConvertTo-Json -Depth 7
"""

    output = run_powershell(command)

    if not output:
        return []

    data = json.loads(output)

    if isinstance(data, dict):
        return [data]

    return data


def get_official_sources(system_info, devices):
    """
    Devuelve las fuentes oficiales que pueden utilizarse
    para comprobar controladores.

    No descarga ni instala nada.
    """

    manufacturer = str(
        system_info.get("Manufacturer") or ""
    ).lower()

    sources = []

    if "lenovo" in manufacturer:
        sources.append({
            "name": "Lenovo Support",
            "type": "OEM",
            "url": "https://pcsupport.lenovo.com/"
        })

    elif "dell" in manufacturer:
        sources.append({
            "name": "Dell Support",
            "type": "OEM",
            "url": "https://www.dell.com/support/home/"
        })

    elif (
    "hp" in manufacturer
    or "hewlett" in manufacturer
):
        sources.append({
            "name": "HP Support",
            "type": "OEM",
            "url": "https://support.hp.com/"
        })

    elif "asus" in manufacturer:
        sources.append({
            "name": "ASUS Support",
            "type": "OEM",
            "url": "https://www.asus.com/support/"
        })

    elif "acer" in manufacturer:
        sources.append({
            "name": "Acer Support",
            "type": "OEM",
            "url": "https://www.acer.com/support"
        })

    elif "msi" in manufacturer:
        sources.append({
            "name": "MSI Support",
            "type": "OEM",
            "url": "https://www.msi.com/support"
        })

    elif "microsoft" in manufacturer:
        sources.append({
            "name": "Microsoft Support",
            "type": "OEM",
            "url": "https://support.microsoft.com/"
        })

    device_manufacturers = set()

    for device in devices:
        name = str(
            device.get("Manufacturer") or ""
        ).lower()

        if name:
            device_manufacturers.add(name)

    known_sources = {
        "amd": {
            "name": "AMD Drivers & Support",
            "url": "https://www.amd.com/en/support/download/drivers.html"
        },
        "advanced micro devices": {
            "name": "AMD Drivers & Support",
            "url": "https://www.amd.com/en/support/download/drivers.html"
        },
        "nvidia": {
            "name": "NVIDIA Drivers",
            "url": "https://www.nvidia.com/Download/index.aspx"
        },
        "intel": {
            "name": "Intel Download Center",
            "url": "https://www.intel.com/content/www/us/en/download-center/home.html"
        },
        "realtek": {
            "name": "Realtek Downloads",
            "url": "https://www.realtek.com/Download/"
        },
        "mediatek": {
            "name": "MediaTek",
            "url": "https://www.mediatek.com/"
        }
    }

    for manufacturer_name in device_manufacturers:

        for key, source in known_sources.items():

            if key in manufacturer_name:

                if not any(
                    x["url"] == source["url"]
                    for x in sources
                ):
                    sources.append({
                        "name": source["name"],
                        "type": "Manufacturer",
                        "url": source["url"]
                    })

    return sources


def match_update(device, update):

    device_ids = [
        str(x).lower()
        for x in (
            device.get("HardwareIds") or []
        )
        if x
    ]

    update_ids = [
        str(x).lower()
        for x in (
            update.get("HardwareIds") or []
        )
        if x
    ]

    for device_id in device_ids:

        for update_id in update_ids:

            if device_id == update_id:
                return True

    manufacturer = str(
        device.get("Manufacturer") or ""
    ).lower()

    update_manufacturer = str(
        update.get("Manufacturer") or ""
    ).lower()

    device_name = str(
        device.get("DeviceName") or ""
    ).lower()

    update_title = str(
        update.get("Title") or ""
    ).lower()

    if (
        manufacturer
        and update_manufacturer
    ):

        if (
            manufacturer in update_manufacturer
            or update_manufacturer in manufacturer
        ):

            words = [
                word
                for word in device_name.split()
                if len(word) > 3
            ]

            if any(
                word in update_title
                for word in words
            ):
                return True

    return False


def _parse_driver_date(value):
    """Convierte DriverDate de WMI/CIM a YYYY-MM-DD.

    Ignora fechas claramente inválidas o valores históricos usados por
    Windows como fecha de referencia (por ejemplo 2006-06-21).
    """
    import datetime
    import re

    if not value:
        return None

    text = str(value).strip()

    # Formato JSON/WMI habitual: /Date(1738022400000)/
    match = re.search(r"/Date\(([-]?\d+)\)/", text)
    if match:
        try:
            millis = int(match.group(1))
            dt = datetime.datetime.fromtimestamp(
                millis / 1000,
                tz=datetime.timezone.utc,
            )
            date = dt.date()
        except (ValueError, OverflowError, OSError):
            return None
    else:
        # Algunos sistemas devuelven ya una fecha legible.
        parsed = None
        for fmt in (
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                parsed = datetime.datetime.strptime(text, fmt).date()
                break
            except ValueError:
                pass
        if parsed is None:
            return None
        date = parsed

    # 2006-06-21 aparece con frecuencia como fecha de referencia en
    # controladores/componentes de Windows y no debe tratarse como
    # evidencia de que el controlador sea realmente de 2006.
    if date.year <= 2007:
        return None

    today = datetime.date.today()
    if date > today + datetime.timedelta(days=1):
        return None

    return date.isoformat()


def _version_tuple(value):
    """Normaliza una versión para comparación segura."""
    import re

    if not value:
        return None

    parts = re.findall(r"\d+", str(value))
    if not parts:
        return None

    numbers = [int(x) for x in parts[:4]]
    while len(numbers) < 4:
        numbers.append(0)
    return tuple(numbers)


def _find_official_source(driver, official_sources):
    provider = str(driver.get("DriverProviderName") or "").strip().lower()
    manufacturer = str(driver.get("Manufacturer") or "").strip().lower()

    aliases = (
        (("advanced micro devices", "amd"), "AMD Drivers & Support"),
        (("nvidia",), "NVIDIA Drivers"),
        (("intel",), "Intel Download Center"),
        (("realtek",), "Realtek Downloads"),
        (("mediatek",), "MediaTek"),
        (("lenovo",), "Lenovo Support"),
        (("dell",), "Dell Support"),
        (("hewlett-packard", "hewlett packard", "hp"), "HP Support"),
        (("asus",), "ASUS Support"),
        (("acer",), "Acer Support"),
        (("microsoft",), "Microsoft Support"),
    )

    # El proveedor tiene prioridad sobre el fabricante del dispositivo.
    for values, source_name in aliases:
        if any(value in provider for value in values):
            for item in official_sources:
                if item.get("name") == source_name:
                    return item

    for values, source_name in aliases:
        if any(value in manufacturer for value in values):
            for item in official_sources:
                if item.get("name") == source_name:
                    return item

    return None


def _analysis_result(status, reason, source=None, evidence="SIN_COMPARACIÓN",
                     confidence="BAJA", review=True):
    return {
        "DriverStatus": status,
        "DriverStatusReason": reason,
        "Evidence": evidence,
        "Confidence": confidence,
        "ReviewRequired": review,
        "OfficialSource": source.get("name") if source else None,
        "OfficialSourceType": source.get("type") if source else None,
        "OfficialSourceURL": source.get("url") if source else None,
    }


def classify_driver(driver, official_sources):
    """Clasifica con niveles de evidencia, sin afirmar obsolescencia sin prueba.

    ACTUALIZACIÓN DISPONIBLE requiere una versión superior encontrada por
    Windows Update para el dispositivo exacto. La antigüedad solo genera
    una alerta de revisión. ACTUALIZADO no se asigna sin una comparación
    autoritativa con una versión conocida como más reciente.
    """
    import datetime

    version = driver.get("DriverVersion")
    provider = str(driver.get("DriverProviderName") or "").strip()
    normalized_date = _parse_driver_date(driver.get("DriverDate"))
    source = _find_official_source(driver, official_sources)

    driver["DriverDateNormalized"] = normalized_date

    if normalized_date:
        driver_date = datetime.date.fromisoformat(normalized_date)
        driver["DriverAgeDays"] = max(0, (datetime.date.today() - driver_date).days)
    else:
        driver["DriverAgeDays"] = None

    if not version:
        return _analysis_result(
            "SIN INFORMACIÓN",
            "Windows no proporcionó una versión del controlador; se conserva en el inventario, pero no se muestra en la revisión principal.",
            source, "SIN_DATOS", "BAJA", False
        )

    update_version = driver.get("WindowsUpdateVersion")
    installed_tuple = _version_tuple(version)
    update_tuple = _version_tuple(update_version)

    if installed_tuple and update_tuple and update_tuple > installed_tuple:
        return _analysis_result(
            "ACTUALIZACIÓN DISPONIBLE",
            "Windows Update ofrece una versión superior asociada a este dispositivo.",
            source, "WINDOWS_UPDATE", "ALTA", True
        )

    provider_lower = provider.lower()
    if "microsoft" in provider_lower:
        return _analysis_result(
            "COMPROBACIÓN MANUAL",
            "Controlador genérico de Microsoft; se conserva en el inventario, pero no se incluye en la cola principal de revisión.",
            source, "SIN_COMPARACIÓN", "MEDIA", False
        )

    age_days = driver.get("DriverAgeDays")
    if age_days is not None and age_days >= 3 * 365:
        if source:
            reason = (
                "La fecha del controlador supera aproximadamente 3 años; "
                "es una señal de revisión, no una confirmación de obsolescencia. "
                "Comparar versión y hardware con la fuente oficial."
            )
            evidence = "ANTIGÜEDAD"
            confidence = "BAJA"
        else:
            reason = (
                "La fecha del controlador supera aproximadamente 3 años, pero "
                "no se identificó una fuente oficial del fabricante para confirmar una versión más reciente."
            )
            evidence = "ANTIGÜEDAD_SIN_FUENTE"
            confidence = "BAJA"
        return _analysis_result(
            "POSIBLEMENTE DESACTUALIZADO", reason, source, evidence, confidence, True
        )

    return _analysis_result(
        "COMPROBACIÓN MANUAL",
        "Hay versión instalada, pero no existe evidencia autoritativa suficiente para confirmar que sea la última versión. No se incluye en la cola principal de revisión.",
        source, "SIN_COMPARACIÓN", "MEDIA", False
    )


def analyze_drivers(devices, official_sources):
    """Añade análisis y una clave para agrupar controladores duplicados."""
    analyzed = []
    for device in devices:
        item = dict(device)
        item.update(classify_driver(item, official_sources))

        manufacturer = str(item.get("Manufacturer") or "").strip().lower()
        provider = str(item.get("DriverProviderName") or "").strip().lower()
        version = str(item.get("DriverVersion") or "").strip().lower()
        inf_name = str(item.get("InfName") or "").strip().lower()
        item["DriverGroupKey"] = "|".join((manufacturer, provider, version, inf_name))
        analyzed.append(item)
    return analyzed


def scan_system():

    system_info = get_system_info()

    devices = get_devices()

    available_updates = (
        get_windows_update_drivers()
    )

    driver_updates = []

    for update in available_updates:

        for device in devices:

            if not match_update(
                device,
                update
            ):
                continue

            installed_version = (
                device.get("DriverVersion")
            )

            available_version = (
                update.get("DriverVersion")
            )

            if version_is_newer_or_equal(
                installed_version,
                available_version
            ):
                continue

            item = dict(update)

            item["DeviceName"] = (
                device.get("DeviceName")
            )

            item["InstanceId"] = (
                device.get("DeviceID")
            )

            item["InstalledVersion"] = (
                installed_version
            )

            item["InstalledProvider"] = (
                device.get("DriverProviderName")
            )

            item["CurrentStatus"] = (
                device.get("Status")
            )

            item["CurrentProblemCode"] = (
                device.get("ProblemCode")
            )

            driver_updates.append(item)

            break

    # Asociar la versión ofrecida por Windows Update al dispositivo
    # para que el análisis pueda distinguir una señal real de actualización
    # de una simple heurística por antigüedad.
    for update in driver_updates:
        instance_id = update.get("InstanceId")
        for device in devices:
            if device.get("DeviceID") == instance_id:
                device["WindowsUpdateVersion"] = update.get("DriverVersion")
                device["WindowsUpdateTitle"] = update.get("Title")
                break

    device_errors = []

    for device in devices:

        status = str(
            device.get("Status") or ""
        ).upper()

        problem_code = device.get(
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

        # ProblemCode es la fuente principal para determinar
        # si Windows reporta un problema real del dispositivo.
        # Get-PnpDevice puede devolver Status="Unknown" en
        # dispositivos perfectamente funcionales, especialmente
        # dispositivos HID, USB, almacenamiento y dispositivos SWD.
        if problem_code != 0:

            device_errors.append({
                "DeviceName":
                    device.get("DeviceName"),

                "DeviceID":
                    device.get("DeviceID"),

                "Status":
                    device.get("Status"),

                "ProblemCode":
                    problem_code,

                "DriverVersion":
                    device.get("DriverVersion"),

                "Manufacturer":
                    device.get("Manufacturer"),
            })

    official_sources = get_official_sources(
        system_info,
        devices
    )

    devices = analyze_drivers(
        devices,
        official_sources
    )

    return {

        "system_info":
            system_info,

        "devices":
            devices,

        "available_windows_updates":
            available_updates,

        "driver_updates":
            driver_updates,

        "device_errors":
            device_errors,

        "official_sources":
            official_sources,

        "summary": {
            "devices": len(devices),
            "windows_updates": len(available_updates),
            "driver_updates": len(driver_updates),
            "device_errors": len(device_errors),
            "official_sources": len(official_sources),
            "driver_status_counts": {
                status: sum(1 for d in devices if d.get("DriverStatus") == status)
                for status in (
                    "ACTUALIZACIÓN DISPONIBLE",
                    "POSIBLEMENTE DESACTUALIZADO",
                    "COMPROBACIÓN MANUAL",
                    "SIN INFORMACIÓN",
                    "ACTUALIZADO",
                )
            },
            "drivers_requiring_review": sum(
                1 for d in devices if d.get("ReviewRequired")
            ),
            "driver_groups": len({
                d.get("DriverGroupKey") for d in devices if d.get("DriverGroupKey")
            }),
            "priority_driver_groups": len({
                d.get("DriverGroupKey") for d in devices
                if d.get("ReviewRequired") and d.get("DriverStatus") in (
                    "ACTUALIZACIÓN DISPONIBLE",
                    "POSIBLEMENTE DESACTUALIZADO",
                ) and d.get("DriverGroupKey")
            }),
        },
    }


if __name__ == "__main__":

    data = scan_system()

    print(
        json.dumps(
            data,
            indent=4,
            ensure_ascii=False,
            default=str
        )
    )