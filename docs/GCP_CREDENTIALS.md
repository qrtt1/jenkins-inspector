# GCP Credentials 支援

jenkee 支援完整的 GCP Service Account credentials 管理，採用 git-style subcommand 結構。

## 功能特色

- 完整的 CRUD 操作：create, list, describe, update, delete
- 從 JSON key file 建立 GCP Service Account credential
- 在 Jenkins job 中使用（透過 credentials-binding plugin）
- 自動驗證 service account key 格式
- 安全的 secret 管理（預設不顯示敏感資訊）
- 使用 GoogleRobotPrivateKeyCredentials 儲存 GCP service account JSON key

## 前置需求

Jenkins 需要安裝以下 plugins：
- `credentials-binding` plugin - 提供 credential binding 功能
- `google-oauth-plugin` - 提供 GoogleRobotPrivateKeyCredentials

在測試環境中，這些 plugins 會自動安裝。

## 指令結構

GCP credentials 管理使用 git-style subcommand 結構：

```
jenkee gcp credential <action> [options]
```

可用的 actions：
- `create` - 建立新的 credential
- `list` - 列出所有 GCP credentials
- `describe` - 查看特定 credential 的詳細資訊
- `update` - 更新現有的 credential
- `delete` - 刪除 credential

查看完整 help：
```bash
jenkee gcp --help
jenkee gcp credential --help
```

## 基本操作

### 1. 準備 Service Account JSON Key

首先，從 GCP Console 下載 service account JSON key file：

1. 前往 [GCP Console - Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. 選擇或建立一個 service account
3. 點選「Keys」→「Add Key」→「Create new key」
4. 選擇「JSON」格式
5. 下載並儲存 JSON key file

### 2. 建立 GCP Credential

```bash
jenkee gcp credential create <credential-id> <json-key-file>
```

範例：

```bash
jenkee gcp credential create my-gcp-sa ~/service-account-key.json
```

成功後會顯示：

```
Created GCP credential: my-gcp-sa
  Project ID: your-project-id
  Service Account: sa@your-project.iam.gserviceaccount.com
```

### 3. 列出 GCP Credentials

```bash
jenkee gcp credential list
```

輸出範例：

```
GCP Service Account Credentials:

ID: my-gcp-sa
  Type: GoogleRobotPrivateKeyCredentials
  Project ID: my-gcp-sa

ID: another-gcp-sa
  Type: GoogleRobotPrivateKeyCredentials
  Project ID: another-gcp-sa
```

### 4. 查看 Credential 詳細資訊

預設不顯示敏感資訊：

```bash
jenkee gcp credential describe my-gcp-sa
```

輸出範例：

```
SUCCESS
Credential: my-gcp-sa
Type: GoogleRobotPrivateKeyCredentials
Scope: GLOBAL
Project ID: my-gcp-sa
Service Account: sa@your-project.iam.gserviceaccount.com

Secret: [PROTECTED]

Use --show-secret flag to display the full JSON key (use with caution!)
```

顯示完整 secret（謹慎使用）：

```bash
jenkee gcp credential describe my-gcp-sa --show-secret
```

這會顯示完整的 service account JSON key 內容，包含 private key。

### 5. 更新 Credential

當需要輪換 service account keys 時：

```bash
jenkee gcp credential update my-gcp-sa ~/new-service-account-key.json
```

成功後會顯示：

```
Updated GCP credential: my-gcp-sa
  Project ID: your-project-id
  Service Account: sa@your-project.iam.gserviceaccount.com
```

### 6. 刪除 Credential

刪除操作需要確認（互動式）：

```bash
jenkee gcp credential delete my-gcp-sa
```

會提示：
```
Are you sure you want to delete credential 'my-gcp-sa'? (y/N):
```

或使用 `--yes-i-really-mean-it` flag 跳過互動式確認（適合自動化腳本）：

```bash
jenkee gcp credential delete my-gcp-sa --yes-i-really-mean-it
```

## 在 Jenkins Job 中使用

### 方法 1：使用 Credentials Binding Plugin (推薦)

在 Pipeline job 中：

```groovy
pipeline {
    agent any
    environment {
        // Bind credential as a file
        GOOGLE_APPLICATION_CREDENTIALS = credentials('my-gcp-sa')
    }
    stages {
        stage('Use GCP') {
            steps {
                sh '''
                    # GOOGLE_APPLICATION_CREDENTIALS 已經指向 credential file
                    gcloud auth activate-service-account --key-file="${GOOGLE_APPLICATION_CREDENTIALS}"
                    gcloud projects list
                '''
            }
        }
    }
}
```

### 方法 2：在 Freestyle Job 中使用

1. 在 job configuration 中，找到「Build Environment」section
2. 勾選「Use secret text(s) or file(s)」
3. 點選「Add」→「Secret file」
4. Variable: `GOOGLE_APPLICATION_CREDENTIALS`
5. Credentials: 選擇你建立的 GCP credential
6. 在 build steps 中使用 `$GOOGLE_APPLICATION_CREDENTIALS`

### 方法 3：使用 Google Cloud SDK Plugin

如果安裝了 Google Cloud SDK plugin：

1. 在 job configuration 中設定「Google Cloud SDK」build wrapper
2. 選擇你的 GCP credential
3. Plugin 會自動處理認證

## 錯誤處理

### 重複的 Credential ID

```bash
$ jenkee gcp credential create my-gcp-sa ~/key.json
Error: Credential 'my-gcp-sa' already exists.
Use 'update' action or delete the existing credential first.
```

解決方式：使用不同的 ID 或先 update/delete 現有的 credential。

### 無效的 JSON File

```bash
$ jenkee gcp credential create test ~/invalid.json
Error: Invalid JSON file: ...
```

確認 JSON file 格式正確且包含必要欄位。

### 缺少必要欄位

```bash
$ jenkee gcp credential create test ~/incomplete.json
Error: Invalid service account key. Missing fields: private_key, client_email
```

Service account key 必須包含以下欄位：
- `type`
- `project_id`
- `private_key_id`
- `private_key`
- `client_email`

### Credential 不存在

```bash
$ jenkee gcp credential describe nonexistent
Error: Credential 'nonexistent' not found.
```

使用 `jenkee gcp credential list` 查看所有可用的 credentials。

## 安全建議

1. 不要將 service account JSON key 提交到版本控制系統
2. 使用最小權限原則設定 service account 權限
3. 定期輪換 service account keys（使用 `update` 指令）
4. 使用 `--show-secret` flag 時要特別小心，避免在共享螢幕或錄影時使用
5. 在 CI/CD 環境中，考慮使用 Workload Identity 或其他更安全的認證方式
6. 刪除不再使用的 credentials

## 技術細節

### Credential 類型

jenkee 使用 `GoogleRobotPrivateKeyCredentials` 來儲存 GCP service account keys。

選擇這個類型的原因：
- 與 Jenkins 的 GCP plugins 相容
- 可直接提供給 GCloudBuildWrapper 與 credential binding 使用
- JSON key 以 Jenkins SecretBytes 加密儲存

### Credential Scope

所有建立的 credentials 使用 `GLOBAL` scope，可在所有 jobs 中使用。

## 測試

GCP credentials 功能包含完整的測試，但這些測試是 optional 的。

### 執行測試

1. 準備一個測試用的 service account JSON key
2. 設定環境變數：

```bash
export JENKEE_TEST_GCLOUD_ADC=/path/to/test-service-account-key.json
```

3. 執行測試：

```bash
pytest tests/test_gcp_credentials.py -v
```

如果沒有設定 `JENKEE_TEST_GCLOUD_ADC`，測試會被跳過。

### 測試涵蓋範圍

- ✅ Help commands
- ✅ Create credential
- ✅ List credentials
- ✅ Describe credential (with/without secret)
- ✅ Update credential
- ✅ Delete credential
- ✅ Error handling (duplicate ID, invalid JSON, missing file, incomplete key, etc.)
- ✅ Freestyle job integration
- ✅ Pipeline job integration (in test plan)

## 範例腳本

### 自動化 Credential 管理

```bash
#!/bin/bash
# rotate-gcp-keys.sh - Rotate GCP service account keys

CREDENTIAL_ID="my-gcp-sa"
NEW_KEY_FILE="$HOME/new-key.json"

# Update credential with new key
if jenkee gcp credential update "$CREDENTIAL_ID" "$NEW_KEY_FILE"; then
    echo "✓ Successfully rotated key for $CREDENTIAL_ID"
    # Securely delete the key file after upload
    shred -u "$NEW_KEY_FILE"
else
    echo "✗ Failed to rotate key"
    exit 1
fi
```

### 批次建立 Credentials

```bash
#!/bin/bash
# create-gcp-credentials.sh - Create multiple GCP credentials

for key_file in keys/*.json; do
    # Extract project_id from filename or JSON
    credential_id=$(basename "$key_file" .json)

    echo "Creating credential: $credential_id"
    jenkee gcp credential create "$credential_id" "$key_file"
done
```

## 未來規劃

- [ ] 支援其他 GCP credential 類型（如 OAuth credentials）
- [ ] 支援 Workload Identity Federation
- [ ] 整合 secret rotation 自動化
- [ ] 支援匯出/匯入 credentials（加密格式）

## 常見問題

### Q: 為什麼不在主 help 中顯示 GCP commands？

A: GCP 功能被設計為 optional/specialized feature，保持主 help 簡潔，只顯示核心功能。使用者可透過 `jenkee gcp --help` 發現這些指令。

### Q: 為什麼改用 `GoogleRobotPrivateKeyCredentials`？

A: 這是 Jenkins GCP credential 的標準類型，能與 GCloudBuildWrapper 等 plugin 正常整合，並且直接使用 service account JSON key。

### Q: 如何在沒有 Jenkins CLI 的情況下使用？

A: 你需要先執行 `jenkee auth` 設定 Jenkins 連線資訊。jenkee 會透過 Jenkins CLI jar 與 Jenkins 互動。

### Q: 支援 Folder-scoped credentials 嗎？

A: 目前只支援 Global scope。如果需要支援 folder scope，請提 issue。

## 參考資源

- [Jenkins Credentials Plugin](https://plugins.jenkins.io/credentials/)
- [GCP Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials)
- [Test Plan for GCP Integration](test-plan-for-gcp-integration.md)
