import subprocess
import sys

NETWORK_NAME = "zona6_red"
SUBNET = "10.3.0.0/24"

def run(cmd):
    print(f"[+] Ejecutando: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def create_network():
    try:
        run(f"docker network create --subnet={SUBNET} {NETWORK_NAME}")
        print("[+] Red creada correctamente")
    except subprocess.CalledProcessError:
        print("[!] La red ya existe o hubo un error")

def delete_network():
    try:
        run(f"docker network rm {NETWORK_NAME}")
        print("[+] Red eliminada correctamente")
    except subprocess.CalledProcessError:
        print("[!] No se pudo eliminar (¿contenedores aún activos?)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python3 network.py up     -> crear red")
        print("  python3 network.py down   -> eliminar red")
        sys.exit(1)

    if sys.argv[1] == "up":
        create_network()
    elif sys.argv[1] == "down":
        delete_network()
    else:
        print("Opción inválida")