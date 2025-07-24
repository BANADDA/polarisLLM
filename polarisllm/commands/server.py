"""
Server Command Handler
"""

import asyncio
import os
import sys
from typing import Optional

from ..core import PolarisConfig, ProcessManager


def handle_server_command(args) -> bool:
    """Handle server start command
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    daemon = getattr(args, 'daemon', False)
    host = getattr(args, 'host', '0.0.0.0')
    port = getattr(args, 'port', 7860)
    
    if daemon:
        return handle_start_daemon_command(args)
    else:
        return handle_start_foreground_command(args)


def handle_start_daemon_command(args) -> bool:
    """Start server in daemon mode (background)
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    print("🚀 Starting PolarisLLM server in daemon mode...")
    
    # Initialize core components
    config = PolarisConfig()
    process_manager = ProcessManager(config)
    
    # Check if server is already running
    existing_pid = process_manager.get_server_pid()
    if existing_pid:
        print(f"⚠️  Server is already running (PID: {existing_pid})")
        print("💡 Use 'polarisllm stop --server' to stop it first")
        return False
    
    # Get server configuration
    server_config = config.get_server_config()
    host = getattr(args, 'host', server_config['host'])
    port = getattr(args, 'port', server_config['port'])
    log_level = getattr(args, 'log_level', server_config['log_level'])
    
    # Create server log file
    server_log = config.logs_dir / "server.log"
    
    # Build server command
    server_cmd = [
        sys.executable, "-m", "polarisllm.main",
        "server",
        "--host", host,
        "--port", str(port),
        "--log-level", log_level
    ]
    
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Log Level: {log_level}")
    print(f"   Log File: {server_log}")
    print()
    
    try:
        # Start server in background
        pid = process_manager.start_background_process(
            cmd=server_cmd,
            model_name="server",
            log_file=server_log
        )
        
        if pid:
            # Save server PID
            process_manager.save_server_pid(pid)
            
            print(f"✅ Server started successfully!")
            print(f"   PID: {pid}")
            print(f"   URL: http://{host}:{port}")
            print()
            print("💡 Commands:")
            print("   polarisllm status              # Check server status")
            print("   polarisllm logs --server       # View server logs")
            print("   polarisllm stop --server       # Stop server")
            
            return True
        else:
            print("❌ Failed to start server")
            return False
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False


def handle_start_foreground_command(args) -> bool:
    """Start server in foreground mode
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    print("🚀 Starting PolarisLLM server...")
    
    # Initialize core components
    config = PolarisConfig()
    process_manager = ProcessManager(config)
    
    # Save current process PID as server PID
    current_pid = os.getpid()
    process_manager.save_server_pid(current_pid)
    
    # Get server configuration
    server_config = config.get_server_config()
    host = getattr(args, 'host', server_config['host'])
    port = getattr(args, 'port', server_config['port'])
    log_level = getattr(args, 'log_level', server_config['log_level'])
    
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Log Level: {log_level}")
    print()
    
    try:
        # Import and start the actual FastAPI server
        from ..main import start_fastapi_server

        # Start server (this will block)
        asyncio.run(start_fastapi_server(host, port, log_level))
        
        return True
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return True
    except Exception as e:
        print(f"❌ Server error: {e}")
        return False
    finally:
        # Clean up server PID file
        try:
            config.server_pid_file.unlink()
        except FileNotFoundError:
            pass


def handle_stop_server_command(args) -> bool:
    """Stop the PolarisLLM server
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    force = getattr(args, 'force', False)
    
    print("🛑 Stopping PolarisLLM server...")
    
    # Initialize core components
    config = PolarisConfig()
    process_manager = ProcessManager(config)
    
    # Get server PID
    server_pid = process_manager.get_server_pid()
    
    if not server_pid:
        print("ℹ️  Server is not running")
        return True
    
    print(f"   PID: {server_pid}")
    
    try:
        # Stop server process
        if process_manager.is_process_running(server_pid):
            import signal
            import time
            
            if not force:
                # Try graceful shutdown
                print("   Sending SIGTERM...")
                os.kill(server_pid, signal.SIGTERM)
                
                # Wait for graceful shutdown
                for _ in range(10):
                    time.sleep(1)
                    if not process_manager.is_process_running(server_pid):
                        break
                else:
                    print("   Graceful shutdown failed, forcing...")
                    force = True
            
            if force and process_manager.is_process_running(server_pid):
                print("   Sending SIGKILL...")
                process_manager.kill_process_tree(server_pid)
        
        # Clean up PID file
        try:
            config.server_pid_file.unlink()
        except FileNotFoundError:
            pass
        
        print("✅ Server stopped successfully")
        return True
        
    except ProcessLookupError:
        # Process already dead
        try:
            config.server_pid_file.unlink()
        except FileNotFoundError:
            pass
        print("✅ Server was already stopped")
        return True
    except PermissionError:
        print(f"❌ Permission denied stopping server (PID: {server_pid})")
        return False
    except Exception as e:
        print(f"❌ Error stopping server: {e}")
        return False


def handle_restart_server_command(args) -> bool:
    """Restart the PolarisLLM server
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    print("🔄 Restarting PolarisLLM server...")
    
    # Stop server first
    stop_success = handle_stop_server_command(args)
    
    if not stop_success:
        print("❌ Failed to stop server, cannot restart")
        return False
    
    # Wait a moment
    import time
    time.sleep(2)
    
    # Start server in daemon mode
    args.daemon = True
    return handle_start_daemon_command(args)


def handle_server_status_command(args) -> bool:
    """Show detailed server status
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    print("🖥️  PolarisLLM Server Status")
    print("=" * 40)
    
    # Initialize core components
    config = PolarisConfig()
    process_manager = ProcessManager(config)
    
    # Check server process
    server_pid = process_manager.get_server_pid()
    
    if server_pid:
        process_info = process_manager.get_process_info(server_pid)
        
        if process_info:
            print(f"Status: 🟢 Running")
            print(f"PID: {server_pid}")
            print(f"Memory: {process_info.get('memory_percent', 0):.1f}%")
            print(f"CPU: {process_info.get('cpu_percent', 0):.1f}%")
            print(f"Start Time: {_format_timestamp(process_info.get('create_time'))}")
            
            # Check API health
            try:
                import requests
                response = requests.get("http://localhost:7860/health", timeout=2)
                if response.status_code == 200:
                    print(f"API: 🟢 Healthy")
                    print(f"URL: http://localhost:7860")
                else:
                    print(f"API: 🟡 HTTP {response.status_code}")
            except Exception:
                print(f"API: 🔴 Not responding")
                
        else:
            print(f"Status: 🟡 PID found but process not accessible")
    else:
        print(f"Status: 🔴 Not running")
    
    print()
    print("💡 Commands:")
    print("   polarisllm start --daemon    # Start in background")
    print("   polarisllm stop --server     # Stop server")
    print("   polarisllm logs --server     # View server logs")
    
    return True


def _format_timestamp(timestamp: Optional[float]) -> str:
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