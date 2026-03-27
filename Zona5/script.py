import os
import socket
import time

def ejecutar(comando, descripcion):
    """Función auxiliar para ejecutar comandos y manejar errores."""
    print(f"[*] {descripcion}...")
    try:
        subprocess.run(comando, shell=True, check=True, capture_output=True, text=True)
        print(f"    [OK]")
        return True
    except subprocess.CalledProcessError as e:
        print(f"    [ERROR] {e.stderr.strip()}")
        return False


def instalar_docker():
    if subprocess.run("command -v docker", shell=True, capture_output=True).returncode != 0:
        ejecutar("sudo apt install -y docker", "Instalando Docker")
        ejecutar("sudo systemctl start docker", "Iniciando servicio Docker")
        ejecutar("sudo systemctl enable docker", "Habilitando Docker en el arranque")
    else:
        print("[*] Docker ya se encuentra instalado. [OK]")

# --- CONFIGURACIÓN DE RED ZONA 5 ---
# Se asignan IPs fijas dentro del rango 10.2.5.0/24
IPS = {
    "JUICE_SHOP": "10.2.5.10",
    "VULNERABLE_LLM": "10.2.5.20",
    "POSTGRESQL": "10.2.5.30",
    "REDIS": "10.2.5.40",
    "RABBITMQ": "10.2.5.50"
}

def testear_servicios():
    print(f"\n=== Testeando Estado en Red 10.2.5.0/24 ===")
    servicios = {
        "Juice Shop": (IPS["JUICE_SHOP"], 3000),
        "Vulnerable LLM": (IPS["VULNERABLE_LLM"], 5000),
        "PostgreSQL": (IPS["POSTGRESQL"], 5432),
        "Redis": (IPS["REDIS"], 6379),
        "RabbitMQ": (IPS["RABBITMQ"], 5672)
    }
    
    todos_ok = True
    for nombre, (ip, puerto) in servicios.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        # Intentamos conectar a la IP específica asignada
        resultado = sock.connect_ex((ip, puerto))
        if resultado == 0:
            print(f"  [🟢 UP]   {nombre} respondiendo en {ip}:{puerto}")
        else:
            print(f"  [🔴 DOWN] {nombre} NO responde en {ip}:{puerto}")
            todos_ok = False
        sock.close()
    print("=========================================")

# --- Modificación en despliegue para usar Binding de IP ---

def desplegar_juice_shop():
    instalar_docker()
    subprocess.run("sudo docker rm -f juice-shop", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Mapeamos el puerto específicamente a la IP elegida
    comando = f"sudo docker run -d -p {IPS['JUICE_SHOP']}:3000:3000 --name juice-shop bkimminich/juice-shop"
    ejecutar(comando, f"Desplegando Juice Shop en {IPS['JUICE_SHOP']}:3000")

def desplegar_vulnerable_llm():
    instalar_docker()
    subprocess.run("sudo docker rm -f vulnerable-llm", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Mapeamos el puerto específicamente a la IP elegida
    comando = f'sudo docker run -d -p {IPS["VULNERABLE_LLM"]}:5000:9000 --name vulnerable-llm --entrypoint /bin/sh opena2a/dvaa -c "npm install openai && npm start"'
    ejecutar(comando, f"Desplegando LLM en {IPS['VULNERABLE_LLM']}:5000")
    time.sleep(10)

def configurar_postgresql():
    ejecutar("sudo apt install -y postgresql postgresql-contrib", "Instalando PostgreSQL")
    # Configurar PostgreSQL para escuchar en su IP asignada
    cmd_listen = f"sudo sed -i \"s/#listen_addresses = 'localhost'/listen_addresses = 'localhost, {IPS['POSTGRESQL']}'/\" /etc/postgresql/*/main/postgresql.conf"
    ejecutar(cmd_listen, f"Configurando PostgreSQL para escuchar en {IPS['POSTGRESQL']}")
    ejecutar("sudo systemctl restart postgresql", "Reiniciando PostgreSQL")

def configurar_redis():
    ejecutar("sudo apt install -y redis-server", "Instalando Redis")
    # Configurar bind para incluir la IP asignada
    cmd_bind = f"sudo sed -i 's/^bind .*/bind 127.0.0.1 {IPS['REDIS']}/' /etc/redis/redis.conf"
    ejecutar(cmd_bind, f"Configurando Redis en IP {IPS['REDIS']}")
    ejecutar("sudo systemctl restart redis-server", "Reiniciando Redis")

def configurar_rabbitmq():
    ejecutar("sudo apt install -y rabbitmq-server", "Instalando RabbitMQ")
    # RabbitMQ por defecto escucha en todas las interfaces, pero validamos el nodo
    ejecutar("sudo rabbitmq-plugins enable rabbitmq_management", "Habilitando consola RabbitMQ")
    ejecutar("sudo systemctl restart rabbitmq-server", "Reiniciando RabbitMQ")# --- 6. Aplicar Hardening (Firewalld) ---
def aplicar_hardening():
    print("[*] Iniciando fase de Hardening con Firewalld...")
    ejecutar("sudo apt install -y firewalld", "Asegurando paquete Firewalld")
    ejecutar("sudo systemctl start firewalld", "Iniciando Firewalld")
    ejecutar("sudo systemctl enable firewalld", "Habilitando Firewalld en el arranque")
    
    # Permitir puertos públicos del Backend (Aplicaciones Docker)
    ejecutar("sudo firewall-cmd --permanent --add-port=3000/tcp", "Firewall: Permitir Juice Shop (3000)")
    ejecutar("sudo firewall-cmd --permanent --add-port=5000/tcp", "Firewall: Permitir Vulnerable LLM (5000)")
    ejecutar("sudo firewall-cmd --permanent --add-service=ssh", "Firewall: Permitir SSH")
    
    # Hardening de servicios core usando Rich Rules (Solo permite acceso a DB/Cache/MQ desde la red de laboratorio 10.2.0.0/16)
    ejecutar("sudo firewall-cmd --permanent --add-rich-rule='rule family=\"ipv4\" source address=\"10.2.0.0/16\" port port=\"5432\" protocol=\"tcp\" accept'", "Firewall: PostgreSQL (Solo red interna)")
    ejecutar("sudo firewall-cmd --permanent --add-rich-rule='rule family=\"ipv4\" source address=\"10.2.0.0/16\" port port=\"6379\" protocol=\"tcp\" accept'", "Firewall: Redis (Solo red interna)")
    ejecutar("sudo firewall-cmd --permanent --add-rich-rule='rule family=\"ipv4\" source address=\"10.2.0.0/16\" port port=\"5672\" protocol=\"tcp\" accept'", "Firewall: RabbitMQ (Solo red interna)")
    
    # Aplicar los cambios
    ejecutar("sudo firewall-cmd --reload", "Recargando reglas del Firewall")
    print("    [OK] Reglas de Firewalld aplicadas con éxito")

# --- 7. Documentar Esquema ---
def generar_documentacion():
    path = "infraestructura_reporte.txt"
    contenido = """
    =========================================
    REPORTE DE INFRAESTRUCTURA: ZONA 5 BACKEND (FEDORA)
    Segmento IP: 10.2.5.0/24
    =========================================
    Servicio       | Estado     | Puerto
    -----------------------------------------
    Juice Shop     | Docker     | 3000
    Vulnerable LLM | Docker     | 5000 (DVAA Simulado)
    PostgreSQL     | Instalado  | 5432
    Redis          | Instalado  | 6379
    RabbitMQ       | Instalado  | 5672 / 15672
    -----------------------------------------
    ESQUEMA DE SEGURIDAD (HARDENING FIREWALLD):
    - SSH (22), Juice Shop (3000) y Vulnerable LLM (5000) expuestos.
    - DB, Cache y MQ restringidos estrictamente al segmento 10.2.0.0/16.
    """
    with open(path, "w") as f:
        f.write(contenido)
    print(f"[+] Documentación generada en: {os.path.abspath(path)}")


def levantar_servicios():
    print("\n=== Levantando Infraestructura ===")
    desplegar_juice_shop()
    desplegar_vulnerable_llm()
    configurar_postgresql()
    configurar_redis()
    configurar_rabbitmq()
    aplicar_hardening()
    generar_documentacion()
    print("[✔] Proceso de despliegue finalizado.")

def botar_servicios():
    print("\n=== Botando Infraestructura ===")
    
    # 1. Detener y limpiar toda la infraestructura de Docker
    ejecutar("sudo docker rm -f juice-shop vulnerable-llm", "Deteniendo y eliminando contenedores de Juice Shop y LLM")
    
    # 2. Detener los servicios instalados nativamente en el sistema
    ejecutar("sudo systemctl stop postgresql redis rabbitmq-server", "Deteniendo PostgreSQL, Redis y RabbitMQ")
    ejecutar("sudo systemctl disable postgresql redis rabbitmq-server", "Deshabilitando el inicio automático de los servicios")

    print("[✔] Todos los servicios han sido detenidos y no quedarán ejecutándose en segundo plano.")

# --- ORQUESTADOR PRINCIPAL ---
# --- ORQUESTADOR PRINCIPAL ---
def main():
    while True:
        print("\n=== Gestor de Despliegue Backend ===")
        print("1) Levantar todos los servicios")
        print("2) Botar todos los servicios")
        print("3) Testear estado de los servicios")
        print("4) Salir")
        
        try:
            opcion = input("Selecciona una opción (1-4): ").strip()
        except KeyboardInterrupt:
            print("\n[!] Operación cancelada por el usuario. Saliendo limpiamente...")
            sys.exit(0)
        except ValueError:
            print("\n[!] Entrada inválida.")
            continue
        
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
