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
sys.path.insert(0, str(Path(__file__).parent / "src"))

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
    
    async def list_running_models(self):
        """List running models"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/admin/models/running") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to list running models: {response.status}")
    
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
    
    async def unload_model(self, model_name: str):
        """Unload a model"""
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/admin/models/{model_name}/unload") as response:
                result = await response.json()
                if response.status == 200:
                    return result
                else:
                    raise Exception(result.get("detail", "Unknown error"))
    
    async def get_model_status(self, model_name: str):
        """Get model status"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/admin/models/{model_name}/status") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    result = await response.json()
                    raise Exception(result.get("detail", "Unknown error"))
    
    async def get_runtime_status(self):
        """Get runtime status"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/admin/status") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get runtime status: {response.status}")

async def cmd_status(client: PolarisClient, args):
    """Show runtime status"""
    console.print("[bold blue]PolarisLLM Runtime Status[/bold blue]")
    
    # Check health
    health = await client.health_check()
    if not health:
        console.print("[red]❌ Runtime is not running or not accessible[/red]")
        return
    
    console.print(f"[green]✅ Runtime is healthy[/green]")
    
    # Get detailed status
    try:
        status = await client.get_runtime_status()
        
        console.print(f"Total Models: {status['total_models']}")
        console.print(f"Running Models: {status['running_models']}")
        console.print(f"Memory Usage: {status['resource_usage']['memory']:.2f} MB")
        
        if status['running_model_details']:
            console.print("\n[bold]Running Models:[/bold]")
            table = Table()
            table.add_column("Name")
            table.add_column("Model ID")
            table.add_column("Status")
            table.add_column("Port")
            table.add_column("Memory (MB)")
            
            for model in status['running_model_details']:
                table.add_row(
                    model['name'],
                    model['model_id'][:50] + "..." if len(model['model_id']) > 50 else model['model_id'],
                    model['status'],
                    str(model['port']),
                    f"{model.get('memory_usage', 0):.1f}"
                )
            
            console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error getting detailed status: {e}[/red]")

async def cmd_list(client: PolarisClient, args):
    """List available models"""
    try:
        if args.running:
            result = await client.list_running_models()
            models = list(result['running'].values())
            title = "Running Models"
        else:
            result = await client.list_models()
            models = result['available']
            title = "Available Models"
        
        console.print(f"[bold blue]{title}[/bold blue]")
        
        if not models:
            console.print("No models found")
            return
        
        table = Table()
        table.add_column("Name")
        table.add_column("Model ID")
        table.add_column("Type")
        table.add_column("Description")
        table.add_column("Tags")
        
        if args.running:
            table.add_column("Status")
            table.add_column("Port")
        
        for model in models:
            row = [
                model['name'],
                model['model_id'][:40] + "..." if len(model['model_id']) > 40 else model['model_id'],
                model.get('model_type', 'N/A') if not args.running else model.get('status', 'N/A'),
                model.get('description', '')[:50],
                ', '.join(model.get('tags', []))
            ]
            
            if args.running:
                row.extend([model.get('status', 'N/A'), str(model.get('port', 'N/A'))])
            
            table.add_row(*row)
        
        console.print(table)
        console.print(f"\nTotal: {len(models)} models")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

async def cmd_load(client: PolarisClient, args):
    """Load a model"""
    try:
        console.print(f"Loading model: {args.model}")
        
        swift_args = {}
        if args.swift_args:
            for arg in args.swift_args:
                key, value = arg.split('=', 1)
                swift_args[key] = value
        
        with console.status("Loading model..."):
            result = await client.load_model(args.model, swift_args)
        
        if result['success']:
            console.print(f"[green]✅ {result['message']}[/green]")
            console.print(f"Port: {result.get('port', 'N/A')}")
        else:
            console.print(f"[red]❌ Failed to load model: {result.get('message', 'Unknown error')}[/red]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

async def cmd_unload(client: PolarisClient, args):
    """Unload a model"""
    try:
        console.print(f"Unloading model: {args.model}")
        
        with console.status("Unloading model..."):
            result = await client.unload_model(args.model)
        
        if result['success']:
            console.print(f"[green]✅ {result['message']}[/green]")
        else:
            console.print(f"[red]❌ Failed to unload model: {result.get('message', 'Unknown error')}[/red]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

async def cmd_info(client: PolarisClient, args):
    """Show model information"""
    try:
        status = await client.get_model_status(args.model)
        
        console.print(f"[bold blue]Model Information: {args.model}[/bold blue]")
        
        table = Table()
        table.add_column("Property")
        table.add_column("Value")
        
        table.add_row("Name", status['name'])
        table.add_row("Model ID", status['model_id'])
        table.add_row("Status", status['status'])
        table.add_row("Port", str(status['port']))
        table.add_row("PID", str(status.get('pid', 'N/A')))
        table.add_row("Memory Usage", f"{status.get('memory_usage', 0):.1f} MB")
        table.add_row("Error Message", status.get('error_message', 'None'))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="PolarisLLM CLI")
    parser.add_argument("--url", default="http://localhost:7860", help="Runtime server URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Status command
    subparsers.add_parser("status", help="Show runtime status")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List models")
    list_parser.add_argument("--running", action="store_true", help="List only running models")
    
    # Load command
    load_parser = subparsers.add_parser("load", help="Load a model")
    load_parser.add_argument("model", help="Model name to load")
    load_parser.add_argument("--swift-args", nargs="*", help="Swift arguments (key=value)")
    
    # Unload command
    unload_parser = subparsers.add_parser("unload", help="Unload a model")
    unload_parser.add_argument("model", help="Model name to unload")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show model information")
    info_parser.add_argument("model", help="Model name")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    client = PolarisClient(args.url)
    
    try:
        if args.command == "status":
            await cmd_status(client, args)
        elif args.command == "list":
            await cmd_list(client, args)
        elif args.command == "load":
            await cmd_load(client, args)
        elif args.command == "unload":
            await cmd_unload(client, args)
        elif args.command == "info":
            await cmd_info(client, args)
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")

if __name__ == "__main__":
    # Add rich to requirements
    try:
        import rich
    except ImportError:
        print("Error: rich not installed. Run: pip install rich")
        sys.exit(1)
    
    asyncio.run(main())