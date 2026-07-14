#!/bin/bash
# build_so.sh - Build GYRO-Secure to .so

echo "🔐 Building GYRO-Secure to .so..."

# Check Python version
PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')")
echo "🐍 Python version: $PYTHON_VERSION"

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install cython setuptools

# Create setup.py
cat > setup.py << 'EOF'
from setuptools import setup
from Cython.Build import cythonize

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
rm -rf build
rm setup.py

# Rename .so file
SO_FILE=$(ls gyro_secure*.so 2>/dev/null | head -1)
if [ -n "$SO_FILE" ]; then
    FINAL_NAME="gyro_secure.cpython-${PYTHON_VERSION}.so"
    mv "$SO_FILE" "$FINAL_NAME"
    echo "✅ Success! Created: $FINAL_NAME"
    echo "📁 Size: $(du -h $FINAL_NAME | cut -f1)"
    
    # Create __init__.py
    echo 'from .gyro_secure import *' > __init__.py
    echo '__version__ = "1.0.0"' >> __init__.py
    
    # Test
    echo "🧪 Testing import..."
    python -c "import gyro_secure; print('✅ Import successful!')" 2>/dev/null && echo "🎉 Ready to use!" || echo "⚠️ Test failed"
else
    echo "❌ Build failed!"
    exit 1
fi
EOF
