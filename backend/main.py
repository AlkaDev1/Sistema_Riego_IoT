"""
main.py — Punto de entrada del servidor FastAPI.

Arranca con:
    uvicorn main:app --host 0.0.0.0 --port 8000

Las rutas /api/... se registran antes del montaje de static/ para que
los endpoints no queden tapados por los archivos estáticos.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import config
import db

# ── Logging básico ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── Scheduler (los jobs se agregan en Tareas 2 y 3) ─────────────────────────
scheduler = AsyncIOScheduler()


# ── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Abriendo pool de conexiones...")
    await db.open_pool(config.CONNINFO)

    logger.info("Cargando tabla configuracion...")
    config.cfg.update(await config.load_cfg(db.pool))
    logger.info("Configuración cargada: %s", config.cfg)

    scheduler.start()
    logger.info("Scheduler iniciado.")

    yield

    scheduler.shutdown()
    logger.info("Scheduler detenido.")
    await db.close_pool()
    logger.info("Pool cerrado.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Sistema IoT de riego",
    description="API del sistema de monitoreo de plantas con nodos ESP32.",
    version="0.1.0",
    lifespan=lifespan,
)


# ── Ruta de salud ─────────────────────────────────────────────────────────────
@app.get(
    "/api/salud",
    summary="Estado del servidor y la base de datos",
    tags=["Sistema"],
)
async def salud():
    """
    Verifica que el servidor está en pie y puede consultar la base de datos.

    - **200** `{"estado": "ok", "base_de_datos": "conectada"}`
    - **503** `{"estado": "error", "base_de_datos": "sin conexión", "detalle": "..."}`
    """
    try:
        async with db.pool.connection() as conn:
            await conn.execute("SELECT 1")
        return {"estado": "ok", "base_de_datos": "conectada"}
    except Exception as exc:
        logger.error("Fallo en /api/salud: %s", exc)
        return JSONResponse(
            status_code=503,
            content={
                "estado": "error",
                "base_de_datos": "sin conexión",
                "detalle": "No se pudo ejecutar una consulta de prueba.",
            },
        )


# ── Manejadores de error globales ─────────────────────────────────────────────
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detalle": "Recurso no encontrado."},
    )


@app.exception_handler(405)
async def method_not_allowed_handler(request, exc):
    return JSONResponse(
        status_code=405,
        content={"detalle": "Método no permitido."},
    )


# ── Archivos estáticos (debe ir DESPUÉS de las rutas /api/) ──────────────────
_static_dir = Path(__file__).parent.parent / "static"
app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")
