#!/usr/bin/env python3
"""
PolarisLLM Runtime Engine - Main Entry Point
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('polaris.log')
        ]
    )

def handle_deploy_command(args):
    """Handle deploy command"""
    print(f"🚀 Deploying model: {args.model}")
    
    # Map common model names to ms-swift format
    model_mapping = {
        "qwen2.5-7b-instruct": {
            "model_type": "qwen2_5",
            "model_id": "Qwen/Qwen2.5-7B-Instruct"
        },
        "deepseek-vl-7b-chat": {
            "model_type": "deepseek_vl",
            "model_id": "deepseek-ai/deepseek-vl-7b-chat"
        },
        "deepseek-coder-6.7b": {
            "model_type": "deepseek",
            "model_id": "deepseek-ai/deepseek-coder-6.7b-instruct"
        }
    }
    
    if args.model in model_mapping:
        model_info = model_mapping[args.model]
        model_type = args.model_type or model_info["model_type"]
        model_id = args.model_id or model_info["model_id"]
    else:
        model_type = args.model_type or "qwen2_5"
        model_id = args.model_id or args.model
    
    print(f"   Model Type: {model_type}")
    print(f"   Model ID: {model_id}")
    print()
    
    try:
        import subprocess
        cmd = ["python", "-m", "swift", "deploy", "--model_type", model_type, "--model_id", model_id]
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode == 0:
            print("✅ Model deployed successfully!")
        else:
            print("❌ Model deployment failed")
            
    except Exception as e:
        print(f"❌ Error deploying model: {e}")
        print("💡 Try running manually: python -m swift deploy --model_type {} --model_id {}".format(model_type, model_id))

def handle_list_command(args):
    """Handle list command"""
    print("📋 Listing deployed models...")
    
    try:
        import subprocess
        result = subprocess.run(["python", "-m", "swift", "list"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("❌ Failed to list models")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        print("💡 Try running manually: python -m swift list")

def handle_status_command(args):
    """Handle status command"""
    print("📊 PolarisLLM Runtime Status")
    print("=" * 30)
    
    # Check if server is running
    try:
        import requests
        response = requests.get("http://localhost:7860/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server Status: Running")
            print(f"   Port: 7860")
            print(f"   Health: {response.json()}")
        else:
            print("⚠️  Server Status: Issues detected")
    except Exception:
        print("❌ Server Status: Not running")
        print("   Start with: polarisllm")
    
    print()
    
    # Check deployed models
    try:
        import subprocess
        result = subprocess.run(["python", "-m", "swift", "list"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("📋 Deployed Models:")
            print(result.stdout)
        else:
            print("❌ Could not retrieve model status")
            
    except Exception as e:
        print(f"❌ Error checking models: {e}")

def sync_main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🌟 PolarisLLM Runtime Engine")
    print("=" * 50)
    print("🚀 Starting the multi-model LLM runtime platform...")
    print()
    
    logger.info("Starting PolarisLLM Runtime Engine")
    
    # Check if ms-swift is installed
    try:
        import swift
        print("✅ ms-swift found")
    except ImportError:
        print("❌ ms-swift not found. Please install it first:")
        print("   pip install ms-swift --upgrade")
        return
    
    # Check if swift command is available
    try:
        import subprocess
        result = subprocess.run(["swift", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️  swift command not found in PATH")
            print("💡 You may need to add swift to your PATH or use python -m swift instead")
    except FileNotFoundError:
        print("⚠️  swift command not found in PATH")
        print("💡 You may need to add swift to your PATH or use python -m swift instead")
    print("🔧 Setting up runtime environment...")
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="PolarisLLM Runtime Engine")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Server command (default)
    server_parser = subparsers.add_parser("server", help="Start the server (default)")
    server_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    server_parser.add_argument("--port", type=int, default=7860, help="Port to bind to")
    server_parser.add_argument("--log-level", default="info", help="Log level")
    
    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy a model")
    deploy_parser.add_argument("--model", required=True, help="Model name to deploy")
    deploy_parser.add_argument("--model-type", help="Model type (e.g., qwen2_5)")
    deploy_parser.add_argument("--model-id", help="Model ID (e.g., Qwen/Qwen2.5-7B-Instruct)")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List deployed models")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show runtime status")
    
    # Add default server arguments to main parser for backward compatibility
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=7860, help="Port to bind to")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    # Handle subcommands
    if args.command == "deploy":
        handle_deploy_command(args)
        return
    elif args.command == "list":
        handle_list_command(args)
        return
    elif args.command == "status":
        handle_status_command(args)
        return
    elif args.command == "server":
        # Use server-specific arguments
        pass
    else:
        # Default to server mode if no command specified
        args.command = "server"
    
    print(f"🌐 Server will start on http://{args.host}:{args.port}")
    print()
    print("📋 Available endpoints:")
    print(f"   • API Documentation: http://{args.host}:{args.port}/docs")
    print(f"   • Health Check: http://{args.host}:{args.port}/health")
    print(f"   • Chat Completions: http://{args.host}:{args.port}/v1/chat/completions")
    print(f"   • Admin Panel: http://{args.host}:{args.port}/admin")
    print()
    print("💡 To load models, use the CLI:")
    print("   polaris-cli status")
    print()
    print("🔄 Starting server... (Press Ctrl+C to stop)")
    print()
    
    # Simple FastAPI server for now
    try:
        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        
        app = FastAPI(
            title="PolarisLLM Runtime Engine",
            description="Multi-model LLM runtime platform",
            version="1.2.0"
        )
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @app.get("/")
        def root():
            return {
                "name": "PolarisLLM Runtime Engine",
                "version": "1.2.0",
                "status": "running",
                "message": "Welcome to PolarisLLM! Visit /docs for API documentation."
            }
        
        @app.get("/health")
        def health():
            return {"status": "healthy", "version": "1.2.0"}
        
        @app.get("/v1/models")
        def list_models():
            return {
                "object": "list",
                "data": [
                    {"id": "qwen2.5-7b-instruct", "object": "model", "owned_by": "polaris"},
                    {"id": "deepseek-vl-7b-chat", "object": "model", "owned_by": "polaris"},
                    {"id": "deepseek-coder-6.7b", "object": "model", "owned_by": "polaris"}
                ]
            }
        
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level=args.log_level
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down PolarisLLM...")
        logger.info("Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        logger.error(f"Failed to start server: {e}")
        print("\n💡 Try installing missing dependencies:")
        print("   pip install ms-swift[llm] --upgrade")

if __name__ == "__main__":
    sync_main()