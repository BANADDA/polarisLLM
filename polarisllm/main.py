#!/usr/bin/env python3
"""
PolarisLLM Runtime Engine - Main Entry Point
Kubernetes for AI Models - Professional Model Orchestration Platform
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Import command handlers
from .commands import (handle_deploy_command, handle_list_command,
                       handle_logs_command, handle_server_command,
                       handle_status_command, handle_stop_command)
from .commands.logs import handle_logs_summary_command
from .commands.server import (handle_restart_server_command,
                              handle_start_daemon_command,
                              handle_stop_server_command)
from .commands.status import handle_cleanup_command, handle_discover_command
from .commands.stop import handle_stop_all_command, handle_undeploy_command
# Import core for server functionality
from .core import PolarisConfig


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


def create_argument_parser():
    """Create comprehensive argument parser"""
    parser = argparse.ArgumentParser(
        description="🌟 PolarisLLM - Kubernetes for AI Models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Server Management
  polarisllm start --daemon          # Start server in background
  polarisllm stop --server           # Stop server
  polarisllm status                  # Show system status
  
  # Model Management  
  polarisllm deploy --model qwen2.5-7b-instruct
  polarisllm list                    # List all models
  polarisllm stop qwen2.5-7b-instruct
  polarisllm undeploy qwen2.5-7b-instruct
  
  # Logs & Monitoring
  polarisllm logs qwen2.5-7b-instruct --follow
  polarisllm logs --server --follow
  
  # Maintenance
  polarisllm discover                # Find running models
  polarisllm cleanup                 # Clean up dead processes
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Start/Server commands
    start_parser = subparsers.add_parser("start", help="Start PolarisLLM server")
    start_parser.add_argument("--daemon", action="store_true", help="Run in background")
    start_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    start_parser.add_argument("--port", type=int, default=7860, help="Port to bind to")
    start_parser.add_argument("--log-level", default="info", help="Log level")
    
    server_parser = subparsers.add_parser("server", help="Server mode (internal)")
    server_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    server_parser.add_argument("--port", type=int, default=7860, help="Port to bind to")
    server_parser.add_argument("--log-level", default="info", help="Log level")
    
    # Stop commands
    stop_parser = subparsers.add_parser("stop", help="Stop models or server")
    stop_group = stop_parser.add_mutually_exclusive_group(required=True)
    stop_group.add_argument("model", nargs="?", help="Model name to stop")
    stop_group.add_argument("--server", action="store_true", help="Stop server")
    stop_group.add_argument("--all", action="store_true", help="Stop all models")
    stop_parser.add_argument("--force", action="store_true", help="Force kill processes")
    
    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy any ms-swift supported model")
    deploy_parser.add_argument("--model", required=True, 
                              help="Model name (shortcut) or full model ID")
    deploy_parser.add_argument("--model-type", 
                              help="Model type for ms-swift (e.g., qwen2_5, llama3_1)")
    deploy_parser.add_argument("--model-id", 
                              help="Full model ID from HuggingFace/ModelScope")
    
    # Undeploy command
    undeploy_parser = subparsers.add_parser("undeploy", help="Undeploy a model (stop + remove)")
    undeploy_parser.add_argument("model", help="Model name to undeploy")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List deployed models")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show system status")
    
    # Logs commands
    logs_parser = subparsers.add_parser("logs", help="View logs")
    logs_group = logs_parser.add_mutually_exclusive_group()
    logs_group.add_argument("model", nargs="?", help="Model name")
    logs_group.add_argument("--server", action="store_true", help="Show server logs")
    logs_group.add_argument("--summary", action="store_true", help="Show logs summary")
    logs_parser.add_argument("--follow", "-f", action="store_true", help="Follow log output")
    logs_parser.add_argument("--lines", "-n", type=int, default=100, help="Number of lines to show")
    
    # Discover command
    discover_parser = subparsers.add_parser("discover", help="Discover running models")
    
    # Cleanup command  
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up dead processes and logs")
    
    # Restart command
    restart_parser = subparsers.add_parser("restart", help="Restart server")
    restart_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    restart_parser.add_argument("--port", type=int, default=7860, help="Port to bind to")
    restart_parser.add_argument("--log-level", default="info", help="Log level")
    
    # Add backward compatibility arguments to main parser
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (legacy)")
    parser.add_argument("--port", type=int, default=7860, help="Port to bind to (legacy)")
    parser.add_argument("--log-level", default="info", help="Log level (legacy)")
    
    return parser


def print_header():
    """Print PolarisLLM header"""
    print("🌟 PolarisLLM Runtime Engine")
    print("=" * 50)
    print("🚀 Kubernetes for AI Models - Professional Orchestration Platform")
    print()


def check_dependencies():
    """Check if required dependencies are available"""
    # Check if ms-swift is installed
    try:
        import swift
        print("✅ ms-swift found")
        return True
    except ImportError:
        print("❌ ms-swift not found. Please install it first:")
        print("   pip install ms-swift --upgrade")
        return False


async def start_fastapi_server(host: str, port: int, log_level: str):
    """Start the FastAPI server (internal function)"""
    import uvicorn

    from src.api.server import create_app

    # Create FastAPI app
    app = create_app()
    
    # Configure uvicorn
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level=log_level.lower(),
        access_log=True
    )
    
    server = uvicorn.Server(config)
    
    print(f"🌐 Server starting on http://{host}:{port}")
    print()
    print("📋 Available endpoints:")
    print(f"   • API Documentation: http://{host}:{port}/docs")
    print(f"   • Health Check: http://{host}:{port}/health")
    print(f"   • Chat Completions: http://{host}:{port}/v1/chat/completions")
    print(f"   • Admin Panel: http://{host}:{port}/admin")
    print()
    print("💡 Management Commands:")
    print("   polarisllm deploy --model <name>    # Deploy a model") 
    print("   polarisllm list                     # List models")
    print("   polarisllm status                   # System status")
    print("   polarisllm logs <model> --follow    # View logs")
    print()
    print("🔄 Server running... (Press Ctrl+C to stop)")
    
    await server.serve()


def sync_main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print_header()
    logger.info("Starting PolarisLLM Runtime Engine")
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Parse arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Handle commands
    try:
        success = True
        
        if args.command == "start":
            success = handle_server_command(args)
            
        elif args.command == "server":
            # Internal server mode - start FastAPI directly
            success = handle_server_command(args)
            
        elif args.command == "stop":
            if args.server:
                success = handle_stop_server_command(args)
            elif args.all:
                success = handle_stop_all_command(args)
            elif args.model:
                success = handle_stop_command(args)
            else:
                print("❌ Must specify --server, --all, or model name")
                success = False
                
        elif args.command == "deploy":
            success = handle_deploy_command(args)
            
        elif args.command == "undeploy":
            success = handle_undeploy_command(args)
            
        elif args.command == "list":
            success = handle_list_command(args)
            
        elif args.command == "status":
            success = handle_status_command(args)
            
        elif args.command == "logs":
            if args.summary:
                success = handle_logs_summary_command(args)
            else:
                success = handle_logs_command(args)
                
        elif args.command == "discover":
            success = handle_discover_command(args)
            
        elif args.command == "cleanup":
            success = handle_cleanup_command(args)
            
        elif args.command == "restart":
            success = handle_restart_server_command(args)
            
        else:
            # Default behavior - start server in foreground (backward compatibility)
            print("🔧 No command specified, starting server in foreground mode...")
            print("💡 Use 'polarisllm start --daemon' for background mode")
            print()
            
            # Set up args for server command
            args.command = "server"
            success = handle_server_command(args)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
        return 1


def main():
    """Entry point for console script"""
    sys.exit(sync_main())


if __name__ == "__main__":
    main()