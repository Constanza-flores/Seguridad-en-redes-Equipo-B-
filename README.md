


# Laboratorio Metasploitable2 — Seguridad en Redes (Equipo B)

Entorno reproducible para levantar **Metasploitable2** (máquina *deliberadamente vulnerable* de Rapid7) como contenedor Docker, y atacarla desde **Kali Linux** con Nmap y Metasploit. Corresponde a la Experiencia 3: *Metasploit & Máquina Vulnerable*.

> ⚠️ **Uso ético:** Metasploitable2 está diseñado para practicar de forma segura en un entorno aislado. Ataca **únicamente** este objetivo local, dentro del alcance del laboratorio. No uses estas técnicas contra sistemas que no te pertenezcan.

## Requisitos

- Máquina virtual con **Kali Linux** (o cualquier Debian-based).
- Python 3 (viene preinstalado en Kali).
- Conexión a internet (para descargar Docker y la imagen).

## Uso rápido

Dentro de la VM Kali, en una terminal:

```bash
# Instala Docker (si falta), descarga la imagen y levanta Metasploitable2
sudo python3 metasploitable_min.py
```

Cuando termine, te muestra la IP del objetivo (RHOSTS), por ejemplo:

```
IP objetivo (RHOSTS): 172.19.0.2
```

Esa IP es tu máquina víctima. Desde Kali la atacas con Nmap y Metasploit.

## Comandos disponibles

El script solo levanta el objetivo. Para gestionar el contenedor después, usa Docker directamente:

| Comando                               | Descripción                                                |
|---------------------------------------|------------------------------------------------------------|
| `sudo python3 metasploitable_min.py`  | Instala Docker (si falta) y levanta Metasploitable2.       |
| `sudo docker ps`                      | Muestra el estado del contenedor (verifica que esté "Up"). |
| `sudo docker logs metasploitable2`    | Muestra los logs del contenedor.                           |
| `sudo docker stop metasploitable2`    | Detiene el objetivo.                                       |
| `sudo docker start metasploitable2`   | Vuelve a arrancar el objetivo detenido.                    |
| `sudo docker restart metasploitable2` | Reinicia el objetivo (deja el estado limpio).              |
| `sudo docker rm -f metasploitable2`   | Detiene y elimina el contenedor por completo.              |

## Obtener la IP del objetivo cuando la necesites

```bash
sudo docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' metasploitable2
```

## Flujo de trabajo (ciclo de explotación)

```bash
# 1. Reconocimiento: descubrir el host
sudo nmap -sn 172.19.0.0/24

# 2. Enumeración de servicios y versiones
sudo nmap -sV -Pn 172.19.0.2

# 3. Investigación de CVE
searchsploit <servicio y version>

# 4. Explotación controlada
msfconsole
```

## Herramientas de ataque en Kali

- **Metasploit Framework** (`msfconsole`) — explotación.
- **Nmap** — escaneo y enumeración.
- **searchsploit** — búsqueda de exploits públicos.
- **netdiscover** — descubrimiento de hosts.
lINK KANBAN:
```
https://seguridadredes.atlassian.net/?continue=https%3A%2F%2Fseguridadredes.atlassian.net%2Fwelcome%2Fsoftware%3FprojectId%3D10000&atlOrigin=eyJpIjoiMTU1ZDZhMjdlMGU5NDkyMGExMDc5NzljNjJiZjY5YjgiLCJwIjoiamlyYS1zb2Z0d2FyZSJ9
```
(SI SE REQUIEREN PERMISOS SOLICITAR A MARCELO F)
