#!/usr/bin/env python3
"""
metasploitable_min.py
Minimo: instala Docker (si falta) y levanta Metasploitable2 en un contenedor.
Uso:   sudo python3 metasploitable_min.py
"""

import os
import shutil
import subprocess
import sys
import time

IMAGE = "tleemcjr/metasploitable2"
NAME = "metasploitable2"
START_CMD = ["sh", "-c", "/bin/services.sh && tail -f /dev/null"]


def sh(cmd, check=True):
    print(f"[*] $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)


def have(binname):
    return shutil.which(binname) is not None


def main():
    # 1. Requisitos basicos
    if sys.platform != "linux":
        sys.exit("[-] Ejecutalo dentro de tu VM Kali (Linux).")
    if not (hasattr(os, "geteuid") and os.geteuid() == 0):
        sys.exit("[-] Necesita root:  sudo python3 metasploitable_min.py")

    # 2. Instalar Docker si no esta
    if not have("docker"):
        print("[*] Docker no encontrado. Instalando...")
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"
        subprocess.run(["apt-get", "update", "-y"], check=True, env=env)
        subprocess.run(["apt-get", "install", "-y", "docker.io"], check=True, env=env)
    else:
        print("[+] Docker ya instalado.")

    # 3. Arrancar el servicio Docker
    subprocess.run(["systemctl", "enable", "--now", "docker"], check=False)
    for _ in range(10):
        if subprocess.run(["docker", "info"],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0:
            break
        time.sleep(2)

    # 4. Descargar la imagen
    sh(["docker", "pull", IMAGE])

    # 5. Levantar el contenedor (o reiniciarlo si ya existe)
    existing = subprocess.run(
        ["docker", "ps", "-aq", "-f", f"name=^{NAME}$"],
        capture_output=True, text=True).stdout.strip()
    if existing:
        print("[*] Contenedor ya existe, arrancandolo...")
        sh(["docker", "start", NAME])
    else:
        sh(["docker", "run", "-d", "--name", NAME,
            "--restart", "unless-stopped", IMAGE] + START_CMD)

    time.sleep(5)

    # 6. Mostrar la IP del objetivo
    ip = subprocess.run(
        ["docker", "inspect", "-f",
         "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", NAME],
        capture_output=True, text=True).stdout.strip()

    print("\n" + "=" * 50)
    print("  Metasploitable2 LEVANTADO")
    print(f"  IP objetivo (RHOSTS): {ip}")
    print("=" * 50)


if __name__ == "__main__":
    main()