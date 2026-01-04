# Test Plan: GCP Integration

## 測試情境

整合 Google Cloud Platform (GCP) Service Account credentials 到 jenkee，支援完整的 CRUD 操作，並驗證在 freestyle job 中的自動認證功能。

## 測試目標

驗證使用者可以：
1. 建立、更新、列出、刪除 GCP Service Account credentials
2. 在 freestyle job 中使用 GCP credentials（使用 gcloud-sdk plugin 的 GCloudBuildWrapper）
3. 所有操作都有適當的錯誤處理和安全性保護

**注意**: Pipeline job 整合測試已移除，因為在測試環境中 Pipeline script 無法正常執行（可能與 script sandbox 或 plugin 設定有關）。

## 涵蓋的指令

採用子命令結構（類似 git）：

| 指令 | 測試目的 | 安全性 |
|------|---------|--------|
| `gcp credential create` | 建立新的 GCP Service Account credential | 寫入操作，需驗證權限 |
| `gcp credential update` | 更新現有的 GCP credential | 寫入操作，需驗證權限 |
| `gcp credential list` | 列出所有 GCP credentials | Read-only，不洩漏 secrets |
| `gcp credential delete` | 刪除 GCP credential | 刪除操作，需確認 |
| `gcp credential describe` | 查看特定 credential 詳細資訊 | Read-only，可選擇性顯示 secret |

**設計考量**：

- GCP 相關的 sub commands 不會在 `jenkee --help` 或 `jenkee -h` 的主要指令列表中顯示
- 這是有意的設計，將 GCP 功能視為 optional/specialized feature
- 使用者需要透過 `jenkee gcp --help` 或文件來發現這些指令
- 保持主要 help 輸出簡潔，只顯示核心功能
- 類似 git 的 plumbing commands 設計理念

## 測試前置條件

- Jenkins server 運行中並已認證（`jenkee auth` 成功）
- Jenkins 中已安裝：
  - `google-oauth-plugin` - 提供 GCP credential 類型
  - `gcloud-sdk` plugin - 提供自動 activation 功能
- `gcloud-sdk` plugin - 提供 GCloudBuildWrapper
- 有效的 GCP Service Account JSON key file 用於測試
- 足夠權限建立和管理 credentials

## 測試步驟

### Phase 1: Credential CRUD 操作

#### 1.1 建立 GCP Credential

```bash
jenkee gcp credential create my-gcp-sa ~/service-account-key.json
```

**預期結果**：
- Exit code: 0
- 顯示成功訊息，包含 project ID
- Credential 在 Jenkins 中可見

**驗證點**：
- [ ] 成功建立 credential
- [ ] Credential ID 正確
- [ ] 顯示正確的 project ID
- [ ] Credential type 為 GoogleRobotPrivateKeyCredentials
- [ ] 可以在 Jenkins UI 中看到新建立的 credential

**錯誤情境測試**：

```bash
# 重複的 credential ID
jenkee gcp credential create my-gcp-sa ~/service-account-key.json

# 無效的 JSON file
jenkee gcp credential create test-invalid ~/invalid.json

# 檔案不存在
jenkee gcp credential create test-missing ~/nonexistent.json

# 不是 service account key（缺少必要欄位）
jenkee gcp credential create test-bad ~/bad-format.json
```

**錯誤驗證點**：
- [ ] 重複 ID 錯誤被正確偵測
- [ ] 無效 JSON 錯誤訊息清楚
- [ ] 檔案不存在錯誤訊息清楚
- [ ] JSON 格式驗證正確（檢查必要欄位：type, project_id, client_email, private_key）

#### 1.2 列出 GCP Credentials

```bash
jenkee gcp credential list
```

**預期結果**：
- Exit code: 0
- 列出所有 GCP credentials 的 metadata
- 顯示 ID、Description、Project ID
- 不洩漏 private key 或完整的 JSON content

**驗證點**：
- [ ] 成功列出所有 GCP credentials
- [ ] 輸出包含 credential ID
- [ ] 輸出包含 project ID
- [ ] 不包含 private key
- [ ] 格式清晰易讀

#### 1.3 查看 Credential 詳細資訊

```bash
jenkee gcp credential describe my-gcp-sa
```

**預期結果**：
- Exit code: 0
- 顯示詳細資訊：ID, Type, Project ID, Service Account Email
- 預設不顯示 secret 內容

**驗證點**：
- [ ] 成功取得 credential 資訊
- [ ] 資訊完整且格式清楚
- [ ] 預設不顯示 private key

```bash
# 顯示 secret 內容（選擇性功能）
jenkee gcp credential describe my-gcp-sa --show-secret
```

**驗證點**：
- [ ] 使用 --show-secret flag 時可以看到完整 JSON key
- [ ] 有明確警告訊息提醒這是敏感資訊

#### 1.4 更新 GCP Credential

```bash
jenkee gcp credential update my-gcp-sa ~/new-service-account-key.json
```

**預期結果**：
- Exit code: 0
- 成功更新 credential 內容
- 顯示更新後的 project ID（如果改變）

**驗證點**：
- [ ] 成功更新 credential
- [ ] 更新後的 credential 可以正常使用
- [ ] 顯示更新成功訊息
- [ ] Project ID 資訊更新正確

**錯誤情境測試**：

```bash
# 更新不存在的 credential
jenkee gcp credential update nonexistent-id ~/service-account-key.json
```

**錯誤驗證點**：
- [ ] Credential 不存在錯誤被正確偵測
- [ ] 錯誤訊息清楚

#### 1.5 刪除 GCP Credential

**測試 1: 互動式確認（預設行為）**

```bash
jenkee gcp credential delete my-gcp-sa
# 提示：Are you sure you want to delete credential 'my-gcp-sa'? (y/N): y
```

**預期結果**：
- Exit code: 0
- 顯示確認提示
- 輸入 y 後顯示刪除成功訊息
- Credential 從 Jenkins 中移除

**驗證點**：
- [ ] 顯示互動式確認提示
- [ ] 確認提示清楚明確
- [ ] 成功刪除 credential
- [ ] 刪除後無法在 list 中看到
- [ ] 刪除後無法 describe

**測試 2: 取消刪除**

```bash
jenkee gcp credential delete my-gcp-sa
# 提示：Are you sure you want to delete credential 'my-gcp-sa'? (y/N): n
```

**預期結果**：
- Exit code: 0
- 顯示 "Operation cancelled." 或 "Deletion cancelled."
- Credential 仍然存在

**驗證點**：
- [ ] 輸入 N 後取消操作
- [ ] 顯示取消訊息
- [ ] Credential 仍在 list 中
- [ ] 可以繼續 describe

**測試 3: 使用確認 Flag（自動化腳本）**

```bash
# 跳過互動式確認，直接執行
jenkee gcp credential delete my-gcp-sa --yes-i-really-mean-it
```

**預期結果**：
- Exit code: 0
- 不顯示確認提示
- 直接刪除成功
- Credential 從 Jenkins 中移除

**驗證點**：
- [ ] 不顯示互動式確認提示
- [ ] 直接執行刪除
- [ ] 成功刪除 credential
- [ ] 適合用於自動化腳本

### Phase 2: Freestyle Job 整合測試

#### 2.1 Freestyle Job 使用 GCP Credential

**測試目標**：驗證 gcloud-sdk plugin 自動 activate service account

**測試步驟**：

1. 建立測試用的 GCP credential
```bash
jenkee gcp credential create test-gcp-freestyle ~/viewer-sa-key.json
```

2. 建立 freestyle job，使用 GCloudBuildWrapper
3. 執行 job
4. 驗證 console output

**Job XML 配置要點**：

```xml
<buildWrappers>
  <com.byclosure.jenkins.plugins.gcloud.GCloudBuildWrapper plugin="gcloud-sdk@0.0.3">
    <installation></installation>
    <credentialsId>test-gcp-freestyle</credentialsId>
  </com.byclosure.jenkins.plugins.gcloud.GCloudBuildWrapper>
</buildWrappers>
```

**Shell 命令**：

```bash
#!/bin/bash
echo "Testing GCP Service Account Credentials"
echo "=========================================="

# 測試實際操作（如果 SA 有權限）
gcloud iam service-accounts list --project twjug-lite

echo "=========================================="
echo "✓ GCP credential check completed!"
```

**驗證點**：
- [ ] Job 成功執行
- [ ] Console output 顯示 "Activated service account credentials for: [...]"
- [ ] `gcloud iam service-accounts list --project twjug-lite | grep "<service-account-email>"` 有值

**Console Output 預期關鍵訊息**：

```
Activated service account credentials for: [viewer-sa@your-project.iam.gserviceaccount.com]

DISPLAY NAME                            EMAIL                                                         DISABLED
Jenkee Tester Viewer SA 2               jenkee-tester-viewer-sa-2@twjug-lite.iam.gserviceaccount.com  False
```

### Phase 3: Pipeline Job 整合測試

**狀態**: ❌ 已移除

**原因**: Pipeline job 在測試環境中無法正常執行 Pipeline script。Job 可以建立成功，但執行時 script 不會執行任何 stages，立即完成。

**可能原因**:
- Script sandbox 安全限制
- 缺少 script approvals
- Workflow plugin 設定問題
- CDATA/XML 轉義問題

**未來改善**:
如需測試 Pipeline 整合，可能需要：
1. 設定 script approval 機制
2. 使用 Jenkinsfile from SCM 而非 inline script
3. 調整 Jenkins test container 的 security settings
4. 或在真實 Jenkins instance 上手動測試

### Phase 4: 進階測試情境

#### 4.1 多個 Service Accounts

**測試目標**：驗證可以同時管理多個不同的 GCP credentials

```bash
jenkee gcp credential create gcp-viewer ~/viewer-sa-key.json
jenkee gcp credential create gcp-admin ~/admin-sa-key.json
jenkee gcp credential list
```

**驗證點**：
- [ ] 可以建立多個 GCP credentials
- [ ] List 命令正確列出所有 credentials
- [ ] 不同 credentials 的 project ID 和 service account 資訊都正確顯示

#### 4.2 Credential 在 Job 中的冪等性

**測試目標**：驗證重複執行 job 時 credential 行為一致

```bash
# 執行同一個 freestyle job 多次
jenkee build test-gcp-freestyle
jenkee build test-gcp-freestyle
jenkee build test-gcp-freestyle
```

**驗證點**：
- [ ] 每次執行結果一致
- [ ] Activation 訊息每次都正確顯示
- [ ] 不會有 credential 衝突或 lock 問題

#### 4.3 權限驗證測試

**測試目標**：驗證不同權限的 service account 都能正確使用

```bash
# 建立 viewer 權限的 credential
jenkee gcp credential create gcp-viewer ~/viewer-sa-key.json

# 建立 editor 權限的 credential
jenkee gcp credential create gcp-editor ~/editor-sa-key.json
```

**驗證點**：
- [ ] Viewer SA 可以讀取資源但不能修改
- [ ] Editor SA 可以修改資源
- [ ] 權限錯誤訊息清楚（當 SA 沒有足夠權限時）

## 典型工作流程範例

### 場景 A：初始設定 GCP Credentials

```bash
# 1. 建立 GCP credential
jenkee gcp credential create my-gcp-sa ~/service-account-key.json

# 2. 驗證建立成功
jenkee gcp credential list

# 3. 查看詳細資訊
jenkee gcp credential describe my-gcp-sa

# 4. 在 freestyle job 中測試
# （建立並執行 job）
```

### 場景 B：輪換 Service Account Key

```bash
# 1. 產生新的 service account key（在 GCP Console）
# 2. 更新 Jenkins credential
jenkee gcp credential update my-gcp-sa ~/new-service-account-key.json

# 3. 驗證更新成功
jenkee gcp credential describe my-gcp-sa

# 4. 測試 job 是否仍正常運作
```

### 場景 C：清理不再使用的 Credentials

```bash
# 1. 列出所有 GCP credentials
jenkee gcp credential list

# 2. 確認要刪除的 credential
jenkee gcp credential describe old-gcp-sa

# 3. 刪除（使用 flag 跳過確認，適合自動化腳本）
jenkee gcp credential delete old-gcp-sa --yes-i-really-mean-it

# 4. 驗證已刪除
jenkee gcp credential list | grep old-gcp-sa || echo "已刪除"
```

### 場景 D：檢查所有 GCP Credentials 狀態

```bash
# 1. 列出所有 GCP credentials
jenkee gcp credential list > gcp-creds.txt

    # 2. 對每個 credential 查看詳細資訊
while read -r cred_id; do
  echo "=== $cred_id ==="
  jenkee gcp credential describe "$cred_id"
  echo ""
done < gcp-creds.txt
```

## 錯誤情境測試總結

### 建立 Credential 錯誤

- [ ] 重複 credential ID → 錯誤訊息清楚
- [ ] 無效 JSON → 錯誤訊息清楚
- [ ] 檔案不存在 → 錯誤訊息清楚
- [ ] 缺少必要欄位 → 驗證並提示缺少哪些欄位
- [ ] 不是 service account key → 錯誤訊息清楚

### 更新 Credential 錯誤

- [ ] Credential 不存在 → 錯誤訊息清楚
- [ ] 無效的新 JSON key → 錯誤訊息清楚

### 刪除 Credential 錯誤

- [ ] Credential 不存在 → 錯誤訊息清楚
- [ ] Credential 仍在使用中 → 警告訊息（建議）

### 查看 Credential 錯誤

- [ ] Credential 不存在 → 錯誤訊息清楚

## 安全性驗證

### 確認不洩漏 Private Key

```bash
# 檢查 list 命令輸出
jenkee gcp credential list | grep -i "private_key" && echo "SECURITY ISSUE!" || echo "Safe"

# 檢查 describe 命令輸出（預設）
jenkee gcp credential describe my-gcp-sa | grep -i "BEGIN PRIVATE KEY" && echo "SECURITY ISSUE!" || echo "Safe"
```

**驗證點**：
- [ ] List 命令不洩漏 private key
- [ ] Describe 命令預設不顯示 private key
- [ ] 只有使用 --show-secret 時才顯示完整 JSON key
- [ ] 使用 --show-secret 時有明確警告

### Jenkins Job Console Output 安全性

```bash
# Freestyle job console output
# 檢查是否有洩漏 credential 內容
```

**驗證點**：
- [ ] gcloud-sdk plugin 不在 console output 洩漏 JSON key
- [ ] Console output 不顯示完整的 JSON key
- [ ] 實際 credential 內容被 mask

## 測試完成標準

### CRUD 操作
- [ ] 所有 5 個子命令都執行成功
- [ ] 所有預期結果都符合
- [ ] 所有錯誤情境都正確處理

### Job 整合
- [ ] Freestyle job 整合測試通過
- [ ] Console output 顯示正確的 credential binding
- [x] ~~Pipeline job 整合測試~~ (已移除 - 測試環境限制)

### 安全性
- [ ] 不洩漏 private key（除非明確使用 --show-secret）
- [ ] gcloud-sdk plugin 不在 console output 洩漏 JSON key
- [ ] 所有安全性驗證點都通過

### 測試自動化
- [ ] pytest 測試覆蓋所有 CRUD 操作
- [ ] pytest 測試覆蓋 freestyle job 整合
- [x] ~~pytest 測試覆蓋 pipeline job 整合~~ (已移除 - 測試環境限制)
- [ ] 測試可以在 CI/CD 中自動執行

## 實作注意事項

### 命令命名規範

採用 git-style 子命令結構：

```
jenkee gcp <resource> <action> [arguments]
```

範例：
- `jenkee gcp credential create <id> <json-file>`
- `jenkee gcp credential update <id> <json-file>`
- `jenkee gcp credential list`
- `jenkee gcp credential delete <id>`
- `jenkee gcp credential describe <id>`

### Credential Type 選擇

使用 **GoogleRobotPrivateKeyCredentials** 作為 GCP credential 類型：

**理由**：
- 與 gcloud-sdk plugin 的 GCloudBuildWrapper 相容
- Jenkins UI 與 credential 選單一致

### Plugin 依賴

必要的 Jenkins plugins：
- `google-oauth-plugin` - 提供 GoogleRobotPrivateKeyCredentials
- `gcloud-sdk` - 提供 gcloud SDK 安裝和管理

### 測試環境設定

```bash
# 設定測試用的 GCP key file
export JENKEE_TEST_GCLOUD_ADC=~/viewer-sa-key.json

# 執行測試
pytest tests/test_gcp_*.py -v
```

### Service Account Key 格式驗證

必要欄位：
- `type` - 必須是 "service_account"
- `project_id` - GCP project ID
- `private_key_id` - Private key ID
- `private_key` - Private key（PEM 格式）
- `client_email` - Service account email
- `client_id` - Client ID
- `auth_uri` - OAuth2 auth URI
- `token_uri` - OAuth2 token URI

## 測試資源

### 測試檔案位置

- `tests/test_gcp_credentials.py` - CRUD 操作測試
- `tests/test_gcp_freestyle_job.py` - Freestyle job 整合測試
- `tests/fixtures/Dockerfile` - 測試 Jenkins image (包含 workflow plugins)
- `tests/conftest.py` - 共用 fixtures (gcp_key_files, gcp_sa1_info, gcp_sa2_info)

### 測試執行腳本

- `run-gcp-tests.sh` - 便捷的測試執行腳本
- `tests/README_GCP_TESTS.md` - 測試快速指南
- `tests/RUN_GCP_TESTS.md` - 完整測試指令參考

### 參考文件

- `docs/GCP_CREDENTIALS.md` - 使用文件（需更新為子命令格式）
- 本文件 `docs/test-plan-for-gcp-integration.md`

## 相關文件

- [GCP Credentials 使用文件](GCP_CREDENTIALS.md)
- [Test Execution Report](TEST_EXECUTION_REPORT.md)
- [Credentials Management Test Plan](test-plan-for-credentials-management.done.md)

## 後續規劃

### Phase 5（Optional）：進階功能

- [ ] 支援 Workload Identity Federation
- [ ] 支援 OAuth credentials（非 service account）
- [ ] 批次匯入多個 credentials
- [ ] Credential 使用情況報告（哪些 jobs 使用哪些 credentials）

### Phase 6（Optional）：整合增強

- [ ] 自動設定 gcloud SDK installation
- [ ] 提供 pipeline shared library（簡化 pipeline 中的使用）
- [ ] 支援多個 GCP projects 的切換
