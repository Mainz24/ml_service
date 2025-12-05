from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from app.infrastructure.routes.home import home_route
from app.infrastructure.routes.user import user_route
from app.infrastructure.routes.transaction import transactions_router
from app.infrastructure.routes.ml_routes import ml_router
from database.database import init_db, get_database_engine, disconnect_db
from config.app_config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()

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
        docs_url="/api/docs",
        redoc_url="/api/redoc"
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
    app.include_router(home_route, tags=['Home'])
    app.include_router(user_route, prefix='/api/users', tags=['Users'])
    app.include_router(transactions_router, prefix="/api/transaction", tags=["Transaction"])
    app.include_router(ml_router, prefix="/api/ml", tags=["MLModel"])

    return app

app = create_application()

@app.on_event("startup")
async def on_startup():
    try:
        logger.info("Initializing database connection...")
        await get_database_engine()  # Подключение и создие engine/sessionmaker
        logger.info("Creating database tables...")
        await init_db(drop_all=False)
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Application shutting down, disposing database engine...")
    await disconnect_db() # Отключение

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