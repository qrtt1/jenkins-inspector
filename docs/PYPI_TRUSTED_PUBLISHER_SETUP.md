# PyPI Trusted Publisher 設定指南

GitHub Actions 可以透過 OpenID Connect (OIDC) 直接發布到 PyPI，不需要使用 API token。這是更安全的發布方式。

## 設定步驟

### 1. 在 PyPI 上設定 Trusted Publisher

1. 登入 PyPI: https://pypi.org
2. 進入專案管理頁面: https://pypi.org/manage/project/jenkee/
3. 點選 "Publishing" 標籤
4. 在 "Add a new pending publisher" 區域填入以下資訊：
   - **PyPI Project Name**: `jenkee`
   - **Owner**: `qrtt1` (你的 GitHub 使用者名稱)
   - **Repository name**: `jenkins-inspector`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`
5. 點選 "Add" 按鈕

### 2. 在 GitHub 上建立 Environment

1. 進入 GitHub repository: https://github.com/qrtt1/jenkins-inspector
2. 點選 "Settings" → "Environments"
3. 點選 "New environment"
4. 輸入名稱: `pypi`
5. (選用) 設定 Protection rules:
   - 可以設定只有特定分支可以部署
   - 可以要求手動審核才能發布

### 3. 測試自動發布

建立一個測試 tag 來觸發 workflow：

```bash
# 更新版本號（例如 0.2.2）
# 編輯 pyproject.toml 的 version 欄位

# 提交變更
git add pyproject.toml
git commit -m "Bump version to 0.2.2"
git push

# 建立並推送 tag
git tag v0.2.2
git push origin v0.2.2
```

### 4. 監看 Workflow 執行

1. 進入 Actions 頁面: https://github.com/qrtt1/jenkins-inspector/actions
2. 查看 "Publish to PyPI" workflow
3. 確認所有步驟都成功完成

## Workflow 流程說明

當你 push 一個 `v*.*.*` 格式的 tag 時，會自動觸發以下流程：

1. **Test Job**: 在 Python 3.10、3.11、3.12 上執行所有測試
2. **Build Job**: 建立 wheel 和 source distribution
3. **Publish Job**: 發布到 PyPI（需要 test 和 build 都成功）

## 安全性優勢

使用 Trusted Publisher 的好處：

- ✅ 不需要在 GitHub Secrets 儲存 PyPI API token
- ✅ 使用短期的 OIDC token，更安全
- ✅ PyPI 可以驗證發布來源
- ✅ 降低 credential 洩漏風險

## 疑難排解

### 發布失敗：權限錯誤

確認：
1. PyPI Trusted Publisher 設定正確
2. GitHub Environment 名稱為 `pypi`
3. Workflow 檔案路徑為 `publish.yml`

### 測試失敗

在推送 tag 前，建議先在本地執行測試：

```bash
pytest -v
```

### 手動發布

如果自動發布失敗，可以使用傳統方式手動發布：

```bash
./scripts/release.sh
```

## 參考資料

- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
