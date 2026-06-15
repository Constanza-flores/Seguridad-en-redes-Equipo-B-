# Laboratorio OWASP Juice Shop — Seguridad en Redes (Equipo B)

Entorno reproducible para levantar [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/)
(aplicación web *deliberadamente vulnerable*) sobre Docker y practicar las
vulnerabilidades de la tarea, desde una máquina virtual **Kali Linux**.

> ⚠️ **Uso ético:** Juice Shop está diseñado para atacarlo de forma segura en
> tu propio entorno aislado. Realiza los ejercicios **solo** en esta VM local.
> No apliques estas técnicas contra sistemas que no te pertenezcan.

## Requisitos

- Máquina virtual con **Kali Linux** (o cualquier Debian-based).
- Python 3 (viene preinstalado en Kali).
- Conexión a internet (para descargar Docker y la imagen).

## Uso rápido

Dentro de la VM Kali, en una terminal:

```bash
# Instala Docker (si falta), descarga la imagen y levanta la app
sudo python3 juiceshop_lab.py up
```

Cuando termine, abre en el navegador de Kali:

```
http://localhost:3000
```

El panel de retos (score board) está en:

```
http://localhost:3000/#/score-board
```

## Comandos disponibles

| Comando                            | Descripción                                              |
|------------------------------------|----------------------------------------------------------|
| `sudo python3 juiceshop_lab.py up` | Instala Docker (si falta) y levanta Juice Shop.          |
| `python3 juiceshop_lab.py status`  | Muestra el estado del contenedor.                        |
| `python3 juiceshop_lab.py logs`    | Muestra los logs de la aplicación.                       |
| `python3 juiceshop_lab.py down`    | Detiene y elimina el contenedor.                         |
| `python3 juiceshop_lab.py reset`   | Borra el contenedor y lo vuelve a levantar (estado limpio). |

> Tras `up`, tu usuario puede haber sido añadido al grupo `docker`. Si los
> comandos sin `sudo` te dan error de permisos, cierra y vuelve a abrir la
> sesión, o usa `sudo`.

## Herramientas de ataque en Kali

Kali ya trae todo lo necesario para la tarea:

- **Burp Suite** / **OWASP ZAP** — proxy de interceptación.
- **sqlmap** — inyección SQL automatizada.
- **curl** / **httpie** — peticiones HTTP manuales.
- **nikto** — escaneo de vulnerabilidades web.
- Las **DevTools** del navegador (F12).

## Recursos

- Guía oficial de retos: <https://pwning.owasp-juice.shop/>
- Repositorio de Juice Shop: <https://github.com/juice-shop/juice-shop>
