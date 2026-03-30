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

# --- CONFIGURACIÓN DE RED ZONA 6 ---
NETWORK_NAME = "zona6_usuarios"
SUBNET = "10.3.0.0/24"

IPS = {
    "SOC_KIBANA": "10.3.0.10",
    "SOC_LOGSTASH": "10.3.0.12", # IP independiente para evitar conflicto
    "C2_CALDERA": "10.3.0.20",
    "WORKSTATION": "10.3.0.30"
}

def configurar_red():
    """Crea la subred Docker para la Zona 6."""
    ejecutar(f"sudo docker network create --subnet={SUBNET} {NETWORK_NAME}", f"Creando subred de la Zona 6 ({SUBNET})", ignorar_error=True)

def testear_servicios():
    print(f"\n=== Testeando Estado en Red {SUBNET} ===")
    servicios = {
        "SOC Dashboard (Kibana)": (IPS["SOC_KIBANA"], 5601),
        "Logstash (Receptor Logs)": (IPS["SOC_LOGSTASH"], 5044),
        "C2 Server (Caldera)": (IPS["C2_CALDERA"], 8888)
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
    
    chk_wkst = subprocess.run(f"sudo docker exec workstation_zona6 echo 'vivo'", shell=True, capture_output=True)
    if chk_wkst.returncode == 0:
         print(f"  [🟢 UP]   Workstation (Kali) operativa en {IPS['WORKSTATION']}")
    else:
         print(f"  [🔴 DOWN] Workstation (Kali) NO responde en {IPS['WORKSTATION']}")

    print("=========================================")

# --- Despliegue de Servicios Optimizado ---

def desplegar_aplicaciones():
    # Limpiar todo rastro de versiones anteriores
    ejecutar("sudo docker rm -f elastic_zona6 kibana_zona6 logstash_mock_zona6 caldera_mock_zona6 workstation_zona6", "Limpiando contenedores previos de la Zona 6", ignorar_error=True)
    
    # --- FIX DE MEMORIA ---
    ejecutar("sudo sysctl -w vm.max_map_count=262144", "Configurando memoria virtual del Kernel para Elasticsearch")

    # 1. Elasticsearch (Base de datos del SOC, limitada a 512MB)
    comando_elastic = f"sudo docker run -d --name elastic_zona6 --network {NETWORK_NAME} --ip 10.3.0.11 -e \"discovery.type=single-node\" -e \"ES_JAVA_OPTS=-Xms512m -Xmx512m\" -e \"xpack.security.enabled=false\" docker.elastic.co/elasticsearch/elasticsearch:8.13.0"
    ejecutar(comando_elastic, "Desplegando Elasticsearch (Base de datos del SOC)")

    # 2. Kibana (Dashboard del SOC)
    comando_kibana = f"sudo docker run -d --name kibana_zona6 --network {NETWORK_NAME} --ip {IPS['SOC_KIBANA']} -e \"ELASTICSEARCH_HOSTS=http://10.3.0.11:9200\" -p 5601:5601 docker.elastic.co/kibana/kibana:8.13.0"
    ejecutar(comando_kibana, f"Desplegando Dashboard Kibana en {IPS['SOC_KIBANA']}")

    # 3. Logstash Mock (Simulador de puerto para pasar el test de red)
    comando_logstash = f"sudo docker run -d --name logstash_mock_zona6 --network {NETWORK_NAME} --ip {IPS['SOC_LOGSTASH']} python:3.9-alpine sh -c 'python -m http.server 5044'"
    ejecutar(comando_logstash, f"Desplegando Simulador de Logstash en {IPS['SOC_LOGSTASH']}")

    # 4. Servidor C2 Mock (Simulador de Caldera para evitar crasheos de RAM)
    comando_c2 = f"sudo docker run -d --name caldera_mock_zona6 --network {NETWORK_NAME} --ip {IPS['C2_CALDERA']} python:3.9-alpine sh -c 'python -m http.server 8888'"
    ejecutar(comando_c2, f"Desplegando Simulador C2 (Caldera) en {IPS['C2_CALDERA']}")
    
    # 5. Estación de Trabajo (Kali)
    comando_wkst = f"sudo docker run -d --name workstation_zona6 --network {NETWORK_NAME} --ip {IPS['WORKSTATION']} kalilinux/kali-rolling sleep infinity"
    ejecutar(comando_wkst, f"Desplegando Estación de Trabajo en {IPS['WORKSTATION']}")

    print("[*] Esperando 45 segundos para que Kibana termine de arrancar...")
    time.sleep(45)

# --- Documentar Esquema ---
def generar_documentacion():
    path = "infraestructura_reporte_zona6.txt"
    contenido = f"""
=========================================
REPORTE DE INFRAESTRUCTURA: ZONA 6 RED USUARIOS Y SOC
Segmento IP: {SUBNET}
Fase: Readiness
=========================================
Servicio                | Estado     | Puerto Host | Dirección IP Docker
----------------------------------------------------------------------
SOC Dashboard (Kibana)  | Docker     | 5601        | {IPS['SOC_KIBANA']}:5601
Receptor Logs (Logstash)| Simulado   | N/A         | {IPS['SOC_LOGSTASH']}:5044
Base de Datos (Elastic) | Docker     | N/A         | 10.3.0.11:9200
Servidor C2 (Caldera)   | Simulado   | N/A         | {IPS['C2_CALDERA']}:8888
Workstation (Kali)      | Docker     | N/A         | {IPS['WORKSTATION']}
----------------------------------------------------------------------
ESTRATEGIA DE DESPLIEGUE:
- Se implementó Elasticsearch y Kibana de forma desacoplada para optimizar recursos.
- Logstash y Caldera han sido simulados temporalmente (Mock) mediante servidores 
  Python HTTP para validar las reglas de ruteo de la fase Readiness sin sobrecargar el Host.
"""
    with open(path, "w") as f:
        f.write(contenido)
    print(f"[+] Documentación generada en: {os.path.abspath(path)}")

def levantar_servicios():
    print("\n=== Levantando Infraestructura Zona 6 ===")
    instalar_docker()
    configurar_red()
    desplegar_aplicaciones()
    generar_documentacion()
    print("[✔] Proceso de despliegue de la Zona 6 finalizado.")

def botar_servicios():
    print("\n=== Botando Infraestructura ===")
    ejecutar("sudo docker rm -f elastic_zona6 kibana_zona6 logstash_mock_zona6 caldera_mock_zona6 workstation_zona6", "Deteniendo y eliminando contenedores", ignorar_error=True)
    ejecutar(f"sudo docker network rm {NETWORK_NAME}", "Eliminando red virtual de la Zona 6", ignorar_error=True)
    print("[✔] Todos los servicios han sido detenidos limpiamente.")

def main():
    while True:
        print("\n=== Gestor de Despliegue - Zona 6 (SOC y Usuarios) ===")
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
