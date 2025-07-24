"""
Status Command Handler
"""

import time
from typing import Any, Dict

import requests

from ..core import (LogManager, ModelRegistry, PolarisConfig, PortManager,
                    ProcessManager)


def handle_status_command(args) -> bool:
    """Handle status command
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    print("📊 PolarisLLM System Status")
    print("=" * 60)
    
    # Initialize core components
    config = PolarisConfig()
    registry = ModelRegistry(config)
    process_manager = ProcessManager(config)
    port_manager = PortManager(config)
    log_manager = LogManager(config)
    
    # Auto-discover models
    registry.discover_running_models()
    registry.refresh_model_status()
    
    # Check server status
    _display_server_status(process_manager)
    
    # Check models status
    _display_models_status(registry)
    
    # Check resource usage
    _display_resource_status(registry, port_manager)
    
    # Check logs status
    _display_logs_status(log_manager)
    
    # Display helpful commands
    _display_help_commands()
    
    return True


def _display_server_status(process_manager: ProcessManager):
    """Display server status information
    
    Args:
        process_manager: ProcessManager instance
    """
    print("🖥️  Server Status:")
    
    # Check if server process is running
    server_pid = process_manager.get_server_pid()
    
    if server_pid:
        process_info = process_manager.get_process_info(server_pid)
        if process_info:
            print(f"   Status: 🟢 Running (PID: {server_pid})")
            print(f"   Memory: {process_info.get('memory_percent', 0):.1f}%")
            print(f"   CPU: {process_info.get('cpu_percent', 0):.1f}%")
            
            # Check if API is responding
            try:
                response = requests.get("http://localhost:7860/health", timeout=2)
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"   API: 🟢 Healthy")
                    print(f"   URL: http://localhost:7860")
                else:
                    print(f"   API: 🟡 Issues (HTTP {response.status_code})")
            except Exception:
                print(f"   API: 🔴 Not responding")
        else:
            print(f"   Status: 🟡 Process found but not accessible")
    else:
        print(f"   Status: 🔴 Not running")
        print(f"   Start with: polarisllm start --daemon")
    
    print()


def _display_models_status(registry: ModelRegistry):
    """Display models status information
    
    Args:
        registry: ModelRegistry instance
    """
    models = registry.list_models()
    stats = registry.get_registry_stats()
    
    print("🤖 Models Status:")
    print(f"   Total Models: {stats['total_models']}")
    print(f"   Running: {stats['running_models']} 🟢")
    print(f"   Stopped: {stats['stopped_models']} 🔴")
    
    if models:
        print("   Detailed Status:")
        for name, model_info in sorted(models.items()):
            status_icon = _get_status_icon(model_info.status)
            uptime = _format_uptime(model_info.deployed_at)
            memory = f"{model_info.memory_usage:.1f}%" if model_info.memory_usage else "N/A"
            
            print(f"     {name}: {status_icon} {model_info.status}")
            print(f"       Port: {model_info.port}, Memory: {memory}, Uptime: {uptime}")
    
    print()


def _display_resource_status(registry: ModelRegistry, port_manager: PortManager):
    """Display resource usage status
    
    Args:
        registry: ModelRegistry instance
        port_manager: PortManager instance
    """
    stats = registry.get_registry_stats()
    
    print("💾 Resource Status:")
    
    # Port usage
    available_ports = port_manager.get_available_port_count()
    total_ports = port_manager.port_end - port_manager.port_start + 1
    used_ports = total_ports - available_ports
    
    print(f"   Ports: {used_ports}/{total_ports} used ({available_ports} available)")
    print(f"   Range: {port_manager.port_start}-{port_manager.port_end}")
    
    # Memory usage (sum of all models)
    total_memory = stats.get('memory_usage', 0)
    if total_memory > 0:
        print(f"   Total Memory: {total_memory:.1f}% (all models combined)")
    
    # Deployment timeline
    oldest = stats.get('oldest_deployment')
    newest = stats.get('newest_deployment')
    
    if oldest and newest:
        print(f"   Oldest Deployment: {_format_timestamp(oldest)}")
        print(f"   Newest Deployment: {_format_timestamp(newest)}")
    
    print()


def _display_logs_status(log_manager: LogManager):
    """Display logs status information
    
    Args:
        log_manager: LogManager instance
    """
    log_summary = log_manager.get_log_summary()
    
    print("📝 Logs Status:")
    
    total_size = log_summary.get('total_size', 0)
    model_count = len(log_summary.get('models', {}))
    server_logs = log_summary.get('server', {})
    
    print(f"   Total Log Size: {_format_size(total_size)}")
    print(f"   Models with Logs: {model_count}")
    
    if server_logs:
        print(f"   Server Log Size: {_format_size(server_logs.get('size', 0))}")
    
    print()


def _display_help_commands():
    """Display helpful commands"""
    print("💡 Quick Commands:")
    print("   polarisllm deploy --model <name>     # Deploy a model")
    print("   polarisllm list                      # List all models")
    print("   polarisllm logs <model> --follow     # View live logs")
    print("   polarisllm stop <model>              # Stop a model")
    print("   polarisllm start --daemon            # Start server in background")


def _get_status_icon(status: str) -> str:
    """Get icon for model status
    
    Args:
        status: Model status
        
    Returns:
        Status icon
    """
    status_icons = {
        "running": "🟢",
        "stopped": "🔴",
        "starting": "🟡",
        "crashed": "💥",
        "unknown": "❓"
    }
    
    return status_icons.get(status, "❓")


def _format_uptime(deployed_at: float) -> str:
    """Format uptime duration
    
    Args:
        deployed_at: Deployment timestamp
        
    Returns:
        Formatted uptime string
    """
    if not deployed_at:
        return "N/A"
    
    uptime_seconds = time.time() - deployed_at
    
    if uptime_seconds < 60:
        return f"{uptime_seconds:.0f}s"
    elif uptime_seconds < 3600:
        return f"{uptime_seconds/60:.0f}m"
    elif uptime_seconds < 86400:
        hours = uptime_seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = uptime_seconds / 86400
        return f"{days:.1f}d"


def _format_size(size_bytes: int) -> str:
    """Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def _format_timestamp(timestamp: float) -> str:
    """Format timestamp in human readable format
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Formatted timestamp string
    """
    if not timestamp:
        return "Unknown"
    
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


def handle_discover_command(args) -> bool:
    """Handle discover models command
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    print("🔍 Discovering running models...")
    print("=" * 40)
    
    # Initialize core components
    config = PolarisConfig()
    registry = ModelRegistry(config)
    
    # Perform discovery
    registry.discover_running_models()
    
    # Show updated list
    models = registry.list_models()
    
    if models:
        print(f"📋 Found {len(models)} total models:")
        for name, model_info in sorted(models.items()):
            status_icon = _get_status_icon(model_info.status)
            print(f"   {name}: {status_icon} {model_info.status} (Port: {model_info.port})")
    else:
        print("No models found")
    
    print()
    print("💡 Use 'polarisllm list' for detailed view")
    
    return True


def handle_cleanup_command(args) -> bool:
    """Handle cleanup command (remove dead processes/logs)
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    print("🧹 Cleaning up PolarisLLM...")
    print("=" * 40)
    
    # Initialize core components
    config = PolarisConfig()
    registry = ModelRegistry(config)
    process_manager = ProcessManager(config)
    port_manager = PortManager(config)
    log_manager = LogManager(config)
    
    # Cleanup dead processes
    print("🔍 Cleaning up dead processes...")
    process_manager.cleanup_dead_processes()
    
    # Cleanup dead models from registry
    print("🔍 Cleaning up dead models...")
    registry.cleanup_dead_models()
    
    # Cleanup port allocations
    print("🔍 Cleaning up port allocations...")
    port_manager.cleanup_dead_ports()
    
    # Cleanup old logs
    print("🔍 Cleaning up old logs...")
    log_manager.cleanup_old_logs()
    
    print()
    print("✅ Cleanup completed!")
    print("💡 Use 'polarisllm status' to verify system state")
    
    return True 