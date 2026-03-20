# 🔴 EQUIPO B - Laboratorio de Ciberseguridad
## Red Team vs Blue Team | Infraestructura y Estrategias

---

## 📋 Descripción del Proyecto

Este repositorio contiene el trabajo del **Equipo B** para el laboratorio de ciberseguridad del curso universitario. Somos responsables de **3 de las 6 zonas de red** del laboratorio completo.

El proyecto consiste en:
- Diseñar y preparar un entorno controlado de ciberseguridad
- Endurecer infraestructura, servicios y endpoints
- Ejecutar pruebas ofensivas y defensivas en forma ética
- Documentar técnicamente evidencias, decisiones y resultados

---

## 👥 Integrantes y Roles

| Rol | Nombre | Responsabilidades |
|-----|--------|-------------------|
| **Líder** | Gabriela González | Coordinar sprints, gestionar equipo, representar al equipo |
| **Coder** | Martín Ortega | Scripts, hardening, infraestructura Docker, automatización |
| **Hunter** | Giuseppe Queirolo | Investigar herramientas, controles, vectores de ataque |
| **Writer** | Constanza Flores | Documentar avances, informes, consolidar evidencias |
| **Integrador/QA** | Marcelo Fernández | Validar calidad, reproducibilidad, consistencia |

---

## 🗺️ Zonas a Nuestro Cargo

El Equipo B es responsable de las siguientes zonas de red:

| Zona | Segmento IP | Propósito | Servicios a desplegar |
|------|-------------|-----------|----------------------|
| **Zona 4 - Integración** | 10.2.4.0/24 | API Gateway, App Servers | crAPI, Kong/NGINX, balanceador, RabbitMQ |
| **Zona 5 - Backend** | 10.2.5.0/24 | Base de datos y servicios core | Juice Shop, PostgreSQL, Redis, RabbitMQ |
| **Zona 6 - Red Usuarios** | 10.3.0.0/24 | Usuarios finales y SOC | Kali Linux, Wazuh/ELK, servidor C2 simulado |

---

## 🚀 Instalación Rápida

### 1. Clonar el repositorio
```bash
git clone https://github.com/tuusuario/equipo-b-lab.git
cd equipo-b-lab
