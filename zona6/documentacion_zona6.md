# 🛡️ Documentación Técnica: Zona 6 - Red Usuarios y SOC

**Proyecto:** Laboratorio de Ciberseguridad - Red Team vs Blue Team  
**Responsable:** Equipo B  
**Fase:** Readiness  

---

## 📝 Resumen de la Zona
[cite_start]La **Zona 6** representa el segmento interno de la organización, albergando la red de usuarios finales y el Centro de Operaciones de Seguridad (SOC)[cite: 404, 495]. [cite_start]Su objetivo principal es proveer visibilidad defensiva mediante herramientas de monitoreo [cite: 500][cite_start], al mismo tiempo que aloja estaciones de trabajo simuladas [cite: 498] [cite_start]y servidores de Comando y Control (C2) para ejercicios ofensivos[cite: 499].

Para esta fase de *Readiness*, la infraestructura de monitoreo ha sido desacoplada y parcialmente simulada (Mocking) para optimizar el consumo de recursos (RAM) en el host, garantizando que las validaciones de ruteo y puertos sean exitosas sin comprometer la estabilidad del sistema.

---

## 🌐 Configuración de Red
* [cite_start]**Segmento IP Físico/Lógico:** `10.3.0.0/24` [cite: 404]
* **Red de Docker:** `zona6_usuarios`
* **Tipo de Despliegue:** Contenedores aislados con enrutamiento interno.

---

## 🛠️ Inventario de Servicios y Direccionamiento IP

A continuación se detallan los servicios desplegados en esta zona, sus IPs y su estado actual en la fase de estructuración:

| Servicio / Activo | Contenedor | IP Lógica (Docker) | Puertos Host | Función Principal en el Laboratorio |
| :--- | :--- | :--- | :--- | :--- |
| **SOC Dashboard** | `kibana_zona6` | `10.3.0.10` | `5601` | Interfaz gráfica (Kibana) para la visualización de logs, alertas y hunting de amenazas. |
| **SOC Database** | `elastic_zona6` | `10.3.0.11` | N/A | Nodo de Elasticsearch limitado a 512MB de RAM para almacenamiento de eventos de seguridad. |
| **Receptor Logs** | `logstash_mock` | `10.3.0.12` | `5044` | Simulación temporal (Mock) del puerto de ingesta de Logstash para validar conectividad desde otras zonas. |
| **Servidor C2** | `caldera_mock`| `10.3.0.20` | `8888` | [cite_start]Simulador temporal del servidor de Comando y Control (C2)[cite: 499]. Prepara el terreno para despliegue de agentes. |
| **Workstation** | `workstation` | `10.3.0.30` | N/A | [cite_start]Estación de trabajo basada en Kali Linux para simular comportamiento de usuarios y compromisos de endpoints[cite: 498]. |

---

## 🚀 Instrucciones de Ejecución (Gestor de Despliegue)

El entorno está orquestado mediante el script automatizado `zona6.py`, el cual gestiona el ciclo de vida de los contenedores y la configuración del kernel requerida por Elasticsearch.

Para ejecutar el orquestador, utiliza privilegios de superusuario:

```bash
sudo python3 zona6.py
