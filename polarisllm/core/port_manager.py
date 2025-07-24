"""
Port Management System for PolarisLLM
"""

import json
import socket
from typing import Any, Dict, Optional, Set

from .config import PolarisConfig


class PortManager:
    """Manages port allocation for models"""
    
    def __init__(self, config: PolarisConfig):
        """Initialize port manager
        
        Args:
            config: PolarisLLM configuration instance
        """
        self.config = config
        self.models_config = config.get_models_config()
        self.port_start = self.models_config["port_range_start"] 
        self.port_end = self.models_config["port_range_end"]
        
    def is_port_available(self, port: int) -> bool:
        """Check if a port is available
        
        Args:
            port: Port number to check
            
        Returns:
            True if port is available, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                result = sock.bind(('localhost', port))
                return True
        except OSError:
            return False
    
    def get_allocated_ports(self) -> Dict[int, str]:
        """Get currently allocated ports from file
        
        Returns:
            Dictionary mapping port -> model_name
        """
        if not self.config.ports_file.exists():
            return {}
        
        try:
            with open(self.config.ports_file, 'r') as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except Exception as e:
            print(f"Warning: Could not load ports file: {e}")
            return {}
    
    def save_allocated_ports(self, ports: Dict[int, str]):
        """Save allocated ports to file
        
        Args:
            ports: Dictionary mapping port -> model_name
        """
        try:
            with open(self.config.ports_file, 'w') as f:
                # Convert int keys to strings for JSON
                data = {str(k): v for k, v in ports.items()}
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save ports file: {e}")
    
    def allocate_port(self, model_name: str, preferred_port: Optional[int] = None) -> Optional[int]:
        """Allocate a port for a model
        
        Args:
            model_name: Name of the model
            preferred_port: Preferred port number (optional)
            
        Returns:
            Allocated port number, or None if no ports available
        """
        allocated_ports = self.get_allocated_ports()
        
        # Check if model already has a port allocated
        for port, name in allocated_ports.items():
            if name == model_name:
                if self.is_port_available(port):
                    return port
                else:
                    # Port is allocated but not available, remove from registry
                    del allocated_ports[port]
                    break
        
        # Try preferred port first
        if preferred_port and self.port_start <= preferred_port <= self.port_end:
            if preferred_port not in allocated_ports and self.is_port_available(preferred_port):
                allocated_ports[preferred_port] = model_name
                self.save_allocated_ports(allocated_ports)
                return preferred_port
        
        # Find next available port in range
        for port in range(self.port_start, self.port_end + 1):
            if port not in allocated_ports and self.is_port_available(port):
                allocated_ports[port] = model_name
                self.save_allocated_ports(allocated_ports)
                return port
        
        # No ports available
        return None
    
    def release_port(self, port: int, model_name: str):
        """Release a port allocation
        
        Args:
            port: Port number to release
            model_name: Name of the model (for verification)
        """
        allocated_ports = self.get_allocated_ports()
        
        if port in allocated_ports and allocated_ports[port] == model_name:
            del allocated_ports[port]
            self.save_allocated_ports(allocated_ports)
    
    def get_model_port(self, model_name: str) -> Optional[int]:
        """Get the allocated port for a model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Port number if allocated, None otherwise
        """
        allocated_ports = self.get_allocated_ports()
        
        for port, name in allocated_ports.items():
            if name == model_name:
                return port
        
        return None
    
    def cleanup_dead_ports(self):
        """Remove port allocations for ports that are no longer in use"""
        allocated_ports = self.get_allocated_ports()
        active_ports = {}
        
        for port, model_name in allocated_ports.items():
            if not self.is_port_available(port):
                # Port is still in use, keep allocation
                active_ports[port] = model_name
        
        if len(active_ports) != len(allocated_ports):
            self.save_allocated_ports(active_ports)
            print(f"Cleaned up {len(allocated_ports) - len(active_ports)} dead port allocations")
    
    def list_allocated_ports(self) -> Dict[str, int]:
        """List all allocated ports by model name
        
        Returns:
            Dictionary mapping model_name -> port
        """
        allocated_ports = self.get_allocated_ports()
        return {name: port for port, name in allocated_ports.items()}
    
    def get_available_port_count(self) -> int:
        """Get number of available ports in range
        
        Returns:
            Number of available ports
        """
        allocated_ports = self.get_allocated_ports()
        total_ports = self.port_end - self.port_start + 1
        return total_ports - len(allocated_ports) 