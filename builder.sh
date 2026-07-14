#!/bin/bash
# build_so.sh - Build GYRO-Secure to .so
# Maintains compatibility with your GitHub naming

echo "🔐 Building GYRO-Secure to .so..."

# Check Python version
PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')")
echo "🐍 Python version: 3.${PYTHON_VERSION}"

# Check if we're in the right directory
if [ ! -f "gyro_secure.py" ]; then
    echo "❌ gyro_secure.py not found!"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install cython setuptools --quiet

# Create setup.py
cat > setup.py << 'EOF'
from setuptools import setup
from Cython.Build import cythonize
import sys
import os

# Termux specific
if 'TERMUX_VERSION' in os.environ:
    os.environ['CFLAGS'] = '-I/data/data/com.termux/files/usr/include/python3.10'
    os.environ['LDFLAGS'] = '-L/data/data/com.termux/files/usr/lib'

setup(
    name="gyro_secure",
    ext_modules=cythonize(
        "gyro_secure.py",
        compiler_directives={
            'language_level': 3,
            'boundscheck': False,
            'wraparound': False,
            'initializedcheck': False,
            'cdivision': True,
        }
    ),
)
EOF

# Build
echo "🔨 Compiling..."
python setup.py build_ext --inplace

# Cleanup
rm -rf build setup.py

# Rename .so file to match your GitHub naming
SO_FILE=$(ls gyro_secure*.so 2>/dev/null | head -1)
if [ -n "$SO_FILE" ]; then
    # Use your existing naming format
    FINAL_NAME="gyro_secure.cpython-${PYTHON_VERSION}.so"
    mv "$SO_FILE" "$FINAL_NAME"
    
    echo ""
    echo "✅ COMPILATION SUCCESSFUL!"
    echo "📁 Output: $FINAL_NAME"
    echo "📊 Size: $(du -h $FINAL_NAME | cut -f1)"
    
    # Test import
    echo ""
    echo "🧪 Testing import..."
    python -c "import gyro_secure; print('✅ Import successful!')" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "🎉 Ready to use!"
    else
        echo "⚠️ Import test failed, but .so file exists"
    fi
else
    echo "❌ Compilation failed!"
    exit 1
fi
