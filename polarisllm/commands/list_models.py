"""
List Models Command Handler
"""

import time
from typing import Any, Dict

from ..core import ModelRegistry, PolarisConfig


def handle_list_command(args) -> bool:
    """Handle list models command
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    print("📋 Deployed Models")
    print("=" * 80)
    
    # Initialize core components
    config = PolarisConfig()
    registry = ModelRegistry(config)
    
    # Auto-discover any running models not in registry
    registry.discover_running_models()
    
    # Refresh model status
    registry.refresh_model_status()
    
    # Get all models
    models = registry.list_models()
    
    if not models:
        print("No models deployed.")
        print()
        print("💡 Deploy a model with: polarisllm deploy --model <model-name>")
        return True
    
    # Display models in a table format
    _display_models_table(models)
    
    # Show summary statistics
    _display_summary_stats(models)
    
    return True


def _display_models_table(models: Dict[str, Any]):
    """Display models in a formatted table
    
    Args:
        models: Dictionary of model info
    """
    # Table headers
    headers = ["NAME", "STATUS", "PORT", "PID", "MEMORY", "UPTIME", "TYPE"]
    
    # Calculate column widths
    col_widths = {
        "NAME": max(len(name) for name in models.keys()) if models else 4,
        "STATUS": 8,
        "PORT": 6,
        "PID": 8,
        "MEMORY": 8,
        "UPTIME": 12,
        "TYPE": 15
    }
    
    # Ensure minimum column widths
    for header in headers:
        col_widths[header] = max(col_widths.get(header, len(header)), len(header))
    
    # Print header
    header_line = "  ".join(h.ljust(col_widths[h]) for h in headers)
    print(header_line)
    print("-" * len(header_line))
    
    # Print model rows
    for name, model_info in sorted(models.items()):
        status = _format_status(model_info.status)
        port = str(model_info.port) if model_info.port else "N/A"
        pid = str(model_info.pid) if model_info.pid else "N/A"
        memory = _format_memory(model_info.memory_usage)
        uptime = _format_uptime(model_info.deployed_at)
        model_type = model_info.model_type
        
        row_data = [
            name.ljust(col_widths["NAME"]),
            status.ljust(col_widths["STATUS"]),
            port.ljust(col_widths["PORT"]),
            pid.ljust(col_widths["PID"]),
            memory.ljust(col_widths["MEMORY"]),
            uptime.ljust(col_widths["UPTIME"]),
            model_type.ljust(col_widths["TYPE"])
        ]
        
        print("  ".join(row_data))
    
    print()


def _format_status(status: str) -> str:
    """Format status with colors/symbols
    
    Args:
        status: Status string
        
    Returns:
        Formatted status
    """
    status_map = {
        "running": "🟢 Running",
        "stopped": "🔴 Stopped", 
        "starting": "🟡 Starting",
        "crashed": "💥 Crashed",
        "unknown": "❓ Unknown"
    }
    
    return status_map.get(status, f"❓ {status}")


def _format_memory(memory_usage: float) -> str:
    """Format memory usage
    
    Args:
        memory_usage: Memory usage percentage
        
    Returns:
        Formatted memory string
    """
    if memory_usage is None:
        return "N/A"
    
    if memory_usage < 1:
        return f"{memory_usage:.1f}%"
    else:
        return f"{memory_usage:.0f}%"


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


def _display_summary_stats(models: Dict[str, Any]):
    """Display summary statistics
    
    Args:
        models: Dictionary of model info
    """
    total_models = len(models)
    running_models = len([m for m in models.values() if m.status == "running"])
    stopped_models = len([m for m in models.values() if m.status == "stopped"])
    total_memory = sum(m.memory_usage or 0 for m in models.values())
    
    print(f"📊 Summary:")
    print(f"   Total Models: {total_models}")
    print(f"   Running: {running_models}")
    print(f"   Stopped: {stopped_models}")
    
    if total_memory > 0:
        print(f"   Total Memory Usage: {total_memory:.1f}%")
    
    print()
    print("💡 Commands:")
    print("   polarisllm logs <model> --follow  # View live logs")
    print("   polarisllm stop <model>           # Stop a model")
    print("   polarisllm status                 # Detailed status") 