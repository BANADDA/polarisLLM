"""
Process Management System for PolarisLLM
"""

import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

from .config import PolarisConfig


class ProcessManager:
    """Manages background processes for models and server"""
    
    def __init__(self, config: PolarisConfig):
        """Initialize process manager
        
        Args:
            config: PolarisLLM configuration instance
        """
        self.config = config
    
    def start_background_process(
        self, 
        cmd: List[str], 
        model_name: str,
        log_file: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None
    ) -> Optional[int]:
        """Start a process in the background using nohup
        
        Args:
            cmd: Command to execute as list
            model_name: Name of the model (for PID tracking)
            log_file: Path to log file for output
            env: Environment variables
            
        Returns:
            Process ID if successful, None otherwise
        """
        if log_file is None:
            log_file = self.config.get_model_log_file(model_name)
        
        pid_file = self.config.get_model_pid_file(model_name)
        
        try:
            # Prepare environment
            process_env = os.environ.copy()
            if env:
                process_env.update(env)
            
            # Start process with nohup-like behavior
            with open(log_file, 'a') as log_f:
                process = subprocess.Popen(
                    cmd,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    env=process_env,
                    preexec_fn=os.setsid if hasattr(os, 'setsid') else None,
                    start_new_session=True if sys.platform == 'win32' else False
                )
            
            # Save PID to file
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))
            
            print(f"✅ Started process {process.pid} for {model_name}")
            print(f"   Logs: {log_file}")
            
            return process.pid
            
        except Exception as e:
            print(f"❌ Failed to start process for {model_name}: {e}")
            return None
    
    def stop_process(self, model_name: str, force: bool = False) -> bool:
        """Stop a background process
        
        Args:
            model_name: Name of the model
            force: Use SIGKILL instead of SIGTERM
            
        Returns:
            True if process was stopped, False otherwise
        """
        pid = self.get_process_pid(model_name)
        if not pid:
            print(f"⚠️  No PID found for {model_name}")
            return False
        
        try:
            if not self.is_process_running(pid):
                print(f"⚠️  Process {pid} for {model_name} is not running")
                self._cleanup_pid_file(model_name)
                return True
            
            # Try graceful shutdown first
            if not force:
                os.kill(pid, signal.SIGTERM)
                
                # Wait a bit for graceful shutdown
                import time
                for _ in range(10):  # Wait up to 10 seconds
                    time.sleep(1)
                    if not self.is_process_running(pid):
                        break
                else:
                    # Force kill if still running
                    print(f"⚠️  Graceful shutdown failed for {model_name}, using force")
                    force = True
            
            if force and self.is_process_running(pid):
                # Kill process tree to ensure all children are terminated
                self.kill_process_tree(pid)
            
            # Clean up PID file
            self._cleanup_pid_file(model_name)
            
            print(f"✅ Stopped process {pid} for {model_name}")
            return True
            
        except ProcessLookupError:
            # Process already dead
            self._cleanup_pid_file(model_name)
            return True
        except PermissionError:
            print(f"❌ Permission denied stopping process {pid} for {model_name}")
            return False
        except Exception as e:
            print(f"❌ Error stopping process for {model_name}: {e}")
            return False
    
    def is_process_running(self, pid: int) -> bool:
        """Check if a process is running
        
        Args:
            pid: Process ID
            
        Returns:
            True if process is running, False otherwise
        """
        try:
            # On Unix, kill with signal 0 doesn't actually kill, just checks existence
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, OSError):
            return False
    
    def get_process_pid(self, model_name: str) -> Optional[int]:
        """Get the PID of a model's process
        
        Args:
            model_name: Name of the model
            
        Returns:
            Process ID if found, None otherwise
        """
        pid_file = self.config.get_model_pid_file(model_name)
        
        if not pid_file.exists():
            return None
        
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
                
            # Verify process is still running
            if self.is_process_running(pid):
                return pid
            else:
                # Clean up stale PID file
                self._cleanup_pid_file(model_name)
                return None
                
        except (ValueError, FileNotFoundError):
            return None
    
    def get_process_info(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a process
        
        Args:
            pid: Process ID
            
        Returns:
            Process information dictionary or None
        """
        try:
            process = psutil.Process(pid)
            
            return {
                "pid": pid,
                "name": process.name(),
                "status": process.status(),
                "cpu_percent": process.cpu_percent(),
                "memory_info": process.memory_info()._asdict(),
                "memory_percent": process.memory_percent(),
                "create_time": process.create_time(),
                "cmdline": process.cmdline()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    
    def kill_process_tree(self, pid: int):
        """Kill a process and all its children
        
        Args:
            pid: Root process ID
        """
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # Kill children first
            for child in children:
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            
            # Kill parent
            parent.kill()
            
            # Wait for processes to die
            gone, alive = psutil.wait_procs(children + [parent], timeout=3)
            
            # Force kill any that are still alive
            for proc in alive:
                try:
                    proc.kill()
                except psutil.NoSuchProcess:
                    pass
                    
        except psutil.NoSuchProcess:
            pass  # Process already dead
    
    def list_running_processes(self) -> Dict[str, Dict[str, Any]]:
        """List all running model processes
        
        Returns:
            Dictionary mapping model_name -> process_info
        """
        running_processes = {}
        
        # Check all PID files
        if not self.config.pids_dir.exists():
            return running_processes
        
        for pid_file in self.config.pids_dir.glob("*.pid"):
            if pid_file.name == "server.pid":
                continue  # Skip server PID
                
            model_name = pid_file.stem.replace("_", "/")  # Reverse safe name conversion
            pid = self.get_process_pid(model_name)
            
            if pid:
                process_info = self.get_process_info(pid)
                if process_info:
                    running_processes[model_name] = process_info
        
        return running_processes
    
    def cleanup_dead_processes(self):
        """Remove PID files for processes that are no longer running"""
        if not self.config.pids_dir.exists():
            return
        
        cleaned = 0
        for pid_file in self.config.pids_dir.glob("*.pid"):
            if pid_file.name == "server.pid":
                continue
                
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                if not self.is_process_running(pid):
                    pid_file.unlink()
                    cleaned += 1
                    
            except (ValueError, FileNotFoundError):
                # Invalid or missing PID file
                try:
                    pid_file.unlink()
                    cleaned += 1
                except FileNotFoundError:
                    pass
        
        if cleaned > 0:
            print(f"Cleaned up {cleaned} dead process PID files")
    
    def _cleanup_pid_file(self, model_name: str):
        """Remove PID file for a model
        
        Args:
            model_name: Name of the model
        """
        pid_file = self.config.get_model_pid_file(model_name)
        try:
            if pid_file.exists():
                pid_file.unlink()
        except FileNotFoundError:
            pass
    
    def get_server_pid(self) -> Optional[int]:
        """Get the PID of the PolarisLLM server
        
        Returns:
            Server process ID if running, None otherwise
        """
        if not self.config.server_pid_file.exists():
            return None
        
        try:
            with open(self.config.server_pid_file, 'r') as f:
                pid = int(f.read().strip())
                
            if self.is_process_running(pid):
                return pid
            else:
                # Clean up stale PID file
                try:
                    self.config.server_pid_file.unlink()
                except FileNotFoundError:
                    pass
                return None
                
        except (ValueError, FileNotFoundError):
            return None
    
    def save_server_pid(self, pid: int):
        """Save server PID to file
        
        Args:
            pid: Server process ID
        """
        try:
            with open(self.config.server_pid_file, 'w') as f:
                f.write(str(pid))
        except Exception as e:
            print(f"Warning: Could not save server PID: {e}") 