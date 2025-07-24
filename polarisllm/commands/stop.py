"""
Stop Command Handler
"""

from ..core import ModelRegistry, PolarisConfig, ProcessManager


def handle_stop_command(args) -> bool:
    """Handle stop model command
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    model_name = getattr(args, 'model', None)
    force = getattr(args, 'force', False)
    
    if not model_name:
        print("❌ Model name is required")
        print("   Usage: polarisllm stop <model-name>")
        return False
    
    print(f"🛑 Stopping model: {model_name}")
    
    # Initialize core components
    config = PolarisConfig()
    registry = ModelRegistry(config)
    process_manager = ProcessManager(config)
    
    # Get model info from registry
    model_info = registry.get_model_info(model_name)
    
    if not model_info:
        print(f"❌ Model '{model_name}' not found in registry")
        print("💡 Use 'polarisllm list' to see deployed models")
        return False
    
    # Check current status
    if model_info.status == "stopped":
        print(f"ℹ️  Model '{model_name}' is already stopped")
        return True
    
    print(f"   Status: {model_info.status}")
    print(f"   Port: {model_info.port}")
    print(f"   PID: {model_info.pid}")
    print()
    
    try:
        # Stop the process  
        success = process_manager.stop_process(model_name, force=force)
        
        if success:
            # Update registry status
            registry.update_model_status(model_name, "stopped", pid=None)
            
            print(f"✅ Successfully stopped model: {model_name}")
            print(f"   Port {model_info.port} is now available")
            
            # Show next steps
            print()
            print("💡 Next steps:")
            print(f"   polarisllm deploy --model {model_name}  # Restart the model")
            print(f"   polarisllm list                         # View all models")
            
            return True
        else:
            print(f"❌ Failed to stop model: {model_name}")
            
            if not force:
                print("💡 Try with --force flag for forceful termination")
            
            return False
            
    except Exception as e:
        print(f"❌ Error stopping model: {e}")
        return False


def handle_stop_all_command(args) -> bool:
    """Handle stop all models command
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    force = getattr(args, 'force', False)
    
    print("🛑 Stopping all models...")
    
    # Initialize core components
    config = PolarisConfig()
    registry = ModelRegistry(config)
    process_manager = ProcessManager(config)
    
    # Get running models
    running_models = registry.get_running_models()
    
    if not running_models:
        print("ℹ️  No running models found")
        return True
    
    print(f"   Found {len(running_models)} running model(s)")
    print()
    
    stopped_count = 0
    failed_count = 0
    
    for model_name, model_info in running_models.items():
        print(f"🛑 Stopping {model_name}...")
        
        try:
            success = process_manager.stop_process(model_name, force=force)
            
            if success:
                registry.update_model_status(model_name, "stopped", pid=None)
                print(f"   ✅ Stopped {model_name}")
                stopped_count += 1
            else:
                print(f"   ❌ Failed to stop {model_name}")
                failed_count += 1
                
        except Exception as e:
            print(f"   ❌ Error stopping {model_name}: {e}")
            failed_count += 1
    
    print()
    print(f"📊 Summary:")
    print(f"   Stopped: {stopped_count}")
    print(f"   Failed: {failed_count}")
    
    if failed_count > 0 and not force:
        print()
        print("💡 Some models failed to stop. Try with --force flag:")
        print("   polarisllm stop --all --force")
    
    return failed_count == 0


def handle_undeploy_command(args) -> bool:
    """Handle undeploy model command (stop + unregister)
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    model_name = getattr(args, 'model', None)
    
    if not model_name:
        print("❌ Model name is required")
        print("   Usage: polarisllm undeploy <model-name>")
        return False
    
    print(f"🗑️  Undeploying model: {model_name}")
    
    # Initialize core components
    config = PolarisConfig()
    registry = ModelRegistry(config)
    process_manager = ProcessManager(config)
    
    # Get model info from registry
    model_info = registry.get_model_info(model_name)
    
    if not model_info:
        print(f"❌ Model '{model_name}' not found in registry")
        return False
    
    print(f"   This will:")
    print(f"   • Stop the running process (PID: {model_info.pid})")
    print(f"   • Release port {model_info.port}")
    print(f"   • Remove from registry")
    print(f"   • Keep log files for debugging")
    print()
    
    try:
        # Stop the process if running
        if model_info.status == "running" and model_info.pid:
            print("🛑 Stopping process...")
            process_manager.stop_process(model_name, force=False)
        
        # Remove from registry (this also releases the port)
        print("🗑️  Removing from registry...")
        success = registry.unregister_model(model_name)
        
        if success:
            print(f"✅ Successfully undeployed model: {model_name}")
            print()
            print("💡 To deploy again:")
            print(f"   polarisllm deploy --model {model_name}")
            
            return True
        else:
            print(f"❌ Failed to unregister model: {model_name}")
            return False
            
    except Exception as e:
        print(f"❌ Error undeploying model: {e}")
        return False 