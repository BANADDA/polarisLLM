"""
PolarisLLM Configuration Management
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class PolarisConfig:
    """Configuration management for PolarisLLM"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration
        
        Args:
            config_dir: Custom config directory, defaults to ~/.polarisllm
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / ".polarisllm"
        
        # Create directory structure
        self.ensure_directories()
        
        # Default configuration
        self.defaults = {
            "server": {
                "host": "0.0.0.0",
                "port": 7860,
                "log_level": "info"
            },
            "models": {
                "port_range_start": 8000,
                "port_range_end": 8100,
                "max_concurrent": 10,
                "auto_restart": True,
                "health_check_interval": 30
            },
            "logging": {
                "max_log_size": "100MB",
                "log_retention_days": 7,
                "enable_rotation": True
            }
        }
    
    def ensure_directories(self):
        """Create necessary directories"""
        directories = [
            self.config_dir,
            self.config_dir / "logs",
            self.config_dir / "pids", 
            self.config_dir / "config"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def registry_file(self) -> Path:
        """Path to model registry file"""
        return self.config_dir / "registry.json"
    
    @property
    def server_pid_file(self) -> Path:
        """Path to server PID file"""
        return self.config_dir / "pids" / "server.pid"
    
    @property 
    def ports_file(self) -> Path:
        """Path to port allocation file"""
        return self.config_dir / "config" / "ports.json"
    
    @property
    def logs_dir(self) -> Path:
        """Path to logs directory"""
        return self.config_dir / "logs"
    
    @property
    def pids_dir(self) -> Path:
        """Path to PIDs directory"""
        return self.config_dir / "pids"
    
    def get_model_log_file(self, model_name: str) -> Path:
        """Get log file path for a model"""
        safe_name = model_name.replace("/", "_").replace(":", "_")
        return self.logs_dir / f"{safe_name}.log"
    
    def get_model_pid_file(self, model_name: str) -> Path:
        """Get PID file path for a model"""
        safe_name = model_name.replace("/", "_").replace(":", "_")
        return self.pids_dir / f"{safe_name}.pid"
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or return defaults"""
        config_file = self.config_dir / "config" / "polarisllm.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                # Merge with defaults
                config = self.defaults.copy()
                self._deep_merge(config, user_config)
                return config
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        return self.defaults.copy()
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        config_file = self.config_dir / "config" / "polarisllm.json"
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")
    
    def _deep_merge(self, base: Dict, override: Dict):
        """Deep merge override into base dictionary"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server-specific configuration"""
        config = self.load_config()
        return config.get("server", self.defaults["server"])
    
    def get_models_config(self) -> Dict[str, Any]:
        """Get model-specific configuration"""
        config = self.load_config()
        return config.get("models", self.defaults["models"])
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging-specific configuration"""
        config = self.load_config()
        return config.get("logging", self.defaults["logging"]) 