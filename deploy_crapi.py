import subprocess
import sys
import os
import urllib.request

def verificar_root():
    """Verifica si el script se está ejecutando con privilegios de superusuario."""
    if os.geteuid() != 0:
        print("[!] ERROR: Este script necesita instalar paquetes y requiere privilegios de administrador.")
        print("Vuelve a ejecutarlo usando sudo: sudo python3 crapi.py")
        sys.exit(1)

def ejecutar_comando(comando, ignorar_error=False):
    """Ejecuta un comando en la terminal y maneja los errores."""
    print(f"[*] Ejecutando: {comando}")
    resultado = subprocess.run(comando, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if resultado.returncode != 0 and not ignorar_error:
        print(f"[!] Error crítico al ejecutar: {comando}")
        print(f"Detalle del error:\n{resultado.stderr}")
        sys.exit(1)
        
    return resultado.returncode, resultado.stdout

def instalar_docker_compose():
    """Instala Docker Compose usando apt (para entornos Debian/Kali)."""
    print("\n[!] Docker Compose no encontrado. Iniciando instalación automática...")
    print("[*] Actualizando repositorios (apt update)...")
    ejecutar_comando("apt update")
    
    print("[*] Instalando docker-compose (apt install)...")
    ejecutar_comando("apt install docker-compose -y")
    print("[+] Instalación de Docker Compose completada con éxito.")

def main():
    print("=== Automatización de Despliegue crAPI (OWASP) ===\n")
    
    # Validar permisos antes de hacer nada
    verificar_root()

    # 1. Verificar si Docker está instalado
    print("[1] Comprobando instalación de Docker...")
    ejecutar_comando("docker --version")
    
    # 2. Verificar si el demonio de Docker está corriendo
    print("\n[2] Comprobando estado del servicio Docker...")
    ejecutar_comando("docker info")
    print("[+] Docker está instalado y en ejecución.")

    # 3. Verificar y/o instalar Docker Compose
    print("\n[3] Comprobando Docker Compose...")
    codigo_plugin, _ = ejecutar_comando("docker compose version", ignorar_error=True)
    
    if codigo_plugin == 0:
        cmd_compose = "docker compose"
    else:
        codigo_standalone, _ = ejecutar_comando("docker-compose --version", ignorar_error=True)
        if codigo_standalone == 0:
            cmd_compose = "docker-compose"
        else:
            # Si no existe ninguna de las dos versiones, forzamos la instalación
            instalar_docker_compose()
            cmd_compose = "docker-compose"
    
    print(f"[+] Se utilizará el comando de orquestación: '{cmd_compose}'")

    # 4. Preparar el directorio y descargar archivos oficiales
    directorio_crapi = "entorno_crapi"
    print(f"\n[4] Creando directorio '{directorio_crapi}' y descargando configuración...")
    os.makedirs(directorio_crapi, exist_ok=True)
    os.chdir(directorio_crapi)

    url_compose = "https://raw.githubusercontent.com/OWASP/crAPI/main/deploy/docker/docker-compose.yml"
    archivo_local = "docker-compose.yml"
    
    try:
        urllib.request.urlretrieve(url_compose, archivo_local)
        print(f"[+] Archivo {archivo_local} descargado exitosamente.")
    except Exception as e:
        print(f"[!] Error al descargar el archivo docker-compose: {e}")
        sys.exit(1)

    # 5. Descargar imágenes y levantar la infraestructura
    print("\n[5] Descargando imágenes y levantando microservicios (Esto puede tardar varios minutos)...")
    ejecutar_comando(f"{cmd_compose} pull")
    ejecutar_comando(f"{cmd_compose} up -d")

    # 6. Resumen de despliegue
    print("\n===================================================")
    print("✅ ¡crAPI se ha desplegado con éxito en la máquina! ✅")
    print("===================================================")
    print("La arquitectura está expuesta en los siguientes puertos:")
    print(" 🌐 Aplicación Web Principal : http://localhost:8888")
    print(" 📧 Servidor de Correos (MailHog) : http://localhost:8025")
    print("\nPara detener el entorno más adelante, ejecuta:")
    print(f" cd {directorio_crapi} && {cmd_compose} down")

if __name__ == "__main__":
    main()
