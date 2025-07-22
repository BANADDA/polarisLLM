"""
Admin endpoints for runtime management
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from ..models import (
    LoadModelRequest, LoadModelResponse, ModelStatusResponse,
    RuntimeStatusResponse, AddModelConfigRequest
)
from ..server import get_runtime
from ...core.runtime import PolarisRuntime
from ...core.config import ModelConfig

router = APIRouter()

@router.post("/models/load", response_model=LoadModelResponse)
async def load_model(
    request: LoadModelRequest,
    background_tasks: BackgroundTasks,
    runtime: PolarisRuntime = Depends(get_runtime)
):
    """Load a model for serving"""
    
    try:
        # Check if model config exists
        model_config = runtime.model_manager.get_model_config(request.model_name)
        if not model_config:
            raise HTTPException(
                status_code=404,
                detail=f"Model configuration not found: {request.model_name}"
            )
        
        # Load the model
        model_status = await runtime.load_model(request.model_name, **request.swift_args)
        
        return LoadModelResponse(
            success=True,
            message=f"Model {request.model_name} loaded successfully",
            model_name=request.model_name,
            port=model_status.port,
            status=model_status.status
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

@router.post("/models/{model_name}/unload")
async def unload_model(
    model_name: str,
    runtime: PolarisRuntime = Depends(get_runtime)
):
    """Unload a running model"""
    
    try:
        success = await runtime.stop_model(model_name)
        
        if success:
            return {"success": True, "message": f"Model {model_name} unloaded successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Model {model_name} is not running")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unload model: {str(e)}")

@router.get("/models/{model_name}/status", response_model=ModelStatusResponse)
async def get_model_status(
    model_name: str,
    runtime: PolarisRuntime = Depends(get_runtime)
):
    """Get status of a specific model"""
    
    try:
        model_status = await runtime.get_model_status(model_name)
        
        if not model_status:
            raise HTTPException(status_code=404, detail=f"Model {model_name} is not running")
        
        return ModelStatusResponse(
            name=model_status.name,
            model_id=model_status.model_id,
            status=model_status.status,
            port=model_status.port,
            pid=model_status.pid,
            memory_usage=model_status.memory_usage,
            gpu_usage=model_status.gpu_usage,
            last_activity=model_status.last_activity,
            error_message=model_status.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(e)}")

@router.get("/status", response_model=RuntimeStatusResponse)
async def get_runtime_status(runtime: PolarisRuntime = Depends(get_runtime)):
    """Get overall runtime status"""
    
    try:
        models_info = await runtime.list_models()
        
        running_models = []
        for model_name, status_data in models_info.get('running', {}).items():
            running_models.append(ModelStatusResponse(**status_data))
        
        return RuntimeStatusResponse(
            total_models=models_info.get('total_available', 0),
            running_models=models_info.get('total_running', 0),
            available_models=[m['name'] for m in models_info.get('available', [])],
            running_model_details=running_models,
            resource_usage={
                "memory": sum(m.memory_usage or 0 for m in running_models),
                "active_ports": len([m for m in running_models if m.status == 'running'])
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get runtime status: {str(e)}")

@router.get("/models/available")
async def list_available_models(runtime: PolarisRuntime = Depends(get_runtime)):
    """List all available model configurations"""
    
    try:
        models_info = await runtime.list_models()
        return {
            "available": models_info.get('available', []),
            "count": len(models_info.get('available', []))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list available models: {str(e)}")

@router.get("/models/running")
async def list_running_models(runtime: PolarisRuntime = Depends(get_runtime)):
    """List all currently running models"""
    
    try:
        models_info = await runtime.list_models()
        return {
            "running": models_info.get('running', {}),
            "count": len(models_info.get('running', {}))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list running models: {str(e)}")

@router.post("/models/configs")
async def add_model_config(
    request: AddModelConfigRequest,
    runtime: PolarisRuntime = Depends(get_runtime)
):
    """Add a new model configuration"""
    
    try:
        model_config = ModelConfig(
            name=request.name,
            model_id=request.model_id,
            model_type=request.model_type,
            template=request.template,
            description=request.description,
            tags=request.tags,
            swift_args=request.swift_args,
            enabled=request.enabled
        )
        
        success = runtime.model_manager.add_model_config(model_config)
        
        if success:
            return {"success": True, "message": f"Model configuration {request.name} added successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add model configuration")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add model config: {str(e)}")

@router.delete("/models/configs/{model_name}")
async def remove_model_config(
    model_name: str,
    runtime: PolarisRuntime = Depends(get_runtime)
):
    """Remove a model configuration"""
    
    try:
        # Check if model is currently running
        model_status = await runtime.get_model_status(model_name)
        if model_status and model_status.status == 'running':
            raise HTTPException(
                status_code=400,
                detail=f"Cannot remove config for running model {model_name}. Stop it first."
            )
        
        success = runtime.model_manager.remove_model_config(model_name)
        
        if success:
            return {"success": True, "message": f"Model configuration {model_name} removed successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Model configuration {model_name} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove model config: {str(e)}")