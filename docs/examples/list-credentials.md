# list-credentials - 列出 Jenkins Credentials

## 用途

列出 Jenkins 系統中的所有 credentials，包含 ID、類型、範圍與相關 metadata。這個工具可以幫助你理解專案中使用了哪些 credentials，並驗證環境配置。

## 基本語法

```bash
jks list-credentials [domain] [--store STORE]
```

參數說明：
- `domain` (選擇性)：過濾特定 domain 的 credentials
- `--store STORE` (選擇性)：指定 credentials store ID，預設為 `system::system::jenkins`

## 功能說明

此指令會：
1. 使用 Jenkins CLI `list-credentials-as-xml` 取得 credentials 資訊
   - 預設查詢 `system::system::jenkins` store（Jenkins 全域 credentials）
   - 可透過 `--store` 參數指定其他 store
   - Store ID 格式為 `{provider}::{resolver}::{context}`
2. 解析 XML 並按 domain 分組顯示
3. 顯示每個 credential 的 metadata（不包含實際的 secret 內容）
4. 支援選擇性的 domain 過濾

## 執行範例

### 列出所有 Credentials

```bash
$ jks list-credentials
=== Domain: (global) ===

ID: jenkins-ssh-key
  Type: BasicSSHUserPrivateKey
  Scope: GLOBAL
  Description: jenkins-ssh-key
  Username: jenkins

ID: stark-notification-token
  Type: StringCredentialsImpl
  Scope: GLOBAL
  Description: Notification service token

ID: gcp-sa-stark-backup
  Type: GoogleRobotPrivateKeyCredentials
  Scope: GLOBAL
  Description: GCP service account
  Project ID: gcp-sa-stark-backup

=== Domain: spider-app-staging ===
Description: Spider Application Beta environment

ID: spider-app-staging-docker-env
  Type: FileCredentialsImpl
  Scope: GLOBAL
  Description: Environment variables
  File Name: spider-app-staging-docker.env
```

### 過濾特定 Domain

```bash
$ jks list-credentials "spider-app-staging"
=== Domain: spider-app-staging ===
Description: Spider Application Beta environment

ID: spider-app-staging-docker-env
  Type: FileCredentialsImpl
  Scope: GLOBAL
  Description: Environment variables
  File Name: spider-app-staging-docker.env

ID: spider-app-staging-gcp-sa
  Type: GoogleRobotPrivateKeyCredentials
  Scope: GLOBAL
  Description: GCP service account
  Project ID: spider-app-staging-gcp-sa
```

### 只看 Global Domain

```bash
$ jks list-credentials "(global)"
=== Domain: (global) ===

ID: fcc26b8a-ce9c-4ee0-9dff-dfab31a2393f
  Type: BasicSSHUserPrivateKey
  Scope: GLOBAL
  Description: jenkins-ssh-key
  Username: jenkins

ID: stark-notification-token
  Type: StringCredentialsImpl
  Scope: GLOBAL
  Description: Notification service token (Jenkins CI App)

...
```

### 使用自訂 Store ID

預設使用 `system::system::jenkins` store，但可以透過 `--store` 參數指定其他 store：

```bash
# 明確指定 store（與預設相同）
$ jks list-credentials --store "system::system::jenkins"

# 嘗試查詢使用者層級的 credentials（通常為空或不存在）
$ jks list-credentials --store "user::system::jenkins"
Error: Failed to list credentials
ERROR: The specified provider does not have a credentials store in the specified context.

# 結合 store 和 domain 過濾
$ jks list-credentials --store "system::system::jenkins" "spider-app-staging"
```

## 輸出欄位說明

### 通用欄位

所有 credential 類型都會顯示：
- **ID**: Credential 在 Jenkins 中的唯一識別碼
- **Type**: Credential 類型
- **Scope**: 使用範圍（通常是 GLOBAL）
- **Description**: 描述文字

### 類型特定欄位

根據不同的 credential 類型，會顯示額外的 metadata：

#### FileCredentialsImpl
```
File Name: docker.env
```

#### BasicSSHUserPrivateKey
```
Username: jenkins
```

#### UsernamePasswordCredentialsImpl
```
Username: admin
```

#### StringCredentialsImpl
（無額外欄位，用於 secret text）

#### GoogleRobotPrivateKeyCredentials
```
Project ID: my-project-sa
```

#### AmazonWebServicesCredentials
```
Access Key ID: AKIA****************
```

#### BrowserStackCredentials
```
Username: browserstack_user
```

## Credential 類型說明

### FileCredentialsImpl
儲存檔案類型的 secret（如 .env, .json）

使用情境：
- Docker environment files
- GCP service account keys
- Firebase service account keys
- Kubeconfig files

### StringCredentialsImpl
儲存純文字 secret（如 API tokens）

使用情境：
- API keys
- Access tokens
- Notification service tokens
- Cloudflare global API key

### BasicSSHUserPrivateKey
SSH private key 與 username

使用情境：
- Git repository access
- SSH 連線認證

### UsernamePasswordCredentialsImpl
使用者名稱與密碼組合

使用情境：
- 服務登入帳號
- API 基本認證
- Proxmox API

### GoogleRobotPrivateKeyCredentials
Google Cloud service account credentials

使用情境：
- GCP API 存取
- GCS 操作
- GCR image push/pull

### AmazonWebServicesCredentials
AWS IAM 認證

使用情境：
- AWS S3 存取
- AWS EC2 操作
- AWS Lambda 部署

## Domain 組織架構

Jenkins credentials 透過 domain 進行分組管理：

### (global)
預設的全域 domain，包含通用的 credentials

### Project-specific domains
針對特定專案的 credential 群組，例如：
- `spider-app-staging` - Spider Application 測試環境
- `spider-app-production-production` - Spider Application 生產環境
- `Team-Alpha` - Alpha 團隊專案
- `Source Control` - 版本控制相關

## 常見使用情境

### 驗證環境 Credentials

檢查特定環境有哪些 credentials：

```bash
# Beta 環境
jks list-credentials "spider-app-staging"

# Production 環境
jks list-credentials "spider-app-production-production"
```

### 找出特定類型的 Credentials

使用 grep 過濾特定類型：

```bash
# 找出所有 FileCredentials
jks list-credentials | grep -A 5 "Type: FileCredentialsImpl"

# 找出所有 GCP service accounts
jks list-credentials | grep -A 5 "Type: GoogleRobotPrivateKeyCredentials"

# 找出所有 SSH keys
jks list-credentials | grep -A 5 "Type: BasicSSHUserPrivateKey"
```

### 檢查 Credential 存在性

驗證 job 配置中使用的 credential 是否存在：

```bash
# 從 job 配置中找出 credential ID
jks get-job my-job | grep credentialsId

# 確認該 credential 存在
jks list-credentials | grep "ID: credential-id"
```

### 比對環境間的 Credentials

檢查 staging 和 production 環境的 credential 命名是否一致：

```bash
# 列出 staging credentials
jks list-credentials "spider-app-staging" | grep "^ID:" > staging-creds.txt

# 列出 production credentials
jks list-credentials "spider-app-production-production" | grep "^ID:" > production-creds.txt

# 比對差異
diff staging-creds.txt production-creds.txt
```

### 產生 Credentials 清單報告

建立專案的 credentials 文件：

```bash
# 匯出特定 domain 的 credentials
jks list-credentials "spider-app-production-production" > project-credentials.txt

# 或製作完整的 credentials 清單
echo "# Jenkins Credentials Inventory" > credentials-inventory.md
echo "" >> credentials-inventory.md
jks list-credentials >> credentials-inventory.md
```

### 查找特定 Credential

搜尋特定 ID 或名稱的 credential：

```bash
# 找出包含 "docker" 的 credentials
jks list-credentials | grep -i -A 4 "docker"

# 找出包含 "firebase" 的 credentials
jks list-credentials | grep -i -A 4 "firebase"

# 找出特定 ID 的詳細資訊
jks list-credentials | grep -A 4 "spider-app-staging-docker-env"
```

### 統計 Credentials 使用

統計各類型 credentials 數量：

```bash
# 統計各類型數量
jks list-credentials | grep "Type:" | sort | uniq -c

# 統計 domain 數量
jks list-credentials | grep "^===" | wc -l

# 統計總 credential 數量
jks list-credentials | grep "^ID:" | wc -l
```

### 追蹤 Deploy Job 使用的 Credentials

結合 `get-job` 和 `list-credentials` 檢查 deploy job 的 credentials：

```bash
# 1. 從 job 找出使用的 credential IDs
CREDS=$(jks get-job my-deploy-job | grep -o 'credentialsId>[^<]*' | cut -d'>' -f2)

# 2. 逐一檢查這些 credentials
for cred in $CREDS; do
  echo "=== Checking $cred ==="
  jks list-credentials | grep -A 5 "ID: $cred"
done
```

## 安全性說明

此命令透過 Jenkins CLI `list-credentials-as-xml` 取得資訊，該 API：
- 只返回 metadata（ID, type, description 等）
- 所有實際的 secret 內容都被標記為 `<secret-redacted/>`
- 不會暴露任何敏感資訊

範例 XML 輸出：
```xml
<com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl>
  <id>my-credential</id>
  <scope>GLOBAL</scope>
  <description>My password</description>
  <username>admin</username>
  <password>
    <secret-redacted/>
  </password>
</com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl>
```

## 相關指令

- `jks get-job <job>` - 查看 job 使用了哪些 credentials
- `jks job-diff <job1> <job2>` - 比較不同環境使用的 credentials 差異

## 限制與注意事項

1. 此命令只能查詢 `system::system::jenkins` store 中的 credentials
2. 不顯示實際的 secret 內容（這是 Jenkins 的安全設計）
3. Domain 名稱必須完全匹配（區分大小寫）
4. 需要有適當的 Jenkins 權限才能執行此命令
5. 某些 credential 類型可能有額外欄位未顯示在輸出中

## 疑難排解

### 錯誤：Credentials not configured

```bash
$ jks list-credentials
Error: Jenkins credentials not configured.
Run 'jks auth' to configure credentials.
```

解決方式：先執行 `jks auth` 設定 Jenkins 認證。

### 錯誤：Failed to list credentials

```bash
$ jks list-credentials
Error: Failed to list credentials
ERROR: Permission denied
```

可能原因：
1. Jenkins 使用者權限不足
2. Jenkins 版本不支援 `list-credentials-as-xml` 命令
3. Credentials plugin 未安裝

### 找不到特定 Domain

```bash
$ jks list-credentials "my-domain"
(no output)
```

確認：
1. Domain 名稱拼寫是否正確（區分大小寫）
2. 使用 `jks list-credentials` 查看所有可用的 domains

## 技術細節：Credentials Store 識別碼

### Store ID 格式

Jenkins CLI 的 `list-credentials-as-xml` 需要一個 `STORE` 參數，格式為：

```
{provider}::{resolver}::{context}
```

### 預設 Store

`jks list-credentials` 預設查詢 `system::system::jenkins` store，這是：
- **Provider**: `system` (SystemCredentialsProvider / Jenkins Credentials Provider)
- **Resolver**: `system` (SystemContextResolver / Jenkins)
- **Context**: `jenkins` (Jenkins 全域 context)

這個 store 包含所有系統層級的 credentials，涵蓋：
- Global domain 的 credentials
- 所有自訂 domain（如 `spider-app-staging`, `Team-Alpha` 等）

### 為什麼預設使用這個 Store？

1. **涵蓋範圍最廣**：`system::system::jenkins` 包含了幾乎所有 Jenkins 中設定的 credentials
2. **實務上最常用**：大多數 CI/CD pipeline 使用的都是這個 store 中的 credentials
3. **簡化使用**：大部分情況下不需要指定 store 參數

如果需要查詢其他 store，可以使用 `--store` 參數覆寫預設值。

### 其他可能的 Store

理論上還有其他 store 格式：
- `user::system::jenkins` - 使用者層級的 credentials（通常為空）
- `folder::item::/path/to/folder` - Folder 層級的 credentials

但在實務上，system store 已經足夠滿足大部分需求。

### 查詢 Store 相關資訊

如果需要了解 Jenkins 支援的 providers 和 resolvers：

```bash
# 列出所有 credentials providers
java -jar jenkins-cli.jar -s <jenkins-url> -auth <user>:<token> list-credentials-providers

# 列出所有 credentials context resolvers
java -jar jenkins-cli.jar -s <jenkins-url> -auth <user>:<token> list-credentials-context-resolvers
```
