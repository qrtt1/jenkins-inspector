#!/bin/bash
set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查當前目錄
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: pyproject.toml not found. Please run from project root.${NC}"
    exit 1
fi

# 取得當前版本
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo -e "${GREEN}Current version: ${CURRENT_VERSION}${NC}"

# 如果有參數就使用參數，否則提示輸入
if [ -n "$1" ]; then
    NEW_VERSION="$1"
else
    echo -e "${YELLOW}Enter new version (e.g., 0.2.2):${NC}"
    read NEW_VERSION
fi

# 驗證版號格式（簡單的語意化版本檢查）
if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}❌ Error: Invalid version format. Use semantic versioning (e.g., 0.2.2)${NC}"
    exit 1
fi

echo -e "${GREEN}New version will be: ${NEW_VERSION}${NC}"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# 更新 pyproject.toml
echo "📝 Updating pyproject.toml..."
sed -i.bak "s/^version = \".*\"/version = \"${NEW_VERSION}\"/" pyproject.toml
rm pyproject.toml.bak

# 更新 jenkins_tools/__init__.py
echo "📝 Updating jenkins_tools/__init__.py..."
sed -i.bak "s/__version__ = \".*\"/__version__ = \"${NEW_VERSION}\"/" jenkins_tools/__init__.py
rm jenkins_tools/__init__.py.bak

# 顯示變更
echo ""
echo -e "${GREEN}✅ Version updated to ${NEW_VERSION}${NC}"
echo ""
echo "Changed files:"
git diff pyproject.toml jenkins_tools/__init__.py

# 詢問是否要 commit 和 tag
echo ""
read -p "Commit and create tag v${NEW_VERSION}? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add pyproject.toml jenkins_tools/__init__.py
    git commit -m "Bump version to ${NEW_VERSION}"
    git tag -a "v${NEW_VERSION}" -m "Release version ${NEW_VERSION}"
    echo -e "${GREEN}✅ Created commit and tag v${NEW_VERSION}${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Push commit: git push origin main"
    echo "  2. Push tag: git push origin v${NEW_VERSION}"
    echo ""
    echo "Or push both at once:"
    echo "  git push origin main --tags"
else
    echo -e "${YELLOW}⏸️  Skipped commit and tag creation.${NC}"
    echo "Changes are ready but not committed."
fi

echo ""
echo -e "${GREEN}✨ Version bump completed!${NC}"
