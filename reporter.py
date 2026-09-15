import json
from datetime import datetime
from pathlib import Path


def get_report_directory():
    documents = Path.home() / "Documents"

    directory = (
        documents
        / "DriverUpdater"
        / "reports"
    )

    directory.mkdir(
        parents=True,
        exist_ok=True
    )

    return directory


def create_reports(
    data,
    update_result=None
):
    directory = get_report_directory()

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    txt_path = (
        directory
        / f"DriverReport_{timestamp}.txt"
    )

    json_path = (
        directory
        / f"DriverReport_{timestamp}.json"
    )

    report = dict(data)

    if update_result is not None:
        report["update_result"] = update_result

    # -------------------------------------------------
    # REPORTE JSON
    # -------------------------------------------------

    with open(
        json_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False,
            default=str
        )

    # -------------------------------------------------
    # REPORTE TXT
    # -------------------------------------------------

    with open(
        txt_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "DriverUpdater V3.1\n"
        )

        file.write(
            "=" * 70 + "\n\n"
        )

        # ---------------------------------------------
        # RESUMEN
        # ---------------------------------------------

        file.write(
            "RESUMEN\n"
        )

        file.write(
            "-" * 70 + "\n"
        )

        summary = data.get(
            "summary",
            {}
        )

        file.write(
            f"Dispositivos: "
            f"{summary.get('devices', 0)}\n"
        )

        file.write(
            f"Actualizaciones Windows Update: "
            f"{summary.get('windows_updates', 0)}\n"
        )

        file.write(
            f"Actualizaciones de drivers: "
            f"{summary.get('driver_updates', 0)}\n\n"
        )

        # ---------------------------------------------
        # ACTUALIZACIONES DETECTADAS
        # ---------------------------------------------

        file.write(
            "ACTUALIZACIONES DETECTADAS\n"
        )

        file.write(
            "-" * 70 + "\n"
        )

        for index, update in enumerate(
            data.get(
                "driver_updates",
                []
            ),
            start=1
        ):

            file.write(
                f"\n[{index}] "
                f"{update.get('Title', '')}\n"
            )

            file.write(
                f"Dispositivo: "
                f"{update.get('DeviceName', '')}\n"
            )

            file.write(
                f"Versión instalada: "
                f"{update.get('InstalledVersion', '')}\n"
            )

            file.write(
                f"Versión disponible: "
                f"{update.get('DriverVersion', '')}\n"
            )

            file.write(
                f"Fabricante: "
                f"{update.get('Manufacturer', '')}\n"
            )

            file.write(
                f"UpdateID: "
                f"{update.get('UpdateID', '')}\n"
            )

        # ---------------------------------------------
        # RESULTADO DE ACTUALIZACIÓN
        # ---------------------------------------------

        if update_result is not None:

            file.write(
                "\n\nRESULTADO DE LA ACTUALIZACIÓN\n"
            )

            file.write(
                "=" * 70 + "\n"
            )

            file.write(
                f"Éxito: "
                f"{update_result.get('success')}\n"
            )

            file.write(
                f"Reinicio requerido: "
                f"{update_result.get('reboot_required')}\n"
            )

            verification = update_result.get(
                "verification",
                {}
            )

            file.write(
                f"Verificación: "
                f"{verification.get('status', 'N/A')}\n"
            )

            before = update_result.get(
                "before",
                {}
            )

            after = update_result.get(
                "after",
                {}
            )

            file.write(
                f"Versión antes: "
                f"{before.get('DriverVersion', 'N/A')}\n"
            )

            file.write(
                f"Versión después: "
                f"{after.get('DriverVersion', 'N/A')}\n"
            )

            file.write(
                f"Estado dispositivo: "
                f"{verification.get('status_value', 'N/A')}\n"
            )

            file.write(
                f"ProblemCode: "
                f"{verification.get('problem_code', 'N/A')}\n"
            )

            if update_result.get("error"):

                file.write(
                    f"\nError: "
                    f"{update_result.get('error')}\n"
                )

        # ---------------------------------------------
        # INVENTARIO DE DISPOSITIVOS
        # ---------------------------------------------

        file.write(
            "\n\nINVENTARIO DE DISPOSITIVOS\n"
        )

        file.write(
            "=" * 70 + "\n"
        )

        for device in data.get(
            "devices",
            []
        ):

            file.write(
                f"\nNombre: "
                f"{device.get('DeviceName', '')}\n"
            )

            file.write(
                f"Fabricante: "
                f"{device.get('Manufacturer', '')}\n"
            )

            file.write(
                f"Estado: "
                f"{device.get('Status', '')}\n"
            )

            file.write(
                f"ProblemCode: "
                f"{device.get('ProblemCode', '')}\n"
            )

            file.write(
                f"Versión: "
                f"{device.get('DriverVersion', '')}\n"
            )

            file.write(
                f"Proveedor: "
                f"{device.get('DriverProviderName', '')}\n"
            )

            file.write(
                f"INF: "
                f"{device.get('InfName', '')}\n"
            )

    return (
        str(txt_path),
        str(json_path)
    )


def create_update_log(result):
    directory = get_report_directory()

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    log_path = (
        directory
        / f"DriverUpdateLog_{timestamp}.txt"
    )

    with open(
        log_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "DriverUpdater V3.1 - "
            "REGISTRO DE OPERACIÓN\n"
        )

        file.write(
            "=" * 70 + "\n\n"
        )

        file.write(
            f"Fecha: "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        file.write(
            f"UpdateID: "
            f"{result.get('update_id', 'N/A')}\n"
        )

        file.write(
            f"Resultado final: "
            f"{result.get('success', False)}\n"
        )

        file.write(
            f"Reinicio requerido: "
            f"{result.get('reboot_required', False)}\n\n"
        )

        sections = [
            ("PUNTO DE RESTAURACIÓN", "restore_point"),
            ("DESCARGA", "download"),
            ("INSTALACIÓN", "installation"),
            ("VERIFICACIÓN", "verification"),
            ("ESTADO ANTES", "before"),
            ("ESTADO DESPUÉS", "after"),
        ]

        for title, key in sections:

            file.write(
                f"{title}\n"
            )

            file.write(
                "-" * 70 + "\n"
            )

            file.write(
                json.dumps(
                    result.get(key, {}),
                    indent=4,
                    ensure_ascii=False,
                    default=str
                )
            )

            file.write("\n\n")

        if result.get("error"):

            file.write(
                "ERROR\n"
            )

            file.write(
                "-" * 70 + "\n"
            )

            file.write(
                str(result["error"])
            )

    return str(log_path)