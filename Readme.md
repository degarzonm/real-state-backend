# Microservicios de Consulta de Inmuebles y “Me gusta”
> **Autor:** Danny Esteban Garzón  
> **Versión:** 1.0.0  

---

## 1. Introducción

Este repositorio contiene un microservicio REST _sin frameworks externos_ que permite a los usuarios consultar los inmuebles
almacenados en **MySQL** y filtrarlos por _año de construcción, ciudad_ y _estado actual_
(`pre_venta`, `en_venta`, `vendido`).  
Además, se documenta —a nivel **conceptual**— el segundo microservicio requerido para gestionar los
“Me gusta” de cada usuario.

---

## 2. Arquitectura y diseño

### 2.1 Vista general

```text
┌────────────┐   HTTP    ┌────────────────────┐       SQL         ┌──────────────┐
│  Cliente   │ ───────▶ ||  PropertyServer   |│ ───────────────▶ │   MySQL DB   │
└────────────┘           │  (http.server)     │                   └──────────────┘
                         │    └─ Handler      │
                         │        └─ Service  │
                         │            └─ DAO  │
                         └────────────────────┘
```

* **Cliente**: Frontend o herramienta de pruebas que consume la API REST, usamos peticiones curl y postman para simular.  
* **PropertyServer**: Servidor HTTP ligero (basado en `http.server`) que inyecta dependencias _por
  composición_, facilitando _testeabilidad_.  
* **Handler**: Interpreta la solicitud, valida _query params_ y delega al `Service`.  
* **Service**: Orquesta la lógica de negocio (filtros, paginación, validaciones).  
* **DAO / Data‑access**: Ejecuta sentencias SQL parametrizadas contra MySQL.

### 2.2 Patrones de diseño aplicados

| Patrón | Uso en el proyecto | Justificación |
|--------|-------------------|---------------|
| **Dependency Injection** | `make_handler(service)` y el constructor de `PropertyService` permiten inyectar mocks durante pruebas unitarias. | Facilita **TDD** y desacopla capas. |
| **Factory Function** | `make_handler` genera clases _ad‑hoc_ con dependencias pre‑configuradas. | Evita _singletons_ y favorece composición. |
| **DAO (Data Access Object)** | `data_access.py` centraliza la interacción con MySQL. | Aísla SQL y simplifica un cambio futuro a cualquier tipo de DB. |
| **Repository‑like Service** | `PropertyService` agrega reglas de negocio (p. ej. paginación segura, filtros). | Separa dominio de infraestructura. |
| **Thin Controller** | El `Handler` sólo coordina y nunca contiene lógica de dominio. | Siguiendo buenas prácticas como _Single Responsibility_. |
| **DTO ligero** | Se devuelven `dict` planos → bajo _overhead_, fácil de serializar. | Por simpleza no usamos herramientas como Pydantic y similares. |

### 2.3 Estructura de carpetas

```
.
├── app/
│   ├── config.py          # Gestión de variables de entorno y defaults
│   ├── data_access.py     # DAO – SQL parametrizado
│   ├── handlers.py        # HTTP request handlers
│   ├── models.py          # Keys de los DTO
│   ├── services.py        # Reglas de negocio
│   ├── server.py          # Encapsula HTTPServer
│   └── __init__.py
├── tests/                 # Unit & integration tests (unittest)
├── .env                   # Credenciales (excluidas en producción!!)
├── requirements.txt
└── README.md              # (este archivo)
```

### 2.4 Modelo de datos (consulta)

*Tabla `property`*  
(id, address, city, price, description, year)

*Tabla `status_history`*  
(id, property_id, status_id, update_date)

*Tabla `status`*  
(id, name)

> **Regla de negocio:**  
> El **estado vigente** de un inmueble es el *última registro* en `status_history`
  (`ROW_NUMBER() OVER …`).

### 2.5 Extensión conceptual para el servicio “Me gusta”

```text
┌────────┐     1       ┌──────────────────┐       N       ┌───────────────┐
│  user  │─────────────│  property_like   │───────────────│   property    │
└────────┘             └──────────────────┘               └───────────────┘
                         user_id  PK,FK
                         property_id PK,FK
                         liked_at   TIMESTAMP
```

**SQL de referencia**

```sql
CREATE TABLE property_like (
  user_id     BIGINT NOT NULL,
  property_id BIGINT NOT NULL,
  liked_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, property_id),
  FOREIGN KEY (user_id)     REFERENCES user(id),
  FOREIGN KEY (property_id) REFERENCES property(id)
);
```

*Motivación*:  
Clave compuesta `(user_id, property_id)` impide duplicados como más de un me gusta por propiedad/usuario; `liked_at` preserva histórico.

---

## 3. Decisiones técnicas y dudas resueltas

| # | Duda / Decisión | Resolución |
|---|-----------------|------------|
| 1 | **¿GET o POST para filtrar?** | GET con _query params_;&nbsp;la operación es idempotente y cacheable. |
| 2 | **Manejo de datos inconsistentes** | Excluir registros sin `address`, `city` o `price`. Se loggea la omisión. |
| 3 | **SQL injection** | Uso sistemático de *place‑holders* `%s` en la capa DAO. algunos frameworks integran esto directamente |
| 4 | **Sin ORMs / frameworks** | Librería estándar + `mysql‑connector‑python` ⇒ simplifica despliegue y alinea con la restricción de la prueba. |
| 5 | **Paginación segura** | `page_size` limitado ∈ [1, 100]; valores inválidos ⇒ _defaults_. |
| 6 | **Fechas fuera de rango** | Años \< 1700 o \> 2050 se sustituyen por `DEFAULT_YEAR_FILTER` (2019). |
| 7 | **Inyección de dependencias** | Handlers y servicios reciben módulos/funciones mockeables en tests. |
| 8 | **Variables de entorno** | `.env` + `python‑dotenv`; alternativa “12 Factor”. |
| 9 | **Logging** | Actualmente `print` para simplicidad del ejercicio; debemos usar `logging` con niveles. |
|10 | **Concurrencia y “Me gusta”** | Bloqueo optimista mediante PK compuesta evita condiciones de carrera básicas. |
|11 | **Seguridad de credenciales** | En producción, usar _secret managers_ (AWS SSM, Vault). |

---

## 4. Instalación y ejecución

### 4.1 Requisitos previos

* Python **3.10+**  
* MySQL ≥ **8.0** accesible desde el host  
* (Opcional) **venv** o **conda** para aislar dependencias

### 4.2 Clonar el repositorio

```bash
git clone https://github.com/degarzonm/real-state-backend.git
cd real-state-backend
```

### 4.3 Configurar variables de entorno

Copiar y editar `.env`:

```bash
cp .env.example .env
# ↳ Ajustar credenciales y puertos si es necesario
```

> En producción, exportamos las mismas variables como _environment_ o usamos un **secret manager**.

### 4.4 Instalar dependencias

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4.5 Ejecutar el servicio

```bash
python -m app.main
# 🟢 Listening on http://0.0.0.0:8000
```

Ejemplo de petición:

```bash
curl "http://localhost:8000/properties?city=bogota&status=en_venta,pre_venta&page=1&size=20"
```

### 4.6 Ejecutar las pruebas

```bash
python -m unittest discover -s tests -v
```

---

## 5. Roadmap y mejoras futuras

* **Swagger / OpenAPI**: Generación automática de contratos.
* **Dockerfile & docker‑compose**: Simplificar despliegues locales.
* **Logging estructurado**: Integración con ELK / Loki.
* **Middleware de seguridad**: Autenticación/JWT para futuras rutas de “Me gusta”.
* **CI/CD**: GitHub Actions con lint + tests.
* **ORM opcional**: SQLAlchemy (**core**) manteniendo el control de SQL.

## 6.Propuesta de rediseño del modelo para acelerar consultas
### 6.1 Problema detectado

La consulta actual:
```sql
SELECT …  
FROM property p
JOIN (
  SELECT …
  FROM status_history
  ROW_NUMBER() OVER (PARTITION BY property_id ORDER BY update_date DESC) = 1
) ls ON p.id = ls.property_id
JOIN status s ON ls.status_id = s.id
WHERE …
```
`ROW_NUMBER()` recorre todo status_history. Dos joins por solicitud elevan latencia y consumo de recursos.

### 6.2 Estrategia: denormalización controlada

```text
┌──────────────────┐ 1 ── N ┌────────────────┐
│  property        │        │ status_history │
│──────────────────│        └────────────────┘
│ id PK            │
│ address          │
│ city             │
│ price            │
│ year             │
│ description      │
│ current_status_id|  FK → status.id   ←─┐ « cache »
└──────────────────┘                     │
                                         │ 1
                                 ┌───────┴────────┐
                                 │    status      │
                                 └────────────────┘
```

### 6.3 SQL de migración

```sql
-- 1. Agregamos una nueva columna en property
ALTER TABLE property ADD COLUMN current_status_id BIGINT NULL,
                     ADD CONSTRAINT fk_prop_status
                     FOREIGN KEY (current_status_id) REFERENCES status(id);

-- 2. Poblar la columna al momento de la migración para guardar el estado actual de cada inmueble
UPDATE property p
JOIN (
  SELECT sh.property_id, sh.status_id
  FROM status_history sh
  JOIN (
    SELECT property_id, MAX(update_date) AS max_date
    FROM status_history GROUP BY property_id
  ) mx USING (property_id, update_date)
) latest USING (property_id)
SET p.current_status_id = latest.status_id;

-- 3. Trigger para actualizar property.current_status_id al insertar en status_history

CREATE TRIGGER trg_status_history_update
AFTER INSERT ON status_history
FOR EACH ROW
BEGIN
  UPDATE property
  SET current_status_id = NEW.status_id
  WHERE id = NEW.property_id;
END

-- 4. Índices
CREATE INDEX idx_property_city_status ON property (city, current_status_id);
CREATE INDEX idx_property_year        ON property (year);
```

### 6.4 Ventajas

La nueva consulta sería más simple, rápida y eficiente:

```sql
SELECT
  p.city, p.address, s.name AS status, p.price, p.year, p.description
FROM property p
JOIN status s ON p.current_status_id = s.id
WHERE s.name IN ('pre_venta','en_venta','vendido')
  AND p.city   = ?
  AND p.year   = ?
LIMIT ? OFFSET ?;
```
### 6.5 Otras posibles mejoras

En caso de que nuestra base de datos llegara a escalar demasiado, podemos empezar a considerar _partitioning_ en la tabla `property` y/o `status_history` para mejorar el rendimiento de las consultas y separar los datos en diferentes nodos, 