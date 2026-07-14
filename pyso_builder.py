#!/usr/bin/env python3
"""
PYSOBuilder Pure Python v3.0
Compile Python to .so using only Python
No bash scripts, no external dependencies
Author: GYRO-XD
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path
import importlib.util

class PYSOBuilder:
    """Pure Python .so compiler - No bash needed!"""
    
    def __init__(self):
        self.version = "3.0.0"
        self.author = "GYRO-XD"
        self.python_version = self._get_python_version()
        self.is_termux = 'TERMUX_VERSION' in os.environ
        
    def _get_python_version(self):
        """Get Python version string (e.g., 310, 311)"""
        return f"{sys.version_info.major}{sys.version_info.minor}"
    
    def _check_dependencies(self):
        """Check and install dependencies using pip"""
        print("📦 Checking dependencies...")
        
        dependencies = ['cython', 'setuptools']
        missing = []
        
        for dep in dependencies:
            try:
                importlib.import_module(dep)
                print(f"   ✅ {dep} found")
            except ImportError:
                missing.append(dep)
                print(f"   ❌ {dep} missing")
        
        if missing:
            print(f"\n📦 Installing: {', '.join(missing)}")
            for dep in missing:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", dep, "--quiet"
                ])
            print("   ✅ All installed!")
        else:
            print("   ✅ All dependencies ready!")
        
        # Check for Python headers in Termux
        if self.is_termux:
            python_include = f"/data/data/com.termux/files/usr/include/python3.{self.python_version[0]}"
            if not Path(python_include).exists():
                print("\n📦 Installing Python development headers...")
                subprocess.check_call(["pkg", "install", "python-dev", "-y"])
        
        return True
    
    def _create_setup_code(self, script_name, base_name, optimize=3):
        """Generate setup.py code as string"""
        return f'''from setuptools import setup
from Cython.Build import cythonize
import os

# Termux specific
if 'TERMUX_VERSION' in os.environ:
    os.environ['CFLAGS'] = '-I/data/data/com.termux/files/usr/include/python3.{self.python_version[0]}'
    os.environ['LDFLAGS'] = '-L/data/data/com.termux/files/usr/lib'

setup(
    name="{base_name}",
    ext_modules=cythonize(
        "{script_name}",
        compiler_directives={{
            'language_level': 3,
            'boundscheck': False,
            'wraparound': False,
            'initializedcheck': False,
            'cdivision': True,
            'embedsignature': False,
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
    
    def _cleanup(self, keep_so=False):
        """Clean build files"""
        patterns = ['*.c', '*.cpp', '*.pyc', '__pycache__', 'build', 'dist', '*.o']
        if not keep_so:
            patterns.append('*.so')
        
        for pattern in patterns:
            for item in Path('.').glob(pattern):
                if item.is_file():
                    item.unlink()
                    print(f"   🧹 Removed: {item}")
                elif item.is_dir():
                    shutil.rmtree(item)
                    print(f"   🧹 Removed: {item}/")
    
    def compile(self, script_path, output_name=None, optimize=3, verbose=False, clean=True):
        """Main compile function - pure Python"""
        
        print(f"\n🔐 PYSOBuilder v{self.version}")
        print("=" * 50)
        print(f"📄 Input: {script_path}")
        print(f"🐍 Python: {sys.version.split()[0]}")
        print(f"💻 Platform: {'Termux' if self.is_termux else 'Linux'}")
        print("=" * 50)
        
        # Validate input
        script_path = Path(script_path)
        if not script_path.exists():
            print(f"❌ Error: '{script_path}' not found!")
            return None
        
        # Check dependencies
        print()
        self._check_dependencies()
        
        # Clean previous builds
        if clean:
            print("\n🧹 Cleaning previous builds...")
            self._cleanup(keep_so=False)
        
        # Set output name
        base_name = script_path.stem if output_name is None else output_name
        
        # Create setup.py in temporary directory
        print("\n🔧 Creating build configuration...")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            
            # Copy script to temp directory
            temp_script = temp_dir / script_path.name
            shutil.copy2(script_path, temp_script)
            
            # Create setup.py
            setup_file = temp_dir / "setup.py"
            setup_file.write_text(self._create_setup_code(script_path.name, base_name, optimize))
            
            # Change to temp directory
            original_dir = Path.cwd()
            os.chdir(temp_dir)
            
            try:
                # Build
                print("🔨 Compiling...")
                env = os.environ.copy()
                if self.is_termux:
                    env['CC'] = 'clang'
                    env['CXX'] = 'clang++'
                
                result = subprocess.run(
                    [sys.executable, "setup.py", "build_ext", "--inplace"],
                    capture_output=True,
                    text=True,
                    env=env
                )
                
                if verbose:
                    if result.stdout:
                        print("\n📝 Build output:")
                        print(result.stdout)
                    if result.stderr and "warning" in result.stderr.lower():
                        print("\n⚠️ Warnings:")
                        print(result.stderr)
                
                # Find the .so file
                so_files = list(temp_dir.glob("*.so"))
                
                if not so_files:
                    print("\n❌ Compilation failed - no .so file generated")
                    if result.stderr:
                        print("\nError details:")
                        print(result.stderr)
                    os.chdir(original_dir)
                    return None
                
                # Get the .so file
                so_file = so_files[0]
                
                # Create final name
                final_name = f"{base_name}.cpython-{self.python_version}.so"
                
                # Copy to original directory
                final_path = original_dir / final_name
                shutil.copy2(so_file, final_path)
                
                # Get file size
                size = final_path.stat().st_size
                
                print("\n" + "=" * 50)
                print("✅ COMPILATION SUCCESSFUL!")
                print("=" * 50)
                print(f"📁 Output: {final_name}")
                print(f"📊 Size: {size / 1024:.2f} KB ({size / 1024 / 1024:.2f} MB)")
                print(f"📏 Lines: {sum(1 for _ in script_path.open())}")
                print("=" * 50)
                
                # Test import
                self._test_import(final_name)
                
                return final_name
                
            except Exception as e:
                print(f"\n❌ Error during compilation: {e}")
                os.chdir(original_dir)
                return None
            finally:
                os.chdir(original_dir)
    
    def _test_import(self, so_file):
        """Test import the compiled .so"""
        print("\n🧪 Testing import...")
        try:
            # Add current directory to path
            sys.path.insert(0, '.')
            
            # Get module name
            module_name = Path(so_file).stem.split('.')[0]
            
            # Import
            module = __import__(module_name)
            
            print("✅ Import successful!")
            
            # List available functions
            attrs = [attr for attr in dir(module) if not attr.startswith('_')]
            if attrs:
                print(f"🔧 Functions: {', '.join(attrs[:5])}")
                if len(attrs) > 5:
                    print(f"   ... and {len(attrs) - 5} more")
            
            return True
        except Exception as e:
            print(f"⚠️ Import test failed: {e}")
            return False
    
    def compile_multiple(self, scripts, output_dir="compiled", optimize=3):
        """Compile multiple scripts"""
        print(f"\n📦 Batch Compilation")
        print("=" * 50)
        print(f"📄 Scripts: {len(scripts)}")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        results = []
        for script in scripts:
            print(f"\n📄 Compiling: {script}")
            so_file = self.compile(script, optimize=optimize)
            if so_file:
                target = output_path / Path(so_file).name
                shutil.move(so_file, target)
                results.append({"script": script, "output": str(target), "status": "success"})
            else:
                results.append({"script": script, "output": None, "status": "failed"})
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 BATCH SUMMARY")
        print("=" * 50)
        success = sum(1 for r in results if r['status'] == 'success')
        print(f"✅ Success: {success}")
        print(f"❌ Failed: {len(results) - success}")
        print(f"📁 Output: {output_dir}/")
        print("=" * 50)
        
        return results
    
    def clean(self, keep_so=False):
        """Clean build files"""
        print("🧹 Cleaning...")
        self._cleanup(keep_so)
        print("✅ Clean complete!")

def main():
    """Main entry point - pure Python CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='PYSOBuilder - Python to .so Compiler (Pure Python)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic compilation
  python pyso_builder.py gyro_secure.py

  # Verbose output
  python pyso_builder.py gyro_secure.py -v

  # Custom output name
  python pyso_builder.py gyro_secure.py -o mymodule

  # Max optimization
  python pyso_builder.py gyro_secure.py -O 3

  # Batch compile multiple files
  python pyso_builder.py file1.py file2.py -b

  # Clean build files
  python pyso_builder.py --clean
        '''
    )
    
    parser.add_argument(
        'scripts',
        nargs='*',
        help='Python scripts to compile'
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
        action='store_true',
        help='Batch compile multiple files'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean build files'
    )
    
    parser.add_argument(
        '--clean-all',
        action='store_true',
        help='Clean all including .so files'
    )
    
    args = parser.parse_args()
    
    # Initialize builder
    builder = PYSOBuilder()
    
    # Handle clean commands
    if args.clean:
        builder.clean(keep_so=True)
        return
    
    if args.clean_all:
        builder.clean(keep_so=False)
        return
    
    # Check if scripts provided
    if not args.scripts:
        parser.print_help()
        return
    
    # Compile
    if args.batch and len(args.scripts) > 1:
        builder.compile_multiple(args.scripts, optimize=args.optimize)
    else:
        script = args.scripts[0]
        builder.compile(
            script,
            output_name=args.output,
            optimize=args.optimize,
            verbose=args.verbose
        )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
