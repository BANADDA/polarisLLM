"""
Logs Command Handler
"""

import sys

from ..core import LogManager, ModelRegistry, PolarisConfig


def handle_logs_command(args) -> bool:
    """Handle logs viewing command
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    model_name = getattr(args, 'model', None)
    follow = getattr(args, 'follow', False)
    lines = getattr(args, 'lines', 100)
    server = getattr(args, 'server', False)
    
    # Initialize core components
    config = PolarisConfig()
    registry = ModelRegistry(config)
    log_manager = LogManager(config)
    
    if server:
        return _handle_server_logs(log_manager, follow, lines)
    
    if not model_name:
        print("❌ Model name is required")
        print("   Usage: polarisllm logs <model-name> [--follow] [--lines N]")
        print("   Usage: polarisllm logs --server [--follow] [--lines N]")
        return False
    
    # Check if model exists
    model_info = registry.get_model_info(model_name)
    if not model_info:
        print(f"❌ Model '{model_name}' not found in registry")
        print("💡 Use 'polarisllm list' to see deployed models")
        return False
    
    return _handle_model_logs(log_manager, model_name, follow, lines)


def _handle_model_logs(log_manager: LogManager, model_name: str, follow: bool, lines: int) -> bool:
    """Handle model logs viewing
    
    Args:
        log_manager: LogManager instance
        model_name: Name of the model
        follow: Whether to follow logs (tail -f style)
        lines: Number of lines to show
        
    Returns:
        True if successful, False otherwise
    """
    print(f"📝 Logs for model: {model_name}")
    print(f"   Lines: {lines}")
    print(f"   Follow: {'Yes' if follow else 'No'}")
    print("=" * 60)
    
    try:
        if follow:
            # Stream logs in real-time
            print("🔄 Streaming logs (Press Ctrl+C to stop)...")
            print()
            
            try:
                for line in log_manager.stream_logs(model_name, follow=True):
                    print(line, end='')
                    sys.stdout.flush()
            except KeyboardInterrupt:
                print("\n\n🛑 Log streaming stopped")
                return True
                
        else:
            # Show last N lines
            log_lines = log_manager.tail_logs(model_name, lines)
            
            if not log_lines:
                print("No logs found")
                return True
            
            for line in log_lines:
                print(line, end='')
        
        return True
        
    except Exception as e:
        print(f"❌ Error viewing logs: {e}")
        return False


def _handle_server_logs(log_manager: LogManager, follow: bool, lines: int) -> bool:
    """Handle server logs viewing
    
    Args:
        log_manager: LogManager instance
        follow: Whether to follow logs
        lines: Number of lines to show
        
    Returns:
        True if successful, False otherwise
    """
    print(f"📝 PolarisLLM Server Logs")
    print(f"   Lines: {lines}")
    print(f"   Follow: {'Yes' if follow else 'No'}")
    print("=" * 60)
    
    server_log_file = log_manager.get_server_log_file()
    
    if not server_log_file.exists():
        print("No server logs found")
        print("💡 Start the server with: polarisllm start --daemon")
        return True
    
    try:
        if follow:
            # Stream server logs in real-time
            print("🔄 Streaming server logs (Press Ctrl+C to stop)...")
            print()
            
            try:
                # Use the log manager's streaming for server logs
                # We'll simulate this by reading the server log file
                _stream_file(server_log_file)
            except KeyboardInterrupt:
                print("\n\n🛑 Log streaming stopped")
                return True
                
        else:
            # Show last N lines of server log
            try:
                with open(server_log_file, 'r') as f:
                    all_lines = f.readlines()
                    recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    
                for line in recent_lines:
                    print(line, end='')
                    
            except Exception as e:
                print(f"Error reading server logs: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error viewing server logs: {e}")
        return False


def _stream_file(file_path):
    """Stream a file in real-time (like tail -f)
    
    Args:
        file_path: Path to the file to stream
    """
    import time
    
    with open(file_path, 'r') as f:
        # Seek to end
        f.seek(0, 2)
        
        while True:
            line = f.readline()
            if line:
                print(line, end='')
                sys.stdout.flush()
            else:
                time.sleep(0.1)


def handle_logs_summary_command(args) -> bool:
    """Handle logs summary command
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    print("📊 Logs Summary")
    print("=" * 50)
    
    # Initialize core components
    config = PolarisConfig()
    log_manager = LogManager(config)
    
    # Get log summary
    summary = log_manager.get_log_summary()
    
    # Display server logs info
    server_info = summary.get("server", {})
    if server_info:
        print("🖥️  Server Logs:")
        print(f"   Size: {_format_size(server_info.get('size', 0))}")
        print(f"   Lines: {server_info.get('lines', 0):,}")
        print(f"   Last Modified: {_format_timestamp(server_info.get('modified'))}")
        print()
    
    # Display model logs info
    models = summary.get("models", {})
    if models:
        print("🤖 Model Logs:")
        for model_name, info in sorted(models.items()):
            print(f"   {model_name}:")
            print(f"     Size: {_format_size(info.get('size', 0))}")
            print(f"     Lines: {info.get('lines', 0):,}")
            print(f"     Last Modified: {_format_timestamp(info.get('modified'))}")
        print()
    
    # Display total info
    total_size = summary.get("total_size", 0)
    total_models = len(models)
    
    print(f"📈 Total:")
    print(f"   Models with logs: {total_models}")
    print(f"   Total log size: {_format_size(total_size)}")
    
    print()
    print("💡 Commands:")
    print("   polarisllm logs <model>           # View model logs")
    print("   polarisllm logs <model> --follow  # Stream live logs")
    print("   polarisllm logs --server          # View server logs")
    
    return True


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
    
    import time
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)) 