#!/bin/bash
set -e

echo "🚀 Starting release process for jenkee..."

# 1. 檢查當前目錄
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run from project root."
    exit 1
fi

# 2. 清理舊的 build artifacts
echo "🧹 Cleaning old build artifacts..."
rm -rf build/ dist/ *.egg-info

# 3. 安裝 release dependencies
echo "📦 Installing release dependencies..."
pip install -e ".[release]"

# 4. 執行測試
echo "🧪 Running tests..."
pytest -v

# 5. Build distribution packages
echo "🔨 Building distribution packages..."
python -m build

# 6. 檢查 distribution
echo "🔍 Checking distribution packages..."
twine check dist/*

# 7. 顯示將要上傳的檔案
echo ""
echo "📋 Files to be uploaded:"
ls -lh dist/

# 8. 上傳到 PyPI
echo ""
read -p "Upload to PyPI? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "⬆️  Uploading to PyPI..."
    twine upload dist/*
    echo "✅ Successfully uploaded to PyPI!"
    echo ""
    echo "📦 Package URL: https://pypi.org/project/jenkee/"
    echo "📥 Install with: pip install jenkee"
else
    echo "⏸️  Upload cancelled."
    echo "   To upload manually: twine upload dist/*"
fi

echo ""
echo "✨ Release process completed!"
