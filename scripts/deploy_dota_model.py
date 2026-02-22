#!/usr/bin/env python3
"""
DOTA Model Deployment Script
Deploys trained DOTA model to AEGIS system
"""

import os
import sys
import shutil
from pathlib import Path

def deploy_dota_model():
    """Deploy DOTA model to AEGIS"""
    
    print("=" * 60)
    print("DOTA MODEL DEPLOYMENT")
    print("=" * 60)
    print()
    
    # Check if model exists
    source_model = Path("runs/dota/dota_aerial_v1/weights/best.pt")
    if not source_model.exists():
        print("❌ ERROR: Trained DOTA model not found!")
        print()
        print("Please train the model first:")
        print("  python3 scripts/train_dota_model.py")
        print()
        sys.exit(1)
    
    print(f"✓ Found trained model: {source_model}")
    print()
    
    # Deployment options
    print("Deployment Options:")
    print("-" * 60)
    print("1. Replace current model (models/best_model.pt)")
    print("2. Deploy as DOTA model (models/dota_model.pt)")
    print("3. Cancel")
    print("-" * 60)
    print()
    
    choice = input("Select option (1/2/3): ").strip()
    
    if choice == "1":
        # Backup current model if exists
        current_model = Path("models/best_model.pt")
        if current_model.exists():
            backup = Path("models/best_model.pt.backup")
            print(f"Backing up current model to: {backup}")
            shutil.copy(current_model, backup)
        
        # Copy DOTA model
        print(f"Deploying DOTA model to: {current_model}")
        shutil.copy(source_model, current_model)
        
        print()
        print("✅ DOTA model deployed successfully!")
        print()
        print("The system will now use DOTA for aerial object detection.")
        print()
        print("Restart AEGIS server:")
        print("  PORT=5001 python3 app.py")
        print()
        
    elif choice == "2":
        # Deploy as separate model
        dota_model = Path("models/dota_model.pt")
        print(f"Deploying DOTA model to: {dota_model}")
        shutil.copy(source_model, dota_model)
        
        print()
        print("✅ DOTA model deployed as separate model!")
        print()
        print("To use DOTA model, set in .env:")
        print("  MODEL_TYPE=dota")
        print()
        print("Or keep current model and switch via environment variable.")
        print()
        
    else:
        print("Deployment cancelled.")
        sys.exit(0)
    
    print("=" * 60)
    print()
    print("DEPLOYMENT COMPLETE")
    print()
    print("Next steps:")
    print("1. Update threat assessment rules for DOTA classes")
    print("2. Test with aerial imagery")
    print("3. Verify detections show DOTA classes")
    print()
    print("=" * 60)

if __name__ == "__main__":
    deploy_dota_model()
