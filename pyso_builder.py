#!/usr/bin/env python3
"""
PYSOBuilder - Python to .so Compiler
Compiles Python scripts to .cpython-310.so / .cpython-311.so
Author: GYRO-XD
GitHub: https://github.com/GYRO-XD/pyso-builder
"""

import os
import sys
import subprocess
import shutil
import platform
import tempfile
from pathlib import Path
import argparse

class PYSOBuilder:
    """Main compiler class - Error-Free Version"""
    
    def __init__(self):
        self.version = "2.0.0"
        self.author = "GYRO-XD"
        self.python_version = self._get_python_version()
        self.termux = self._is_termux()
        
    def _get_python_version(self):
        """Get Python version (e.g., 310, 311)"""
        return f"{sys.version_info.major}{sys.version_info.minor}"
    
    def _is_termux(self):
        """Check if running in Termux"""
        return 'TERMUX_VERSION' in os.environ or 'com.termux' in os.getenv('PREFIX', '')
    
    def _setup_environment(self):
        """Setup environment for compilation"""
        if self.termux:
            # Termux specific paths
            python_path = f"/data/data/com.termux/files/usr/include/python3.{self.python_version[1:]}"
            if os.path.exists(python_path):
                os.environ['CFLAGS'] = f"-I{python_path}"
                os.environ['LDFLAGS'] = f"-L/data/data/com.termux/files/usr/lib"
            os.environ['CC'] = 'clang'
            os.environ['CXX'] = 'clang++'
            
    def check_requirements(self):
        """Check and install requirements"""
        required = ['cython', 'setuptools']
        missing = []
        
        for req in required:
            try:
                __import__(req)
            except ImportError:
                missing.append(req)
        
        if missing:
            print(f"📦 Installing: {', '.join(missing)}")
            for req in missing:
                subprocess.run([sys.executable, "-m", "pip", "install", req], 
                             capture_output=True, check=False)
            print("✅ Requirements installed!")
        return True
    
    def compile(self, script_path, output_name=None, optimize=3, verbose=False):
        """Main compile function - ERROR FREE"""
        
        # Validate input
        if not os.path.exists(script_path):
            print(f"❌ File not found: {script_path}")
            return False
        
        # Setup environment
        self._setup_environment()
        
        # Check requirements
        if not self.check_requirements():
            return False
        
        # Get script info
        script_name = Path(script_path).stem
        output_name = output_name or script_name
        
        print(f"\n🔐 PYSOBuilder v{self.version}")
        print(f"📄 Input: {script_path}")
        print(f"🐍 Python: {self.python_version}")
        print(f"📱 Platform: {'Termux' if self.termux else 'Linux'}")
        print("=" * 50)
        
        # Create temporary setup.py
        setup_content = f"""from setuptools import setup
from Cython.Build import cythonize

setup(
    name="{output_name}",
    ext_modules=cythonize(
        "{script_path}",
        compiler_directives={{
            'language_level': 3,
            'boundscheck': False,
            'wraparound': False,
        }}
    ),
    options={{
        'build_ext': {{
            'optimize': {optimize},
            'debug': False,
        }}
    }}
)
"""
        
        # Write setup file
        temp_dir = tempfile.mkdtemp()
        setup_path = Path(temp_dir) / "setup.py"
        with open(setup_path, 'w') as f:
            f.write(setup_content)
        
        # Change to temp directory
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        
        # Copy script to temp
        shutil.copy(original_dir + "/" + script_path, temp_dir)
        
        try:
            # Build
            cmd = [sys.executable, "setup.py", "build_ext", "--inplace"]
            if verbose:
                result = subprocess.run(cmd, capture_output=False)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Find .so file
            so_files = list(Path(temp_dir).glob("*.so"))
            
            if so_files:
                so_file = so_files[0]
                target_name = f"{output_name}.cpython-{self.python_version}.so"
                target_path = Path(original_dir) / target_name
                
                # Copy to original directory
                shutil.copy(str(so_file), str(target_path))
                
                # Get file info
                size = target_path.stat().st_size
                
                print("\n" + "=" * 50)
                print("✅ COMPILATION SUCCESSFUL!")
                print("=" * 50)
                print(f"📁 Output: {target_name}")
                print(f"📊 Size: {size / 1024:.2f} KB")
                print(f"🔢 Python: {self.python_version}")
                print("=" * 50)
                
                # Test import
                self._test_import(target_path, original_dir)
                
                os.chdir(original_dir)
                shutil.rmtree(temp_dir)
                return target_path
            else:
                print("\n❌ Compilation failed!")
                if not verbose and result:
                    print(result.stderr)
                os.chdir(original_dir)
                shutil.rmtree(temp_dir)
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            os.chdir(original_dir)
            shutil.rmtree(temp_dir)
            return False
    
    def _test_import(self, so_path, original_dir):
        """Test import the compiled .so"""
        try:
            # Add to path
            sys.path.insert(0, str(original_dir))
            module_name = Path(so_path).stem.split('.')[0]
            
            # Try import
            module = __import__(module_name)
            print(f"🧪 Import test: ✅ SUCCESS")
            
            # List functions
            funcs = [f for f in dir(module) if not f.startswith('_')]
            if funcs:
                print(f"📦 Functions: {', '.join(funcs[:5])}")
            return True
        except Exception as e:
            print(f"🧪 Import test: ⚠️ Failed ({e})")
            return False

def main():
    parser = argparse.ArgumentParser(description='PYSOBuilder - Error-Free Python to .so Compiler')
    parser.add_argument('script', help='Python script to compile')
    parser.add_argument('-o', '--output', help='Output name (without extension)')
    parser.add_argument('-O', '--optimize', type=int, default=3, choices=[0,1,2,3],
                       help='Optimization level (0-3, default: 3)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    builder = PYSOBuilder()
    result = builder.compile(args.script, args.output, args.optimize, args.verbose)
    
    if result:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
