#!/usr/bin/env python3
"""
PolarisLLM CLI - Command Line Interface for Runtime Management
"""

import asyncio
import sys
import argparse
import json
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import aiohttp
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich import print as rprint

console = Console()

class PolarisClient:
    """Client for communicating with PolarisLLM runtime"""
    
    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url.rstrip('/')
        
    async def health_check(self):
        """Check if runtime is healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return None
        except:
            return None
    
    async def list_models(self):
        """List available models"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/admin/models/available") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to list models: {response.status}")
    
    async def load_model(self, model_name: str, swift_args: dict = None):
        """Load a model"""
        data = {"model_name": model_name}
        if swift_args:
            data["swift_args"] = swift_args
            
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/admin/models/load", json=data) as response:
                result = await response.json()
                if response.status == 200:
                    return result
                else:
                    raise Exception(result.get("detail", "Unknown error"))

async def cmd_status(client: PolarisClient, args):
    """Show runtime status"""
    console.print("[bold blue]PolarisLLM Runtime Status[/bold blue]")
    
    # Check health
    health = await client.health_check()
    if not health:
        console.print("[red]❌ Runtime is not running or not accessible[/red]")
        console.print("💡 Start the runtime with: polarisllm")
        return
    
    console.print(f"[green]✅ Runtime is healthy[/green]")

async def cmd_start(args):
    """Start the runtime server"""
    console.print("[bold blue]🚀 Starting PolarisLLM Runtime Engine[/bold blue]")
    
    # Import and run the main function
    from .main import sync_main
    sync_main()

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="PolarisLLM CLI")
    parser.add_argument("--url", default="http://localhost:7860", help="Runtime server URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Start command
    subparsers.add_parser("start", help="Start the runtime engine")
    
    # Status command
    subparsers.add_parser("status", help="Show runtime status")
    
    args = parser.parse_args()
    
    if not args.command:
        # Default action: start the server
        args.command = "start"
    
    client = PolarisClient(args.url)
    
    try:
        if args.command == "start":
            asyncio.run(cmd_start(args))
        elif args.command == "status":
            asyncio.run(cmd_status(client, args))
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    main()