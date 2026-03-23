import subprocess
import os
import urllib.request
from pathlib import Path

def ejecutar_comando(comando, ignorar_errores=False):
    """Ejecuta un comando en la terminal y muestra la salida."""
    print(f"\n[+] Ejecutando: {comando}")
    try:
        subprocess.run(comando, shell=True, check=True, executable='/bin/bash')
    except subprocess.CalledProcessError as e:
        if not ignorar_errores:
            print(f"[-] Error ejecutando el comando: {e}")
        else:
            print(f"[*] Aviso: El comando devolvió un error, pero se continuará la ejecución.")

def main():
    print("=== Iniciando Despliegue Automatizado: Zona 4 - Integración ===")
    
    # 1. Crear la red de la Zona 4
    # Segmento IP: 10.2.4.0/24 según las especificaciones del documento
    ejecutar_comando("docker network create --subnet=10.2.4.0/24 zona4_integracion", ignorar_errores=True)

    # 2. Crear directorio de trabajo para configuraciones
    base_dir = Path.home() / "laboratorio_equipoB" / "zona4"
    base_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(base_dir)

    # 3. Generar configuración de NGINX con CORS y Rate Limiting
    nginx_conf_path = base_dir / "nginx.conf"
    nginx_conf_content = """
worker_processes 1;
events { worker_connections 1024; }
http {
    # Implementación de Rate Limiting (10 peticiones por segundo)
    limit_req_zone $binary_remote_addr zone=limite_api:10m rate=10r/s;

    server {
        listen 80;
        server_name localhost;

        location / {
            # Aplicar Rate Limiting
            limit_req zone=limite_api burst=20 nodelay;

            # Establecer políticas CORS
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
            add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;

            # Proxy Pass hacia crAPI (El contenedor de crAPI web estará en 10.2.4.30)
            proxy_pass http://10.2.4.30:80;
        }
    }
}
"""
    with open(nginx_conf_path, "w") as f:
        f.write(nginx_conf_content)
    print(f"[+] Archivo nginx.conf creado en {nginx_conf_path}")

    # 4. Desplegar API Gateway (NGINX) con la configuración montada
    ejecutar_comando(
        f"docker run -d --name api_gateway_zona4 --network zona4_integracion --ip 10.2.4.10 "
        f"-p 80:80 -v {nginx_conf_path}:/etc/nginx/nginx.conf:ro nginx"
    )

    # 5. Desplegar Servicios de Mensajería (Redis y RabbitMQ)
    ejecutar_comando("docker run -d --name redis_zona4 --network zona4_integracion --ip 10.2.4.20 redis")
    ejecutar_comando("docker run -d --name rabbitmq_zona4 --network zona4_integracion --ip 10.2.4.21 -p 15672:15672 rabbitmq:3-management")

    # 6. Desplegar crAPI
    print("\n[+] Descargando docker-compose de crAPI...")
    crapi_url = "https://raw.githubusercontent.com/OWASP/crAPI/main/deploy/docker/docker-compose.yml"
    urllib.request.urlretrieve(crapi_url, "docker-compose.yml")
    
    # Levantar crAPI (esto levanta varios contenedores en su propia red por defecto)
    ejecutar_comando("docker-compose up -d")

    # Conectar el servicio web de crAPI a nuestra red de la Zona 4 con la IP esperada por el NGINX
    print("\n[+] Conectando crAPI a la red zona4_integracion...")
    ejecutar_comando("docker network connect --ip 10.2.4.30 zona4_integracion crapi-web", ignorar_errores=True)

    print("\n=== Despliegue de la Zona 4 finalizado con éxito ===")
    print("Puedes verificar los contenedores activos ejecutando: docker ps")

if _name_ == "_main_":
    main()
