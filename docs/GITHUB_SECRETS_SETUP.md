# GitHub Secrets Setup for GCP Tests

本專案的 GCP 相關測試需要兩組 Service Account keys。這些 keys 應該設定為 GitHub repository secrets，以便在 CI/CD pipeline 中執行測試。

## Required Secrets

需要設定以下兩個 secrets：

### 1. GCP_SA1_KEY
第一組 Service Account key (SA-1)

```bash
# 取得 key 內容（本地端）
cat tests/fixtures/gcp-keys/jenkee-tester-viewer-sa-1.json
```

### 2. GCP_SA2_KEY
第二組 Service Account key (SA-2)，用於測試 key rotation

```bash
# 取得 key 內容（本地端）
cat tests/fixtures/gcp-keys/jenkee-tester-viewer-sa-2.json
```

## 如何設定 GitHub Secrets

### 方法 1: 透過 GitHub Web UI

1. 前往 repository 設定頁面
2. 點選 "Settings" → "Secrets and variables" → "Actions"
3. 點選 "New repository secret"
4. 設定第一個 secret：
   - Name: `GCP_SA1_KEY`
   - Value: 貼上完整的 SA-1 JSON key 內容
5. 點選 "Add secret"
6. 重複步驟 3-5 設定第二個 secret：
   - Name: `GCP_SA2_KEY`
   - Value: 貼上完整的 SA-2 JSON key 內容

### 方法 2: 透過 GitHub CLI

```bash
# 設定 GCP_SA1_KEY
gh secret set GCP_SA1_KEY < tests/fixtures/gcp-keys/jenkee-tester-viewer-sa-1.json

# 設定 GCP_SA2_KEY
gh secret set GCP_SA2_KEY < tests/fixtures/gcp-keys/jenkee-tester-viewer-sa-2.json
```

## 驗證設定

### 檢查 Secrets 是否已設定

```bash
gh secret list | grep GCP
```

應該看到：
```
GCP_SA1_KEY	2026-01-01T07:56:47Z
GCP_SA2_KEY	2026-01-01T07:56:53Z
```

### 驗證 GitHub Actions 執行

設定完成後，下次 push 或 pull request 時，GitHub Actions 會自動：

1. 檢查 secrets 是否存在
2. 如果存在，建立 key files 並執行 GCP 測試
3. 如果不存在，顯示 warning 並 skip GCP 相關測試

#### Secrets 正確設定時

檢查 GitHub Actions 執行 log 的 "Setup GCP test keys" step，應該看到：

```
✓ GCP test keys configured
```

然後在測試執行時會看到 GCP 相關測試執行：

```
tests/test_gcp_credentials.py::test_gcp_help PASSED
tests/test_gcp_credentials.py::test_create_gcp_credential PASSED
...
```

#### Secrets 缺少或設定錯誤時

會看到 warning：

```
::warning::GCP_SA1_KEY or GCP_SA2_KEY secrets not configured. GCP tests will be skipped.
::warning::See docs/GITHUB_SECRETS_SETUP.md for setup instructions.
```

測試會顯示 SKIPPED：

```
tests/test_gcp_credentials.py::test_gcp_help SKIPPED (GCP key files not found in CI environment...)
```

## Service Account 資訊

目前使用的 Service Accounts：

- **SA-1**: `jenkee-tester-viewer-sa-1@twjug-lite.iam.gserviceaccount.com`
  - Role: `roles/viewer`
  - Project: `twjug-lite`

- **SA-2**: `jenkee-tester-viewer-sa-2@twjug-lite.iam.gserviceaccount.com`
  - Role: `roles/viewer`
  - Project: `twjug-lite`

## 安全注意事項

1. **絕對不要**將 Service Account keys 提交到版本控制
2. **定期輪換** Service Account keys（建議每 90 天）
3. **使用最小權限原則**：測試用的 SA 只有 `roles/viewer` 權限
4. **監控使用情況**：定期檢查 GCP audit logs
5. 如果 keys 洩漏，立即：
   - 在 GCP Console 中 revoke keys
   - 在 GitHub 中刪除 secrets
   - 產生新的 keys 並重新設定

## Key Rotation

當需要輪換 keys 時：

```bash
# 1. 產生新的 keys
gcloud iam service-accounts keys create tests/fixtures/gcp-keys/jenkee-tester-viewer-sa-1.json \
    --iam-account=jenkee-tester-viewer-sa-1@twjug-lite.iam.gserviceaccount.com

gcloud iam service-accounts keys create tests/fixtures/gcp-keys/jenkee-tester-viewer-sa-2.json \
    --iam-account=jenkee-tester-viewer-sa-2@twjug-lite.iam.gserviceaccount.com

# 2. 更新 GitHub Secrets（使用方法 2）
gh secret set GCP_SA1_KEY < tests/fixtures/gcp-keys/jenkee-tester-viewer-sa-1.json
gh secret set GCP_SA2_KEY < tests/fixtures/gcp-keys/jenkee-tester-viewer-sa-2.json

# 3. 刪除舊的 keys（在 GCP Console 或使用 gcloud）
gcloud iam service-accounts keys list \
    --iam-account=jenkee-tester-viewer-sa-1@twjug-lite.iam.gserviceaccount.com

gcloud iam service-accounts keys delete <OLD_KEY_ID> \
    --iam-account=jenkee-tester-viewer-sa-1@twjug-lite.iam.gserviceaccount.com
```

## Troubleshooting

### 測試被 skip 但 secrets 已設定

檢查 secrets 內容是否正確：

```bash
# 驗證 local key file 格式
cat tests/fixtures/gcp-keys/jenkee-tester-viewer-sa-1.json | jq .

# 應該包含這些欄位：
# - type
# - project_id
# - private_key_id
# - private_key
# - client_email
```

### GitHub Actions 中看到 authentication 錯誤

1. 確認 secrets 沒有多餘的空白或換行
2. 重新設定 secrets
3. 檢查 Service Account 是否仍然有效且未被 disable

## 相關文件

- [GCP Credentials Management](GCP_CREDENTIALS.md)
- [Test Plan for GCP Integration](test-plan-for-gcp-integration.md)
- [GitHub Actions Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
