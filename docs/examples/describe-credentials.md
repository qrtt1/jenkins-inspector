# describe-credentials Command

查看特定 Jenkins credential 的詳細資訊。

## 用途

`describe-credentials` 命令用於：
- 查看 credential 的完整metadata
- 了解 credential 的類型與設定
- 取得在 job 中使用該 credential 的方式
- 確認 credential 所屬的 domain

## 基本語法

```bash
jks describe-credentials <credential-id> [--store STORE] [--show-secret]
```

### 參數說明

| 參數 | 說明 | 必填 |
|------|------|------|
| `<credential-id>` | Credential 的 ID | 是 |
| `--store STORE` | Credentials store 識別碼 | 否 |
| `--show-secret` | 顯示 secret 內容（密碼、私鑰等敏感資料） | 否 |

### Store 識別碼

預設值為 `system::system::jenkins`，通常不需要指定。

格式：`{scope}::{domain}::{name}`
- scope: `system`
- domain: 通常為 `system`
- name: store 名稱，通常為 `jenkins`

## 使用範例

### 1. 查看 File Credentials

查看 Docker 環境變數檔案 credential：

```bash
$ jks describe-credentials spider-app-staging-docker-env
=== Domain: spider-app-staging ===
Description: Spider Application Beta environment

ID: spider-app-staging-docker-env
Type: FileCredentialsImpl
Scope: GLOBAL
Description: (no description)

Details:
  File Name: spider-app-staging-docker.env
  Content: [PROTECTED - Secret file content is not accessible]

Usage in Job:
  Use 'Secret file' credential binding in job configuration
  The file will be available at a temporary path during build
```

### 2. 查看 GCP Service Account

查看 GCP Service Account credential：

```bash
$ jks describe-credentials spider-app-staging-gcp-jenkins-sa
=== Domain: spider-app-staging ===
Description: Spider Application Beta environment

ID: spider-app-staging-gcp-jenkins-sa
Type: GoogleRobotPrivateKeyCredentials
Scope: GLOBAL
Description: A Google robot account for accessing Google APIs and services.

Details:
  Project ID: spider-app-staging-gcp-jenkins-sa
  Service Account Key: [PROTECTED - Key content is not accessible]

Usage in Job:
  Use with Google Cloud Build Wrapper
  Or use 'Google Service Account from private key' credential binding
```

### 3. 查看 SSH Private Key

查看 SSH 私鑰 credential：

```bash
$ jks describe-credentials fcc26b8a-ce9c-4ee0-9dff-dfab31a2393f
=== Domain: (global) ===

ID: fcc26b8a-ce9c-4ee0-9dff-dfab31a2393f
Type: BasicSSHUserPrivateKey
Scope: GLOBAL
Description: jenkins-ssh-key

Details:
  Username: jenkins
  Private Key Source: BasicSSHUserPrivateKey$DirectEntryPrivateKeySource
  Private Key: [PROTECTED - Key content is not accessible]

Usage in Job:
  Use 'SSH User Private Key' credential binding
  Or use in SSH-based SCM configurations
```

### 4. 查看 Username/Password Credentials

```bash
$ jks describe-credentials A10-API
=== Domain: Source Control ===

ID: A10-API
Type: UsernamePasswordCredentialsImpl
Scope: GLOBAL
Description: (no description)

Details:
  Username: study
  Password: [PROTECTED - Password is not accessible]

Usage in Job:
  Use 'Username and password' credential binding
  Separate variables for username and password can be specified
```

### 5. 查看 Secret Text

```bash
$ jks describe-credentials stark-notification-token
=== Domain: (global) ===

ID: stark-notification-token
Type: StringCredentialsImpl
Scope: GLOBAL
Description: Notification service token (Jenkins CI App)

Details:
  Secret Text: [PROTECTED - Secret content is not accessible]

Usage in Job:
  Use 'Secret text' credential binding
  The secret will be available as an environment variable
```

## 支援的 Credential 類型

| 類型 | 說明 | 顯示欄位 | `--show-secret` 支援 |
|------|------|---------|---------------------|
| `FileCredentialsImpl` | Secret file | File Name | ✅ 顯示檔案內容 |
| `StringCredentialsImpl` | Secret text | - | ✅ 顯示 secret text |
| `BasicSSHUserPrivateKey` | SSH private key | Username, Private Key Source | ✅ 顯示私鑰 |
| `UsernamePasswordCredentialsImpl` | Username and password | Username | ✅ 顯示密碼 |
| `GoogleRobotPrivateKeyCredentials` | GCP Service Account | Project ID | ✅ 顯示 service account JSON |
| `AmazonWebServicesCredentials` | AWS IAM Credentials | Access Key ID | ❌ 尚未支援 |
| `BrowserStackCredentials` | BrowserStack | Username | ❌ 尚未支援 |
| `GitLabApiTokenImpl` | GitLab API Token | - | ❌ 尚未支援 |

### Secret 支援說明

標示 ✅ 的類型支援使用 `--show-secret` 參數顯示實際的 secret 內容。

標示 ❌ 的類型目前尚未實作 secret 擷取功能，使用 `--show-secret` 時會顯示：
```
Note: Secret retrieval is not supported for credential type 'AmazonWebServicesCredentials'
```

如需為特定類型新增 secret 支援，請參考 `jenkins_tools/credential_describers/` 目錄下現有的實作範例。

## 安全性說明

### 預設行為

預設情況下，所有敏感資料（密碼、私鑰、token 等）都會顯示為 `[PROTECTED - Use --show-secret to display]`，以保護機密資訊。

### 顯示 Secret 內容

使用 `--show-secret` 參數可以顯示實際的 secret 內容：

```bash
# 顯示 secret text
$ jks describe-credentials stark-notification-token --show-secret
=== Domain: (global) ===

ID: stark-notification-token
Type: StringCredentialsImpl
Scope: GLOBAL
Description: Notification service token (Jenkins CI App)

Details:
  Secret Text: slack_token_redacted_for_example

Usage in Job:
  Use 'Secret text' credential binding
  The secret will be available as an environment variable
```

```bash
# 顯示 file credential 內容
$ jks describe-credentials spider-app-staging-docker-env --show-secret
Details:
  File Name: spider-app-staging-docker.env
  Content:
============================================================
# Environment variables
ENV=staging
DATABASE_URL=postgresql://user:pass@host:5432/db
...
============================================================
```

```bash
# 顯示 GCP service account key
$ jks describe-credentials spider-app-staging-gcp-jenkins-sa --show-secret
Details:
  Project ID: spider-app-staging-gcp-jenkins-sa
  Service Account Key:
============================================================
{
  "type": "service_account",
  "project_id": "spider-app-staging",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  ...
}
============================================================
```

### 安全性注意事項

使用 `--show-secret` 時請注意：

1. **終端機歷史記錄**：輸出的 secret 可能會被記錄在終端機的 scroll buffer 中
2. **螢幕截圖/錄影**：確保沒有螢幕分享或錄影進行中
3. **日誌檔案**：避免將輸出重導向到不安全的日誌檔案
4. **存取控制**：確保只有授權人員才能執行此命令

建議的安全做法：

```bash
# 將 secret 直接儲存到安全的檔案
jks describe-credentials my-cred --show-secret > /tmp/secret.txt
chmod 600 /tmp/secret.txt

# 使用完畢後立即刪除
rm /tmp/secret.txt

# 或使用 | 管線傳遞給其他工具，不留下記錄
jks describe-credentials my-cred --show-secret | some-secure-tool
```

Jenkins Credentials Store 使用加密儲存，只有在 job 執行期間才會解密並注入到環境中。

## 常見使用情境

### 1. 確認 Credential 設定

在設定 job 前，先確認 credential 是否存在且設定正確：

```bash
# 列出所有 credentials
jks list-credentials spider-app-staging

# 查看特定 credential 詳細資訊
jks describe-credentials spider-app-staging-docker-env
```

### 2. 了解 Credential 使用方式

查看如何在 job 中使用特定 credential：

```bash
$ jks describe-credentials spider-app-staging-gcs-sa
# 輸出會包含 "Usage in Job" 區段說明使用方式
```

### 3. 比對環境差異

確認 staging 和 production 環境使用不同的 credentials：

```bash
# Beta 環境
jks describe-credentials spider-app-staging-docker-env

# Prod 環境
jks describe-credentials spider-app-production-docker-env
```

### 4. 驗證 Credential 類型

確認 credential 類型符合預期：

```bash
jks describe-credentials spider-app-staging-gcp-jenkins-sa | grep "Type:"
# 輸出: Type: GoogleRobotPrivateKeyCredentials
```

## 錯誤處理

### Credential 不存在

```bash
$ jks describe-credentials non-existent-id
Error: Credential 'non-existent-id' not found in store 'system::system::jenkins'
```

**解決方式**：
1. 使用 `jks list-credentials` 確認 credential ID
2. 檢查是否拼寫錯誤
3. 確認 credential 是否在不同的 domain

### 認證失敗

```bash
$ jks describe-credentials some-credential
Error: Jenkins credentials not configured.
Run 'jks auth' to configure credentials.
```

**解決方式**：
1. 執行 `jks auth` 驗證認證設定
2. 確認 `~/.jenkins-inspector/.env` 檔案存在且正確

## 工作流程整合

### 1. 設定新專案時

```bash
# 1. 列出可用的 credentials
jks list-credentials

# 2. 查看需要使用的 credential 詳細資訊
jks describe-credentials spider-app-staging-docker-env

# 3. 在 job 配置中加入對應的 credential binding
```

### 2. Troubleshooting Deploy Job

```bash
# 1. 檢查 job 使用的 credentials
jks get-job spider-shield-console-deploy-staging | grep credentialsId

# 2. 逐一查看每個 credential 的設定
jks describe-credentials spider-app-staging-docker-env
jks describe-credentials spider-app-staging-gcs-sa
jks describe-credentials spider-app-staging-firebase-sa

# 3. 確認 credential 類型與 job 配置一致
```

### 3. 文件化專案設定

```bash
# 產生專案使用的 credentials 清單
jks list-credentials spider-app-staging > credentials-list.txt

# 查看每個 credential 的詳細資訊
for cred_id in spider-app-staging-docker-env spider-app-staging-gcs-sa; do
  echo "=== $cred_id ==="
  jks describe-credentials $cred_id
  echo
done
```

## 相關命令

| 命令 | 說明 |
|------|------|
| `list-credentials` | 列出所有 credentials |
| `list-credentials <domain>` | 列出特定 domain 的 credentials |
| `get-job <job-name>` | 查看 job 使用的 credentials |
| `job-diff <job1> <job2>` | 比較兩個 job 的 credential 設定差異 |

## 參考資料

- [list-credentials.md](list-credentials.md) - 列出 credentials 命令文件
- [Jenkins Credentials Plugin](https://plugins.jenkins.io/credentials/)
