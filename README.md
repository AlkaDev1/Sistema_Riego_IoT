# Sistema_De_Control_Riego_ESP32
Sistema de control de riego por medio de una red de 4 ESP32 conectados a una pagina web local.

## Panel de zonas

La primera pantalla implementada es el panel de zonas para escritorio, con los datos de ejemplo en `static/data/zonas.json`. Incluye el encabezado, resumen del sistema, cuatro tarjetas de zona, alertas y pie común. Las tarjetas y los enlaces de navegación ya apuntan a las rutas provisionales para las siguientes pantallas.

También está implementado el detalle de la Zona 2 (`zona.html?id=2`) con la ficha de Albahaca, gráficas SVG, métricas, historial y riego manual simulado. Las demás zonas de detalle permanecen provisionales; en particular, la Zona 4 conserva su variante sin planta para una etapa posterior.

### Ejecución local

No abrir `static/index.html` con doble clic: los módulos y `fetch` necesitan HTTP.

```text
cd static
python -m http.server 8000
```

Después visitar `http://localhost:8000` en el navegador. El uso de localhost solo corresponde al comando local de desarrollo; no está escrito en el código de la aplicación.

### Decisiones del mockup

- El nombre de la aplicación es **Sistema**, porque es el nombre consistente en el encabezado del mockup.
- En las tarjetas del panel la planta aparece una sola vez, junto con su foto. El detalle de zona será el lugar para la ficha completa.
- El subtítulo usa el estilo pequeño y secundario en todas las pantallas.
- Un nodo está “en línea” cuando reportó en el último ciclo esperado. Una zona sin lecturas mostrará “Sin lecturas todavía” en el detalle.
- Se usa punto decimal para México: por ejemplo, `3.70 V`.
- La gráfica de detalle ocupará todo el ancho disponible y sus etiquetas se adaptarán al tamaño de pantalla.
- No se muestran notas de validación de los mockups ni valores `undefined` o `null`; los datos faltantes se representan como `—`.
- El menú móvil tendrá separación suficiente y desplazamiento interno si la pantalla no alcanza.

### Responsive

El estilo parte de celular y agrega estos puntos de quiebre: `620px` para móvil amplio, `900px` para tableta y el diseño de escritorio desde `901px`. El panel de escritorio usa cuatro tarjetas de zona en una fila; tableta usa dos columnas y móvil una.

## Backend

El servidor corre en Python 3.11 o superior con FastAPI y Uvicorn. Se conecta a PostgreSQL 15 o superior y sirve tanto la API REST como la aplicación web estática.

### Prerrequisitos

- Python 3.11+
- PostgreSQL 15+
- El cliente `psql` disponible en la terminal

### 1. Crear la base de datos y el usuario

Ejecutar como superusuario de PostgreSQL (una sola vez):

```bash
sudo -u postgres psql -c "CREATE ROLE riego_user LOGIN PASSWORD 'tu_contraseña';"
sudo -u postgres createdb -O riego_user riego_iot
sudo -u postgres psql -d riego_iot -c "GRANT ALL ON SCHEMA public TO riego_user;"
```

### 2. Cargar los scripts SQL

El orden importa: primero el DDL y luego los datos iniciales.

```bash
psql -h localhost -U riego_user -d riego_iot -f backend/sql/schema.sql
psql -h localhost -U riego_user -d riego_iot -f backend/sql/datos_iniciales.sql
```

### 3. Crear el archivo .env

```bash
cp .env.example .env
```

Editar `.env` con los datos reales de conexión:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=riego_iot
DB_USER=riego_user
DB_PASSWORD=tu_contraseña
```

El archivo `.env` nunca se sube al repositorio (está en `.gitignore`).

### 4. Crear el entorno virtual e instalar dependencias

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 5. Arrancar el servidor

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

Agregar `--reload` durante el desarrollo para que el servidor se reinicie al guardar cambios.

El servidor queda disponible en:
- **Laptop:** `http://localhost:8000`
- **Celular u otro dispositivo en la misma red:** `http://<IP-de-la-laptop>:8000`

Para conocer la IP local de la laptop: `ip a` en Linux/Mac o `ipconfig` en Windows.

### 6. Abrir el puerto en el firewall (Windows)

Si la laptop usa Windows y el celular no puede conectarse, agregar una regla de entrada:

```
Panel de control → Firewall de Windows Defender → Reglas de entrada
→ Nueva regla → Puerto → TCP 8000 → Permitir la conexión
```

### 7. Verificar que el servidor funciona

```bash
curl http://localhost:8000/api/salud
# → {"estado":"ok","base_de_datos":"conectada"}
```

La documentación interactiva de la API está en `http://localhost:8000/docs`.

---

