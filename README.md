# Laboratorio OWASP crAPI — Seguridad en Redes (Equipo B)

Entorno reproducible para levantar OWASP crAPI desde una máquina virtual Kali Linux.

## Uso rápido

Dentro de la VM Kali, en una terminal:
```bash
# Instala Docker Compose (si falta), descarga la configuración y levanta la arquitectura de microservicios
sudo python3 crapi.py
Comando,Descripción

sudo python3 crapi.py,Instala dependencias de orquestación y despliega crAPI de forma automatizada.
cd entorno_crapi && sudo docker-compose ps,Muestra el estado de los diferentes contenedores/microservicios activos.
cd entorno_crapi && sudo docker-compose logs,Muestra los registros y logs de auditoría del ecosistema de la API.
cd entorno_crapi && sudo docker-compose down,Detiene los servicios y libera los puertos ocupados por la aplicación.
```
Link Kanban
https://seguridadredes.atlassian.net/jira/software/projects/KAN/boards/1

(SI SE REQUIEREN PERMISOS SOLICITAR A MARCELO F)
<img width="1273" height="866" alt="image" src="https://github.com/user-attachments/assets/07865ceb-4f76-4af5-bea8-625de56e7d4c" />
