"""
Model Registry System for PolarisLLM
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import PolarisConfig
from .port_manager import PortManager
from .process_manager import ProcessManager


class ModelInfo:
    """Information about a deployed model"""
    
    def __init__(
        self,
        name: str,
        model_id: str,
        model_type: str,
        port: int,
        pid: Optional[int] = None,
        status: str = "unknown",
        deployed_at: Optional[float] = None,
        last_activity: Optional[float] = None,
        memory_usage: Optional[float] = None,
        swift_args: Optional[Dict] = None
    ):
        self.name = name
        self.model_id = model_id
        self.model_type = model_type
        self.port = port
        self.pid = pid
        self.status = status  # running, stopped, crashed, unknown
        self.deployed_at = deployed_at or time.time()
        self.last_activity = last_activity or time.time()
        self.memory_usage = memory_usage
        self.swift_args = swift_args or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "model_id": self.model_id,
            "model_type": self.model_type,
            "port": self.port,
            "pid": self.pid,
            "status": self.status,
            "deployed_at": self.deployed_at,
            "last_activity": self.last_activity,
            "memory_usage": self.memory_usage,
            "swift_args": self.swift_args
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelInfo':
        """Create ModelInfo from dictionary"""
        return cls(**data)
    
    def update_status(self, status: str, pid: Optional[int] = None):
        """Update model status and activity"""
        self.status = status
        self.last_activity = time.time()
        if pid is not None:
            self.pid = pid


class ModelRegistry:
    """Registry for tracking deployed models"""
    
    def __init__(self, config: PolarisConfig):
        """Initialize model registry
        
        Args:
            config: PolarisLLM configuration instance
        """
        self.config = config
        self.port_manager = PortManager(config)
        self.process_manager = ProcessManager(config)
        self._models = {}
        
        # Load existing registry
        self.load_registry()
    
    def register_model(
        self,
        name: str,
        model_id: str,
        model_type: str,
        port: int,
        pid: Optional[int] = None,
        swift_args: Optional[Dict] = None
    ) -> ModelInfo:
        """Register a new model
        
        Args:
            name: Model name
            model_id: Model ID (e.g., Qwen/Qwen2.5-7B-Instruct)
            model_type: Model type (e.g., qwen2_5)
            port: Port number
            pid: Process ID
            swift_args: Additional swift arguments
            
        Returns:
            ModelInfo instance
        """
        model_info = ModelInfo(
            name=name,
            model_id=model_id,
            model_type=model_type,
            port=port,
            pid=pid,
            status="running" if pid else "starting",
            swift_args=swift_args
        )
        
        self._models[name] = model_info
        self.save_registry()
        
        print(f"✅ Registered model: {name}")
        return model_info
    
    def unregister_model(self, name: str) -> bool:
        """Unregister a model
        
        Args:
            name: Model name
            
        Returns:
            True if successful, False otherwise
        """
        if name in self._models:
            model_info = self._models[name]
            
            # Release port allocation
            self.port_manager.release_port(model_info.port, name)
            
            # Remove from registry
            del self._models[name]
            self.save_registry()
            
            print(f"✅ Unregistered model: {name}")
            return True
        
        return False
    
    def get_model_info(self, name: str) -> Optional[ModelInfo]:
        """Get information about a model
        
        Args:
            name: Model name
            
        Returns:
            ModelInfo instance or None
        """
        return self._models.get(name)
    
    def list_models(self) -> Dict[str, ModelInfo]:
        """List all registered models
        
        Returns:
            Dictionary mapping model name to ModelInfo
        """
        return self._models.copy()
    
    def update_model_status(self, name: str, status: str, pid: Optional[int] = None):
        """Update model status
        
        Args:
            name: Model name
            status: New status
            pid: Process ID (optional)
        """
        if name in self._models:
            self._models[name].update_status(status, pid)
            self.save_registry()
    
    def discover_running_models(self):
        """Discover and register running swift models that aren't in registry"""
        print("🔍 Discovering running models...")
        
        # Get running processes
        running_processes = self.process_manager.list_running_processes()
        discovered = 0
        
        for model_name, process_info in running_processes.items():
            if model_name not in self._models:
                # Try to determine model info from process
                cmdline = process_info.get("cmdline", [])
                model_id, model_type, port = self._parse_swift_cmdline(cmdline)
                
                if model_id and model_type and port:
                    # Register discovered model
                    self.register_model(
                        name=model_name,
                        model_id=model_id,
                        model_type=model_type,
                        port=port,
                        pid=process_info["pid"]
                    )
                    discovered += 1
                    print(f"   Discovered: {model_name} on port {port}")
        
        if discovered > 0:
            print(f"✅ Discovered {discovered} running models")
        else:
            print("ℹ️  No new models discovered")
    
    def refresh_model_status(self):
        """Refresh status of all registered models"""
        for name, model_info in self._models.items():
            if model_info.pid:
                if self.process_manager.is_process_running(model_info.pid):
                    # Update process info
                    process_info = self.process_manager.get_process_info(model_info.pid)
                    if process_info:
                        model_info.update_status("running")
                        model_info.memory_usage = process_info.get("memory_percent")
                else:
                    # Process is dead
                    model_info.update_status("stopped")
                    model_info.pid = None
            else:
                # No PID, check if port is in use
                if not self.port_manager.is_port_available(model_info.port):
                    model_info.update_status("running")
                else:
                    model_info.update_status("stopped")
        
        self.save_registry()
    
    def cleanup_dead_models(self):
        """Remove models that are no longer running from registry"""
        self.refresh_model_status()
        
        dead_models = []
        for name, model_info in self._models.items():
            if model_info.status in ["stopped", "crashed"]:
                # Check if it's been dead for a while (5 minutes)
                if time.time() - model_info.last_activity > 300:
                    dead_models.append(name)
        
        for name in dead_models:
            print(f"🧹 Cleaning up dead model: {name}")
            self.unregister_model(name)
        
        if dead_models:
            print(f"✅ Cleaned up {len(dead_models)} dead models")
    
    def get_running_models(self) -> Dict[str, ModelInfo]:
        """Get only running models
        
        Returns:
            Dictionary of running models
        """
        self.refresh_model_status()
        return {
            name: info for name, info in self._models.items()
            if info.status == "running"
        }
    
    def get_model_by_port(self, port: int) -> Optional[ModelInfo]:
        """Get model by port number
        
        Args:
            port: Port number
            
        Returns:
            ModelInfo instance or None
        """
        for model_info in self._models.values():
            if model_info.port == port:
                return model_info
        return None
    
    def load_registry(self):
        """Load registry from file"""
        if not self.config.registry_file.exists():
            return
        
        try:
            with open(self.config.registry_file, 'r') as f:
                data = json.load(f)
            
            models_data = data.get("models", {})
            for name, model_data in models_data.items():
                self._models[name] = ModelInfo.from_dict(model_data)
                
        except Exception as e:
            print(f"Warning: Could not load registry: {e}")
    
    def save_registry(self):
        """Save registry to file"""
        try:
            data = {
                "last_updated": time.time(),
                "models": {
                    name: model_info.to_dict()
                    for name, model_info in self._models.items()
                }
            }
            
            with open(self.config.registry_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save registry: {e}")
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics
        
        Returns:
            Dictionary with registry stats
        """
        self.refresh_model_status()
        
        stats = {
            "total_models": len(self._models),
            "running_models": len([m for m in self._models.values() if m.status == "running"]),
            "stopped_models": len([m for m in self._models.values() if m.status == "stopped"]),
            "ports_used": len(set(m.port for m in self._models.values())),
            "memory_usage": sum(m.memory_usage or 0 for m in self._models.values()),
            "oldest_deployment": min((m.deployed_at for m in self._models.values()), default=None),
            "newest_deployment": max((m.deployed_at for m in self._models.values()), default=None)
        }
        
        return stats
    
    def _parse_swift_cmdline(self, cmdline: List[str]) -> tuple:
        """Parse swift command line to extract model info
        
        Args:
            cmdline: Command line arguments
            
        Returns:
            Tuple of (model_id, model_type, port)
        """
        model_id = None
        model_type = None
        port = None
        
        for i, arg in enumerate(cmdline):
            if arg == "--model" and i + 1 < len(cmdline):
                model_id = cmdline[i + 1]
            elif arg == "--model_type" and i + 1 < len(cmdline):
                model_type = cmdline[i + 1]
            elif arg == "--port" and i + 1 < len(cmdline):
                try:
                    port = int(cmdline[i + 1])
                except ValueError:
                    pass
        
        return model_id, model_type, port 