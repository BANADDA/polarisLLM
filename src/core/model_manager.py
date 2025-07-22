"""
Model Registry and Management for PolarisLLM
"""

import os
import yaml
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .config import ModelConfig, RuntimeConfig

class ModelManager:
    """Manages model configurations and registry"""
    
    def __init__(self, runtime_config: RuntimeConfig):
        self.logger = logging.getLogger(__name__)
        self.config = runtime_config
        self.models: Dict[str, ModelConfig] = {}
        
    async def load_model_configs(self):
        """Load all model configurations from the models directory"""
        models_config_dir = Path(self.config.config_dir) / "models"
        
        # Create default model configs if directory doesn't exist
        if not models_config_dir.exists():
            self._create_default_configs(models_config_dir)
        
        # Load all YAML files from models directory
        for config_file in models_config_dir.glob("*.yaml"):
            try:
                with open(config_file, 'r') as f:
                    data = yaml.safe_load(f)
                
                if isinstance(data, dict):
                    # Single model config
                    model_config = ModelConfig(**data)
                    self.models[model_config.name] = model_config
                    
                elif isinstance(data, list):
                    # Multiple model configs
                    for model_data in data:
                        model_config = ModelConfig(**model_data)
                        self.models[model_config.name] = model_config
                
                self.logger.info(f"Loaded model config from {config_file}")
                
            except Exception as e:
                self.logger.error(f"Failed to load model config {config_file}: {e}")
        
        self.logger.info(f"Loaded {len(self.models)} model configurations")
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model"""
        return self.models.get(model_name)
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available models"""
        return [
            {
                'name': config.name,
                'model_id': config.model_id,
                'model_type': config.model_type,
                'description': config.description,
                'tags': config.tags,
                'enabled': config.enabled
            }
            for config in self.models.values()
            if config.enabled
        ]
    
    def add_model_config(self, model_config: ModelConfig) -> bool:
        """Add a new model configuration"""
        try:
            self.models[model_config.name] = model_config
            
            # Save to file
            config_file = Path(self.config.config_dir) / "models" / f"{model_config.name}.yaml"
            os.makedirs(config_file.parent, exist_ok=True)
            
            with open(config_file, 'w') as f:
                yaml.dump(model_config.__dict__, f, default_flow_style=False)
            
            self.logger.info(f"Added model config: {model_config.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add model config {model_config.name}: {e}")
            return False
    
    def remove_model_config(self, model_name: str) -> bool:
        """Remove a model configuration"""
        try:
            if model_name in self.models:
                del self.models[model_name]
                
                # Remove config file
                config_file = Path(self.config.config_dir) / "models" / f"{model_name}.yaml"
                if config_file.exists():
                    config_file.unlink()
                
                self.logger.info(f"Removed model config: {model_name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to remove model config {model_name}: {e}")
            return False
    
    def _create_default_configs(self, models_dir: Path):
        """Create default model configurations"""
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Default models based on the ms-swift supported models
        default_models = [
            {
                'name': 'deepseek-vl-7b-chat',
                'model_id': 'deepseek-ai/deepseek-vl-7b-chat',
                'model_type': 'deepseek_vl',
                'template': 'deepseek_vl',
                'description': 'DeepSeek VL 7B Chat - Vision Language Model',
                'tags': ['vision', 'chat'],
                'swift_args': {
                    'max_length': 4096
                }
            },
            {
                'name': 'qwen2.5-7b-instruct',
                'model_id': 'Qwen/Qwen2.5-7B-Instruct',
                'model_type': 'qwen2_5',
                'template': 'qwen2_5',
                'description': 'Qwen 2.5 7B Instruct - General purpose chat model',
                'tags': ['chat', 'instruct'],
                'swift_args': {
                    'max_length': 8192
                }
            },
            {
                'name': 'llama3.1-8b-instruct',
                'model_id': 'meta-llama/Meta-Llama-3.1-8B-Instruct',
                'model_type': 'llama3_1',
                'template': 'llama3_2',
                'description': 'Llama 3.1 8B Instruct - Meta\'s instruction-tuned model',
                'tags': ['chat', 'instruct'],
                'swift_args': {
                    'max_length': 8192
                }
            },
            {
                'name': 'mistral-7b-instruct',
                'model_id': 'mistralai/Mistral-7B-Instruct-v0.3',
                'model_type': 'mistral',
                'template': 'llama',
                'description': 'Mistral 7B Instruct - Efficient instruction model',
                'tags': ['chat', 'instruct'],
                'swift_args': {
                    'max_length': 4096
                }
            },
            {
                'name': 'deepseek-coder-6.7b',
                'model_id': 'deepseek-ai/deepseek-coder-6.7b-instruct',
                'model_type': 'deepseek',
                'template': 'deepseek',
                'description': 'DeepSeek Coder 6.7B - Code generation model',
                'tags': ['coding', 'instruct'],
                'swift_args': {
                    'max_length': 4096
                }
            }
        ]
        
        # Save each model config
        for model_data in default_models:
            config_file = models_dir / f"{model_data['name']}.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(model_data, f, default_flow_style=False)
        
        self.logger.info(f"Created {len(default_models)} default model configurations")