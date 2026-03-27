import subprocess

def run(cmd):
    print(f"[+] Ejecutando: {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[-] Error: {e}")