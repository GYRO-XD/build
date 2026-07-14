#!/bin/bash
# builder.sh - Quick build script for PYSOBuilder

echo "🚀 PYSOBuilder - Python to .so Compiler"
echo "========================================"

# Check Python
if ! command -v python &> /dev/null; then
    echo "❌ Python not found! Install Python first."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Make the tool executable
chmod +x pyso_builder.py

# Create symlink
if [ ! -f "/usr/local/bin/pyso" ]; then
    echo "🔗 Creating symlink: pyso"
    ln -sf "$(pwd)/pyso_builder.py" /usr/local/bin/pyso 2>/dev/null || echo "⚠️ Run with sudo or as root to create symlink"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Usage:"
echo "  ./pyso_builder.py script.py"
echo "  python pyso_builder.py script.py -v"
echo "  pyso script.py  # After symlink creation"
echo ""
echo "Or build with:"
echo "  python pyso_builder.py your_script.py"
