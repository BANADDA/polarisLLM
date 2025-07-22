"""
PolarisLLM Runtime Core - Main runtime engine for managing models
"""

import asyncio
import logging
import os
import subprocess
import signal
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml
import psutil

from .model_manager import ModelManager
from .config import RuntimeConfig

@dataclass
class ModelStatus:
    """Status information for a running model"""
    name: str
    model_id: str
    status: str  # 'loading', 'running', 'stopped', 'error'
    port: int
    pid: Optional[int] = None
    memory_usage: Optional[float] = None
    gpu_usage: Optional[float] = None
    last_activity: Optional[float] = None
    error_message: Optional[str] = None

class PolarisRuntime:
    """Main runtime engine for PolarisLLM"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.config = RuntimeConfig.load(config_path)
        self.model_manager = ModelManager(self.config)
        self.running_models: Dict[str, ModelStatus] = {}
        self.port_pool = list(range(self.config.port_range_start, self.config.port_range_end + 1))
        self.used_ports = set()
        self._shutdown_event = asyncio.Event()
        
    async def start(self):
        """Start the runtime engine"""
        self.logger.info("Starting PolarisLLM Runtime Engine")
        
        # Create necessary directories
        os.makedirs(self.config.models_dir, exist_ok=True)
        os.makedirs(self.config.logs_dir, exist_ok=True)
        
        # Load model configurations
        await self.model_manager.load_model_configs()
        
        # Start monitoring task
        asyncio.create_task(self._monitor_models())
        
        self.logger.info("Runtime engine started successfully")
        
    async def stop(self):
        """Stop the runtime engine"""
        self.logger.info("Stopping PolarisLLM Runtime Engine")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Stop all running models
        tasks = []
        for model_name in list(self.running_models.keys()):
            tasks.append(self.stop_model(model_name))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.logger.info("Runtime engine stopped")
        
    async def load_model(self, model_name: str, **kwargs) -> ModelStatus:
        """Load and start a model"""
        if model_name in self.running_models:
            if self.running_models[model_name].status == 'running':
                self.logger.warning(f"Model {model_name} is already running")
                return self.running_models[model_name]
            else:
                # Stop existing model first
                await self.stop_model(model_name)
        
        # Get available port
        port = self._get_available_port()
        if port is None:
            raise RuntimeError("No available ports for model deployment")
        
        # Get model configuration
        model_config = self.model_manager.get_model_config(model_name)
        if not model_config:
            raise ValueError(f"Model configuration not found: {model_name}")
        
        # Create model status
        status = ModelStatus(
            name=model_name,
            model_id=model_config.model_id,
            status='loading',
            port=port
        )
        self.running_models[model_name] = status
        self.used_ports.add(port)
        
        try:
            # Start model deployment using ms-swift
            await self._deploy_model_swift(model_name, model_config, port, **kwargs)
            
            # Wait for model to be ready
            await self._wait_for_model_ready(model_name, port)
            
            status.status = 'running'
            status.last_activity = time.time()
            
            self.logger.info(f"Model {model_name} loaded successfully on port {port}")
            return status
            
        except Exception as e:
            status.status = 'error'
            status.error_message = str(e)
            self.used_ports.discard(port)
            self.logger.error(f"Failed to load model {model_name}: {e}")
            raise
    
    async def stop_model(self, model_name: str) -> bool:
        """Stop a running model"""
        if model_name not in self.running_models:
            self.logger.warning(f"Model {model_name} is not running")
            return False
        
        status = self.running_models[model_name]
        
        try:
            # Kill the process if it exists
            if status.pid:
                try:
                    process = psutil.Process(status.pid)
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=10)
                    except psutil.TimeoutExpired:
                        # Force kill if needed
                        process.kill()
                        process.wait()
                        
                except psutil.NoSuchProcess:
                    pass  # Process already dead
            
            # Free the port
            self.used_ports.discard(status.port)
            
            # Remove from running models
            del self.running_models[model_name]
            
            self.logger.info(f"Model {model_name} stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping model {model_name}: {e}")
            return False
    
    async def list_models(self) -> Dict[str, Any]:
        """List all available and running models"""
        available = self.model_manager.list_available_models()
        running = {name: asdict(status) for name, status in self.running_models.items()}
        
        return {
            'available': available,
            'running': running,
            'total_available': len(available),
            'total_running': len(running)
        }
    
    async def get_model_status(self, model_name: str) -> Optional[ModelStatus]:
        """Get status of a specific model"""
        return self.running_models.get(model_name)
    
    async def _deploy_model_swift(self, model_name: str, model_config, port: int, **kwargs):
        """Deploy model using ms-swift backend"""
        
        # Prepare swift command
        cmd = [
            'swift', 'deploy',
            '--model_type', model_config.model_type,
            '--model_id', model_config.model_id,
            '--port', str(port),
            '--host', self.config.host
        ]
        
        # Add template if specified
        if hasattr(model_config, 'template') and model_config.template:
            cmd.extend(['--template', model_config.template])
        
        # Add custom arguments from kwargs
        for key, value in kwargs.items():
            if key.startswith('swift_'):
                swift_key = key[6:]  # Remove 'swift_' prefix
                cmd.extend([f'--{swift_key}', str(value)])
        
        # Add model-specific arguments from config
        if hasattr(model_config, 'swift_args') and model_config.swift_args:
            for key, value in model_config.swift_args.items():
                cmd.extend([f'--{key}', str(value)])
        
        # Set environment variables
        env = os.environ.copy()
        env.update(self.config.env_vars)
        
        # Start the process
        self.logger.info(f"Starting model deployment: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Store PID
        self.running_models[model_name].pid = process.pid
        
        # Monitor process startup
        startup_timeout = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < startup_timeout:
            if process.poll() is not None:
                # Process ended
                stdout, stderr = process.communicate()
                raise RuntimeError(f"Model deployment failed: {stderr}")
            
            await asyncio.sleep(1)
            
            # Check if model is responding
            if await self._check_model_health(port):
                break
        else:
            # Timeout
            process.terminate()
            raise RuntimeError("Model deployment timed out")
    
    async def _wait_for_model_ready(self, model_name: str, port: int, timeout: int = 300):
        """Wait for model to be ready to serve requests"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if await self._check_model_health(port):
                return
            await asyncio.sleep(2)
        
        raise RuntimeError(f"Model {model_name} failed to become ready within {timeout} seconds")
    
    async def _check_model_health(self, port: int) -> bool:
        """Check if model is healthy and responding"""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{self.config.host}:{port}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except:
            return False
    
    def _get_available_port(self) -> Optional[int]:
        """Get an available port from the pool"""
        for port in self.port_pool:
            if port not in self.used_ports:
                return port
        return None
    
    async def _monitor_models(self):
        """Background task to monitor model health and resource usage"""
        while not self._shutdown_event.is_set():
            try:
                for model_name, status in list(self.running_models.items()):
                    if status.pid:
                        try:
                            process = psutil.Process(status.pid)
                            
                            # Update resource usage
                            status.memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                            
                            # Check if process is still alive
                            if not process.is_running():
                                status.status = 'stopped'
                                self.logger.warning(f"Model {model_name} process died unexpectedly")
                            
                            # Check health
                            elif not await self._check_model_health(status.port):
                                status.status = 'error'
                                status.error_message = "Health check failed"
                            
                            else:
                                status.status = 'running'
                                status.error_message = None
                                
                        except psutil.NoSuchProcess:
                            status.status = 'stopped'
                            status.pid = None
            
            except Exception as e:
                self.logger.error(f"Error in model monitoring: {e}")
            
            await asyncio.sleep(30)  # Monitor every 30 seconds