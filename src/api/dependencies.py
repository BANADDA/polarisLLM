"""
FastAPI Dependencies for PolarisLLM API
"""

from typing import Optional

from fastapi import HTTPException

# Import the CLI's orchestration system instead of the old runtime
from polarisllm.core import ModelRegistry, PolarisConfig

# Global components (set by server.py)
_config: Optional[PolarisConfig] = None
_registry: Optional[ModelRegistry] = None

def set_orchestration_components(config: PolarisConfig, registry: ModelRegistry) -> None:
    """Set the global orchestration components"""
    global _config, _registry
    _config = config
    _registry = registry

def get_model_registry() -> ModelRegistry:
    """Get the model registry for FastAPI dependency injection"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Model registry not initialized")
    return _registry

def get_config() -> PolarisConfig:
    """Get the config for FastAPI dependency injection"""
    if _config is None:
        raise HTTPException(status_code=503, detail="Config not initialized")
    return _config

# Legacy compatibility - will be removed
def get_runtime():
    """Legacy compatibility function"""
    raise HTTPException(status_code=503, detail="Legacy runtime system disabled. Use new orchestration system.") 