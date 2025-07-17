#!/bin/bash
set -e

# Configuration
MODEL_NAME="deepseek-vl-7b-chat"
MODEL_ID="deepseek-ai/deepseek-vl-7b-chat"
DEPLOYMENT_PORT=9089
DEPLOYMENT_HOST="0.0.0.0"
DEPLOYMENT_DIR="$HOME/llm-deployment-server"
VENV_DIR="$DEPLOYMENT_DIR/llm_venv"
MODEL_DIR="$DEPLOYMENT_DIR/deepseek-vl-7b"
LOG_FILE="$MODEL_DIR/deploy.log"

##############################
# Helper Functions
##############################

err_report() {
  echo "Error on line $1"
}

trap 'err_report $LINENO' ERR

abort() {
  printf "%s\n" "$@" >&2
  exit 1
}

if [[ -t 1 ]]
then
  tty_escape() { printf "\033[%sm" "$1"; }
else
  tty_escape() { :; }
fi
tty_mkbold() { tty_escape "1;$1"; }
tty_underline="$(tty_escape "4;39")"
tty_blue="$(tty_mkbold 34)"
tty_red="$(tty_mkbold 31)"
tty_green="$(tty_mkbold 32)"
tty_yellow="$(tty_mkbold 33)"
tty_bold="$(tty_mkbold 39)"
tty_reset="$(tty_escape 0)"

shell_join() {
  local arg
  printf "%s" "$1"
  shift
  for arg in "$@"
  do
    printf " "
    printf "%s" "${arg// /\ }"
  done
}

ohai() {
  printf "${tty_blue}==>${tty_bold} %s${tty_reset}\n" "$(shell_join "$@")"
}

warn() {
  printf "${tty_yellow}Warning${tty_reset}: %s\n" "$1" >&2
}

success() {
  printf "${tty_green}✅ %s${tty_reset}\n" "$1"
}

error() {
  printf "${tty_red}❌ %s${tty_reset}\n" "$1" >&2
}

title() {
  echo ""
  printf "%s#########################################################################%s\n" "${tty_blue}" "${tty_reset}"
  printf "${tty_blue}#### ${tty_bold} %s${tty_reset}\n" "$(shell_join "$@")"
  printf "%s#########################################################################%s\n" "${tty_blue}" "${tty_reset}"
}

##############################
# GPU Detection Functions
##############################

detect_gpu() {
  local gpu_count=0
  local gpu_devices=""
  
  if command -v nvidia-smi &> /dev/null; then
    gpu_count=$(nvidia-smi --query-gpu=count --format=csv,noheader,nounits | head -1)
    if [ "$gpu_count" -gt 0 ]; then
      success "Detected $gpu_count NVIDIA GPU(s)"
      nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader
      
      # Default to first GPU unless specified
      if [ -z "$CUDA_VISIBLE_DEVICES" ]; then
        export CUDA_VISIBLE_DEVICES=0
        ohai "Using GPU 0 (first GPU) by default"
      else
        ohai "Using GPU(s): $CUDA_VISIBLE_DEVICES"
      fi
    else
      error "NVIDIA drivers detected but no GPUs found"
      return 1
    fi
  else
    error "nvidia-smi not found. Please install NVIDIA drivers."
    return 1
  fi
}

##############################
# Step 1: Environment Setup
##############################

setup_environment() {
  title "Step 1: Environment Setup"
  echo "🌘 Step 1: START"

  # Create deployment directory
  mkdir -p "$DEPLOYMENT_DIR"
  mkdir -p "$MODEL_DIR"
  
  # Check if virtual environment exists
  if [ -d "$VENV_DIR" ]; then
    ohai "Virtual environment already exists at $VENV_DIR"
  else
    ohai "Creating virtual environment at $VENV_DIR"
    python -m venv "$VENV_DIR"
  fi

  # Activate virtual environment
  if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    success "Virtual environment activated"
  else
    abort "❌ Failed to create virtual environment"
  fi

  echo "🌕 Step 1: COMPLETE"
}

##############################
# Step 2: Install Dependencies
##############################

install_dependencies() {
  title "Step 2: Install Dependencies"
  echo "🌘 Step 2: START"

  # Ensure virtual environment is activated
  if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
  else
    abort "❌ Virtual environment not found. Run setup_environment first."
  fi

  ohai "Installing PyTorch and vision libraries..."
  echo "This may take several minutes depending on your internet connection..."
  pip install torch torchvision --progress-bar on --verbose

  ohai "Installing computer vision libraries..."
  echo "Installing timm for vision transformers..."
  pip install timm --progress-bar on --verbose

  ohai "Installing transformer libraries..."
  echo "Installing transformers (this is a large package)..."
  pip install transformers==4.36.2 --progress-bar on --verbose
  echo "Installing PEFT for parameter-efficient fine-tuning..."
  pip install peft==0.15.0 --progress-bar on --verbose

  ohai "Installing deployment framework..."
  echo "Installing ms-swift for model deployment..."
  pip install ms-swift --progress-bar on --verbose

  # Verify key installations
  if ! command -v swift &> /dev/null; then
    error "Swift deployment tool not found in PATH"
    return 1
  fi

  success "All dependencies installed successfully"
  echo "🌕 Step 2: COMPLETE"
}

##############################
# Step 3: Process Management
##############################

manage_existing_processes() {
  title "Step 3: Process Management"
  echo "🌘 Step 3: START"

  ohai "Checking for existing processes on port $DEPLOYMENT_PORT..."
  
  if netstat -tuln 2>/dev/null | grep ":$DEPLOYMENT_PORT" > /dev/null; then
    warn "Port $DEPLOYMENT_PORT is in use. Stopping existing processes..."
    
    if command -v fuser &> /dev/null; then
      fuser -k "$DEPLOYMENT_PORT/tcp" 2>/dev/null || true
    else
      # Alternative method using lsof
      if command -v lsof &> /dev/null; then
        local pids=$(lsof -ti:$DEPLOYMENT_PORT 2>/dev/null || true)
        if [ -n "$pids" ]; then
          echo "$pids" | xargs kill -9 2>/dev/null || true
        fi
      fi
    fi
    
    sleep 3
    success "Existing processes stopped"
  else
    success "Port $DEPLOYMENT_PORT is available"
  fi

  echo "🌕 Step 3: COMPLETE"
}

##############################
# Step 4: Model Deployment
##############################

deploy_model() {
  title "Step 4: Model Deployment"
  echo "🌘 Step 4: START"

  # Ensure virtual environment is activated
  if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
  else
    abort "❌ Virtual environment not found. Run setup_environment first."
  fi

  # Detect and setup GPU
  detect_gpu || abort "❌ GPU detection failed"

  ohai "Deploying $MODEL_NAME on GPU(s): $CUDA_VISIBLE_DEVICES"
  ohai "Model: $MODEL_ID"
  ohai "Port: $DEPLOYMENT_PORT"  
  ohai "Host: $DEPLOYMENT_HOST"
  ohai "Log file: $LOG_FILE"

  echo ""
  echo "${tty_yellow}📥 Starting model deployment...${tty_reset}"
  echo "   This will download the model (~13GB) and may take 10-30 minutes"
  echo "   depending on your internet connection and hardware."
  echo ""

  # Start deployment in background
  CUDA_VISIBLE_DEVICES="$CUDA_VISIBLE_DEVICES" \
  nohup "$VENV_DIR/bin/python" "$VENV_DIR/bin/swift" deploy \
    --model "$MODEL_ID" \
    --infer_backend pt \
    --port "$DEPLOYMENT_PORT" \
    --host "$DEPLOYMENT_HOST" > "$LOG_FILE" 2>&1 &

  # Get and store process ID
  DEPLOY_PID=$!
  echo "$DEPLOY_PID" > "$MODEL_DIR/deploy.pid"

  success "Model deployment started with PID: $DEPLOY_PID"
  
  echo ""
  echo "${tty_blue}📊 Monitoring deployment progress...${tty_reset}"
  echo "   Press Ctrl+C to stop monitoring (deployment will continue in background)"
  echo ""
  
  # Monitor deployment logs for the first 30 seconds
  monitor_deployment_start
  echo "🌕 Step 4: COMPLETE"
}

##############################
# Step 5: Post-Deployment Info
##############################

show_deployment_info() {
  title "Step 5: Deployment Information"
  echo "🌘 Step 5: START"

  local deploy_pid_file="$MODEL_DIR/deploy.pid"
  local deploy_pid=""

  if [ -f "$deploy_pid_file" ]; then
    deploy_pid=$(cat "$deploy_pid_file")
  fi

  echo ""
  success "DeepSeek-VL-7B-Chat deployment completed!"
  echo ""
  echo "${tty_bold}Deployment Details:${tty_reset}"
  echo "  Model: $MODEL_ID"
  echo "  Port: $DEPLOYMENT_PORT"
  echo "  Host: $DEPLOYMENT_HOST"
  echo "  GPU(s): $CUDA_VISIBLE_DEVICES"
  echo "  PID: $deploy_pid"
  echo "  Log file: $LOG_FILE"
  echo ""
  echo "${tty_bold}Useful Commands:${tty_reset}"
  echo "  Monitor deployment: ${tty_blue}$0 logs${tty_reset}"
  echo "  Manual log monitoring: ${tty_blue}tail -f $LOG_FILE${tty_reset}"
  echo "  Test deployment: ${tty_blue}python $DEPLOYMENT_DIR/test_specific_image.py${tty_reset}"
  echo "  Check process: ${tty_blue}ps -p $deploy_pid${tty_reset}"
  echo "  Stop deployment: ${tty_blue}$0 stop${tty_reset}"
  echo ""
  echo "${tty_bold}API Endpoint:${tty_reset}"
  echo "  http://$DEPLOYMENT_HOST:$DEPLOYMENT_PORT"
  echo ""
  warn "The model will continue running in the background even after closing this terminal."
  
  echo "🌕 Step 5: COMPLETE"
}

##############################
# Monitoring Functions
##############################

monitor_deployment_start() {
  local timeout=30
  local elapsed=0
  
  echo "Waiting for deployment to start..."
  
  # Wait for log file to be created
  while [ ! -f "$LOG_FILE" ] && [ $elapsed -lt 10 ]; do
    sleep 1
    elapsed=$((elapsed + 1))
    echo -n "."
  done
  
  if [ ! -f "$LOG_FILE" ]; then
    warn "Log file not created yet. Deployment may take a moment to start."
    return 1
  fi
  
  echo ""
  success "Log file created. Showing deployment progress..."
  echo ""
  
  # Monitor log file for initial startup
  timeout 30s tail -f "$LOG_FILE" 2>/dev/null || {
    echo ""
    echo "${tty_yellow}⏰ Initial monitoring timeout reached.${tty_reset}"
    echo "   Deployment continues in background."
    echo ""
  }
}

monitor_deployment_logs() {
  title "Live Deployment Logs"
  
  if [ ! -f "$LOG_FILE" ]; then
    error "Log file not found: $LOG_FILE"
    echo "Run deployment first with: ./install.sh"
    return 1
  fi
  
  echo "Monitoring deployment logs in real-time..."
  echo "Press Ctrl+C to stop monitoring (deployment will continue)"
  echo ""
  echo "${tty_blue}======== DEPLOYMENT LOGS ========${tty_reset}"
  
  tail -f "$LOG_FILE"
}

##############################
# Utility Functions
##############################

check_deployment_status() {
  title "Deployment Status Check"
  
  local deploy_pid_file="$MODEL_DIR/deploy.pid"
  
  if [ -f "$deploy_pid_file" ]; then
    local deploy_pid=$(cat "$deploy_pid_file")
    if ps -p "$deploy_pid" > /dev/null 2>&1; then
      success "Deployment is running (PID: $deploy_pid)"
      echo "Port status:"
      netstat -tuln | grep ":$DEPLOYMENT_PORT" || echo "Port not found in netstat"
    else
      error "Deployment process not found (PID: $deploy_pid)"
    fi
  else
    error "No deployment PID file found"
  fi
}

stop_deployment() {
  title "Stopping Deployment"
  
  local deploy_pid_file="$MODEL_DIR/deploy.pid"
  
  if [ -f "$deploy_pid_file" ]; then
    local deploy_pid=$(cat "$deploy_pid_file")
    if ps -p "$deploy_pid" > /dev/null 2>&1; then
      ohai "Stopping deployment process (PID: $deploy_pid)..."
      kill "$deploy_pid"
      sleep 3
      
      if ps -p "$deploy_pid" > /dev/null 2>&1; then
        warn "Process still running, force killing..."
        kill -9 "$deploy_pid"
      fi
      
      success "Deployment stopped"
      rm -f "$deploy_pid_file"
    else
      warn "Process not running (PID: $deploy_pid)"
    fi
  else
    warn "No deployment PID file found"
  fi
}

doctor() {
  title "Doctor - System Check"
  
  echo "System Information:"
  echo "  OS: $(uname -s)"
  echo "  Architecture: $(uname -m)"
  echo ""
  
  echo "Python Environment:"
  if command -v python &> /dev/null; then
    echo "  Python: $(python --version)"
  else
    error "Python not found"
  fi
  
  echo ""
  echo "Virtual Environment:"
  if [ -d "$VENV_DIR" ]; then
    success "Virtual environment exists at $VENV_DIR"
  else
    error "Virtual environment not found at $VENV_DIR"
  fi
  
  echo ""
  echo "GPU Status:"
  if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv
  else
    error "nvidia-smi not found"
  fi
  
  echo ""
  echo "Network Status:"
  if netstat -tuln 2>/dev/null | grep ":$DEPLOYMENT_PORT" > /dev/null; then
    success "Port $DEPLOYMENT_PORT is in use"
  else
    echo "Port $DEPLOYMENT_PORT is available"
  fi
}

print_help() {
  title "DeepSeek-VL-7B-Chat Deployment Script"
  echo ""
  echo "Usage: $0 [COMMAND]"
  echo ""
  echo "Commands:"
  echo "  (no args)              - Full deployment (all steps)"
  echo "  setup_environment      - Create virtual environment"
  echo "  install_dependencies   - Install required packages"
  echo "  manage_processes       - Stop existing processes"
  echo "  deploy_model          - Deploy the model"
  echo "  show_info             - Show deployment information"
  echo "  status                - Check deployment status"
  echo "  stop                  - Stop deployment"
  echo "  logs                  - Monitor deployment logs in real-time"
  echo "  doctor                - System diagnostics"
  echo "  help                  - Show this help message"
  echo ""
  echo "Environment Variables:"
  echo "  CUDA_VISIBLE_DEVICES  - Specify GPU(s) to use (default: 0)"
  echo ""
  echo "Examples:"
  echo "  $0                           # Full deployment"
  echo "  CUDA_VISIBLE_DEVICES=1 $0   # Use GPU 1"
  echo "  $0 status                    # Check status"
  echo "  $0 logs                      # Monitor deployment logs"
  echo "  $0 stop                      # Stop deployment"
}

##############################
# Main Script Logic
##############################

# Check if there are arguments to this script
if [[ "$#" -eq 0 ]]; then
  title "Performing full deployment of DeepSeek-VL-7B-Chat"
  setup_environment
  install_dependencies
  manage_existing_processes
  deploy_model
  show_deployment_info
else
  for arg in "$@"
  do
    case $arg in
      setup_environment)
        setup_environment
        ;;
      install_dependencies)
        install_dependencies
        ;;
      manage_processes)
        manage_existing_processes
        ;;
      deploy_model)
        deploy_model
        ;;
      show_info)
        show_deployment_info
        ;;
      status)
        check_deployment_status
        ;;
      stop)
        stop_deployment
        ;;
      logs)
        monitor_deployment_logs
        ;;
      doctor)
        doctor
        ;;
      help|--help|-h)
        print_help
        ;;
      *)
        error "Unknown argument: $arg"
        print_help
        exit 1
        ;;
    esac
  done
fi