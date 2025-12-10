from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from contextlib import asynccontextmanager

from app.infrastructure.routes.home import home_route
from app.infrastructure.routes.user import user_route
from app.infrastructure.routes.html_routes import html_router
from app.infrastructure.routes.transaction import transactions_router
from app.infrastructure.routes.ml_routes import ml_router
import database.database
from config.app_config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database connection...")
    await database.database.get_database_engine()
    logger.info("Creating database tables...")
    await database.database.init_db(drop_all=False)
    logger.info("Application startup completed successfully")
    yield
    logger.info("Application shutting down, disposing database engine...")
    await database.database.disconnect_db()

def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    
    app = FastAPI(
        # title=settings.APP_NAME,
        # description=settings.APP_DESCRIPTION,
        # version=settings.API_VERSION,
        title="ML Prediction Service",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan = lifespan  # ← ИСПОЛЬЗУЕМ lifespan вместо on_event
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(html_router)
    app.include_router(home_route, tags=['Home'])
    app.include_router(user_route, prefix='/api/users', tags=['Users'])
    app.include_router(transactions_router, prefix="/api/transaction", tags=["Transaction"])
    app.include_router(ml_router, prefix="/api/ml", tags=["MLModel"])

    return app

app = create_application()


if __name__ == '__main__':
    exclude_cache = ".cache"
    logging.basicConfig(level=logging.DEBUG)
    uvicorn.run(
        'api:app',
        host='0.0.0.0',
        port=8080,
        reload=True,
        log_level="info",
        reload_excludes = [exclude_cache]
    )

