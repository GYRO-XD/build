#!/usr/bin/env python3
"""
Universal PYSO Builder v4.0
Compiles Python to .so for ALL Python versions in one script
Author: GYRO-XD
"""

import os
import sys
import shutil
import subprocess
import tempfile
import json
from pathlib import Path
from datetime import datetime
import importlib.util

class UniversalSOBuilder:
    """Compile Python to .so for all Python versions"""
    
    def __init__(self):
        self.version = "4.0.0"
        self.author = "GYRO-XD"
        self.versions = ['310', '311']  # Python versions to compile for
        self.current_python = self._get_python_version()
        self.is_termux = 'TERMUX_VERSION' in os.environ
        
    def _get_python_version(self):
        """Get current Python version"""
        return f"{sys.version_info.major}{sys.version_info.minor}"
    
    def _check_dependencies(self):
        """Check and install dependencies"""
        print("📦 Checking dependencies...")
        
        deps = ['cython', 'setuptools']
        missing = []
        
        for dep in deps:
            try:
                importlib.import_module(dep)
                print(f"   ✅ {dep}")
            except ImportError:
                missing.append(dep)
                print(f"   ❌ {dep}")
        
        if missing:
            print(f"\n📦 Installing: {', '.join(missing)}")
            for dep in missing:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", dep, "--quiet"
                ])
            print("   ✅ Done!")
        
        # Termux headers
        if self.is_termux:
            python_include = f"/data/data/com.termux/files/usr/include/python3.{self.current_python[0]}"
            if not Path(python_include).exists():
                print("\n📦 Installing Python headers...")
                subprocess.check_call(["pkg", "install", "python-dev", "-y"])
        
        return True
    
    def _find_python_versions(self):
        """Find available Python versions on system"""
        available = []
        python_paths = []
        
        # Common Python locations
        if self.is_termux:
            python_paths = [
                "/data/data/com.termux/files/usr/bin/python",
                "/data/data/com.termux/files/usr/bin/python3",
            ]
            # Check for python3.10, python3.11, etc.
            for ver in ['3.10', '3.11', '3.12']:
                p = f"/data/data/com.termux/files/usr/bin/python{ver}"
                if Path(p).exists():
                    python_paths.append(p)
        else:
            python_paths = [
                "python3.10", "python3.11", "python3.12",
                "/usr/bin/python3.10", "/usr/bin/python3.11",
                "/usr/local/bin/python3.10", "/usr/local/bin/python3.11"
            ]
        
        for p in python_paths:
            try:
                result = subprocess.run(
                    [p, "-c", "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')"],
                    capture_output=True, text=True, timeout=2
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    if version in self.versions:
                        available.append({
                            'path': p,
                            'version': version,
                            'display': f"Python {version[0]}.{version[1]}"
                        })
            except:
                pass
        
        return available
    
    def _create_setup_code(self, script_name, base_name, optimize=3):
        """Generate setup.py code"""
        return f'''from setuptools import setup
from Cython.Build import cythonize
import os

# Termux specific
if 'TERMUX_VERSION' in os.environ:
    os.environ['CFLAGS'] = '-I/data/data/com.termux/files/usr/include/python3.{self.current_python[0]}'
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
    
    def _compile_with_python(self, python_path, script_path, base_name, optimize=3, verbose=False):
        """Compile using specific Python version"""
        print(f"\n🔨 Compiling with {python_path}...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            
            # Copy script
            temp_script = temp_dir / script_path.name
            shutil.copy2(script_path, temp_script)
            
            # Create setup.py
            setup_file = temp_dir / "setup.py"
            setup_file.write_text(self._create_setup_code(script_path.name, base_name, optimize))
            
            # Get version
            result = subprocess.run(
                [python_path, "-c", "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')"],
                capture_output=True, text=True
            )
            version = result.stdout.strip()
            
            # Build
            env = os.environ.copy()
            if self.is_termux:
                env['CC'] = 'clang'
                env['CXX'] = 'clang++'
            
            result = subprocess.run(
                [python_path, str(setup_file), "build_ext", "--inplace"],
                capture_output=True,
                text=True,
                env=env,
                cwd=str(temp_dir)
            )
            
            if verbose:
                if result.stdout:
                    print(result.stdout)
                if result.stderr and "error" in result.stderr.lower():
                    print(result.stderr)
            
            # Find .so file
            so_files = list(temp_dir.glob("*.so"))
            if not so_files:
                print(f"   ❌ Compilation failed for Python {version}")
                if result.stderr:
                    print(f"   Error: {result.stderr[:200]}")
                return None
            
            # Copy .so file
            so_file = so_files[0]
            final_name = f"{base_name}.cpython-{version}.so"
            final_path = Path.cwd() / final_name
            shutil.copy2(so_file, final_path)
            
            print(f"   ✅ Compiled: {final_name}")
            return final_name
    
    def compile_universal(self, script_path, output_name=None, optimize=3, verbose=False):
        """Compile for ALL Python versions"""
        
        print(f"\n🔐 Universal PYSO Builder v{self.version}")
        print("=" * 60)
        print(f"📄 Script: {script_path}")
        print(f"🎯 Targets: Python {', '.join(self.versions)}")
        print("=" * 60)
        
        # Validate
        script_path = Path(script_path)
        if not script_path.exists():
            print(f"❌ Error: '{script_path}' not found!")
            return None
        
        # Check dependencies
        print()
        self._check_dependencies()
        
        # Set base name
        base_name = script_path.stem if output_name is None else output_name
        
        # Find available Python versions
        print("\n🔍 Finding Python versions...")
        python_versions = self._find_python_versions()
        
        if not python_versions:
            print("   ⚠️ No other Python versions found, using current")
            python_versions = [{
                'path': sys.executable,
                'version': self.current_python,
                'display': f"Python {self.current_python[0]}.{self.current_python[1]}"
            }]
        
        # Filter to target versions
        target_versions = [v for v in python_versions if v['version'] in self.versions]
        
        if not target_versions:
            print(f"   ⚠️ No target versions found. Available: {[v['version'] for v in python_versions]}")
            print("   Using current Python only")
            target_versions = [{
                'path': sys.executable,
                'version': self.current_python,
                'display': f"Python {self.current_python[0]}.{self.current_python[1]}"
            }]
        
        print(f"   ✅ Found {len(target_versions)} versions")
        for v in target_versions:
            print(f"      - {v['display']}")
        
        # Compile for each version
        print("\n" + "=" * 60)
        print("🔨 Compiling for all versions...")
        print("=" * 60)
        
        results = {}
        for python_info in target_versions:
            version = python_info['version']
            python_path = python_info['path']
            
            so_file = self._compile_with_python(
                python_path, script_path, base_name, optimize, verbose
            )
            
            if so_file:
                results[version] = {
                    'file': str(so_file),
                    'version': version,
                    'status': 'success'
                }
            else:
                results[version] = {
                    'file': None,
                    'version': version,
                    'status': 'failed'
                }
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 COMPILATION SUMMARY")
        print("=" * 60)
        
        success = sum(1 for r in results.values() if r['status'] == 'success')
        print(f"✅ Success: {success}")
        print(f"❌ Failed: {len(results) - success}")
        print()
        
        for version, result in results.items():
            status = "✅" if result['status'] == 'success' else "❌"
            file_info = result['file'] if result['file'] else "Failed"
            print(f"   {status} Python {version[0]}.{version[1]}: {file_info}")
        
        print("=" * 60)
        
        # Generate report
        self._generate_report(results, script_path)
        
        return results
    
    def _generate_report(self, results, script_path):
        """Generate compilation report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'version': self.version,
            'author': self.author,
            'script': str(script_path),
            'results': results
        }
        
        report_file = Path("compile_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Report saved: {report_file}")
    
    def clean(self):
        """Clean build files"""
        print("🧹 Cleaning...")
        patterns = ['*.so', '*.c', '*.cpp', '*.pyc', '__pycache__', 'build', 'dist']
        for pattern in patterns:
            for item in Path('.').glob(pattern):
                if item.is_file():
                    item.unlink()
                    print(f"   Removed: {item}")
                elif item.is_dir():
                    shutil.rmtree(item)
                    print(f"   Removed: {item}/")
        print("✅ Clean complete!")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Universal PYSO Builder - Compile for all Python versions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Compile for all Python versions
  python universal_builder.py gyro_secure.py

  # Verbose mode
  python universal_builder.py gyro_secure.py -v

  # Custom output name
  python universal_builder.py gyro_secure.py -o mymodule

  # Clean only
  python universal_builder.py --clean
        '''
    )
    
    parser.add_argument(
        'script',
        nargs='?',
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
        '--clean',
        action='store_true',
        help='Clean build files'
    )
    
    args = parser.parse_args()
    
    builder = UniversalSOBuilder()
    
    if args.clean:
        builder.clean()
        return
    
    if not args.script:
        parser.print_help()
        return
    
    builder.compile_universal(
        args.script,
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
        print(f"\n❌ Error: {e}")
        sys.exit(1)
