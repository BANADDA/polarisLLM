# 🚀 PolarisLLM Deployment Guide

<div align="center">

![PolarisLLM](https://img.shields.io/badge/PolarisLLM-Deployment-blue?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![GPU](https://img.shields.io/badge/GPU-Required-red?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-yellow?style=for-the-badge)

**A comprehensive deployment platform for Large Language Models with public API access**
*Currently featuring DeepSeek-VL-7B-Chat as the first deployment template*

[🔧 Quick Start](#-quick-start) • [📖 Full Guide](#-installation-guide) • [🌐 Public Access](#-public-access-with-cloudflare-tunnel) • [🧪 Testing](#-testing-the-api) • [🔧 Troubleshooting](#-troubleshooting)

</div>

---

## 🌟 Features

- ✅ **Automated Setup**: One-command deployment with dependency management
- ✅ **GPU Optimized**: Automatic GPU detection and optimization
- ✅ **Public API**: Ready-to-use REST API endpoints
- ✅ **Cloudflare Integration**: Instant public URL generation
- ✅ **Process Management**: Built-in start/stop/monitor capabilities
- ✅ **Multi-Model Support**: Template-based deployment for various LLMs
- ✅ **Vision Support**: Text + Image understanding capabilities (model-dependent)
- ✅ **Production Ready**: Logging, monitoring, and error handling

## 🎯 About PolarisLLM

**PolarisLLM** is a template-based deployment platform for Large Language Models that provides:

- 🔧 **Standardized Deployment**: Consistent deployment patterns across different models
- 🚀 **Rapid Prototyping**: One-command deployment for quick experimentation
- 🌐 **Public API Access**: Built-in tunneling for instant public availability
- 📋 **Template System**: Reusable deployment scripts for various model architectures

**Current Templates:**
- ✅ `deploy_deepseek_vl2.sh` - DeepSeek-VL-7B-Chat (Vision + Text)

**Coming Soon:**
- 🔄 `deploy_llama3.sh` - Llama 3 models
- 🔄 `deploy_mistral.sh` - Mistral models
- 🔄 `deploy_qwen.sh` - Qwen models

## 🎯 Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/BANADDA/polarisLLM.git
cd polarisLLM

# 2. Deploy your chosen model (DeepSeek-VL-7B-Chat example)
./deploy_deepseek_vl2.sh

# 3. Test the API
curl -X POST http://localhost:9089/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-vl-7b-chat", "messages": [{"role": "user", "content": "Hello!"}], "max_tokens": 100}'
```

> **Note**: This guide uses DeepSeek-VL-7B-Chat as the reference implementation. More model templates will be added to the PolarisLLM platform.

## 📋 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **GPU**: NVIDIA GPU with CUDA support (RTX 4090 recommended)
- **RAM**: 16GB+ system RAM
- **Storage**: 50GB+ free space
- **Python**: 3.8 or higher

### Software Dependencies
- NVIDIA drivers (latest)
- CUDA toolkit
- Python 3.8+
- pip package manager

### Hardware Verification
```bash
# Check GPU availability
nvidia-smi

# Check Python version
python --version

# Check available space
df -h
```

---

## 🔧 Installation Guide

### Step 1: Environment Setup
```bash
# Create deployment directory
mkdir -p ~/llm-deployment-server
cd ~/llm-deployment-server

# Download deployment script (DeepSeek-VL-7B-Chat template)
curl -O https://raw.githubusercontent.com/BANADDA/polarisLLM/main/deploy_deepseek_vl2.sh
chmod +x deploy_deepseek_vl2.sh
```

### Step 2: Run Full Deployment
```bash
# Deploy everything (takes 10-30 minutes)
./deploy_deepseek_vl2.sh
```

> **PolarisLLM Templates**: Each model has its own deployment script following the same pattern. Future templates will include `deploy_llama3.sh`, `deploy_mistral.sh`, etc.

### Step 3: Monitor Deployment
```bash
# Check deployment status
./deploy_deepseek_vl2.sh status

# View live logs
./deploy_deepseek_vl2.sh logs

# System diagnostics
./deploy_deepseek_vl2.sh doctor
```

---

## 🧪 Testing the API

> **Note**: All PolarisLLM deployments use the same OpenAI-compatible API format. Only the model name changes between different deployments.

### Basic Text Chat
```bash
curl -X POST http://localhost:9089/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-vl-7b-chat",
    "messages": [
      {"role": "user", "content": "Explain quantum computing in simple terms"}
    ],
    "max_tokens": 150
  }'
```

**Expected Response:**
```json
{
  "model": "deepseek-vl-7b-chat",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Quantum computing is like having a super-powerful computer that can solve certain problems much faster than regular computers. Instead of using bits (0s and 1s), quantum computers use quantum bits or 'qubits' that can be both 0 and 1 at the same time. This allows them to explore many possible solutions simultaneously, making them excellent for complex calculations like code-breaking, drug discovery, and optimization problems.",
        "tool_calls": null
      },
      "finish_reason": "stop",
      "logprobs": null
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 95,
    "total_tokens": 107
  },
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1752767890
}
```

### Vision + Text (Image Analysis)
> **Note**: This feature is available for vision-capable models like DeepSeek-VL. Text-only models in PolarisLLM won't support image inputs.

```bash
curl -X POST http://localhost:9089/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-vl-7b-chat",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "What do you see in this image?"},
          {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
        ]
      }
    ],
    "max_tokens": 200
  }'
```

### Streaming Response
```bash
curl -X POST http://localhost:9089/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-vl-7b-chat",
    "messages": [{"role": "user", "content": "Write a short poem about technology"}],
    "max_tokens": 100,
    "stream": true
  }'
```

---

## 🌐 Public Access with Cloudflare Tunnel

### One-Time Setup
```bash
# 1. Install Cloudflare Tunnel
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# 2. Set your API token (get from Cloudflare dashboard)
export CLOUDFLARE_API_TOKEN="your_token_here"
```

### Create Public URL
```bash
# Create instant public URL
cloudflared tunnel --url http://localhost:9089
```

**Output Example:**
```
+--------------------------------------------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
|  https://amazing-example-tunnel.trycloudflare.com                                         |
+--------------------------------------------------------------------------------------------+
```

### Background Tunnel (Production)
```bash
# Start tunnel in background
nohup cloudflared tunnel --url http://localhost:9089 > tunnel.log 2>&1 &

# Save process ID
echo $! > tunnel.pid

# Stop tunnel later
kill $(cat tunnel.pid)
```

### Test Public API
```bash
# Test your public endpoint
curl -X POST https://your-tunnel-url.trycloudflare.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-vl-7b-chat", "messages": [{"role": "user", "content": "Hello from public API!"}], "max_tokens": 50}'
```

---

## 🎛️ Management Commands

### Deployment Control
```bash
# Start deployment
./deploy_deepseek_vl2.sh

# Check status
./deploy_deepseek_vl2.sh status

# Stop deployment
./deploy_deepseek_vl2.sh stop

# View logs
./deploy_deepseek_vl2.sh logs

# System check
./deploy_deepseek_vl2.sh doctor

# Help
./deploy_deepseek_vl2.sh help
```

### Individual Steps
```bash
# Setup environment only
./deploy_deepseek_vl2.sh setup_environment

# Install dependencies only
./deploy_deepseek_vl2.sh install_dependencies

# Deploy model only
./deploy_deepseek_vl2.sh deploy_model
```

---

## 🔧 Troubleshooting

### Common Issues

#### ❌ GPU Not Detected
```bash
# Check NVIDIA drivers
nvidia-smi

# If not found, install drivers
sudo apt update
sudo apt install nvidia-driver-XXX  # Replace XXX with latest version
```

#### ❌ Port Already in Use
```bash
# Check what's using port 9089
sudo netstat -tulpn | grep 9089

# Stop conflicting process
sudo kill -9 <PID>
```

#### ❌ Virtual Environment Issues
```bash
# Remove and recreate
rm -rf ~/llm-deployment-server/llm_venv
./deploy_deepseek_vl2.sh setup_environment
```

#### ❌ Model Download Fails
```bash
# Check internet connectivity
ping google.com

# Check available disk space
df -h

# Retry deployment
./deploy_deepseek_vl2.sh deploy_model
```

#### ❌ Tunnel Not Working
```bash
# Check firewall
sudo ufw status

# Test local API first
curl http://localhost:9089/v1/models

# Restart tunnel
pkill cloudflared
cloudflared tunnel --url http://localhost:9089
```

### Log Files
```bash
# Deployment logs
tail -f ~/llm-deployment-server/deepseek-vl-7b/deploy.log

# Tunnel logs
tail -f tunnel.log

# System logs
journalctl -u deepseek-model
```

---

## 📊 Performance Optimization

### GPU Memory Management
```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# Set specific GPU
export CUDA_VISIBLE_DEVICES=0
./deploy_deepseek_vl2.sh deploy_model
```

### API Rate Limiting
```bash
# Add nginx proxy for rate limiting (optional)
sudo apt install nginx
# Configure proxy settings as needed
```

---

## 🔒 Security Considerations

### Firewall Setup
```bash
# Allow only necessary ports
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 9089  # API (if direct access needed)
```

### API Security
- Always use HTTPS in production
- Implement authentication for public APIs
- Monitor API usage and set rate limits
- Keep system and dependencies updated

---

## 📚 API Reference

### Endpoints
- `POST /v1/chat/completions` - Chat completions
- `GET /v1/models` - List available models
- `POST /v1/completions` - Text completions (legacy)

### Parameters
- `model`: Model name (varies by deployment: "deepseek-vl-7b-chat", "llama3-8b", etc.)
- `messages`: Array of message objects
- `max_tokens`: Maximum response length
- `temperature`: Response randomness (0.0-1.0)
- `stream`: Enable streaming responses

> **PolarisLLM Standard**: All deployments follow OpenAI-compatible API format for consistency.

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Model Providers** (DeepSeek AI, Meta AI, Mistral AI, etc.) for their excellent open-source models
- **Cloudflare** for the excellent tunnel service
- **ms-swift** and other deployment frameworks for making LLM deployment accessible
- **Community contributors** for testing and feedback on PolarisLLM templates

---

<div align="center">

**Made with ❤️ by the PolarisLLM Team**

[⭐ Star this repo](https://github.com/BANADDA/polarisLLM) • [🐛 Report Bug](https://github.com/BANADDA/polarisLLM/issues) • [💡 Request Feature](https://github.com/BANADDA/polarisLLM/issues)

</div>
