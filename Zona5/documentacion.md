# 🛡️ Documentación Técnica: Zona 5 - Backend

**Proyecto:** Laboratorio de Ciberseguridad - Red Team vs Blue Team  
**Responsable:** Equipo B  
**Fase:** Readiness  

---

## 📝 Resumen de la Zona
La **Zona 5** actúa como el núcleo de procesamiento y almacenamiento de datos (Backend) de la infraestructura corporativa simulada. Aloja aplicaciones con vulnerabilidades modernas orientadas a pruebas ofensivas (OWASP Top 10, inyecciones de prompts en IA) y servicios críticos (bases de datos, caché y colas de mensajería) que son el objetivo principal de exfiltración de datos. 

Todos los componentes han sido contenerizados con Docker para garantizar un entorno aislado, reproducible y seguro para el host.

---

## 🌐 Configuración de Red
* **Segmento IP Físico/Lógico:** `10.2.5.0/24`
* **Red de Docker:** `zona5_backend`
* **Tipo de Despliegue:** Contenedores estáticos con IP asignada (Bridge customizado).

---

## 🛠️ Inventario de Servicios y Direccionamiento IP

A continuación se detallan los servicios desplegados en esta zona, sus direcciones IP internas estáticas y sus puertos de escucha:

| Servicio / Activo | Contenedor | IP Lógica (Docker) | Puertos (Int/Ext) | Función Principal en el Laboratorio |
| :--- | :--- | :--- | :--- | :--- |
| **Juice Shop** | `juice-shop` | `10.2.5.10` | `3000:3000` | Plataforma de e-commerce moderna intencionalmente vulnerable (OWASP Top 10). Usada como vector de ataque web. |
| **Vulnerable LLM** | `vulnerable-llm` | `10.2.5.20` | `9000:5000` | Aplicación DVAA (*Damn Vulnerable AI Application*). Simula una IA susceptible a *Prompt Injection* y exfiltración. |
| **PostgreSQL 14**| `postgres_zona5` | `10.2.5.30` | `5432:5432` | Motor de base de datos relacional core. Contiene los datos estructurados que el Red Team buscará comprometer. |
| **Redis** | `redis_zona5` | `10.2.5.40` | `6379:6379` | Sistema de caché en memoria de alta velocidad. |
| **RabbitMQ** | `rabbitmq_zona5` | `10.2.5.50` | `5672:5672`<br>`15672:15673` | Gestor de colas de mensajería (Broker). El panel de administración web está mapeado al 15673 para evitar colisiones. |

---

## 🔒 Esquema de Seguridad y Hardening (Blue Team)

Para reducir la superficie de ataque y simular políticas empresariales, se aplicaron controles de acceso a nivel de red mediante **iptables** directamente en la tarjeta de red del host (`eth0` -> `DOCKER-USER`).

* **Acceso Público Permitido:** Los puertos web de las aplicaciones (`3000` para Juice Shop y `5000` para LLM) están expuestos.
* **Restricción de Servicios Core:** El acceso a los puertos de PostgreSQL (`5432`), Redis (`6379`) y RabbitMQ (`5672`) está **estrictamente bloqueado** desde el exterior. 
* **Lista Blanca (Whitelist):** Los servicios core solo aceptan tráfico entrante proveniente de la superred corporativa interna del laboratorio (`10.2.0.0/16`).

---

## 🚀 Instrucciones de Ejecución (Gestor de Despliegue)

La infraestructura está orquestada mediante el script de Python `zona5.py`, el cual automatiza la instalación de dependencias, creación de redes, despliegue de contenedores y aplicación de firewall.

Para ejecutar el orquestador, utiliza privilegios de superusuario:

```bash
sudo python3 zona5.py
