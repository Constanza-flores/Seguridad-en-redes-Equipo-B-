## 1. Información General de la Zona

La Zona 4 corresponde a la capa de integración de aplicaciones y servicios interno. Toda la infraestructura de esta zona ha sido desplegada mediante contenedores Docker automatizados a través de un script en Python (`zona4.py`).

* **Propósito:** API Gateway, App Servers y enrutamiento interno.
* **Segmento de Red Asignado:** `10.2.4.0/24`.
* **Nombre de la red Docker:** `zona4_integracion`

---

## 2. Inventario de Activos y Asignación IP (Topología)

Se configuró el enrutamiento estático interno para garantizar el cumplimiento del segmento IP requerido[cite: 926]. Los contenedores desplegados y sus direcciones IPv4 asignadas son:

| Servicio / Activo | Contenedor Docker | Dirección IP | Puerto(s) Expuesto(s) | Función |
| :--- | :--- | :--- | :--- | :--- |
| **API Gateway** | `api_gateway_zona4` | `10.2.4.10` | 80 | [cite_start]Balanceador de carga y proxy inverso (NGINX)[cite: 930, 931]. |
| **Caché** | `redis_zona4` | `10.2.4.20` | 6379 | [cite_start]Servicio de almacenamiento en memoria (Redis)[cite: 932]. |
| **Message Queue** | `rabbitmq_zona4` | `10.2.4.21` | 5672, 15672 | [cite_start]Servicio de mensajería asíncrona (RabbitMQ)[cite: 932]. |
| **Aplicación Vulnerable**| `crapi-web` | `10.2.4.30` | 80, 8888 | [cite_start]Frontend principal de crAPI (Completely Ridiculous API)[cite: 882, 929]. |

*Nota: La aplicación crAPI levanta microservicios adicionales en la red (Identity, Community, Workshop, Mailhog, MongoDB, Postgresdb) que se comunican internamente con `crapi-web`.*

---

## 3. Configuraciones de Seguridad Aplicadas (Hardening Base)

Como parte de los requerimientos de la fase de Readiness [cite: 786][cite_start], se implementaron políticas de control de tráfico en el nodo de entrada (API Gateway `10.2.4.10`) editando el archivo `nginx.conf`[cite: 933].

### 3.1. Políticas CORS (Cross-Origin Resource Sharing)
Se establecieron cabeceras HTTP para controlar el acceso a los recursos de la API desde orígenes cruzados[cite: 933]:
* `Access-Control-Allow-Origin: *` (Permite acceso general simulando una API pública).
* `Access-Control-Allow-Methods: GET, POST, OPTIONS, PUT, DELETE` (Restringe los verbos HTTP permitidos).
* `Access-Control-Allow-Headers: Authorization, Content-Type` (Define las cabeceras válidas en la solicitud).

### 3.2. Rate Limiting (Límite de Tasa)
Para mitigar ataques de denegación de servicio (DoS) o fuerza bruta a nivel de aplicación, se configuró una política de limitación de solicitudes[cite: 933]:
* **Zona de memoria:** `limite_api` (10 MB asignados para rastrear IPs mediante `$binary_remote_addr`).
* **Tasa permitida (Rate):** 10 peticiones por segundo (`10r/s`).
* **Ráfaga (Burst):** Permite un exceso momentáneo de hasta 20 peticiones en cola (`burst=20 nodelay`) antes de devolver un error HTTP `503 Service Unavailable`.

---

## 4. Evidencias de Validación (QA)

Para comprobar el correcto funcionamiento y la reproducibilidad del entorno[cite: 706, 708, 818], se definen las siguientes pruebas de aceptación ejecutables desde la terminal de Kali Linux:

**A. Verificación del mapa de red y asignación IP:**
```bash
sudo docker network inspect -f '{{range .Containers}}{{.IPv4Address}} - {{.Name}}{{"\n"}}{{end}}' zona4_integracion
