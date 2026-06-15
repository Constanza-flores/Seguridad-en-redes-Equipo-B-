#!/usr/bin/env python3
"""
juiceshop_lab.py
================
Script reproducible para montar un laboratorio de OWASP Juice Shop sobre Docker.
Pensado para ejecutarse en una maquina virtual Kali Linux (Debian-based).

OWASP Juice Shop es una aplicacion web *deliberadamente vulnerable*, mantenida
por OWASP con fines educativos. Este script automatiza:

  1. Verificar/instalar Docker.
  2. Habilitar y arrancar el servicio Docker.
  3. Descargar (pull) la imagen oficial de Juice Shop.
  4. Levantar el contenedor exponiendo el puerto 3000.
  5. Esperar a que la app responda y mostrar la URL.

USO TIPICO (dentro de la VM Kali):

    sudo python3 juiceshop_lab.py up        # instala todo y levanta la app
    python3 juiceshop_lab.py status         # ver estado del contenedor
    python3 juiceshop_lab.py logs           # ver logs de la app
    python3 juiceshop_lab.py down           # detener y borrar el contenedor
    python3 juiceshop_lab.py reset          # borrar contenedor y volver a levantar (estado limpio)

Despues de 'up', abre en el navegador de Kali:  http://localhost:3000

AVISO LEGAL/ETICO: Juice Shop esta hecho para practicar de forma segura en TU
propio entorno aislado. Solo atacalo en esta VM local. No uses estas tecnicas
contra sistemas que no te pertenezcan o sin autorizacion explicita.
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request

# ----------------------------- Configuracion -------------------------------- #

IMAGE = "bkimminich/juice-shop"      # imagen oficial de OWASP Juice Shop
CONTAINER_NAME = "juice-shop"        # nombre del contenedor para reconocerlo
HOST_PORT = 3000                     # puerto en la VM (host)
CONTAINER_PORT = 3000                # puerto dentro del contenedor
URL = f"http://localhost:{HOST_PORT}"
HEALTHCHECK_TIMEOUT = 120            # segundos a esperar a que la app responda


# ----------------------------- Utilidades ----------------------------------- #

class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def info(msg):
    print(f"{Colors.BLUE}[*]{Colors.END} {msg}")


def ok(msg):
    print(f"{Colors.GREEN}[+]{Colors.END} {msg}")


def warn(msg):
    print(f"{Colors.YELLOW}[!]{Colors.END} {msg}")


def err(msg):
    print(f"{Colors.RED}[-]{Colors.END} {msg}")


def run(cmd, check=True, capture=False, quiet=False):
    """Ejecuta un comando del sistema. Devuelve el CompletedProcess."""
    if not quiet:
        info(f"$ {' '.join(cmd)}")
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )


def command_exists(name):
    """True si un binario existe en el PATH."""
    return shutil.which(name) is not None


def is_root():
    return hasattr(os, "geteuid") and os.geteuid() == 0


def require_linux():
    if platform.system() != "Linux":
        err("Este script esta pensado para Kali Linux (Linux).")
        err(f"Sistema detectado: {platform.system()}.")
        err("Ejecutalo dentro de tu maquina virtual Kali.")
        sys.exit(1)


def require_root_for_install():
    """Instalar paquetes y manejar systemd requiere privilegios de root."""
    if not is_root():
        err("Esta operacion necesita privilegios de root.")
        err("Vuelve a ejecutar con sudo, por ejemplo:")
        err(f"    sudo python3 {os.path.basename(__file__)} up")
        sys.exit(1)


# --------------------------- Logica de Docker -------------------------------- #

def docker_installed():
    return command_exists("docker")


def install_docker():
    """Instala Docker en Kali/Debian via apt (paquete docker.io)."""
    info("Docker no esta instalado. Procediendo a instalarlo via apt...")
    require_root_for_install()

    # Actualizar indices de paquetes e instalar docker.io (en repos de Kali/Debian).
    env = os.environ.copy()
    env["DEBIAN_FRONTEND"] = "noninteractive"

    info("Actualizando indices de apt...")
    subprocess.run(["apt-get", "update", "-y"], check=True, env=env)

    info("Instalando docker.io ...")
    subprocess.run(
        ["apt-get", "install", "-y", "docker.io"],
        check=True,
        env=env,
    )

    if not docker_installed():
        err("La instalacion de Docker no se completo correctamente.")
        sys.exit(1)
    ok("Docker instalado correctamente.")


def ensure_docker_service():
    """Habilita y arranca el servicio Docker (systemd)."""
    # En Kali, systemd gestiona el servicio docker.
    if command_exists("systemctl"):
        info("Habilitando y arrancando el servicio Docker (systemd)...")
        subprocess.run(["systemctl", "enable", "docker"], check=False)
        subprocess.run(["systemctl", "start", "docker"], check=False)

    # Verificar que el daemon responde.
    for _ in range(10):
        result = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode == 0:
            ok("El daemon de Docker esta activo.")
            return
        time.sleep(2)

    # Intento alternativo si no hay systemd (poco comun en Kali).
    if command_exists("service"):
        subprocess.run(["service", "docker", "start"], check=False)
        time.sleep(3)
        result = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode == 0:
            ok("El daemon de Docker esta activo.")
            return

    err("No se pudo conectar con el daemon de Docker.")
    err("Prueba manualmente: sudo systemctl start docker")
    sys.exit(1)


def container_exists():
    """True si existe un contenedor con nuestro nombre (corriendo o detenido)."""
    result = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name=^{CONTAINER_NAME}$",
         "--format", "{{.Names}}"],
        capture_output=True, text=True,
    )
    return CONTAINER_NAME in result.stdout.split()


def container_running():
    result = subprocess.run(
        ["docker", "ps", "--filter", f"name=^{CONTAINER_NAME}$",
         "--format", "{{.Names}}"],
        capture_output=True, text=True,
    )
    return CONTAINER_NAME in result.stdout.split()


def pull_image():
    info(f"Descargando la imagen {IMAGE} (puede tardar la primera vez)...")
    subprocess.run(["docker", "pull", IMAGE], check=True)
    ok("Imagen lista.")


def start_container():
    """Levanta el contenedor de Juice Shop. Maneja el caso de uno ya existente."""
    if container_running():
        ok(f"El contenedor '{CONTAINER_NAME}' ya esta corriendo.")
        return

    if container_exists():
        info(f"Reiniciando contenedor existente '{CONTAINER_NAME}'...")
        subprocess.run(["docker", "start", CONTAINER_NAME], check=True)
        ok("Contenedor reiniciado.")
        return

    info("Creando y levantando un nuevo contenedor de Juice Shop...")
    subprocess.run(
        [
            "docker", "run", "-d",
            "--name", CONTAINER_NAME,
            "-p", f"{HOST_PORT}:{CONTAINER_PORT}",
            "--restart", "unless-stopped",
            IMAGE,
        ],
        check=True,
    )
    ok("Contenedor creado.")


def wait_until_up():
    """Hace polling a la URL hasta que Juice Shop responda 200."""
    info(f"Esperando a que Juice Shop responda en {URL} ...")
    deadline = time.time() + HEALTHCHECK_TIMEOUT
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(URL, timeout=3) as resp:
                if resp.status == 200:
                    ok("Juice Shop esta operativo.")
                    return True
        except Exception:
            pass
        time.sleep(3)
        print("    ... aun arrancando", end="\r")
    warn("Se agoto el tiempo de espera, pero el contenedor puede seguir iniciando.")
    warn(f"Revisa los logs con:  python3 {os.path.basename(__file__)} logs")
    return False


def print_banner():
    print()
    print(f"{Colors.BOLD}{Colors.GREEN}" + "=" * 60 + f"{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}  OWASP Juice Shop esta listo para la practica{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}" + "=" * 60 + f"{Colors.END}")
    print()
    print(f"  URL de la aplicacion : {Colors.BOLD}{URL}{Colors.END}")
    print(f"  Contenedor           : {CONTAINER_NAME}")
    print(f"  Imagen               : {IMAGE}")
    print()
    print("  Pistas para la tarea:")
    print(f"    - Panel de puntuacion (retos): {URL}/#/score-board")
    print("    - Documentacion oficial: https://pwning.owasp-juice.shop/")
    print("    - Herramientas en Kali: Burp Suite, OWASP ZAP, sqlmap, curl, nikto")
    print()
    print("  Comandos utiles:")
    print(f"    python3 {os.path.basename(__file__)} status   # estado")
    print(f"    python3 {os.path.basename(__file__)} logs     # logs")
    print(f"    python3 {os.path.basename(__file__)} down     # detener")
    print()


# ------------------------------ Subcomandos ---------------------------------- #

def cmd_up(args):
    require_linux()

    if not docker_installed():
        install_docker()
    else:
        ok("Docker ya esta instalado.")

    ensure_docker_service()
    pull_image()
    start_container()
    wait_until_up()
    print_banner()


def cmd_down(args):
    require_linux()
    if not docker_installed():
        err("Docker no esta instalado; no hay nada que detener.")
        return
    if container_exists():
        info(f"Deteniendo y borrando el contenedor '{CONTAINER_NAME}'...")
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], check=False)
        ok("Contenedor detenido y eliminado.")
    else:
        warn(f"No existe el contenedor '{CONTAINER_NAME}'.")


def cmd_status(args):
    require_linux()
    if not docker_installed():
        err("Docker no esta instalado.")
        return
    print()
    subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name=^{CONTAINER_NAME}$"],
        check=False,
    )
    print()
    if container_running():
        ok(f"Juice Shop esta corriendo en {URL}")
    elif container_exists():
        warn("El contenedor existe pero esta detenido. Usa 'up' para levantarlo.")
    else:
        warn("No hay contenedor de Juice Shop. Usa 'up' para crearlo.")


def cmd_logs(args):
    require_linux()
    if not container_exists():
        err(f"No existe el contenedor '{CONTAINER_NAME}'.")
        return
    info("Mostrando logs (Ctrl+C para salir)...")
    try:
        subprocess.run(["docker", "logs", "-f", "--tail", "100", CONTAINER_NAME])
    except KeyboardInterrupt:
        print()


def cmd_reset(args):
    """Borra el contenedor (estado limpio de la app) y lo vuelve a levantar."""
    require_linux()
    info("Reiniciando el laboratorio a un estado limpio...")
    cmd_down(args)
    start_container()
    wait_until_up()
    print_banner()


# ------------------------------- Entrada ------------------------------------- #

def build_parser():
    parser = argparse.ArgumentParser(
        description="Laboratorio reproducible de OWASP Juice Shop sobre Docker (Kali Linux).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Ejemplo:  sudo python3 juiceshop_lab.py up",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("up", help="Instala Docker (si falta) y levanta Juice Shop.")
    sub.add_parser("down", help="Detiene y elimina el contenedor.")
    sub.add_parser("status", help="Muestra el estado del contenedor.")
    sub.add_parser("logs", help="Muestra los logs de la app.")
    sub.add_parser("reset", help="Borra el contenedor y vuelve a levantarlo (estado limpio).")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Sin subcomando: por defecto 'up'.
    command = args.command or "up"

    handlers = {
        "up": cmd_up,
        "down": cmd_down,
        "status": cmd_status,
        "logs": cmd_logs,
        "reset": cmd_reset,
    }

    try:
        handlers[command](args)
    except subprocess.CalledProcessError as e:
        err(f"Fallo un comando del sistema (codigo {e.returncode}).")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print()
        warn("Interrumpido por el usuario.")
        sys.exit(130)


if __name__ == "__main__":
    main()
