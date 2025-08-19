#!/usr/bin/env python3
"""
Setup script for MMPose installation
"""

import subprocess
import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(command, description):
    """Run a command and handle errors"""
    try:
        logger.info(f"🔄 {description}")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8 or higher is required")
        return False
    logger.info(f"✅ Python version {sys.version} is compatible")
    return True

def install_mmpose():
    """Install MMPose and dependencies"""
    logger.info("🚀 Starting MMPose installation...")
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install PyTorch FIRST (required for MMPose)
    logger.info("📦 Installing PyTorch first (required for MMPose)...")
    if not run_command("pip install torch torchvision", "Installing PyTorch"):
        return False
    
    # Try mim installation first
    logger.info("🔄 Attempting installation via openmim...")
    if install_via_mim():
        return True
    
    # Fallback to pip installation
    logger.info("🔄 Falling back to pip installation...")
    return install_via_pip()

def install_via_mim():
    """Install via openmim"""
    try:
        # Install openmim
        if not run_command("pip install -U openmim", "Installing openmim"):
            return False
        
        # Install MMEngine
        if not run_command("mim install mmengine", "Installing MMEngine"):
            return False
        
        # Install MMCV
        if not run_command("mim install mmcv", "Installing MMCV"):
            return False
        
        # Install MMDetection
        if not run_command("mim install mmdet", "Installing MMDetection"):
            return False
        
        # Install MMPose LAST (depends on all above)
        if not run_command("mim install mmpose", "Installing MMPose"):
            return False
        
        logger.info("✅ MMPose installation via openmim completed successfully!")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ openmim installation failed: {e}")
        return False

def install_via_pip():
    """Install via pip (fallback method)"""
    try:
        logger.info("📦 Installing MMPose dependencies via pip...")
        
        # Install basic dependencies
        dependencies = [
            "mmengine",
            "mmcv",
            "mmdet", 
            "mmpose"
        ]
        
        for dep in dependencies:
            if not run_command(f"pip install {dep}", f"Installing {dep}"):
                logger.warning(f"⚠️ Failed to install {dep}, continuing...")
        
        logger.info("✅ MMPose installation via pip completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ pip installation failed: {e}")
        return False

def test_mmpose_installation():
    """Test if MMPose is working correctly"""
    logger.info("🧪 Testing MMPose installation...")
    
    try:
        import mmpose
        import mmdet
        import mmcv
        import mmengine
        import torch
        
        logger.info("✅ All MMPose dependencies imported successfully")
        
        # Test basic functionality
        from mmpose.apis import init_pose_model
        logger.info("✅ MMPose APIs imported successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ MMPose import failed: {e}")
        return False

def create_config_files():
    """Create basic configuration files for MMPose"""
    logger.info("📝 Creating MMPose configuration files...")
    
    config_dir = "services/ai/mmpose/configs"
    os.makedirs(config_dir, exist_ok=True)
    
    # Create basic config
    config_content = """# Basic MMPose configuration
model = dict(
    type='TopDown',
    pretrained=None,
    backbone=dict(
        type='HRNet',
        in_channels=3,
        norm_cfg=dict(type='SyncBN', requires_grad=True),
        norm_eval=True,
        extra=dict(
            stage1=dict(
                num_modules=1,
                num_branches=1,
                block='BOTTLENECK',
                num_blocks=(4, ),
                num_channels=(64, )),
            stage2=dict(
                num_modules=1,
                num_branches=2,
                block='BASIC',
                num_blocks=(4, 4),
                num_channels=(32, 64)),
            stage3=dict(
                num_modules=4,
                num_branches=3,
                block='BASIC',
                num_blocks=(4, 4, 4),
                num_channels=(32, 64, 128)),
            stage4=dict(
                num_modules=3,
                num_branches=4,
                block='BASIC',
                num_blocks=(4, 4, 4, 4),
                num_channels=(32, 64, 128, 256)))),
    keypoint_head=dict(
        type='TopDownSimpleHead',
        in_channels=32,
        out_channels=17,
        loss_keypoint=dict(type='JointsMSELoss', use_target_weight=True)),
    train_cfg=dict(),
    test_cfg=dict(
        flip_test=True,
        post_process='default',
        shift_heatmap=True,
        modulate_kernel=11))
"""
    
    config_file = os.path.join(config_dir, "basic_config.py")
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    logger.info(f"✅ Configuration file created: {config_file}")
    return True

def main():
    """Main installation function"""
    logger.info("🎯 MMPose Setup for iDance Challenge Scoring")
    logger.info("=" * 50)
    
    # Install MMPose
    if not install_mmpose():
        logger.error("❌ MMPose installation failed")
        return False
    
    # Test installation
    if not test_mmpose_installation():
        logger.error("❌ MMPose installation test failed")
        return False
    
    # Create config files
    if not create_config_files():
        logger.error("❌ Failed to create configuration files")
        return False
    
    logger.info("🎉 MMPose setup completed successfully!")
    logger.info("📋 Next steps:")
    logger.info("   1. Update your challenge submission code to use the new MMPose service")
    logger.info("   2. Test with a sample video")
    logger.info("   3. Monitor performance and accuracy")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 