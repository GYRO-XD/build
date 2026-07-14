#!/usr/bin/env python3
"""
PYSOBuilder v2.0 - Python to .so Compiler
Error-Free Compilation Tool for Termux
GitHub: GYRO-XD/pyso-builder
"""

import os
import sys
import subprocess
import shutil
import argparse
import platform
import tempfile
import json
from pathlib import Path
from datetime import datetime

class PYSOBuilder:
    def __init__(self):
        self.version = "2.0.0"
        self.author = "GYRO-XD"
        self.python_version = self.get_python_version()
        
    def get_python_version(self):
        """Get Python version (e.g., 310, 311)"""
        return f"{sys.version_info.major}{sys.version_info.minor}"
    
    def check_environment(self):
        """Check and prepare compilation environment"""
        errors = []
        
        # Check Python headers
        python_include = f"/data/data/com.termux/files/usr/include/python3.{self.python_version[0]}" if 'TERMUX' in os.environ.get('TERMUX_VERSION', '') else None
        
        if 'TERMUX' in os.environ.get('TERMUX_VERSION', ''):
            if not os.path.exists(python_include):
                print("📦 Installing Python development headers...")
                os.system("pkg install python-dev -y")
        
        # Install Cython if missing
        try:
            import Cython
            print(f"✅ Cython {Cython.__version__} found")
        except ImportError:
            print("📦 Installing Cython...")
            os.system(f"{sys.executable} -m pip install cython setuptools wheel --quiet")
        
        return True
    
    def detect_platform(self):
        """Detect platform for naming"""
        system = platform.system().lower()
        arch = platform.machine().lower()
        return f"{system}_{arch}"
    
    def compile_script(self, script_path, output_name=None, optimize=3, verbose=False):
        """Compile Python script to .so with error handling"""
        
        print(f"\n🔐 PYSOBuilder v{self.version}")
        print("=" * 50)
        
        # Check if script exists
        script_path = Path(script_path)
        if not script_path.exists():
            print(f"❌ Error: '{script_path}' not found!")
            return None
        
        print(f"📄 Input: {script_path}")
        print(f"🐍 Python: {self.python_version}")
        print(f"💻 Platform: {self.detect_platform()}")
        print("=" * 50)
        
        # Prepare environment
        self.check_environment()
        
        # Get base name
        base_name = script_path.stem if output_name is None else output_name
        
        # Create setup.py
        setup_code = f'''from setuptools import setup
from Cython.Build import cythonize
import sys
import os

# Set compiler flags for Termux
if 'TERMUX_VERSION' in os.environ:
    os.environ['CFLAGS'] = '-I/data/data/com.termux/files/usr/include/python3.{self.python_version[0]}'
    os.environ['LDFLAGS'] = '-L/data/data/com.termux/files/usr/lib'

setup(
    name="{base_name}",
    ext_modules=cythonize(
        "{script_path.name}",
        compiler_directives={{
            'language_level': 3,
            'boundscheck': False,
            'wraparound': False,
            'initializedcheck': False,
            'cdivision': True,
        }}
    ),
    options={{
        'build_ext': {{
            'optimize': {optimize},
            'debug': False,
        }}
    }}
)
'''
        
        # Write setup file
        setup_path = Path("setup_temp.py")
        with open(setup_path, "w") as f:
            f.write(setup_code)
        
        # Compile
        print("\n🔨 Compiling...")
        try:
            # Run compilation with error capture
            env = os.environ.copy()
            if 'TERMUX_VERSION' in env:
                env['CC'] = 'clang'
                env['CXX'] = 'clang++'
            
            result = subprocess.run(
                [sys.executable, str(setup_path), "build_ext", "--inplace"],
                capture_output=True,
                text=True,
                env=env
            )
            
            if verbose:
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print("⚠️ Compiler warnings:")
                    print(result.stderr)
            
            # Cleanup
            if setup_path.exists():
                setup_path.unlink()
            
            # Remove build directory
            if Path("build").exists():
                shutil.rmtree("build")
            
            # Find generated .so file
            so_files = list(Path(".").glob(f"{base_name}*.so")) + list(Path(".").glob("*.so"))
            
            # Filter out Python files
            so_files = [f for f in so_files if f.name != "setup_temp.py"]
            
            if so_files:
                # Get the most recent .so file
                so_file = max(so_files, key=lambda f: f.stat().st_mtime)
                
                # Rename to standard format
                final_name = f"{base_name}.cpython-{self.python_version}.so"
                shutil.move(str(so_file), final_name)
                
                size = Path(final_name).stat().st_size
                
                print("\n" + "=" * 50)
                print("✅ COMPILATION SUCCESSFUL!")
                print("=" * 50)
                print(f"📁 Output: {final_name}")
                print(f"📊 Size: {size / 1024:.2f} KB")
                print("=" * 50)
                
                return final_name
            
            # Check for .pyc or other files
            print("\n❌ Compilation failed - no .so file generated")
            if result.stderr:
                print("\nError details:")
                print(result.stderr)
            return None
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            if setup_path.exists():
                setup_path.unlink()
            return None
    
    def batch_compile(self, scripts, output_dir="compiled"):
        """Batch compile multiple scripts"""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        results = []
        for script in scripts:
            print(f"\n📄 Compiling: {script}")
            so_file = self.compile_script(script)
            if so_file:
                target = output_path / Path(so_file).name
                shutil.move(so_file, target)
                results.append({"script": script, "output": str(target), "status": "success"})
            else:
                results.append({"script": script, "output": None, "status": "failed"})
        
        return results

def main():
    parser = argparse.ArgumentParser(
        description='PYSOBuilder - Python to .so Compiler',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'script',
        help='Python script to compile'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output name (without extension)'
    )
    
    parser.add_argument(
        '-O', '--optimize',
        type=int,
        default=3,
        choices=[0, 1, 2, 3],
        help='Optimization level (0-3, default: 3)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '-b', '--batch',
        nargs='*',
        help='Batch compile multiple files'
    )
    
    args = parser.parse_args()
    
    builder = PYSOBuilder()
    
    if args.batch:
        # Batch compile
        results = builder.batch_compile(args.batch)
        print("\n" + "=" * 50)
        print("📊 BATCH SUMMARY")
        print("=" * 50)
        success = sum(1 for r in results if r['status'] == 'success')
        print(f"✅ Success: {success}")
        print(f"❌ Failed: {len(results) - success}")
    else:
        # Single file
        builder.compile_script(args.script, args.output, args.optimize, args.verbose)

if __name__ == "__main__":
    main()
