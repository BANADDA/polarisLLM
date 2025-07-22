"""
Chat completion endpoints (OpenAI compatible)
"""

import asyncio
import json
import uuid
import time
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import aiohttp

from ..models import ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChunk
from ..models import ChatCompletionChoice, ChatMessage, ChatCompletionUsage
from ..models import ChatCompletionChunkChoice, ErrorResponse
from ..server import get_runtime
from ...core.runtime import PolarisRuntime

router = APIRouter()

@router.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    runtime: PolarisRuntime = Depends(get_runtime)
):
    """Create a chat completion (OpenAI compatible)"""
    
    # Check if model is running
    model_status = await runtime.get_model_status(request.model)
    if not model_status or model_status.status != 'running':
        raise HTTPException(
            status_code=404,
            detail=f"Model {request.model} is not running. Please load it first."
        )
    
    # Prepare request for ms-swift backend
    swift_request = {
        "model": model_status.model_id,
        "messages": [msg.dict() for msg in request.messages],
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "top_p": request.top_p,
        "stream": request.stream,
        "stop": request.stop,
    }
    
    if request.stream:
        return StreamingResponse(
            _stream_chat_completion(swift_request, model_status.port, request.model),
            media_type="text/plain"
        )
    else:
        return await _non_stream_chat_completion(swift_request, model_status.port, request.model)

async def _non_stream_chat_completion(swift_request: dict, port: int, model_name: str):
    """Handle non-streaming chat completion"""
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://localhost:{port}/v1/chat/completions",
                json=swift_request,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Model inference failed: {error_text}"
                    )
                
                result = await response.json()
                
                # Transform response to match OpenAI format
                return ChatCompletionResponse(
                    id=f"polaris-{uuid.uuid4().hex[:8]}",
                    model=model_name,
                    choices=[
                        ChatCompletionChoice(
                            index=choice.get("index", 0),
                            message=ChatMessage(
                                role=choice["message"]["role"],
                                content=choice["message"]["content"]
                            ),
                            finish_reason=choice.get("finish_reason")
                        )
                        for choice in result.get("choices", [])
                    ],
                    usage=ChatCompletionUsage(
                        prompt_tokens=result.get("usage", {}).get("prompt_tokens", 0),
                        completion_tokens=result.get("usage", {}).get("completion_tokens", 0),
                        total_tokens=result.get("usage", {}).get("total_tokens", 0)
                    )
                )
                
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to model: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

async def _stream_chat_completion(
    swift_request: dict, 
    port: int, 
    model_name: str
) -> AsyncGenerator[str, None]:
    """Handle streaming chat completion"""
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://localhost:{port}/v1/chat/completions",
                json=swift_request,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    error_chunk = {
                        "error": "model_error",
                        "message": f"Model inference failed: {error_text}"
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"
                    return
                
                completion_id = f"polaris-{uuid.uuid4().hex[:8]}"
                
                async for line in response.content:
                    line_text = line.decode('utf-8').strip()
                    
                    if line_text.startswith('data: '):
                        data_part = line_text[6:]  # Remove 'data: ' prefix
                        
                        if data_part == '[DONE]':
                            yield "data: [DONE]\n\n"
                            break
                        
                        try:
                            # Parse the chunk from ms-swift
                            chunk_data = json.loads(data_part)
                            
                            # Transform to OpenAI format
                            polaris_chunk = ChatCompletionChunk(
                                id=completion_id,
                                model=model_name,
                                choices=[
                                    ChatCompletionChunkChoice(
                                        index=choice.get("index", 0),
                                        delta=choice.get("delta", {}),
                                        finish_reason=choice.get("finish_reason")
                                    )
                                    for choice in chunk_data.get("choices", [])
                                ]
                            )
                            
                            yield f"data: {polaris_chunk.json()}\n\n"
                            
                        except json.JSONDecodeError:
                            # Skip invalid JSON lines
                            continue
                    
                    elif line_text:  # Non-empty non-data line
                        yield f"{line_text}\n"
                
    except aiohttp.ClientError as e:
        error_chunk = {
            "error": "connection_error", 
            "message": f"Failed to connect to model: {str(e)}"
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
    except Exception as e:
        error_chunk = {
            "error": "internal_error",
            "message": f"Internal error: {str(e)}"
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"