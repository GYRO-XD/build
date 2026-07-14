#!/usr/bin/env python3
"""
Universal PYSO Builder v4.1
Fixed for Termux - No python-dev package needed
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
    """Compile Python to .so for all versions - Fixed for Termux"""
    
    def __init__(self):
        self.version = "4.1.0"
        self.author = "GYRO-XD"
        self.versions = ['310', '311']
        self.current_python = self._get_python_version()
        self.is_termux = 'TERMUX_VERSION' in os.environ
        
    def _get_python_version(self):
        return f"{sys.version_info.major}{sys.version_info.minor}"
    
    def _check_dependencies(self):
        """Check and install dependencies - Fixed for Termux"""
        print("📦 Checking dependencies...")
        
        # Install Python packages
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
        
        # For Termux - No python-dev needed!
        if self.is_termux:
            print("   ✅ Termux detected - headers included in Python package")
            
            # Check if clang is installed (needed for compilation)
            try:
                subprocess.check_call(["clang", "--version"], 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.DEVNULL)
                print("   ✅ Clang found")
            except:
                print("   📦 Installing clang...")
                subprocess.check_call(["pkg", "install", "clang", "-y"])
        
        return True
    
    def _find_python_versions(self):
        """Find available Python versions - Fixed for Termux"""
        available = []
        
        if self.is_termux:
            # Termux only has one Python version
            python_path = sys.executable
            version = self.current_python
            if version in self.versions:
                available.append({
                    'path': python_path,
                    'version': version,
                    'display': f"Python {version[0]}.{version[1]}"
                })
            
            # Check if other versions are installed via symlinks
            for ver in ['310', '311']:
                if ver != version:
                    # Try to find python3.10 or python3.11
                    for p in [
                        f"/data/data/com.termux/files/usr/bin/python3.{ver[0]}.{ver[1]}",
                        f"/data/data/com.termux/files/usr/bin/python{ver[0]}.{ver[1]}"
                    ]:
                        if Path(p).exists():
                            available.append({
                                'path': p,
                                'version': ver,
                                'display': f"Python {ver[0]}.{ver[1]}"
                            })
                            break
        else:
            # Linux/Other systems
            for ver in ['310', '311']:
                for p in [
                    f"python3.{ver[0]}.{ver[1]}",
                    f"python{ver[0]}.{ver[1]}",
                    f"/usr/bin/python3.{ver[0]}.{ver[1]}",
                    f"/usr/local/bin/python3.{ver[0]}.{ver[1]}"
                ]:
                    try:
                        result = subprocess.run(
                            [p, "-c", "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')"],
                            capture_output=True, text=True, timeout=2
                        )
                        if result.returncode == 0 and result.stdout.strip() == ver:
                            available.append({
                                'path': p,
                                'version': ver,
                                'display': f"Python {ver[0]}.{ver[1]}"
                            })
                            break
                    except:
                        pass
        
        return available
    
    def _create_setup_code(self, script_name, base_name, optimize=3):
        """Generate setup.py code - Fixed for Termux"""
        return f'''from setuptools import setup
from Cython.Build import cythonize
import os
import sys

# Set compiler flags for Termux
if 'TERMUX_VERSION' in os.environ:
    # Termux uses clang and includes headers in the main package
    os.environ['CC'] = 'clang'
    os.environ['CXX'] = 'clang++'
    
    # Python headers location in Termux
    python_include = f"/data/data/com.termux/files/usr/include/python{{sys.version_info.major}}.{{sys.version_info.minor}}"
    if os.path.exists(python_include):
        os.environ['CFLAGS'] = f"-I{{python_include}}"
    
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
        """Compile using specific Python version - Fixed for Termux"""
        print(f"\n🔨 Compiling with {python_path}...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            
            temp_script = temp_dir / script_path.name
            shutil.copy2(script_path, temp_script)
            
            setup_file = temp_dir / "setup.py"
            setup_file.write_text(self._create_setup_code(script_path.name, base_name, optimize))
            
            result = subprocess.run(
                [python_path, "-c", "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')"],
                capture_output=True, text=True
            )
            version = result.stdout.strip()
            
            env = os.environ.copy()
            if self.is_termux:
                env['CC'] = 'clang'
                env['CXX'] = 'clang++'
                # Fix for Termux headers
                python_include = f"/data/data/com.termux/files/usr/include/python{version[0]}.{version[1]}"
                if os.path.exists(python_include):
                    env['CFLAGS'] = f"-I{python_include}"
                env['LDFLAGS'] = '-L/data/data/com.termux/files/usr/lib'
            
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
            
            so_files = list(temp_dir.glob("*.so"))
            if not so_files:
                print(f"   ❌ Compilation failed for Python {version}")
                if result.stderr:
                    print(f"   Error: {result.stderr[:200]}")
                return None
            
            so_file = so_files[0]
            final_name = f"{base_name}.cpython-{version}.so"
            final_path = Path.cwd() / final_name
            shutil.copy2(so_file, final_path)
            
            print(f"   ✅ Compiled: {final_name}")
            return final_name
    
    def compile_universal(self, script_path, output_name=None, optimize=3, verbose=False):
        """Main compile function"""
        
        print(f"\n🔐 Universal PYSO Builder v{self.version}")
        print("=" * 60)
        print(f"📄 Script: {script_path}")
        print(f"🎯 Targets: Python {', '.join(self.versions)}")
        if self.is_termux:
            print(f"💻 Platform: Termux (using clang)")
        print("=" * 60)
        
        script_path = Path(script_path)
        if not script_path.exists():
            print(f"❌ Error: '{script_path}' not found!")
            return None
        
        print()
        self._check_dependencies()
        
        base_name = script_path.stem if output_name is None else output_name
        
        print("\n🔍 Finding Python versions...")
        python_versions = self._find_python_versions()
        
        if not python_versions:
            print("   ⚠️ No other Python versions found, using current")
            python_versions = [{
                'path': sys.executable,
                'version': self.current_python,
                'display': f"Python {self.current_python[0]}.{self.current_python[1]}"
            }]
        
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
        
        # Test imports
        if success > 0:
            print("\n🧪 Testing imports...")
            for version, result in results.items():
                if result['status'] == 'success':
                    try:
                        sys.path.insert(0, '.')
                        module_name = Path(result['file']).stem.split('.')[0]
                        __import__(module_name)
                        print(f"   ✅ Python {version[0]}.{version[1]}: Import successful!")
                    except Exception as e:
                        print(f"   ⚠️ Python {version[0]}.{version[1]}: Import error: {e}")
        
        self._generate_report(results, script_path)
        return results
    
    def _generate_report(self, results, script_path):
        """Generate compilation report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'version': self.version,
            'author': self.author,
            'platform': 'Termux' if self.is_termux else 'Linux',
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
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Universal PYSO Builder - Fixed for Termux',
        formatter_class=argparse.RawDescriptionHelpFormatter
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
