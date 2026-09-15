import threading
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

from scanner import scan_system
from updater import update_driver
from reporter import create_reports, create_update_log
from safety import is_admin

VERSION = "V3.8.2"


class DriverUpdaterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"DriverUpdater {VERSION}")
        self.geometry("1050x700")
        self.minsize(900, 600)

        self.data = {}
        self.priority_groups = []
        self.current_result = None

        self._build_ui()
        self.after(300, self.start_scan)

    def _build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        header = ttk.Frame(root)
        header.pack(fill="x")

        ttk.Label(
            header,
            text=f"DriverUpdater {VERSION}",
            font=("Segoe UI", 20, "bold")
        ).pack(side="left")

        ttk.Label(
            header,
            text="Detección y análisis seguro de controladores",
            font=("Segoe UI", 10)
        ).pack(side="left", padx=18, pady=(8, 0))

        self.btn_scan = ttk.Button(
            header, text="Analizar", command=self.start_scan
        )
        self.btn_scan.pack(side="right")

        self.status_var = tk.StringVar(value="Listo.")
        ttk.Label(
            root, textvariable=self.status_var
        ).pack(fill="x", pady=(8, 4))

        progress_frame = ttk.Frame(root)
        progress_frame.pack(fill="x", pady=(0, 8))

        self.progress = ttk.Progressbar(
            progress_frame, mode="indeterminate", length=300
        )
        self.progress.pack(fill="x")

        info = ttk.LabelFrame(root, text="Equipo", padding=8)
        info.pack(fill="x", pady=(0, 8))

        self.info_vars = {}
        fields = [
            ("Fabricante", "Manufacturer"),
            ("Modelo", "Model"),
            ("Windows", "WindowsVersion"),
            ("Build", "WindowsBuild"),
            ("BIOS", "BIOSVersion"),
        ]

        for i, (label, key) in enumerate(fields):
            ttk.Label(info, text=f"{label}:").grid(
                row=0, column=i * 2, sticky="w", padx=(0, 4)
            )
            var = tk.StringVar(value="Desconocido")
            self.info_vars[key] = var
            ttk.Label(info, textvariable=var).grid(
                row=0, column=i * 2 + 1, sticky="w", padx=(0, 16)
            )

        summary = ttk.Frame(root)
        summary.pack(fill="x", pady=(0, 8))

        self.cards = {}
        for title, key in [
            ("Analizados", "devices"),
            ("Actualización disponible", "available"),
            ("Posiblemente desactualizados", "old"),
            ("Errores", "errors"),
        ]:
            frame = ttk.LabelFrame(summary, text=title, padding=8)
            frame.pack(side="left", fill="x", expand=True, padx=3)
            var = tk.StringVar(value="0")
            self.cards[key] = var
            ttk.Label(
                frame, textvariable=var,
                font=("Segoe UI", 18, "bold")
            ).pack()

        body = ttk.Panedwindow(root, orient="vertical")
        body.pack(fill="both", expand=True)

        list_frame = ttk.LabelFrame(
            body, text="Controladores prioritarios", padding=6
        )
        detail_frame = ttk.LabelFrame(
            body, text="Detalles", padding=6
        )
        body.add(list_frame, weight=3)
        body.add(detail_frame, weight=2)

        columns = ("name", "manufacturer", "version", "date", "status")
        self.tree = ttk.Treeview(
            list_frame, columns=columns, show="headings",
            selectmode="browse"
        )

        headings = {
            "name": "Controlador",
            "manufacturer": "Fabricante",
            "version": "Versión",
            "date": "Fecha",
            "status": "Estado",
        }

        widths = {
            "name": 320, "manufacturer": 150,
            "version": 120, "date": 110, "status": 210
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

        yscroll = ttk.Scrollbar(
            list_frame, orient="vertical",
            command=self.tree.yview
        )
        xscroll = ttk.Scrollbar(
            list_frame, orient="horizontal",
            command=self.tree.xview
        )
        self.tree.configure(
            yscrollcommand=yscroll.set,
            xscrollcommand=xscroll.set
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self.show_selected)

        self.detail = tk.Text(
            detail_frame, height=10, wrap="word",
            font=("Consolas", 10), state="disabled"
        )
        detail_scroll = ttk.Scrollbar(
            detail_frame, orient="vertical",
            command=self.detail.yview
        )
        self.detail.configure(yscrollcommand=detail_scroll.set)
        self.detail.pack(side="left", fill="both", expand=True)
        detail_scroll.pack(side="right", fill="y")

        actions = ttk.Frame(root)
        actions.pack(fill="x", pady=(10, 0))

        self.btn_install = ttk.Button(
            actions, text="Instalar actualización seleccionada",
            command=self.install_selected, state="disabled"
        )
        self.btn_install.pack(side="left")

        self.btn_source = ttk.Button(
            actions, text="Abrir fuente oficial",
            command=self.open_source, state="disabled"
        )
        self.btn_source.pack(side="left", padx=8)

        self.btn_about = ttk.Button(
            actions, text="Acerca de",
            command=self.show_about
        )
        self.btn_about.pack(side="left", padx=8)

        ttk.Label(
            actions,
            text="Los controladores genéricos y comprobaciones manuales "
                 "no saturan esta vista; siguen en los reportes."
        ).pack(side="right")

    def set_status(self, text):
        self.after(0, lambda: self.status_var.set(text))

    def start_scan(self):
        if self.btn_scan["state"] == "disabled":
            return

        self.btn_scan.config(state="disabled")
        self.btn_install.config(state="disabled")
        self.btn_source.config(state="disabled")
        self.progress.start(12)
        self.status_var.set("Analizando dispositivos y controladores...")
        self._clear_tree()
        self._set_detail("")

        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        try:
            data = scan_system()
            self.after(0, lambda: self._scan_finished(data))
        except Exception as exc:
            self.after(
                0,
                lambda: self._scan_failed(str(exc))
            )

    def _scan_failed(self, error):
        self.progress.stop()
        self.btn_scan.config(state="normal")
        self.status_var.set("Error durante el análisis.")
        messagebox.showerror(
            "DriverUpdater",
            f"No se pudo completar el análisis:\n\n{error}"
        )

    def _scan_finished(self, data):
        self.progress.stop()
        self.progress["value"] = 0
        self.data = data
        self.btn_scan.config(state="normal")

        info = data.get("system_info", {})
        for key, var in self.info_vars.items():
            var.set(str(info.get(key) or "Desconocido"))

        devices = data.get("devices", [])
        updates = data.get("driver_updates", [])
        errors = data.get("device_errors", [])

        counts = {}
        for device in devices:
            status = device.get("DriverStatus", "SIN INFORMACIÓN")
            counts[status] = counts.get(status, 0) + 1

        self.cards["devices"].set(str(len(devices)))
        self.cards["available"].set(
            str(counts.get("ACTUALIZACIÓN DISPONIBLE", 0))
        )
        self.cards["old"].set(
            str(counts.get("POSIBLEMENTE DESACTUALIZADO", 0))
        )
        self.cards["errors"].set(str(len(errors)))

        self._build_priority_groups(devices)
        self._populate_tree()

        summary = data.get("summary", {})
        self.status_var.set(
            f"Análisis terminado. {len(self.priority_groups)} "
            f"grupo(s) prioritario(s). "
            f"Windows Update: {summary.get('driver_updates', len(updates))}."
        )

    def _build_priority_groups(self, devices):
        priority = [
            d for d in devices
            if d.get("DriverStatus") in (
                "ACTUALIZACIÓN DISPONIBLE",
                "POSIBLEMENTE DESACTUALIZADO",
            )
        ]

        groups = {}
        for device in priority:
            key = device.get("DriverGroupKey")
            if not key:
                key = "|".join((
                    str(device.get("Manufacturer") or "").strip().lower(),
                    str(device.get("DriverProviderName") or "").strip().lower(),
                    str(device.get("DriverVersion") or "").strip().lower(),
                    str(device.get("InfName") or "").strip().lower(),
                ))
            groups.setdefault(key, []).append(device)

        self.priority_groups = list(groups.values())

    def _populate_tree(self):
        self._clear_tree(reset_groups=False)

        for index, members in enumerate(self.priority_groups):
            d = members[0]
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    d.get("DeviceName")
                    or d.get("FriendlyName")
                    or "Desconocido",
                    d.get("Manufacturer") or "Desconocido",
                    d.get("DriverVersion") or "Desconocida",
                    d.get("DriverDateNormalized") or "Desconocida",
                    d.get("DriverStatus") or "SIN INFORMACIÓN",
                )
            )

    def _clear_tree(self, reset_groups=True):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if reset_groups:
            self.priority_groups = []

    def _set_detail(self, text):
        self.detail.config(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", text)
        self.detail.config(state="disabled")

    def _selected_group(self):
        selection = self.tree.selection()
        if not selection:
            return None
        index = int(selection[0])
        if 0 <= index < len(self.priority_groups):
            return self.priority_groups[index]
        return None

    def show_selected(self, _event=None):
        group = self._selected_group()
        if not group:
            self.btn_install.config(state="disabled")
            self.btn_source.config(state="disabled")
            return

        d = group[0]
        lines = [
            d.get("DeviceName") or d.get("FriendlyName") or "Desconocido",
            "=" * 60,
            f"Dispositivos asociados : {len(group)}",
            f"Fabricante             : {d.get('Manufacturer') or 'Desconocido'}",
            f"Proveedor              : {d.get('DriverProviderName') or 'Desconocido'}",
            f"Versión instalada      : {d.get('DriverVersion') or 'Desconocida'}",
            f"Fecha                  : {d.get('DriverDateNormalized') or 'Desconocida'}",
            f"Estado                 : {d.get('DriverStatus') or 'SIN INFORMACIÓN'}",
            f"Evidencia              : {d.get('Evidence') or 'SIN_DATOS'}",
            f"Confianza              : {d.get('Confidence') or 'BAJA'}",
            f"Revisión requerida     : {d.get('ReviewRequired') or 'SÍ'}",
            f"Motivo                 : {d.get('DriverStatusReason') or 'Sin información'}",
        ]

        if d.get("DriverAgeDays") is not None:
            lines.append(f"Antigüedad             : {d.get('DriverAgeDays')} días")

        if d.get("WindowsUpdateVersion"):
            lines.append(
                f"Windows Update ofrece  : {d.get('WindowsUpdateVersion')}"
            )

        if d.get("OfficialSource"):
            lines.append(
                f"Fuente oficial         : {d.get('OfficialSource')}"
            )
        if d.get("OfficialSourceURL"):
            lines.append(
                f"URL                    : {d.get('OfficialSourceURL')}"
            )

        if len(group) > 1:
            lines.append("")
            lines.append("Dispositivos asociados:")
            for member in group:
                lines.append(
                    f"  - {member.get('DeviceName') or member.get('FriendlyName') or 'Desconocido'}"
                )

        self._set_detail("\n".join(lines))

        has_update = any(
            d2.get("DriverStatus") == "ACTUALIZACIÓN DISPONIBLE"
            for d2 in group
        )
        self.btn_install.config(
            state="normal" if has_update else "disabled"
        )
        self.btn_source.config(
            state="normal" if d.get("OfficialSourceURL") else "disabled"
        )

    def open_source(self):
        group = self._selected_group()
        if not group:
            return
        url = group[0].get("OfficialSourceURL")
        if url:
            webbrowser.open(url)

    def install_selected(self):
        group = self._selected_group()
        if not group:
            return

        updates = self.data.get("driver_updates", [])
        candidates = []

        for update in updates:
            instance_id = update.get("InstanceId")
            for device in group:
                if instance_id and instance_id == device.get("DeviceID"):
                    candidates.append(update)
                    break

        if not candidates:
            messagebox.showwarning(
                "DriverUpdater",
                "No se encontró una actualización de Windows Update "
                "asociada al controlador seleccionado."
            )
            return

        selected = candidates[0]
        title = selected.get("Title", "Actualización de controlador")

        confirm = messagebox.askyesno(
            "Confirmar instalación",
            f"Se instalará mediante Windows Update:\n\n"
            f"{title}\n\n"
            "La operación utilizará las comprobaciones de seguridad "
            "de DriverUpdater.\n\n¿Deseas continuar?"
        )
        if not confirm:
            return

        if not is_admin():
            messagebox.showerror(
                "Permisos",
                "DriverUpdater debe ejecutarse como administrador "
                "para instalar el controlador."
            )
            return

        self.btn_scan.config(state="disabled")
        self.btn_install.config(state="disabled")
        self.btn_source.config(state="disabled")
        self.progress.start(12)
        self.status_var.set("Instalando y verificando el controlador...")

        threading.Thread(
            target=self._install_worker,
            args=(selected,),
            daemon=True
        ).start()

    def _install_worker(self, selected):
        try:
            result = update_driver(
                selected.get("UpdateID"),
                create_restore=True,
                instance_id=selected.get("InstanceId"),
                expected_version=selected.get("DriverVersion"),
            )

            try:
                report_paths = create_reports(self.data, result)
                log_path = create_update_log(result)
            except Exception:
                report_paths = []
                log_path = None

            self.after(
                0,
                lambda: self._install_finished(
                    result, report_paths, log_path
                )
            )
        except Exception as exc:
            self.after(
                0,
                lambda: self._install_failed(str(exc))
            )

    def _install_failed(self, error):
        self.progress.stop()
        self.btn_scan.config(state="normal")
        self.status_var.set("Error durante la instalación.")
        messagebox.showerror(
            "DriverUpdater",
            f"La instalación produjo un error:\n\n{error}"
        )

    def _install_finished(self, result, report_paths, log_path):
        self.progress.stop()
        self.progress["value"] = 0
        self.btn_scan.config(state="normal")
        self.current_result = result

        success = bool(result.get("success"))
        verification = result.get("verification", {})
        before = result.get("before", {})
        after = result.get("after", {})

        text = (
            f"Resultado: {'COMPLETADA' if success else 'NO COMPLETADA'}\n\n"
            f"Versión antes: {before.get('DriverVersion', 'Desconocida')}\n"
            f"Versión después: {after.get('DriverVersion', 'Desconocida')}\n"
            f"Verificación: {verification.get('status', 'NO DISPONIBLE')}\n"
            f"ProblemCode: {verification.get('problem_code', 'Desconocido')}\n"
            f"Reinicio: {'NECESARIO' if result.get('reboot_required') else 'No indicado'}\n"
        )

        if result.get("error"):
            text += f"\nDetalle: {result.get('error')}\n"

        if report_paths:
            text += "\nReportes:\n" + "\n".join(report_paths)
        if log_path:
            text += f"\n\nRegistro:\n{log_path}"

        self._set_detail(text)
        self.status_var.set(
            "Instalación completada y verificada."
            if success else
            "La actualización no se considera completada."
        )

        messagebox.showinfo(
            "DriverUpdater",
            "Proceso terminado.\n\n"
            + ("La actualización se considera completada."
               if success else
               "La actualización NO se considera completada.")
        )

        self.start_scan()


    def show_about(self):
        messagebox.showinfo(
            "Acerca de DriverUpdater",
            "DriverUpdater V3.8.3 "
            "Programado por Facundo Pérez 2026"
        )


def main():
    app = DriverUpdaterGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
