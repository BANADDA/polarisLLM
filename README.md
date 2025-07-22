# PolarisLLM Runtime Engine

A high-performance multi-model LLM runtime engine built with Python and ms-swift, providing OpenAI-compatible APIs for running multiple language models concurrently.

## 🚀 Features

- **Multi-Model Serving**: Load and serve multiple LLM models simultaneously
- **OpenAI Compatible**: Drop-in replacement for OpenAI Chat Completions API
- **Dynamic Model Management**: Load/unload models on demand via API or CLI
- **Built on ms-swift**: Leverages the robust ms-swift framework for model deployment
- **Resource Monitoring**: Real-time monitoring of model resource usage
- **Health Checks**: Automatic health monitoring and recovery
- **Easy Configuration**: YAML-based model and runtime configuration
- **CLI Management**: Rich CLI interface for model and runtime management
- **Docker Support**: Containerized deployment with docker-compose

## 📦 Installation

### Option 1: Local Installation

```bash
git clone <repository-url>
cd polarisLLM

# Install dependencies
pip install -r requirements.txt

# Install ms-swift
pip install ms-swift[llm] --upgrade
```

### Option 2: Docker Installation

```bash
git clone <repository-url>
cd polarisLLM

# Build and run with Docker
docker-compose up -d
```

## 🎯 Quick Start

### 1. Start the Runtime Engine

```bash
# Local
python main.py

# Docker
docker-compose up -d polaris-runtime
```

The server will start on `http://localhost:7860`

### 2. Load a Model

```bash
# Using CLI
python cli.py load deepseek-vl-7b-chat

# Using API
curl -X POST "http://localhost:7860/admin/models/load" \
  -H "Content-Type: application/json" \
  -d '{"model_name": "deepseek-vl-7b-chat"}'
```

### 3. Chat with the Model

```bash
# Using curl
curl -X POST "http://localhost:7860/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-vl-7b-chat",
    "messages": [
      {"role": "user", "content": "Hello! How are you?"}
    ]
  }'
```

## 🛠️ CLI Usage

The CLI provides convenient model management:

```bash
# Check runtime status
python cli.py status

# List available models
python cli.py list

# List running models
python cli.py list --running

# Load a model with custom arguments
python cli.py load qwen2.5-7b-instruct --swift-args max_length=4096

# Unload a model
python cli.py unload qwen2.5-7b-instruct

# Get model information
python cli.py info deepseek-vl-7b-chat
```

## 📚 Supported Models

PolarisLLM supports all models available in ms-swift. Default configurations include:

- **deepseek-vl-7b-chat**: Vision-language model for image and text
- **qwen2.5-7b-instruct**: General purpose chat model
- **llama3.1-8b-instruct**: Meta's instruction-tuned model
- **mistral-7b-instruct**: Efficient instruction model
- **deepseek-coder-6.7b**: Code generation model

## 🔧 Configuration

### Runtime Configuration (`config/runtime.yaml`)

```yaml
host: "0.0.0.0"
port_range_start: 8000
port_range_end: 8100
max_concurrent_models: 5
model_timeout: 300
env_vars:
  CUDA_VISIBLE_DEVICES: "0"
  HF_HUB_CACHE: "./cache/huggingface"
```

### Model Configuration (`config/models/*.yaml`)

```yaml
name: "custom-model"
model_id: "path/to/model"
model_type: "qwen2_5"
template: "qwen2_5"
description: "Custom model description"
tags: ["chat", "custom"]
swift_args:
  max_length: 8192
  temperature: 0.7
```

## 🌐 API Endpoints

### OpenAI Compatible Endpoints

- `POST /v1/chat/completions` - Create chat completion
- `GET /v1/models` - List available models

### Admin Endpoints

- `POST /admin/models/load` - Load a model
- `POST /admin/models/{model_name}/unload` - Unload a model
- `GET /admin/models/{model_name}/status` - Get model status
- `GET /admin/status` - Get runtime status
- `GET /admin/models/available` - List available model configurations
- `GET /admin/models/running` - List running models

### Utility Endpoints

- `GET /health` - Health check
- `GET /` - API information

## 🐳 Docker Deployment

### Basic Deployment

```bash
docker-compose up -d
```

### With GPU Support

1. Install nvidia-docker2
2. Uncomment GPU section in docker-compose.yml
3. Start with GPU access:

```bash
docker-compose up -d
```

### With Redis Cache

```bash
docker-compose --profile with-cache up -d
```

## 📊 Monitoring

### Health Checks

The runtime includes built-in health monitoring:

```bash
curl http://localhost:7860/health
```

### Resource Monitoring

View real-time resource usage:

```bash
python cli.py status
```

### Logs

```bash
# Local logs
tail -f polaris.log

# Docker logs
docker-compose logs -f polaris-runtime
```

## 🔌 Integration Examples

### Python Client

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:7860/v1",
    api_key="not-required"
)

response = client.chat.completions.create(
    model="deepseek-vl-7b-chat",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### JavaScript Client

```javascript
import OpenAI from 'openai';

const client = new OpenAI({
    baseURL: 'http://localhost:7860/v1',
    apiKey: 'not-required'
});

const completion = await client.chat.completions.create({
    model: 'qwen2.5-7b-instruct',
    messages: [
        { role: 'user', content: 'Hello!' }
    ]
});

console.log(completion.choices[0].message.content);
```

## 🛡️ Production Considerations

1. **Resource Management**: Monitor GPU/CPU usage and memory consumption
2. **Load Balancing**: Use reverse proxy for multiple runtime instances
3. **Security**: Add authentication for admin endpoints
4. **Logging**: Configure structured logging for production monitoring
5. **Scaling**: Use Kubernetes for large-scale deployments

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- Documentation: See inline code documentation
- Issues: Submit issues via GitHub
- Community: Join our Discord/Slack community

## 🔄 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Client    │    │   FastAPI Server │    │  Runtime Core   │
│                 │────│                  │────│                 │
│ - Model Mgmt    │    │ - OpenAI API     │    │ - Model Manager │
│ - Status Check  │    │ - Admin API      │    │ - Process Mgmt  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                │                        │
                       ┌────────▼────────┐    ┌─────────▼─────────┐
                       │  Model Instance │    │  Model Instance   │
                       │                 │    │                   │
                       │ - ms-swift      │    │ - ms-swift        │
                       │ - Port 8000     │    │ - Port 8001       │
                       └─────────────────┘    └───────────────────┘
```

## 🎉 Acknowledgments

- Built on the excellent [ms-swift](https://github.com/modelscope/swift) framework
- Inspired by OpenAI's API design
- Thanks to the open-source LLM community