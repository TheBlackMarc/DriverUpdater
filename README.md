# DriverUpdater

Herramienta para Windows que detecta, analiza y ayuda a actualizar los controladores (drivers) del sistema, priorizando la seguridad: crea un punto de restauración antes de instalar cualquier actualización y verifica el estado del dispositivo después de instalarla.

## Características

- Escaneo de dispositivos y controladores del sistema.
- Detección de controladores con actualización disponible mediante Windows Update.
- Agrupación de dispositivos que comparten el mismo controlador (evita duplicados en la vista).
- Detección de errores de dispositivos (Device Manager).
- Identificación de fuentes oficiales del fabricante cuando es posible.
- Creación de un punto de restauración del sistema antes de instalar un controlador.
- Verificación posterior a la instalación (versión, estado del dispositivo, código de error).
- Generación de reportes en `.txt` y `.json`, además de un registro detallado de cada actualización.
- Interfaz gráfica (Tkinter) y también una versión por consola.

## Requisitos

- Windows 10/11.
- Python 3.10 o superior (solo si vas a ejecutar el código fuente o compilarlo vos mismo).
- Permisos de administrador para instalar controladores.

## Uso desde el código fuente

```bash
python main_gui.py    # Interfaz gráfica
python main.py         # Versión por consola
```

## Compilar a ejecutable (.exe)

El proyecto incluye `build_exe.bat`, que genera un `.exe` de un solo archivo, sin ventana de consola y con ícono personalizado.

1. Colocá tu ícono en la misma carpeta con el nombre `icono.ico`.
2. Ejecutá `build_exe.bat`.
3. El ejecutable final queda en `dist\DriverUpdater.exe`.

El script instala PyInstaller automáticamente si no lo tenés instalado.

## Reportes

Los reportes y registros generados por la aplicación se guardan en:

```
C:\Users\<usuario>\Documents\DriverUpdater\reports\
```

## Aviso importante

Este programa modifica controladores del sistema, lo cual conlleva riesgos inherentes (incompatibilidades, fallos de dispositivos, necesidad de reinicio, etc.). Se recomienda:

- Ejecutarlo siempre como administrador.
- Revisar que el punto de restauración se haya creado correctamente antes de continuar.
- No interrumpir el proceso de instalación.

El autor no se hace responsable por daños derivados del uso de esta herramienta. Se distribuye "tal cual" ("as is"), sin garantía de ningún tipo, según los términos de la licencia incluida.

## Licencia

Este proyecto está bajo la licencia **GPLv3**. Ver el archivo [LICENSE](LICENSE) para más información.

## Autor

Programado por Facundo Pérez, 2026.
