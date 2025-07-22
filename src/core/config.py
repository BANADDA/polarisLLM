"""
Configuration management for PolarisLLM Runtime
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    name: str
    model_id: str
    model_type: str
    template: Optional[str] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)
    swift_args: Dict[str, Any] = field(default_factory=dict)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

@dataclass  
class RuntimeConfig:
    """Main runtime configuration"""
    host: str = "0.0.0.0"
    port_range_start: int = 8000
    port_range_end: int = 8100
    models_dir: str = "models"
    logs_dir: str = "logs"
    config_dir: str = "config"
    max_concurrent_models: int = 5
    model_timeout: int = 300
    health_check_interval: int = 30
    env_vars: Dict[str, str] = field(default_factory=dict)
    swift_path: str = "swift"
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> 'RuntimeConfig':
        """Load configuration from file"""
        if config_path is None:
            config_path = os.getenv('POLARIS_CONFIG', 'config/runtime.yaml')
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)
        else:
            # Create default config
            config = cls()
            config.save(config_path)
            return config
    
    def save(self, config_path: str):
        """Save configuration to file"""
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(self.__dict__, f, default_flow_style=False)