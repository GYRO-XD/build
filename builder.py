#!/usr/bin/env python3
"""
run_gyro.py - Pure Python launcher
Just run this to use GYRO-Secure
"""

import sys
import os
from pathlib import Path

def main():
    """Run GYRO-Secure"""
    print("🔐 Starting GYRO-Secure...")
    
    # Check if .so file exists
    so_files = list(Path('.').glob('gyro_secure*.so'))
    if so_files:
        print(f"✅ Found: {so_files[0].name}")
    else:
        print("⚠️ No .so file found, using Python source")
    
    try:
        # Try to import gyro_secure
        import gyro_secure
        gyro_secure.main()
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        print("Make sure gyro_secure.py or .so file is in this directory")
        sys.exit(1)

if __name__ == "__main__":
    main()
