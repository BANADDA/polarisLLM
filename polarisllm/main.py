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
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=7860, help="Port to bind to")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
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