from scanner import scan_system
from updater import update_driver
from reporter import create_reports, create_update_log
from safety import is_admin

VERSION = "V3.7"


def print_header():
    print("=" * 70)
    print(f"DriverUpdater {VERSION}")
    print("Detección, análisis, actualización y verificación de controladores")
    print("=" * 70)
    print()


def print_driver_analysis(data):
    devices = data.get("devices", [])
    print("ANÁLISIS DE CONTROLADORES PRIORITARIOS")
    print("-" * 70)
    print(f"Controladores analizados: {len(devices)}")

    counts = {}
    for d in devices:
        status = d.get("DriverStatus", "SIN INFORMACIÓN")
        counts[status] = counts.get(status, 0) + 1

    for status in (
        "ACTUALIZACIÓN DISPONIBLE",
        "POSIBLEMENTE DESACTUALIZADO",
        "COMPROBACIÓN MANUAL",
        "SIN INFORMACIÓN",
        "ACTUALIZADO",
    ):
        if status in counts:
            print(f"{status:<28}: {counts[status]}")

    priority = [
        d for d in devices
        if d.get("DriverStatus") in (
            "ACTUALIZACIÓN DISPONIBLE",
            "POSIBLEMENTE DESACTUALIZADO",
        )
    ]

    print()
    if not priority:
        print("No hay controladores prioritarios para revisar.")
        print("Los controladores genéricos de Microsoft y las comprobaciones manuales quedan fuera de esta vista.")
        return

    # Agrupar dispositivos que usan exactamente el mismo controlador.
    # La información completa de cada dispositivo sigue quedando en los reportes.
    groups = {}
    for d in priority:
        key = d.get("DriverGroupKey") or "|".join((
            str(d.get("Manufacturer") or "").strip().lower(),
            str(d.get("DriverProviderName") or "").strip().lower(),
            str(d.get("DriverVersion") or "").strip().lower(),
            str(d.get("InfName") or "").strip().lower(),
        ))
        groups.setdefault(key, []).append(d)

    print(f"Mostrando {len(groups)} controlador(es) único(s) de {len(priority)} dispositivo(s) prioritario(s).")
    print("Los duplicados se agrupan y los controladores genéricos de Microsoft no se muestran aquí.")
    print()

    for index, members in enumerate(groups.values(), 1):
        d = members[0]
        print(f"[{index}] {d.get('DeviceName') or d.get('FriendlyName') or 'Desconocido'}")
        if len(members) > 1:
            print(f"    Dispositivos : {len(members)} (mismo controlador)" )
        print(f"    Fabricante  : {d.get('Manufacturer') or 'Desconocido'}")
        print(f"    Proveedor   : {d.get('DriverProviderName') or 'Desconocido'}")
        print(f"    Versión     : {d.get('DriverVersion') or 'Desconocida'}")
        print(f"    Fecha       : {d.get('DriverDateNormalized') or 'Desconocida'}")
        print(f"    Estado      : {d.get('DriverStatus', 'SIN INFORMACIÓN')}")
        print(f"    Evidencia   : {d.get('Evidence', 'SIN_DATOS')}")
        print(f"    Confianza   : {d.get('Confidence', 'BAJA')}")
        print(f"    Motivo      : {d.get('DriverStatusReason') or 'Sin información'}")
        if d.get("DriverAgeDays") is not None:
            print(f"    Antigüedad  : {d.get('DriverAgeDays')} días")
        if d.get("WindowsUpdateVersion"):
            print(f"    WU ofrece   : {d.get('WindowsUpdateVersion')}")
        if d.get("OfficialSource"):
            print(f"    Fuente      : {d['OfficialSource']}")
            print(f"    URL         : {d.get('OfficialSourceURL', '')}")
        if len(members) > 1:
            print("    Dispositivos asociados:")
            for member in members:
                print(f"      - {member.get('DeviceName') or member.get('FriendlyName') or 'Desconocido'}")
        print()


def print_device_errors(data):
    errors = data.get("device_errors", [])
    print("ERRORES DE DISPOSITIVOS")
    print("-" * 70)
    if not errors:
        print("No se detectaron errores de dispositivos.")
        return
    print(f"Se detectaron {len(errors)} dispositivo(s) con posible problema:")
    print()
    for index, device in enumerate(errors, start=1):
        print(f"[{index}] {device.get('DeviceName', 'Desconocido')}")
        print(f"    Fabricante  : {device.get('Manufacturer', 'Desconocido')}")
        print(f"    Estado      : {device.get('Status', 'Desconocido')}")
        print(f"    ProblemCode : {device.get('ProblemCode', 'Desconocido')}")
        print(f"    Versión     : {device.get('DriverVersion', 'Desconocida')}")
        print()


def print_official_sources(data):
    sources = data.get("official_sources", [])
    print("FUENTES OFICIALES")
    print("-" * 70)
    if not sources:
        print("No se identificaron fuentes oficiales automáticamente.")
        return
    for source in sources:
        print(f"[{source.get('type', 'OFICIAL')}] {source.get('name', 'Desconocido')}")
        print(f"    {source.get('url', '')}")
    print()


def print_system_info(data):
    info = data.get("system_info", {})
    print("EQUIPO")
    print("-" * 70)
    print(f"Fabricante : {info.get('Manufacturer', 'Desconocido')}")
    print(f"Modelo     : {info.get('Model', 'Desconocido')}")
    print(f"Windows    : {info.get('WindowsVersion', 'Desconocido')}")
    print(f"Build      : {info.get('WindowsBuild', 'Desconocido')}")
    print(f"BIOS       : {info.get('BIOSVersion', 'Desconocida')}")
    print()


def main():
    print_header()
    try:
        print("[1/5] Analizando dispositivos y controladores...")
        data = scan_system()
    except Exception as exc:
        print("\nERROR durante el análisis:")
        print(exc)
        input("\nPulsa ENTER para salir...")
        return

    summary = data.get("summary", {})
    print()
    print_system_info(data)
    print(f"Dispositivos detectados: {summary.get('devices', 0)}")
    print(f"Actualizaciones Windows Update: {summary.get('windows_updates', 0)}")
    print(f"Actualizaciones de drivers: {summary.get('driver_updates', 0)}")
    print(f"Errores de dispositivos: {summary.get('device_errors', 0)}")
    print(f"Fuentes oficiales detectadas: {summary.get('official_sources', 0)}")
    print(f"Grupos de controladores: {summary.get('driver_groups', 0)}")
    print(f"Controladores prioritarios: {summary.get('drivers_requiring_review', 0)}")
    print(f"Grupos prioritarios únicos: {summary.get('priority_driver_groups', 0)}")
    print()
    print_driver_analysis(data)
    print_device_errors(data)
    print()
    print_official_sources(data)

    updates = data.get("driver_updates", [])
    if not updates:
        print("ACTUALIZACIONES DE CONTROLADORES")
        print("-" * 70)
        print("No se encontraron actualizaciones de controladores mediante Windows Update.")
        print()
        print("NOTA: Esto NO significa necesariamente que todos los controladores estén actualizados.")
        print("La V3.7 separa evidencia de Windows Update, señales de antigüedad y comprobaciones manuales, y oculta controladores genéricos de la vista principal.")
        report_paths = create_reports(data)
        print("\nReportes:\n")
        for path in report_paths:
            print(f"  {path}")
        input("\nPulsa ENTER para salir...")
        return

    print("\nACTUALIZACIONES DISPONIBLES")
    print("-" * 70)
    for index, update in enumerate(updates, start=1):
        print(f"[{index}] {update.get('Title', 'Sin título')}")
        print(f"    Dispositivo : {update.get('DeviceName', 'Desconocido')}")
        print(f"    Versión     : {update.get('InstalledVersion', 'Desconocida')} -> {update.get('DriverVersion', 'Desconocida')}")
        print()

    print("[0] Cancelar")
    while True:
        try:
            number = int(input("Selecciona una actualización: ").strip())
        except ValueError:
            print("Introduce un número válido.")
            continue
        if number == 0:
            return
        if 1 <= number <= len(updates):
            break
        print("Selección fuera de rango.")

    selected = updates[number - 1]
    print(f"\nActualización seleccionada: {selected.get('Title', 'Sin título')}")
    confirmation = input("¿Deseas continuar? [S/N]: ").strip().lower()
    if confirmation not in ("s", "si", "sí"):
        print("Operación cancelada.")
        return

    if not is_admin():
        print("\nERROR: DriverUpdater debe ejecutarse como administrador.")
        input("\nPulsa ENTER para salir...")
        return

    print("\n[2/5] Creando punto de restauración...")
    print("[3/5] Descargando e instalando controlador...")
    print("[4/5] Verificando dispositivo y controlador...")
    result = update_driver(selected.get("UpdateID"), create_restore=True,
                           instance_id=selected.get("InstanceId"),
                           expected_version=selected.get("DriverVersion"))

    print("\n[5/5] RESULTADO")
    print("-" * 70)
    restore_point = result.get("restore_point", {})
    download = result.get("download", {})
    installation = result.get("installation", {})
    verification = result.get("verification", {})
    before = result.get("before", {})
    after = result.get("after", {})
    print("Punto de restauración : " + ("OK" if restore_point.get("success") else "ERROR"))
    print("Descarga              : " + ("OK" if download.get("success") else "ERROR"))
    print("Instalación            : " + ("OK" if installation.get("success") else "ERROR"))
    print(f"Verificación           : {verification.get('status', 'NO DISPONIBLE')}")
    print(f"Versión antes          : {before.get('DriverVersion', 'Desconocida')}")
    print(f"Versión después        : {after.get('DriverVersion', 'Desconocida')}")
    print(f"Estado dispositivo     : {verification.get('status_value', 'Desconocido')}")
    print(f"ProblemCode            : {verification.get('problem_code', 'Desconocido')}")
    print("REINICIO               : " + ("NECESARIO" if result.get("reboot_required") else "No indicado"))
    print("\nACTUALIZACIÓN COMPLETADA." if result.get("success") else "\nLA ACTUALIZACIÓN NO SE CONSIDERA COMPLETADA.")
    if result.get("error"):
        print(f"Detalle: {result['error']}")
    report_paths = create_reports(data, result)
    log_path = create_update_log(result)
    print("\nReportes:\n")
    for path in report_paths:
        print(f"  {path}")
    print(f"\nRegistro detallado:\n  {log_path}")
    input("\nPulsa ENTER para salir...")


if __name__ == "__main__":
    main()
