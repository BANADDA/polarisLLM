"""
Deploy Command Handler
"""

import subprocess
from typing import Dict, Optional

from ..core import (LogManager, ModelRegistry, PolarisConfig, PortManager,
                    ProcessManager)


def handle_deploy_command(args) -> bool:
    """Handle model deployment command
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    print(f"🚀 Deploying model: {args.model}")
    
    # Initialize core components
    config = PolarisConfig()
    registry = ModelRegistry(config)
    port_manager = PortManager(config)
    process_manager = ProcessManager(config)
    log_manager = LogManager(config)
    
    # Auto-detect model parameters
    model_type, model_id = _resolve_model_params(args)
    
    print(f"   Model Type: {model_type}")
    print(f"   Model ID: {model_id}")
    print()
    
    # Check if model is already deployed
    existing_model = registry.get_model_info(args.model)
    if existing_model:
        if existing_model.status == "running":
            print(f"⚠️  Model {args.model} is already running on port {existing_model.port}")
            print(f"   Use 'polarisllm stop {args.model}' to stop it first")
            return False
        else:
            print(f"ℹ️  Found existing deployment of {args.model}, restarting...")
            # Stop any existing process
            if existing_model.pid:
                process_manager.stop_process(args.model)
    
    # Allocate port
    port = port_manager.allocate_port(args.model)
    if not port:
        print(f"❌ No available ports in range {port_manager.port_start}-{port_manager.port_end}")
        return False
    
    print(f"📡 Allocated port: {port}")
    
    # Create log file
    log_file = log_manager.create_log_file(args.model)
    
    # Build swift command
    swift_cmd = [
        "swift", "deploy",
        "--model_type", model_type,
        "--model", model_id,
        "--port", str(port),
        "--host", "0.0.0.0"
    ]
    
    # Add any additional swift args
    if hasattr(args, 'swift_args') and args.swift_args:
        for key, value in args.swift_args.items():
            swift_cmd.extend([f"--{key}", str(value)])
    
    print(f"🔧 Command: {' '.join(swift_cmd)}")
    print(f"📝 Logs: {log_file}")
    print()
    
    # Start deployment in background
    print("🚀 Starting deployment in background...")
    
    try:
        # Start background process
        pid = process_manager.start_background_process(
            cmd=swift_cmd,
            model_name=args.model,
            log_file=log_file
        )
        
        if pid:
            # Register model in registry
            registry.register_model(
                name=args.model,
                model_id=model_id,
                model_type=model_type,
                port=port,
                pid=pid,
                swift_args=getattr(args, 'swift_args', {})
            )
            
            print(f"✅ Model deployment started successfully!")
            print(f"   Name: {args.model}")
            print(f"   PID: {pid}")
            print(f"   Port: {port}")
            print(f"   Status: Initializing...")
            print()
            print(f"🔍 Monitor with: polarisllm logs {args.model} --follow")
            print(f"📊 Check status: polarisllm status")
            print(f"🌐 Access via: http://localhost:7860/v1/chat/completions")
            
            return True
        else:
            print("❌ Failed to start deployment process")
            # Release allocated port
            port_manager.release_port(port, args.model)
            return False
            
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        # Release allocated port
        port_manager.release_port(port, args.model)
        return False


def _resolve_model_params(args) -> tuple:
    """Resolve model type and ID from arguments
    
    Args:
        args: Command line arguments
        
    Returns:
        Tuple of (model_type, model_id)
    """
    # Convenience shortcuts for popular models
    convenience_shortcuts = {
        "qwen2.5-7b-instruct": {
            "model_type": "qwen2_5", 
            "model_id": "Qwen/Qwen2.5-7B-Instruct"
        },
        "qwen2.5-14b-instruct": {
            "model_type": "qwen2_5",
            "model_id": "Qwen/Qwen2.5-14B-Instruct"
        },
        "qwen2.5-32b-instruct": {
            "model_type": "qwen2_5",
            "model_id": "Qwen/Qwen2.5-32B-Instruct"
        },
        "qwen2.5-72b-instruct": {
            "model_type": "qwen2_5",
            "model_id": "Qwen/Qwen2.5-72B-Instruct"
        },
        "deepseek-vl-7b-chat": {
            "model_type": "deepseek_vl",
            "model_id": "deepseek-ai/deepseek-vl-7b-chat"
        },
        "deepseek-coder-6.7b": {
            "model_type": "deepseek",
            "model_id": "deepseek-ai/deepseek-coder-6.7b-instruct"
        },
        "deepseek-coder-33b": {
            "model_type": "deepseek",
            "model_id": "deepseek-ai/deepseek-coder-33b-instruct"
        },
        "llama3.1-8b-instruct": {
            "model_type": "llama3_1",
            "model_id": "meta-llama/Meta-Llama-3.1-8B-Instruct"
        },
        "llama3.1-70b-instruct": {
            "model_type": "llama3_1",
            "model_id": "meta-llama/Meta-Llama-3.1-70B-Instruct"
        },
        "mistral-7b-instruct": {
            "model_type": "mistral",
            "model_id": "mistralai/Mistral-7B-Instruct-v0.3"
        },
        "yi-34b-chat": {
            "model_type": "yi",
            "model_id": "01-ai/Yi-34B-Chat"
        }
    }
    
    # Check for convenience shortcut
    if args.model in convenience_shortcuts:
        model_info = convenience_shortcuts[args.model]
        model_type = getattr(args, 'model_type', None) or model_info["model_type"]
        model_id = getattr(args, 'model_id', None) or model_info["model_id"]
        print(f"📋 Using convenience shortcut for {args.model}")
        return model_type, model_id
    
    # Direct specification with both parameters
    if hasattr(args, 'model_type') and hasattr(args, 'model_id') and args.model_type and args.model_id:
        print(f"📋 Using direct model specification")
        return args.model_type, args.model_id
    
    # Model type specified, use model name as model_id
    if hasattr(args, 'model_type') and args.model_type:
        print(f"📋 Using model_type: {args.model_type}, model_id: {args.model}")
        return args.model_type, args.model
    
    # Auto-detect from model path
    if "/" in args.model:
        model_id = args.model
        model_type = _auto_detect_model_type(args.model)
        print(f"📋 Auto-detected model type: {model_type}")
        return model_type, model_id
    
    # Default fallback
    print(f"⚠️  Using default model_type: qwen2_5")
    print(f"💡 For better results, specify: --model-type <type> --model-id <id>")
    return "qwen2_5", args.model


def _auto_detect_model_type(model_id: str) -> str:
    """Auto-detect model type from model ID
    
    Args:
        model_id: Model ID string
        
    Returns:
        Detected model type
    """
    model_id_lower = model_id.lower()
    
    # Common model type patterns
    if "qwen2.5" in model_id_lower or "qwen2_5" in model_id_lower:
        return "qwen2_5"
    elif "qwen2-vl" in model_id_lower:
        return "qwen2_vl"
    elif "qwen2" in model_id_lower:
        return "qwen2"
    elif "llama-3.1" in model_id_lower or "llama3.1" in model_id_lower:
        return "llama3_1"
    elif "llama-3" in model_id_lower or "llama3" in model_id_lower:
        return "llama3"
    elif "mistral" in model_id_lower:
        return "mistral"
    elif "deepseek-vl" in model_id_lower:
        return "deepseek_vl"
    elif "deepseek-coder" in model_id_lower:
        return "deepseek"
    elif "deepseek" in model_id_lower:
        return "deepseek"
    elif "yi-" in model_id_lower:
        return "yi"
    elif "baichuan" in model_id_lower:
        return "baichuan"
    elif "chatglm" in model_id_lower:
        return "chatglm"
    elif "internlm" in model_id_lower:
        return "internlm"
    else:
        # Default fallback
        return "qwen2_5" 