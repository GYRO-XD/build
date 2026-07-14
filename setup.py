#!/usr/bin/env python3
"""
setup_gyro.py - Complete one-time setup
Creates everything needed for GYRO-Secure
"""

import os
import sys
import subprocess
from pathlib import Path

def setup():
    print("🔧 Setting up GYRO-Secure...")
    
    # Check Python
    print(f"🐍 Python: {sys.version.split()[0]}")
    
    # Install dependencies
    print("📦 Installing dependencies...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", 
        "cython", "setuptools", "requests", 
        "beautifulsoup4", "rich", "--quiet"
    ])
    
    # Check for Termux
    if 'TERMUX_VERSION' in os.environ:
        print("📦 Installing Termux packages...")
        subprocess.check_call(["pkg", "install", "python-dev", "clang", "-y"])
    
    print("✅ Setup complete!")
    print("\nNow run:")
    print("  python pyso_builder.py gyro_secure.py")
    print("  python gyro_secure.py")

if __name__ == "__main__":
    setup()
