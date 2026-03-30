import os
import socket
import time
import subprocess
import sys
import urllib.request
from pathlib import Path

def ejecutar(comando, descripcion, ignorar_error=False):
    """Función auxiliar para ejecutar comandos y manejar errores."""
    print(f"[*] {descripcion}...")
    try:
        subprocess.run(comando, shell=True, check=True, capture_output=True, text=True, executable='/bin/bash')
        print(f"    [OK]")
        return True
    except subprocess.CalledProcessError as e:
        if not ignorar_error:
            print(f"    [ERROR] {e.stderr.strip()}")
        else:
            print(f"    [Aviso] Comando devolvió error pero se continúa: {e.stderr.strip()}")
        return False

def instalar_dependencias():
    if subprocess.run("command -v docker", shell=True, capture_output=True).returncode != 0:
        ejecutar("apt-get update && apt-get install -y docker.io docker-compose curl", "Instalando dependencias (Docker, Docker-Compose, Curl)")
        ejecutar("systemctl enable --now docker", "Habilitando Docker en el arranque")
        print("[*] Esperando a que el demonio de Docker esté listo...")
        time.sleep(3)
    else:
        print("[*] Docker ya se encuentra instalado. [OK]")

# --- CONFIGURACIÓN DE RED ZONA 4 ---
NETWORK_NAME = "zona4_integracion"
SUBNET = "10.2.4.0/24"

IPS = {
    "API_GATEWAY": "10.2.4.10",
    "REDIS": "10.2.4.20",
    "RABBITMQ": "10.2.4.21",
    "CRAPI_WEB": "10.2.4.30"
}

def configurar_red():
    """Crea la subred Docker para la Zona 4."""
    ejecutar(f"docker network create --subnet={SUBNET} {NETWORK_NAME}", f"Creando subred de la Zona 4 ({SUBNET})", ignorar_error=True)

def testear_servicios():
    print(f"\n=== Testeando Estado en Red {SUBNET} ===")
    servicios = {
        "API Gateway (NGINX)": (IPS["API_GATEWAY"], 80),
        "Redis (Cache)": (IPS["REDIS"], 6379),
        "RabbitMQ (Mensajería)": (IPS["RABBITMQ"], 5672),
        "crAPI (Web UI)": (IPS["CRAPI_WEB"], 80)
    }
    
    todos_ok = True
    for nombre, (ip, puerto) in servicios.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        resultado = sock.connect_ex((ip, puerto))
        if resultado == 0:
            print(f"  [🟢 UP]   {nombre} respondiendo en {ip}:{puerto}")
        else:
            print(f"  [🔴 DOWN] {nombre} NO responde en {ip}:{puerto}")
            todos_ok = False
        sock.close()
    print("=========================================")

# --- Despliegue de Servicios ---
def desplegar_aplicaciones():
    base_dir = Path.home() / "laboratorio_equipoB" / "zona4"
    base_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(base_dir)

    ejecutar("docker rm -f api_gateway_zona4 redis_zona4 rabbitmq_zona4", "Limpiando contenedores previos de Zona 4", ignorar_error=True)

    # 1. Generar configuración de NGINX con CORS y Rate Limiting
    nginx_conf_path = base_dir / "nginx.conf"
    nginx_conf_content = f"""
worker_processes 1;
events {{ worker_connections 1024; }}
http {{
    limit_req_zone $binary_remote_addr zone=limite_api:10m rate=10r/s;
    server {{
        listen 80;
        server_name localhost;
        location / {{
            limit_req zone=limite_api burst=20 nodelay;
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
            add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;
            proxy_pass http://{IPS['CRAPI_WEB']}:80;
        }}
    }}
}}
"""
    with open(nginx_conf_path, "w") as f:
        f.write(nginx_conf_content)
    print(f"[*] Archivo NGINX generado en: {nginx_conf_path}")

    # 2. Desplegar API Gateway (NGINX)
    comando_nginx = f"docker run -d --name api_gateway_zona4 --network {NETWORK_NAME} --ip {IPS['API_GATEWAY']} -p 80:80 -v {nginx_conf_path}:/etc/nginx/nginx.conf:ro nginx"
    ejecutar(comando_nginx, f"Desplegando API Gateway en {IPS['API_GATEWAY']}")

    # 3. Desplegar Redis y RabbitMQ
    ejecutar(f"docker run -d --name redis_zona4 --network {NETWORK_NAME} --ip {IPS['REDIS']} redis", f"Desplegando Redis en {IPS['REDIS']}")
    ejecutar(f"docker run -d --name rabbitmq_zona4 --network {NETWORK_NAME} --ip {IPS['RABBITMQ']} -p 15672:15672 rabbitmq:3-management", f"Desplegando RabbitMQ en {IPS['RABBITMQ']}")

    # 4. Desplegar crAPI
    print("[*] Descargando docker-compose de crAPI...")
    crapi_url = "https://raw.githubusercontent.com/OWASP/crAPI/main/deploy/docker/docker-compose.yml"
    urllib.request.urlretrieve(crapi_url, "docker-compose.yml")
    
    ejecutar("docker-compose up -d", "Levantando entorno completo de crAPI")

    # 5. Conectar crAPI a la red de Zona 4
    print("[*] Esperando a que crAPI inicie para conectar la red...")
    time.sleep(5)
    ejecutar(f"docker network connect --ip {IPS['CRAPI_WEB']} {NETWORK_NAME} crapi-web", f"Conectando crAPI a la red {NETWORK_NAME} en {IPS['CRAPI_WEB']}", ignorar_error=True)

# --- Documentar Esquema ---
def generar_documentacion():
    path = Path.home() / "laboratorio_equipoB" / "zona4" / "infraestructura_reporte_zona4.txt"
    contenido = f"""
=========================================
REPORTE DE INFRAESTRUCTURA: ZONA 4 INTEGRACIÓN
Segmento IP: {SUBNET}
=========================================
Servicio               | Estado     | Dirección IP Docker
---------------------------------------------------------
API Gateway (NGINX)    | Docker     | {IPS['API_GATEWAY']}:80
Redis (Caché)          | Docker     | {IPS['REDIS']}:6379
RabbitMQ (Mensajería)  | Docker     | {IPS['RABBITMQ']}:5672
crAPI (Web UI)         | Docker     | {IPS['CRAPI_WEB']}:80
---------------------------------------------------------
ESTRATEGIA DE DESPLIEGUE:
- NGINX actúa como proxy reverso con políticas de CORS y Rate Limiting (10 req/s).
- crAPI opera nativamente en su propia red de compose, pero se le adjunta 
  la IP {IPS['CRAPI_WEB']} en la red '{NETWORK_NAME}' para integración.
"""
    with open(path, "w") as f:
        f.write(contenido)
    print(f"[+] Documentación generada en: {path}")

def levantar_servicios():
    print("\n=== Levantando Infraestructura Zona 4 ===")
    instalar_dependencias()
    configurar_red()
    desplegar_aplicaciones()
    generar_documentacion()
    print("[✔] Proceso de despliegue de la Zona 4 finalizado.")

def botar_servicios():
    print("\n=== Botando Infraestructura Zona 4 ===")
    base_dir = Path.home() / "laboratorio_equipoB" / "zona4"
    
    # Detener crAPI si existe el docker-compose
    if (base_dir / "docker-compose.yml").exists():
        os.chdir(base_dir)
        ejecutar("docker-compose down", "Deteniendo contenedores de crAPI", ignorar_error=True)
        
    ejecutar("docker rm -f api_gateway_zona4 redis_zona4 rabbitmq_zona4", "Deteniendo API Gateway, Redis y RabbitMQ", ignorar_error=True)
    ejecutar(f"docker network rm {NETWORK_NAME}", "Eliminando red virtual de la Zona 4", ignorar_error=True)
    print("[✔] Todos los servicios han sido detenidos limpiamente.")

def main():
    while True:
        print("\n=== Gestor de Despliegue - Zona 4 (Integración) ===")
        print("1) Levantar todos los servicios")
        print("2) Botar todos los servicios")
        print("3) Testear estado de los servicios")
        print("4) Salir")
        
        try:
            opcion = input("Selecciona una opción (1-4): ").strip()
        except KeyboardInterrupt:
            print("\n[!] Operación cancelada por el usuario. Saliendo limpiamente...")
            sys.exit(0)
        
        if opcion == '1':
            levantar_servicios()
        elif opcion == '2':
            botar_servicios()
        elif opcion == '3':
            testear_servicios()
        elif opcion == '4':
            print("Saliendo del gestor...")
            break
        else:
            print("[!] Opción no válida. Por favor, ingresa 1, 2, 3 o 4.")

if __name__ == "__main__":
    main()
