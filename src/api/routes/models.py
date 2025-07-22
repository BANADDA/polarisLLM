"""
Model management endpoints (OpenAI compatible)
"""

from fastapi import APIRouter, HTTPException, Depends

from ..models import ModelListResponse, ModelInfo
from ..server import get_runtime
from ...core.runtime import PolarisRuntime

router = APIRouter()

@router.get("/models", response_model=ModelListResponse)
async def list_models(runtime: PolarisRuntime = Depends(get_runtime)):
    """List available models (OpenAI compatible)"""
    
    try:
        models_info = await runtime.list_models()
        available_models = models_info.get('available', [])
        
        # Transform to OpenAI format
        model_list = []
        for model in available_models:
            model_list.append(ModelInfo(
                id=model['name'],
                owned_by="polaris"
            ))
        
        return ModelListResponse(data=model_list)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

@router.get("/models/{model_name}")
async def get_model_info(
    model_name: str,
    runtime: PolarisRuntime = Depends(get_runtime)
):
    """Get information about a specific model"""
    
    try:
        # Check if model exists in registry
        model_config = runtime.model_manager.get_model_config(model_name)
        if not model_config:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        # Get runtime status if running
        model_status = await runtime.get_model_status(model_name)
        
        return {
            "id": model_name,
            "object": "model",
            "owned_by": "polaris",
            "config": {
                "model_id": model_config.model_id,
                "model_type": model_config.model_type,
                "template": model_config.template,
                "description": model_config.description,
                "tags": model_config.tags
            },
            "status": {
                "is_running": model_status is not None,
                "status": model_status.status if model_status else "stopped",
                "port": model_status.port if model_status else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")