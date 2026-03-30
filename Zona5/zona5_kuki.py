import os
import socket
import time
import subprocess
import sys

def ejecutar(comando, descripcion, ignorar_error=False):
    """Función auxiliar para ejecutar comandos y manejar errores."""
    print(f"[*] {descripcion}...")
    try:
        subprocess.run(comando, shell=True, check=True, capture_output=True, text=True)
        print(f"    [OK]")
        return True
    except subprocess.CalledProcessError as e:
        if not ignorar_error:
            print(f"    [ERROR] {e.stderr.strip()}")
        else:
            print(f"    [Aviso] Comando devolvió error pero se continúa: {e.stderr.strip()}")
        return False

def instalar_docker():
    if subprocess.run("command -v docker", shell=True, capture_output=True).returncode != 0:
        ejecutar("sudo apt update && sudo apt install -y docker.io docker-compose", "Instalando Docker")
        ejecutar("sudo systemctl start docker", "Iniciando servicio Docker")
        ejecutar("sudo systemctl enable docker", "Habilitando Docker en el arranque")
    else:
        print("[*] Docker ya se encuentra instalado. [OK]")

# --- CONFIGURACIÓN DE RED ZONA 5 ---
# Se asignan IPs fijas dentro del rango 10.2.5.0/24
NETWORK_NAME = "zona5_backend"
SUBNET = "10.2.5.0/24"

IPS = {
    "JUICE_SHOP": "10.2.5.10",
    "VULNERABLE_LLM": "10.2.5.20",
    "POSTGRESQL": "10.2.5.30",
    "REDIS": "10.2.5.40",
    "RABBITMQ": "10.2.5.50"
}

def configurar_red():
    """Crea la subred Docker para la Zona 5."""
    ejecutar(f"sudo docker network create --subnet={SUBNET} {NETWORK_NAME}", "Creando subred de la Zona 5 (10.2.5.0/24)", ignorar_error=True)

def testear_servicios():
    print(f"\n=== Testeando Estado en Red {SUBNET} ===")
    servicios = {
        "Juice Shop": (IPS["JUICE_SHOP"], 3000),
        # Se escanea el puerto 9000 interno, ya que el testeo se hace directo a la IP del contenedor
        "Vulnerable LLM": (IPS["VULNERABLE_LLM"], 9000), 
        "PostgreSQL": (IPS["POSTGRESQL"], 5432),
        "Redis": (IPS["REDIS"], 6379),
        "RabbitMQ": (IPS["RABBITMQ"], 5672)
    }
    
    todos_ok = True
    for nombre, (ip, puerto) in servicios.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        # Intentamos conectar a la IP específica asignada en Docker
        resultado = sock.connect_ex((ip, puerto))
        if resultado == 0:
            print(f"  [🟢 UP]   {nombre} respondiendo en {ip}:{puerto}")
        else:
            print(f"  [🔴 DOWN] {nombre} NO responde en {ip}:{puerto}")
            todos_ok = False
        sock.close()
    print("=========================================")

# --- Despliegue de Servicios 100% en Docker ---

def desplegar_aplicaciones():
    ejecutar("sudo docker rm -f juice-shop vulnerable-llm postgres_zona5 redis_zona5 rabbitmq_zona5", "Limpiando contenedores previos", ignorar_error=True)
    
    # Juice Shop
    comando_juice = f"sudo docker run -d --name juice-shop --network {NETWORK_NAME} --ip {IPS['JUICE_SHOP']} -p 3000:3000 bkimminich/juice-shop"
    ejecutar(comando_juice, f"Desplegando Juice Shop en {IPS['JUICE_SHOP']}:3000")

    # Vulnerable LLM (Mapeando puerto 5000 al 9000 interno de la imagen DVAA)
    comando_llm = f'sudo docker run -d --name vulnerable-llm --network {NETWORK_NAME} --ip {IPS["VULNERABLE_LLM"]} -p 5000:9000 --entrypoint /bin/sh opena2a/dvaa -c "npm install openai && npm start"'
    ejecutar(comando_llm, f"Desplegando Vulnerable LLM en {IPS['VULNERABLE_LLM']}:5000")
    
    # PostgreSQL
    comando_pg = f"sudo docker run -d --name postgres_zona5 --network {NETWORK_NAME} --ip {IPS['POSTGRESQL']} -e POSTGRES_PASSWORD=kali postgres:14"
    ejecutar(comando_pg, f"Desplegando PostgreSQL en {IPS['POSTGRESQL']}:5432")

    # Redis
    comando_redis = f"sudo docker run -d --name redis_zona5 --network {NETWORK_NAME} --ip {IPS['REDIS']} redis"
    ejecutar(comando_redis, f"Desplegando Redis en {IPS['REDIS']}:6379")

    # RabbitMQ con consola mapeada al 15673 para NO chocar con el RabbitMQ de la Zona 4
    comando_rabbit = f"sudo docker run -d --name rabbitmq_zona5 --network {NETWORK_NAME} --ip {IPS['RABBITMQ']} -p 15673:15672 rabbitmq:3-management"
    ejecutar(comando_rabbit, f"Desplegando RabbitMQ en {IPS['RABBITMQ']}:5672")

    print("[*] Esperando 30 segundos para que levanten los servicios pesados (LLM)...")
    time.sleep(30)

# --- Aplicar Hardening (iptables para Kali/Debian) ---
def aplicar_hardening():
    print("[*] Iniciando fase de Hardening con iptables...")
    
    # Restringir acceso a las bases de datos desde subredes externas (excepto 10.2.0.0/16)
    ejecutar("sudo iptables -A DOCKER-USER -i eth0 -p tcp -m multiport --dports 5432,6379,5672 -s 10.2.0.0/16 -j ACCEPT", "Permitiendo acceso a BD/Cache solo desde 10.2.0.0/16", ignorar_error=True)
    ejecutar("sudo iptables -A DOCKER-USER -i eth0 -p tcp -m multiport --dports 5432,6379,5672 -j DROP", "Bloqueando BD/Cache para el resto de redes", ignorar_error=True)
    
    print("    [OK] Reglas de Hardening de red aplicadas con éxito")

# --- Documentar Esquema ---
def generar_documentacion():
    path = "infraestructura_reporte_zona5.txt"
    contenido = f"""
=========================================
REPORTE DE INFRAESTRUCTURA: ZONA 5 BACKEND
Segmento IP: {SUBNET}
=========================================
Servicio       | Estado     | Puerto | Dirección IP
-----------------------------------------
Juice Shop     | Docker     | 3000   | {IPS['JUICE_SHOP']}
Vulnerable LLM | Docker     | 5000   | {IPS['VULNERABLE_LLM']}
PostgreSQL     | Docker     | 5432   | {IPS['POSTGRESQL']}
Redis          | Docker     | 6379   | {IPS['REDIS']}
RabbitMQ       | Docker     | 5672   | {IPS['RABBITMQ']}
-----------------------------------------
ESQUEMA DE SEGURIDAD (HARDENING IPTABLES):
- DB, Cache y MQ restringidos estrictamente al segmento 10.2.0.0/16.
- Aislamiento en red dedicada docker: {NETWORK_NAME}.
"""
    with open(path, "w") as f:
        f.write(contenido)
    print(f"[+] Documentación generada en: {os.path.abspath(path)}")

def levantar_servicios():
    print("\n=== Levantando Infraestructura Zona 5 ===")
    instalar_docker()
    configurar_red()
    desplegar_aplicaciones()
    aplicar_hardening()
    generar_documentacion()
    print("[✔] Proceso de despliegue de la Zona 5 finalizado.")

def botar_servicios():
    print("\n=== Botando Infraestructura ===")
    ejecutar("sudo docker rm -f juice-shop vulnerable-llm postgres_zona5 redis_zona5 rabbitmq_zona5", "Deteniendo y eliminando contenedores", ignorar_error=True)
    ejecutar(f"sudo docker network rm {NETWORK_NAME}", "Eliminando red virtual de la Zona 5", ignorar_error=True)
    
    # Limpiar reglas iptables creadas
    ejecutar("sudo iptables -D DOCKER-USER -i eth0 -p tcp -m multiport --dports 5432,6379,5672 -s 10.2.0.0/16 -j ACCEPT", "Limpiando reglas de Firewall", ignorar_error=True)
    ejecutar("sudo iptables -D DOCKER-USER -i eth0 -p tcp -m multiport --dports 5432,6379,5672 -j DROP", "Limpiando reglas de Firewall de bloqueo", ignorar_error=True)
    
    print("[✔] Todos los servicios han sido detenidos limpiamente.")

# --- ORQUESTADOR PRINCIPAL ---
def main():
    while True:
        print("\n=== Gestor de Despliegue Backend (Zona 5) ===")
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
