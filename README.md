# 🌟 PolarisLLM - AI Model Orchestration Platform

**Deploy and manage 300+ AI models with simple commands**

Transform your server into a powerful AI platform. Deploy models in the background, manage them with ease, and access everything through OpenAI-compatible APIs.

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://pypi.org/project/polarisllm/)
[![Python](https://img.shields.io/badge/python-3.8+-brightgreen.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## ✨ What You Get

🚀 **Background Model Deployment** - Models run automatically in the background  
🎛️ **Simple Management** - Start, stop, and monitor with easy commands  
📊 **Real-time Monitoring** - See status, memory usage, and live logs  
🔌 **OpenAI Compatible** - Works with existing OpenAI code  
🌐 **300+ Models** - Qwen, Llama, DeepSeek, Mistral, and more  

---

## 🚀 Get Started

### Install
```bash
pip install polarisllm --upgrade
```

### Start Server
```bash
polarisllm start --daemon
```
```
🌟 PolarisLLM Runtime Engine
==================================================
🚀 Starting PolarisLLM server in daemon mode...
   Host: 0.0.0.0
   Port: 7860
   Log File: /home/user/.polarisllm/logs/server.log

✅ Server started successfully!
   PID: 12345
   URL: http://0.0.0.0:7860

💡 Commands:
   polarisllm status              # Check server status
   polarisllm logs --server       # View server logs
   polarisllm stop --server       # Stop server
```

### Deploy Your First Model
```bash
polarisllm deploy --model qwen2.5-7b-instruct
```
```
🚀 Deploying model: qwen2.5-7b-instruct
📋 Using convenience shortcut for qwen2.5-7b-instruct
   Model Type: qwen2_5
   Model ID: Qwen/Qwen2.5-7B-Instruct

📡 Allocated port: 8000
🔧 Command: swift deploy --model_type qwen2_5 --model Qwen/Qwen2.5-7B-Instruct --port 8000 --host 0.0.0.0
📝 Logs: /home/user/.polarisllm/logs/qwen2.5-7b-instruct.log

🚀 Starting deployment in background...
✅ Started process 12346 for qwen2.5-7b-instruct
✅ Model deployment started successfully!
   Name: qwen2.5-7b-instruct
   PID: 12346
   Port: 8000
   Status: Initializing...

🔍 Monitor with: polarisllm logs qwen2.5-7b-instruct --follow
📊 Check status: polarisllm status
🌐 Access via: http://localhost:7860/v1/chat/completions
```

### Check What's Running
```bash
polarisllm list
```
```
📋 Deployed Models
========================================================================
NAME                    STATUS      PORT    MEMORY   UPTIME    TYPE
qwen2.5-7b-instruct     🟢 Running  8000    15.2%    2.5h      qwen2_5

📊 Summary:
   Total Models: 1
   Running: 1
   Stopped: 0

💡 Commands:
   polarisllm logs qwen2.5-7b-instruct --follow  # View live logs
   polarisllm stop qwen2.5-7b-instruct           # Stop a model
   polarisllm status                              # Detailed status
```

---

## 🎮 Common Commands

### Deploy Models
```bash
# Popular models (shortcuts available)
polarisllm deploy --model qwen2.5-7b-instruct
polarisllm deploy --model deepseek-coder-6.7b
polarisllm deploy --model mistral-7b-instruct

# Any model with full name
polarisllm deploy --model my-llama \
  --model-type llama3_1 \
  --model-id meta-llama/Meta-Llama-3.1-8B-Instruct
```

**Sample deployment output:**
```
🚀 Deploying model: deepseek-coder-6.7b
📋 Using convenience shortcut for deepseek-coder-6.7b
   Model Type: deepseek
   Model ID: deepseek-ai/deepseek-coder-6.7b-instruct

📡 Allocated port: 8001
🚀 Starting deployment in background...
✅ Model deployed successfully on port 8001!
```

### Manage Your Models
```bash
polarisllm list                    # See all models
polarisllm status                  # System overview
polarisllm stop qwen2.5-7b-instruct    # Stop a model
polarisllm undeploy qwen2.5-7b-instruct # Remove completely
```

**Status output:**
```bash
$ polarisllm status
📊 PolarisLLM System Status
============================================================
🖥️  Server Status:
   Status: 🟢 Running (PID: 12345)
   Memory: 2.1%
   CPU: 0.5%
   API: 🟢 Healthy
   URL: http://localhost:7860

🤖 Models Status:
   Total Models: 2
   Running: 2 🟢
   Stopped: 0 🔴
   Detailed Status:
     qwen2.5-7b-instruct: 🟢 running
       Port: 8000, Memory: 15.2%, Uptime: 2.5h
     deepseek-coder-6.7b: 🟢 running
       Port: 8001, Memory: 12.8%, Uptime: 1.2h

💾 Resource Status:
   Ports: 2/100 used (98 available)
   Range: 8000-8100
   Total Memory: 28.0% (all models combined)

💡 Quick Commands:
   polarisllm deploy --model <name>     # Deploy a model
   polarisllm list                      # List all models
   polarisllm logs <model> --follow     # View live logs
   polarisllm stop <model>              # Stop a model
   polarisllm start --daemon            # Start server in background
```

### Watch Logs
```bash
polarisllm logs qwen2.5-7b-instruct --follow    # Live logs
polarisllm logs --server --follow               # Server logs
```

**Sample log output:**
```
📝 Logs for model: qwen2.5-7b-instruct
   Lines: 100
   Follow: Yes
============================================================
🔄 Streaming logs (Press Ctrl+C to stop)...

[INFO:swift] Successfully registered model
[INFO:swift] rank: -1, local_rank: -1, world_size: 1
[INFO:swift] Loading the model using model_dir: /cache/Qwen2___5-7B-Instruct
[INFO:swift] Loading model weights...
[INFO:swift] Model loaded successfully
[INFO:swift] Server started on http://0.0.0.0:8000
[INFO:swift] Waiting for requests...
```

### Server Control
```bash
polarisllm start --daemon     # Start in background
polarisllm stop --server      # Stop server
polarisllm restart           # Restart everything
```

---

## 🤖 Available Models

**Popular Shortcuts:**
- `qwen2.5-7b-instruct` - Great all-around chat model
- `qwen2.5-14b-instruct` - Larger version for better responses
- `deepseek-coder-6.7b` - Excellent for programming
- `deepseek-vl-7b-chat` - Understands images and text
- `mistral-7b-instruct` - Fast and efficient
- `llama3.1-8b-instruct` - Meta's latest model

**Categories:**
- **Chat**: General conversation and Q&A
- **Code**: Programming and development help  
- **Vision**: Image understanding and analysis
- **Audio**: Speech and sound processing

*See all 300+ models: `python -m swift list-models`*

---

## 🔌 Use with Your Code

### Python
```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:7860/v1",
    api_key="not-required"
)

response = client.chat.completions.create(
    model="qwen2.5-7b-instruct",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

**Sample response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "qwen2.5-7b-instruct",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! I'm an AI assistant powered by PolarisLLM. How can I help you today?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 9,
    "completion_tokens": 20,
    "total_tokens": 29
  }
}
```

### JavaScript
```javascript
import OpenAI from 'openai';

const client = new OpenAI({
    baseURL: 'http://localhost:7860/v1',
    apiKey: 'not-required'
});

const completion = await client.chat.completions.create({
    model: 'qwen2.5-7b-instruct',
    messages: [{ role: 'user', content: 'Hello!' }]
});
```

### cURL
```bash
curl -X POST "http://localhost:7860/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-7b-instruct",
    "messages": [{"role": "user", "content": "Write a Python function to add two numbers"}]
  }'
```

**Sample cURL response:**
```json
{
  "id": "chatcmpl-456",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "qwen2.5-7b-instruct",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Here's a simple Python function to add two numbers:\n\n```python\ndef add_numbers(a, b):\n    return a + b\n\n# Example usage\nresult = add_numbers(5, 3)\nprint(result)  # Output: 8\n```"
    },
    "finish_reason": "stop"
  }]
}
```

---

## 📊 See What's Running

```bash
$ polarisllm list
📋 Deployed Models
========================================================================
NAME                    STATUS      PORT    MEMORY   UPTIME    TYPE
qwen2.5-7b-instruct     🟢 Running  8000    15.2%    2.5h      qwen2_5
deepseek-coder-6.7b     🟢 Running  8001    12.8%    1.2h      deepseek
mistral-7b-instruct     🔴 Stopped  8002    N/A      N/A       mistral
```

```bash
$ polarisllm status
📊 System Status
===========================================
🖥️  Server: 🟢 Running at http://localhost:7860
🤖 Models: 2 running, 1 stopped
💾 Resources: 2/100 ports used, 28% memory
```

---

## 🚫 Fix Common Issues

**Model won't start?**
```bash
polarisllm logs <model-name>    # Check what went wrong
polarisllm cleanup              # Clean up any stuck processes
```

**Sample error log:**
```
📝 Logs for model: qwen2.5-7b-instruct
============================================================
[ERROR:swift] CUDA out of memory. Tried to allocate 2.0 GiB
[INFO:swift] Try reducing batch size or using a smaller model
[ERROR:swift] Model loading failed
```

**Server not working?**
```bash
polarisllm status               # See what's happening
polarisllm restart              # Restart everything
```

**Need to free up space?**
```bash
polarisllm stop --all           # Stop all models
polarisllm cleanup              # Clean up old processes
```

**Sample cleanup output:**
```
🧹 Cleaning up PolarisLLM...
========================================
🔍 Cleaning up dead processes...
🔍 Cleaning up dead models...
🔍 Cleaning up port allocations...
Cleaned up 2 dead port allocations
🔍 Cleaning up old logs...
Cleaned up 3 old log files

✅ Cleanup completed!
💡 Use 'polarisllm status' to verify system state
```

---

## 💡 Pro Tips

- Models run in background automatically - they survive terminal restarts
- Use `--follow` with logs to watch models start up in real-time
- Each model gets its own port (8000, 8001, 8002...)
- Server remembers your models even after restarts
- Use shortcuts for popular models, full names for everything else

---

## 🤝 Need Help?

- **GitHub Issues**: [Report bugs or request features](https://github.com/polarisllm/polarisLLM/issues)
- **PyPI Package**: [Install from here](https://pypi.org/project/polarisllm/)

---

## 📄 License

MIT License - Free to use for any purpose