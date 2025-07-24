"""
Log Management System for PolarisLLM
"""

import os
import time
from pathlib import Path
from typing import Generator, List, Optional

from .config import PolarisConfig


class LogManager:
    """Manages logs for models and server"""
    
    def __init__(self, config: PolarisConfig):
        """Initialize log manager
        
        Args:
            config: PolarisLLM configuration instance
        """
        self.config = config
        self.logging_config = config.get_logging_config()
    
    def get_log_file(self, model_name: str) -> Path:
        """Get log file path for a model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Path to the log file
        """
        return self.config.get_model_log_file(model_name)
    
    def get_server_log_file(self) -> Path:
        """Get server log file path
        
        Returns:
            Path to the server log file
        """
        return self.config.logs_dir / "server.log"
    
    def create_log_file(self, model_name: str) -> Path:
        """Create a log file for a model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Path to the created log file
        """
        log_file = self.get_log_file(model_name)
        
        # Create parent directory if it doesn't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create log file with initial entry
        if not log_file.exists():
            with open(log_file, 'w') as f:
                f.write(f"=== PolarisLLM Model Log: {model_name} ===\n")
                f.write(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
        
        return log_file
    
    def tail_logs(self, model_name: str, lines: int = 100) -> List[str]:
        """Get the last N lines from a model's log file
        
        Args:
            model_name: Name of the model
            lines: Number of lines to return
            
        Returns:
            List of log lines
        """
        log_file = self.get_log_file(model_name)
        
        if not log_file.exists():
            return [f"No log file found for {model_name}"]
        
        try:
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            return [f"Error reading log file: {e}"]
    
    def stream_logs(self, model_name: str, follow: bool = True) -> Generator[str, None, None]:
        """Stream logs from a model in real-time
        
        Args:
            model_name: Name of the model
            follow: Whether to follow the log file (tail -f style)
            
        Yields:
            Log lines as they are written
        """
        log_file = self.get_log_file(model_name)
        
        if not log_file.exists():
            yield f"No log file found for {model_name}\n"
            return
        
        try:
            with open(log_file, 'r') as f:
                # Seek to end if following
                if follow:
                    f.seek(0, 2)  # Seek to end
                
                while True:
                    line = f.readline()
                    if line:
                        yield line
                    elif follow:
                        time.sleep(0.1)  # Wait a bit before checking again
                    else:
                        break
                        
        except KeyboardInterrupt:
            yield "\n--- Log streaming interrupted ---\n"
        except Exception as e:
            yield f"Error streaming logs: {e}\n"
    
    def clear_logs(self, model_name: str) -> bool:
        """Clear logs for a model
        
        Args:
            model_name: Name of the model
            
        Returns:
            True if successful, False otherwise
        """
        log_file = self.get_log_file(model_name)
        
        try:
            if log_file.exists():
                # Archive current log before clearing
                self._archive_log(model_name)
                
                # Create new empty log file
                self.create_log_file(model_name)
                return True
            else:
                return True  # No log to clear
                
        except Exception as e:
            print(f"Error clearing logs for {model_name}: {e}")
            return False
    
    def rotate_logs(self, model_name: str) -> bool:
        """Rotate logs for a model
        
        Args:
            model_name: Name of the model
            
        Returns:
            True if successful, False otherwise
        """
        if not self.logging_config.get("enable_rotation", True):
            return True
        
        log_file = self.get_log_file(model_name)
        
        if not log_file.exists():
            return True
        
        try:
            # Check if rotation is needed
            max_size = self._parse_size(self.logging_config.get("max_log_size", "100MB"))
            current_size = log_file.stat().st_size
            
            if current_size > max_size:
                self._archive_log(model_name)
                self.create_log_file(model_name)
                print(f"Rotated logs for {model_name} (size: {current_size} bytes)")
                return True
                
            return True
            
        except Exception as e:
            print(f"Error rotating logs for {model_name}: {e}")
            return False
    
    def cleanup_old_logs(self):
        """Clean up old log files based on retention policy"""
        retention_days = self.logging_config.get("log_retention_days", 7)
        current_time = time.time()
        cutoff_time = current_time - (retention_days * 24 * 60 * 60)
        
        cleaned = 0
        
        try:
            # Clean up regular log files
            for log_file in self.config.logs_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    cleaned += 1
            
            # Clean up archived log files
            for archive_file in self.config.logs_dir.glob("*.log.*"):
                if archive_file.stat().st_mtime < cutoff_time:
                    archive_file.unlink()
                    cleaned += 1
            
            if cleaned > 0:
                print(f"Cleaned up {cleaned} old log files")
                
        except Exception as e:
            print(f"Error cleaning up old logs: {e}")
    
    def get_log_summary(self) -> dict:
        """Get summary of all log files
        
        Returns:
            Dictionary with log file information
        """
        summary = {
            "models": {},
            "server": {},
            "total_size": 0
        }
        
        try:
            # Check model logs
            for log_file in self.config.logs_dir.glob("*.log"):
                if log_file.name == "server.log":
                    continue
                
                model_name = log_file.stem.replace("_", "/")
                stat = log_file.stat()
                
                summary["models"][model_name] = {
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "lines": self._count_lines(log_file)
                }
                summary["total_size"] += stat.st_size
            
            # Check server log
            server_log = self.get_server_log_file()
            if server_log.exists():
                stat = server_log.stat()
                summary["server"] = {
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "lines": self._count_lines(server_log)
                }
                summary["total_size"] += stat.st_size
        
        except Exception as e:
            print(f"Error getting log summary: {e}")
        
        return summary
    
    def _archive_log(self, model_name: str):
        """Archive a log file with timestamp
        
        Args:
            model_name: Name of the model
        """
        log_file = self.get_log_file(model_name)
        
        if log_file.exists():
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            archive_file = log_file.with_suffix(f".log.{timestamp}")
            log_file.rename(archive_file)
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string (e.g., '100MB') to bytes
        
        Args:
            size_str: Size string
            
        Returns:
            Size in bytes
        """
        size_str = size_str.upper().strip()
        
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            # Assume bytes
            return int(size_str)
    
    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a file efficiently
        
        Args:
            file_path: Path to the file
            
        Returns:
            Number of lines
        """
        try:
            with open(file_path, 'rb') as f:
                lines = sum(1 for _ in f)
            return lines
        except Exception:
            return 0 