"""
Pydantic models for API requests and responses
"""

from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field
import time

# Chat Completion Models (OpenAI Compatible)

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    top_p: Optional[float] = Field(default=1.0, ge=0, le=1)
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = Field(default=0, ge=-2, le=2)
    frequency_penalty: Optional[float] = Field(default=0, ge=-2, le=2)

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None

class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage

# Streaming Models

class ChatCompletionChunkChoice(BaseModel):
    index: int
    delta: Dict[str, Any]
    finish_reason: Optional[str] = None

class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatCompletionChunkChoice]

# Model List Models

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "polaris"

class ModelListResponse(BaseModel):
    object: str = "list"
    data: List[ModelInfo]

# Admin Models

class LoadModelRequest(BaseModel):
    model_name: str
    swift_args: Optional[Dict[str, Any]] = {}

class LoadModelResponse(BaseModel):
    success: bool
    message: str
    model_name: str
    port: Optional[int] = None
    status: str

class ModelStatusResponse(BaseModel):
    name: str
    model_id: str
    status: str
    port: int
    pid: Optional[int] = None
    memory_usage: Optional[float] = None
    gpu_usage: Optional[float] = None
    last_activity: Optional[float] = None
    error_message: Optional[str] = None

class RuntimeStatusResponse(BaseModel):
    total_models: int
    running_models: int
    available_models: List[str]
    running_model_details: List[ModelStatusResponse]
    resource_usage: Dict[str, Any]

class AddModelConfigRequest(BaseModel):
    name: str
    model_id: str
    model_type: str
    template: Optional[str] = None
    description: str = ""
    tags: List[str] = []
    swift_args: Dict[str, Any] = {}
    enabled: bool = True

# Error Models

class ErrorResponse(BaseModel):
    error: str
    message: str
    code: Optional[str] = None