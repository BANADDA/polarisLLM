"""
FastAPI Server for PolarisLLM Runtime Engine
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

from ..core.runtime import PolarisRuntime
from .models import *
from .routes import chat, models, admin

# Global runtime instance
runtime: Optional[PolarisRuntime] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global runtime
    
    # Startup
    logging.info("Starting PolarisLLM Runtime Engine")
    runtime = PolarisRuntime()
    await runtime.start()
    
    yield
    
    # Shutdown  
    logging.info("Shutting down PolarisLLM Runtime Engine")
    if runtime:
        await runtime.stop()

def create_app() -> FastAPI:
    """Create FastAPI application"""
    
    app = FastAPI(
        title="PolarisLLM Runtime Engine",
        description="High-performance multi-model LLM runtime engine using ms-swift",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(chat.router, prefix="/v1", tags=["chat"])
    app.include_router(models.router, prefix="/v1", tags=["models"])
    app.include_router(admin.router, prefix="/admin", tags=["admin"])
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "runtime": "running" if runtime else "stopped",
            "models": len(runtime.running_models) if runtime else 0
        }
    
    @app.get("/")
    async def root():
        """Root endpoint with API information"""
        return {
            "name": "PolarisLLM Runtime Engine",
            "version": "1.0.0",
            "description": "Multi-model LLM runtime engine",
            "endpoints": {
                "chat": "/v1/chat/completions",
                "models": "/v1/models",
                "admin": "/admin",
                "health": "/health",
                "docs": "/docs"
            }
        }
    
    return app

def get_runtime() -> PolarisRuntime:
    """Get the global runtime instance"""
    if runtime is None:
        raise HTTPException(status_code=503, detail="Runtime not initialized")
    return runtime

async def run_server(
    host: str = "0.0.0.0",
    port: int = 7860,
    reload: bool = False,
    log_level: str = "info"
):
    """Run the FastAPI server"""
    config = uvicorn.Config(
        "src.api.server:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True
    )
    
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(run_server())