# 🌟 PolarisLLM Runtime Engine

**The Ultimate Multi-Model LLM Runtime Platform**

PolarisLLM is a production-ready, high-performance runtime engine that transforms how you deploy and serve Large Language Models. Built on the robust ms-swift framework, it provides seamless OpenAI-compatible APIs while enabling dynamic multi-model serving, making it the perfect solution for developers, researchers, and enterprises who need flexible, scalable LLM infrastructure.

## 🎯 **Why PolarisLLM?**

**🚀 Turn Any Server Into an LLM Powerhouse**
- Deploy multiple models simultaneously on a single machine
- Switch between models without restarts or downtime
- Support for 300+ models including Qwen, Llama, DeepSeek, Mistral, and more

**⚡ Production-Ready Performance**
- Built on battle-tested ms-swift framework
- Automatic resource management and optimization
- Real-time health monitoring and auto-recovery

**🔌 Drop-in OpenAI Compatibility**
- Use existing OpenAI client libraries without modification
- Seamless integration with popular frameworks like LangChain, LlamaIndex
- Perfect for migration from proprietary APIs to self-hosted solutions

## ✨ **Key Features**

### 🎛️ **Dynamic Model Management**
- **Hot-swap models** without server restarts
- **Concurrent serving** of multiple models on different ports
- **Intelligent resource allocation** and memory management
- **Auto-scaling** based on demand

### 🔗 **Universal Compatibility**
- **OpenAI API compatible** - works with existing tools and libraries
- **300+ supported models** from HuggingFace and ModelScope
- **Multi-modal support** - text, vision, code, and audio models
- **Streaming responses** for real-time applications

### 🛠️ **Developer Experience**
- **Rich CLI interface** with beautiful status displays
- **RESTful admin APIs** for programmatic control
- **YAML configuration** for easy model definitions
- **Comprehensive logging** and error handling

### 🏗️ **Production Ready**
- **Docker containerization** with GPU support
- **Health checks** and automatic recovery
- **Resource monitoring** and performance metrics
- **Horizontal scaling** support

## 📦 **Installation**

### 🎉 **Quick Install (Recommended)**
```bash
# Install from PyPI - that's it!
pip install polarisllm

# Start the engine
polaris start
```

### 🐳 **Docker Installation**
```bash
# Run with Docker
docker run -p 7860:7860 polarisllm/polarisllm

# Or with docker-compose
git clone https://github.com/polarisllm/polarisLLM.git
cd polarisLLM
docker-compose up -d
```

### 🛠️ **Development Installation**
```bash
git clone https://github.com/polarisllm/polarisLLM.git
cd polarisLLM
pip install -e .
pip install ms-swift[llm] --upgrade
```

## 🚀 **Quick Start Guide**

### **Step 1: Install & Start** ⚡
```bash
# Install PolarisLLM (includes ms-swift dependency)
pip install polarisllm

# Start the runtime engine
polarisllm
```
*Server starts on `http://localhost:7860` with beautiful web interface*

### **Step 2: Verify Installation** ✅
```bash
# Check if server is running
curl http://localhost:7860/health

# View available models
curl http://localhost:7860/v1/models

# Open API documentation
# Visit: http://localhost:7860/docs
```

### **Step 3: Load and Use Models** 🤖
```bash
# First, load a model using ms-swift (use python -m swift if swift command not in PATH)
swift deploy --model_type qwen2_5 --model_id Qwen/Qwen2.5-7B-Instruct
# OR: python -m swift deploy --model_type qwen2_5 --model_id Qwen/Qwen2.5-7B-Instruct

# Then use with OpenAI-compatible API
curl -X POST "http://localhost:7860/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-7b-instruct", 
    "messages": [{"role": "user", "content": "Hello! How are you?"}]
  }'
```

### **Step 4: Use with Your Favorite Tools** 🔧
```python
# Works with OpenAI Python client
import openai

client = openai.OpenAI(
    base_url="http://localhost:7860/v1",
    api_key="not-required"  # No API key needed!
)

response = client.chat.completions.create(
    model="qwen2.5-7b-instruct",
    messages=[{"role": "user", "content": "Write a Python function to sort a list"}]
)
print(response.choices[0].message.content)
```

## 🎮 **Real-World Examples**

### **Example 1: Multi-Model AI Assistant**
```bash
# Load different specialized models
polaris load qwen2.5-7b-instruct      # General chat
polaris load deepseek-coder-6.7b      # Code generation  
polaris load deepseek-vl-7b-chat      # Vision understanding

# Use different models for different tasks
curl -X POST "http://localhost:7860/v1/chat/completions" \
  -d '{"model": "deepseek-coder-6.7b", "messages": [{"role": "user", "content": "Write a REST API in FastAPI"}]}'
```

### **Example 2: LangChain Integration**
```python
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Connect to your local PolarisLLM
llm = OpenAI(
    openai_api_base="http://localhost:7860/v1",
    openai_api_key="not-required",
    model_name="qwen2.5-7b-instruct"
)

# Use with LangChain as usual
prompt = PromptTemplate(template="Explain {topic} in simple terms")
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(topic="machine learning")
```

### **Example 3: Batch Processing**
```python
import asyncio
import aiohttp

async def process_documents():
    models = ["qwen2.5-7b-instruct", "deepseek-coder-6.7b"]
    
    for model in models:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:7860/v1/chat/completions",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Analyze this document..."}]
                }
            ) as response:
                result = await response.json()
                print(f"{model}: {result}")
```

## 🛠️ **Available Commands**

### **Server Commands**
```bash
# Start the runtime engine (main command)
polarisllm

# Alternative start commands
polaris-llm
polaris-server

# Start with custom options
polarisllm --host 0.0.0.0 --port 8080

# View help
polarisllm --help
```

### **Model Management (via ms-swift)**
```bash
# List available models
swift list-models
# OR: python -m swift list-models

# Deploy a chat model
swift deploy --model_type qwen2_5 --model_id Qwen/Qwen2.5-7B-Instruct
# OR: python -m swift deploy --model_type qwen2_5 --model_id Qwen/Qwen2.5-7B-Instruct

# Deploy a vision model  
swift deploy --model_type deepseek_vl --model_id deepseek-ai/deepseek-vl-7b-chat

# Deploy a code model
swift deploy --model_type deepseek --model_id deepseek-ai/deepseek-coder-6.7b-instruct

# Check deployment status
swift list
# OR: python -m swift list
```

## 🤖 **Supported Models (300+)**

PolarisLLM supports the entire ms-swift model ecosystem. Here are some popular choices:

### **🎯 General Chat Models**
- **Qwen2.5-7B-Instruct**: Alibaba's flagship model - excellent for general tasks
- **Llama-3.1-8B-Instruct**: Meta's latest - great reasoning capabilities  
- **Mistral-7B-Instruct**: Efficient and fast - perfect for production
- **DeepSeek-V2.5**: Advanced reasoning and long context support

### **💻 Code Generation Models** 
- **DeepSeek-Coder-6.7B**: State-of-the-art code generation
- **CodeQwen1.5-7B**: Multi-language programming support
- **Qwen2.5-Coder-7B**: Latest coding model with enhanced capabilities

### **👁️ Vision-Language Models**
- **DeepSeek-VL-7B-Chat**: Advanced vision understanding
- **Qwen2-VL-7B-Instruct**: Multi-modal reasoning 
- **LLaVA-NeXT**: Image analysis and description

### **🎵 Multi-Modal Models**
- **Qwen2-Audio**: Speech and audio understanding
- **Qwen2.5-Omni**: Text, image, and audio in one model

*See the complete list of 300+ supported models in our [Model Catalog](https://github.com/polarisllm/models)*

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

## 🌟 **Use Cases**

### **🏢 Enterprise & Startups**
- **Private AI Infrastructure**: Keep models in-house for data privacy
- **Cost Optimization**: Reduce API costs by 90% compared to cloud providers
- **Multi-tenant Applications**: Serve different models to different customers
- **A/B Testing**: Compare model performance with easy switching

### **👨‍💻 Developers & Researchers**
- **Local Development**: Test AI features without API costs
- **Model Comparison**: Evaluate different models on the same dataset
- **Fine-tuning Pipeline**: Deploy custom fine-tuned models
- **Prototype Rapidly**: Build AI applications with zero setup friction

### **📚 Educational & Training**
- **AI Courses**: Provide students with hands-on LLM experience
- **Research Projects**: Access to latest models for academic research
- **Hackathons**: Quick setup for AI-focused competitions

## 🏆 **Why Choose PolarisLLM Over Alternatives?**

| Feature | PolarisLLM | Ollama | text-generation-webui | OpenAI API |
|---------|------------|---------|----------------------|------------|
| **Multi-model serving** | ✅ Concurrent | ⚠️ Sequential | ❌ Single | ✅ Multiple |
| **OpenAI compatibility** | ✅ Full | ❌ Limited | ❌ None | ✅ Native |
| **Model variety** | ✅ 300+ models | ⚠️ GGUF only | ⚠️ Limited | ⚠️ Proprietary |
| **Production ready** | ✅ Yes | ⚠️ Basic | ❌ No | ✅ Yes |
| **Self-hosted** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **Cost** | ✅ Free | ✅ Free | ✅ Free | 💰 Expensive |
| **Setup time** | ✅ < 2 minutes | ⚠️ 5-10 min | ❌ 30+ min | ✅ Instant |

## 🤝 **Community & Support**

### **Getting Help**
- 📖 **Documentation**: Comprehensive guides and API reference
- 💬 **GitHub Discussions**: Community Q&A and feature requests  
- 🐛 **Issue Tracking**: Bug reports and feature requests
- 📧 **Email Support**: contact@polarisllm.dev

### **Contributing**
- 🍴 **Fork & PR**: Contributions welcome!
- 🧪 **Testing**: Help test new models and features
- 📝 **Documentation**: Improve guides and examples
- 🌍 **Translation**: Help localize for global users

### **Stay Updated**
- ⭐ **Star us on GitHub**: Get notifications for releases
- 🐦 **Follow @PolarisLLM**: Latest updates and tips
- 📰 **Newsletter**: Monthly model updates and tutorials

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