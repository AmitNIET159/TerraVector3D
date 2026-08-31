"""BhuDrishti 3D — FastAPI application entry point."""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.config import get_settings
from app.routers import health, parcels, buildings, spatial_units, identity, rights, topology, geospatial, reports

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_TITLE,
        version=settings.APP_VERSION,
        description="Master backend API for BhuDrishti 3D — a 3D cadastral management system."
    )

    app.include_router(health.router)
    app.include_router(parcels.router, prefix="/api/v1")
    app.include_router(buildings.router, prefix="/api/v1")
    app.include_router(spatial_units.router, prefix="/api/v1")
    app.include_router(identity.router, prefix="/api/v1")
    app.include_router(rights.router, prefix="/api/v1")
    app.include_router(topology.router, prefix="/api/v1")
    app.include_router(geospatial.router, prefix="/api/v1")
    app.include_router(reports.router, prefix="/api/v1")

    @app.exception_handler(OperationalError)
    async def db_exception_handler(request: Request, exc: OperationalError):
        logger.error("Database error: %s", exc)
        return JSONResponse(status_code=503, content={"detail": "Database connection failed."})

    @app.on_event("startup")
    async def startup_event():
        try:
            from app.services.module_adapter import verify_all_modules
            module_status = verify_all_modules()
            for name, available in module_status.items():
                if available:
                    logger.info("Module '%s' found and ready", name)
                else:
                    logger.warning("Module '%s' NOT found", name)
        except Exception as e:
            logger.error("Failed to verify modules: %s", e)

    return app

app = create_app()
