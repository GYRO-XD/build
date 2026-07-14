#!/usr/bin/env python3
"""
PYSOBuilder - Professional Python to .so Compiler
Compile Python scripts to .cpython-310.so files with one command
Author: GYRO-XD
GitHub: https://github.com/GYRO-XD/pyso-builder
"""

import os
import sys
import subprocess
import shutil
import argparse
import json
import platform
import time
from pathlib import Path
from datetime import datetime
import tempfile

class PYSOBuilder:
    """Main class for compiling Python to .so"""
    
    def __init__(self):
        self.version = "1.0.0"
        self.author = "GYRO-XD"
        self.supported_python = ['3.8', '3.9', '3.10', '3.11', '3.12']
        self.python_version = self.get_python_version()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def get_python_version(self):
        """Get current Python version"""
        version = f"{sys.version_info.major}{sys.version_info.minor}"
        return version
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        dependencies = ['cython', 'setuptools']
        missing = []
        
        for dep in dependencies:
            try:
                __import__(dep)
                print(f"✅ {dep} found")
            except ImportError:
                missing.append(dep)
                print(f"❌ {dep} not found")
        
        if missing:
            print(f"\n📦 Installing missing dependencies: {', '.join(missing)}")
            for dep in missing:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
            print("✅ All dependencies installed!")
        else:
            print("✅ All dependencies are ready!")
    
    def detect_platform(self):
        """Detect platform for naming"""
        system = platform.system()
        arch = platform.machine()
        return f"{system.lower()}_{arch}"
    
    def create_setup_file(self, script_path, output_name=None, optimize=3, verbose=False):
        """Create a temporary setup.py file"""
        
        script_name = Path(script_path).stem
        if output_name is None:
            output_name = script_name
        
        # Read the script content
        with open(script_path, 'r') as f:
            script_content = f.read()
        
        # Check if script has main function
        has_main = 'def main' in script_content or "if __name__ == '__main__'" in script_content
        
        # Create setup content
        setup_content = f'''from setuptools import setup
from Cython.Build import cythonize
import sys

# Compiler directives for optimization
directives = {{
    'language_level': 3,
    'boundscheck': False,
    'wraparound': False,
    'initializedcheck': False,
    'cdivision': True,
    'embedsignature': {str(verbose).lower()},
    'profile': False,
    'linetrace': False,
    'nonecheck': False,
    'overflowcheck': False,
}}

setup(
    name="{output_name}",
    ext_modules=cythonize(
        "{script_path}",
        compiler_directives=directives,
        annotate={str(verbose).lower()},
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
        setup_path = Path(tempfile.gettempdir()) / "setup_temp.py"
        with open(setup_path, 'w') as f:
            f.write(setup_content)
        
        return setup_path
    
    def compile_to_so(self, script_path, output_name=None, optimize=3, verbose=False, 
                     keep_temp=False, platform_specific=False):
        """Compile Python script to .so"""
        
        print(f"\n🔐 PYSOBuilder v{self.version}")
        print("=" * 50)
        
        # Check if script exists
        if not Path(script_path).exists():
            print(f"❌ Error: Script '{script_path}' not found!")
            return False
        
        print(f"📄 Input: {script_path}")
        print(f"🐍 Python: {sys.version.split()[0]}")
        print(f"💻 Platform: {self.detect_platform()}")
        print("=" * 50)
        
        # Check dependencies
        print("\n📦 Checking dependencies...")
        self.check_dependencies()
        
        # Create setup file
        print("\n🔧 Creating build configuration...")
        setup_path = self.create_setup_file(script_path, output_name, optimize, verbose)
        
        # Build
        print("\n🔨 Compiling...")
        try:
            # Run the build
            result = subprocess.run(
                [sys.executable, str(setup_path), "build_ext", "--inplace"],
                capture_output=True,
                text=True
            )
            
            if verbose:
                print(result.stdout)
                if result.stderr:
                    print(result.stderr)
            
            # Cleanup setup file
            if not keep_temp:
                if setup_path.exists():
                    setup_path.unlink()
            
            # Find the generated .so file
            so_files = list(Path('.').glob(f"{Path(script_path).stem}*.so"))
            if not so_files:
                so_files = list(Path('.').glob("*.so"))
            
            if so_files:
                so_file = so_files[0]
                
                # Rename to standard format
                if platform_specific:
                    platform_tag = self.detect_platform()
                    final_name = f"{Path(script_path).stem}.cpython-{self.python_version}-{platform_tag}.so"
                else:
                    final_name = f"{Path(script_path).stem}.cpython-{self.python_version}.so"
                
                # Move and rename
                shutil.move(str(so_file), final_name)
                
                # Get file size
                size = Path(final_name).stat().st_size
                size_kb = size / 1024
                size_mb = size_kb / 1024
                
                print("\n" + "=" * 50)
                print("✅ COMPILATION SUCCESSFUL!")
                print("=" * 50)
                print(f"📁 Output: {final_name}")
                print(f"📊 Size: {size_mb:.2f} MB ({size_kb:.2f} KB)")
                print(f"📏 Lines: {sum(1 for _ in open(script_path))}")
                print(f"🔢 Python: {self.python_version}")
                print(f"💻 Platform: {self.detect_platform()}")
                print("=" * 50)
                
                # Test import
                self.test_import(final_name)
                
                return final_name
            else:
                print("\n❌ Compilation failed! No .so file generated.")
                return False
                
        except Exception as e:
            print(f"\n❌ Error during compilation: {e}")
            return False
    
    def test_import(self, so_file):
        """Test if the .so file can be imported"""
        print("\n🧪 Testing import...")
        try:
            # Get the module name
            module_name = Path(so_file).stem.split('.')[0]
            
            # Add current directory to path
            sys.path.insert(0, '.')
            
            # Try to import
            module = __import__(module_name)
            
            print(f"✅ Import successful!")
            print(f"📦 Module: {module_name}")
            
            # List available functions
            functions = [attr for attr in dir(module) if not attr.startswith('_')]
            if functions:
                print(f"🔧 Functions: {', '.join(functions[:10])}")
                if len(functions) > 10:
                    print(f"   ... and {len(functions) - 10} more")
            
            return True
        except Exception as e:
            print(f"⚠️ Import failed: {e}")
            return False
    
    def batch_compile(self, scripts, output_dir="compiled", optimize=3, verbose=False):
        """Compile multiple Python scripts"""
        
        print(f"\n🔐 Batch Compilation v{self.version}")
        print("=" * 50)
        print(f"📄 Scripts: {len(scripts)} files")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        results = []
        for script in scripts:
            if not Path(script).exists():
                print(f"❌ Skipping {script}: Not found")
                continue
            
            print(f"\n📄 Compiling: {script}")
            
            # Compile
            so_file = self.compile_to_so(script, optimize=optimize, verbose=verbose)
            
            if so_file:
                # Move to output directory
                target = output_path / Path(so_file).name
                shutil.move(so_file, target)
                results.append({
                    'script': script,
                    'output': str(target),
                    'status': 'success'
                })
            else:
                results.append({
                    'script': script,
                    'output': None,
                    'status': 'failed'
                })
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 BATCH COMPILATION SUMMARY")
        print("=" * 50)
        successful = len([r for r in results if r['status'] == 'success'])
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {len(results) - successful}")
        print(f"📁 Output: {output_dir}/")
        print("=" * 50)
        
        return results
    
    def generate_report(self, results, output_file="compile_report.json"):
        """Generate compilation report"""
        
        report = {
            'timestamp': self.timestamp,
            'version': self.version,
            'python_version': self.python_version,
            'platform': self.detect_platform(),
            'results': results
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Report generated: {output_file}")
        return output_file
    
    def clean(self, keep_so=False):
        """Clean build files"""
        patterns = ['*.c', '*.cpp', '*.o', '*.pyc', '__pycache__', 'build', 'dist']
        
        if not keep_so:
            patterns.append('*.so')
            patterns.append('*.pyd')
        
        for pattern in patterns:
            for item in Path('.').glob(pattern):
                if item.is_file():
                    item.unlink()
                    print(f"🧹 Removed: {item}")
                elif item.is_dir():
                    shutil.rmtree(item)
                    print(f"🧹 Removed: {item}/")
        
        print("✅ Clean complete!")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='PYSOBuilder - Professional Python to .so Compiler',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Compile single file
  python pyso_builder.py my_script.py

  # Compile with custom output name
  python pyso_builder.py my_script.py -o mymodule

  # Compile with optimization level 3 (max)
  python pyso_builder.py my_script.py -O 3

  # Batch compile multiple files
  python pyso_builder.py file1.py file2.py file3.py -b

  # Verbose output
  python pyso_builder.py my_script.py -v

  # Keep temporary files
  python pyso_builder.py my_script.py -k

  # Generate platform-specific .so
  python pyso_builder.py my_script.py -p

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
        help='Output name for the .so file (without extension)'
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
        '-k', '--keep-temp',
        action='store_true',
        help='Keep temporary files'
    )
    
    parser.add_argument(
        '-p', '--platform-specific',
        action='store_true',
        help='Include platform info in .so filename'
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
        help='Clean all build files including .so files'
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate JSON report'
    )
    
    args = parser.parse_args()
    
    # Initialize builder
    builder = PYSOBuilder()
    
    # Handle clean commands
    if args.clean:
        builder.clean(keep_so=True)
        sys.exit(0)
    
    if args.clean_all:
        builder.clean(keep_so=False)
        sys.exit(0)
    
    # Check if scripts provided
    if not args.scripts:
        parser.print_help()
        sys.exit(1)
    
    # Check Python version
    if builder.python_version not in builder.supported_python:
        print(f"⚠️ Python {builder.python_version} is not fully tested")
        print(f"Supported versions: {', '.join(builder.supported_python)}")
    
    # Compile
    if args.batch and len(args.scripts) > 1:
        # Batch compilation
        results = builder.batch_compile(
            args.scripts,
            output_dir="compiled",
            optimize=args.optimize,
            verbose=args.verbose
        )
        
        if args.report:
            builder.generate_report(results)
    else:
        # Single file compilation
        script = args.scripts[0]
        so_file = builder.compile_to_so(
            script,
            output_name=args.output,
            optimize=args.optimize,
            verbose=args.verbose,
            keep_temp=args.keep_temp,
            platform_specific=args.platform_specific
        )
        
        if args.report and so_file:
            report = {
                'timestamp': builder.timestamp,
                'version': builder.version,
                'python_version': builder.python_version,
                'platform': builder.detect_platform(),
                'input': script,
                'output': so_file,
                'status': 'success'
            }
            builder.generate_report([report])

if __name__ == "__main__":
    main()
