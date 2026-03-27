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


def testear_servicios():
    print("\n=== Testeando Estado de los Servicios ===")
    
    # Diccionario con los servicios y los puertos donde deberían estar escuchando
    servicios = {
        "Juice Shop (Docker)": 3000,
        "Vulnerable LLM (Docker)": 5000,
        "PostgreSQL (Nativo)": 5432,
        "Redis (Nativo)": 6379,
        "RabbitMQ (Nativo)": 5672,
        "RabbitMQ Management UI": 15672
    }
    
    todos_ok = True
   
    for nombre, puerto in servicios.items():
        # Creamos un socket temporal para intentar la conexión
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.5) # Espera máxima de 1.5 segundos por servicio
        
        resultado = sock.connect_ex(('127.0.0.1', puerto))
        
        if resultado == 0:
            print(f"  [🟢 UP]   {nombre} está respondiendo en el puerto {puerto}")
        else:
            print(f"  [🔴 DOWN] {nombre} NO responde en el puerto {puerto}")
            todos_ok = False
            
        sock.close()
        
    print("=========================================")
    if todos_ok:
        print("[✔] Todos los servicios están operativos y escuchando.")
    else:
        print("[!] Hay servicios caídos. Revisa los logs o intenta levantarlos de nuevo.")

# --- 0. Pre-requisito: Instalar Docker en Fedora ---

def instalar_docker():
    if subprocess.run("command -v docker", shell=True, capture_output=True).returncode != 0:
        ejecutar("sudo apt install -y docker", "Instalando Docker")
        ejecutar("sudo systemctl start docker", "Iniciando servicio Docker")
        ejecutar("sudo systemctl enable docker", "Habilitando Docker en el arranque")
    else:
        print("[*] Docker ya se encuentra instalado. [OK]")

# --- 1. Desplegar Juice Shop en Docker ---
def desplegar_juice_shop():
    instalar_docker()
    # CORREGIDO: Se eliminó capture_output=True
    subprocess.run("sudo docker rm -f juice-shop", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ejecutar("sudo docker run -d -p 3000:3000 --name juice-shop bkimminich/juice-shop", "Desplegando Juice Shop en Docker (Puerto 3000)")

# --- 2. Desplegar Vulnerable LLM (Sin API Key) ---
def desplegar_vulnerable_llm():
    print("[*] Preparando Damn Vulnerable AI Agent (LLM Simulado)...")
    instalar_docker()
    subprocess.run("sudo docker rm -f vulnerable-llm", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Parcheamos el arranque: sobreescribimos el entrypoint para instalar 'openai' primero y luego iniciar el agente
    comando_docker = 'sudo docker run -d -p 5000:9000 --name vulnerable-llm --entrypoint /bin/sh opena2a/dvaa -c "npm install openai && npm start"'
    
    ejecutar(comando_docker, "Desplegando DVAA Vulnerable LLM con parche de dependencias")
    
    # Damos tiempo para que npm install termine dentro del contenedor antes de continuar
    print("    [!] Esperando 10 segundos para la instalación de dependencias internas...")
    time.sleep(10)# --- 3. Configurar Servidor de Base de Datos ---

def configurar_postgresql():
    ejecutar("sudo apt install -y postgresql-server postgresql-contrib", "Instalando PostgreSQL")
    
    # En Fedora, es estricto inicializar la DB antes del primer arranque
    if not os.path.exists("/var/lib/pgsql/data/PG_VERSION"):
        ejecutar("sudo postgresql-setup --initdb", "Inicializando cluster de PostgreSQL")
        
    ejecutar("sudo systemctl start postgresql", "Iniciando servicio PostgreSQL")
    ejecutar("sudo systemctl enable postgresql", "Habilitando PostgreSQL en el arranque")

def configurar_redis():
    ejecutar("sudo apt install -y redis", "Instalando Redis")
    # Configurar para que escuche solo localmente. En Fedora puede estar en /etc/redis/redis.conf o /etc/redis.conf
    cmd_sed = "sudo sed -i 's/^bind .*/bind 127.0.0.1 ::1/' /etc/redis/redis.conf /etc/redis.conf 2>/dev/null || true"
    ejecutar(cmd_sed, "Configurando Redis para aceptar solo conexiones locales")
    ejecutar("sudo systemctl start redis-server", "Iniciando Redis")
    ejecutar("sudo systemctl enable redis-server", "Habilitando Redis")


def configurar_rabbitmq():
    ejecutar("sudo apt install -y rabbitmq-server", "Instalando RabbitMQ")
    ejecutar("sudo rabbitmq-plugins enable rabbitmq_management", "Habilitando consola web de RabbitMQ")
    ejecutar("sudo systemctl start rabbitmq-server", "Iniciando RabbitMQ")
    ejecutar("sudo systemctl enable rabbitmq-server", "Habilitando RabbitMQ")

# --- 6. Aplicar Hardening (Firewalld) ---
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
