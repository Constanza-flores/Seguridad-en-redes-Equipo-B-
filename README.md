# Laboratorio OWASP Juice Shop — Seguridad en Redes (Equipo B)

Entorno reproducible para levantar [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/)
desde una máquina virtual **Kali Linux**.


## Uso rápido

Dentro de la VM Kali, en una terminal:

```bash
# Instala Docker (si falta), descarga la imagen y levanta la app
sudo python3 juiceshop_lab.py up
```

Cuando termine,en el navegador de Kali:
```
http://localhost:3000
```

## Comandos disponibles

| Comando                            | Descripción                                              |
|------------------------------------|----------------------------------------------------------|
| `sudo python3 juiceshop_lab.py up` | Instala Docker (si falta) y levanta Juice Shop.          |
| `python3 juiceshop_lab.py status`  | Muestra el estado del contenedor.                        |
| `python3 juiceshop_lab.py logs`    | Muestra los logs de la aplicación.                       |
| `python3 juiceshop_lab.py down`    | Detiene y elimina el contenedor.                         |
| `python3 juiceshop_lab.py reset`   | Borra el contenedor y lo vuelve a levantar (estado limpio). |


lINK KANBAN:
```
https://seguridadredes.atlassian.net/?continue=https%3A%2F%2Fseguridadredes.atlassian.net%2Fwelcome%2Fsoftware%3FprojectId%3D10000&atlOrigin=eyJpIjoiMTU1ZDZhMjdlMGU5NDkyMGExMDc5NzljNjJiZjY5YjgiLCJwIjoiamlyYS1zb2Z0d2FyZSJ9
```
(SI SE REQUIEREN PERMISOS SOLICITAR A MARCELO F)