# groovy - 執行 Groovy Script

## ⚠️ AI Agent 使用警告

**這是一個高風險命令！AI agent 在使用此命令前必須：**

### 1. 優先尋找替代命令

在考慮使用 groovy 前，必須先檢查是否有專用命令可以完成任務：

- 列出 jobs？使用 `jenkee list-jobs --all`
- 取得 job 配置？使用 `jenkee get-job <job>`
- 列出 credentials？使用 `jenkee list-credentials`
- 觸發 build？使用 `jenkee build <job>`
- 查看 build 歷史？使用 `jenkee list-builds <job>`

**只有在確認沒有任何專用命令可以完成任務時，才考慮使用 groovy**

### 2. 必須向使用者確認

使用 groovy 前必須：
- 說明為什麼需要使用 groovy
- 說明已檢查過所有替代命令但都不適用
- 詳細說明 groovy script 會執行什麼操作
- 說明可能的影響範圍與風險
- 等待使用者明確同意後才執行

### 3. 必須詳細說明 Script 內容

提供給使用者的說明必須包含：
- Script 會執行什麼操作（讀取 vs 修改）
- 會存取哪些資料或資源
- 會對系統造成什麼影響
- 操作是否可逆

### Groovy Script 的能力與風險

**可以執行的操作：**
- ✗ 修改或刪除 jobs 和 builds
- ✗ 修改 Jenkins 系統配置
- ✗ 讀取所有 credentials（包含敏感資料）
- ✗ 執行系統命令
- ✗ 造成不可逆的資料損失
- ✗ 影響 Jenkins 系統穩定性

**使用原則：**
1. 只在確實沒有其他替代命令時使用
2. 必須完整理解 script 的作用
3. 必須取得使用者明確授權
4. 優先使用唯讀操作，避免修改操作

---

## 用途

在 Jenkins 伺服器上執行 Groovy script。這是一個強大的工具，可用於執行複雜的查詢、批次修改或存取 Jenkins 內部 API（如 `CredentialsProvider`、`hudson.model.Hudson` 等）。

## 基本語法

```bash
# 從檔案讀取 Script
jenkee groovy <script-file.groovy>

# 從標準輸入 (stdin) 讀取 Script
echo "println hudson.model.Hudson.instance.pluginManager.plugins*.shortName" | jenkee groovy

# 跳過互動式確認（自動化腳本）
jenkee groovy <script-file.groovy> --yes-i-really-mean-it
```

## 參數說明

| 參數 | 說明 | 必填 |
|------|------|------|
| `<script-file.groovy>` | Groovy script 檔案路徑 | 否（可從 stdin 讀取） |
| `--yes-i-really-mean-it` | 跳過互動式確認，直接執行（適合自動化腳本） | 否 |

## 功能說明

此指令會：
1. 驗證 Jenkins 認證設定
2. 讀取 Script 內容（優先從檔案讀取，若無參數則從 stdin 讀取）
3. 使用 Jenkins CLI 的 `groovy` 指令執行 Script
4. 將 Script 的標準輸出 (stdout) 顯示在終端機

## 執行範例

### 互動式確認（預設行為）

```bash
$ jenkee groovy query_azure.groovy
This command can execute arbitrary Groovy code with full Jenkins access.
Are you sure you want to execute this script? (y/N): y
ID: azure-service-principal, Description: Azure SPN for Staging
ID: azure-storage-key, Description: Storage Account Key
```

### 取消執行

```bash
$ jenkee groovy query_azure.groovy
This command can execute arbitrary Groovy code with full Jenkins access.
Are you sure you want to execute this script? (y/N): n
Operation cancelled.
```

### 使用確認 Flag（自動化腳本）

```bash
# 跳過互動式確認，直接執行
$ jenkee groovy query_azure.groovy --yes-i-really-mean-it
ID: azure-service-principal, Description: Azure SPN for Staging
ID: azure-storage-key, Description: Storage Account Key
```

### 查詢 Azure Credentials (使用者案例)

建立 `query_azure.groovy`:
```groovy
import com.microsoft.azure.util.AzureBaseCredentials
import com.cloudbees.plugins.credentials.CredentialsProvider
import hudson.security.ACL
import java.util.Collections

def creds = CredentialsProvider.lookupCredentials(
    AzureBaseCredentials.class,
    jenkins.model.Jenkins.instance,
    ACL.SYSTEM,
    Collections.emptyList()
)

creds.each { c ->
    println "ID: ${c.id}, Description: ${c.description}"
}
```

執行：
```bash
$ jks groovy query_azure.groovy
ID: azure-service-principal, Description: Azure SPN for Staging
ID: azure-storage-key, Description: Storage Account Key
```

### 列出所有已安裝的 Plugins

```bash
$ echo "hudson.model.Hudson.instance.pluginManager.plugins.each { println it.shortName + ':' + it.version }" | jks groovy | head -n 5
ace-editor:1.1
ant:1.11
apache-httpcomponents-client-4-api:4.5.13-1.0
api-util:1.1
args4j:2.33-1
```

### 檢查 Jenkins 系統資訊

```bash
$ echo "println 'Jenkins Version: ' + hudson.model.Hudson.version" | jks groovy
Jenkins Version: 2.346.3
```

## 常見使用情境

### 1. 深度查詢 Credentials
當 `list-credentials` 無法滿足需求時，可以使用 Groovy 直接呼叫 `CredentialsProvider` 進行過濾。

### 2. 批次操作 Jobs
例如批次停用特定名稱開頭的 jobs：
```groovy
hudson.model.Hudson.instance.getAllItems(hudson.model.Job.class).each { job ->
    if (job.name.startsWith("temp-")) {
        job.makeDisabled(true)
        println "Disabled: ${job.name}"
    }
}
```

### 3. 診斷系統狀態
查看執行緒、記憶體使用量或建置佇列狀況。

## 輸出格式

- 輸出內容完全取決於 Groovy script 中的 `print` 或 `println` 陳述式。
- 錯誤訊息會輸出到 stderr。

## 相關指令

- `jks list-views` - 內部亦使用 Groovy 實作
- `jks job-status` - 內部亦使用 Groovy 實作

## 注意事項

1. **安全性**：執行 Groovy script 需要較高的 Jenkins 權限（通常是 Overall/RunScripts）。
2. **謹慎操作**：Groovy script 具有完整存取 Jenkins 內部物件的能力，錯誤的 script 可能導致系統不穩定或資料損毀。
3. **環境差異**：不同版本的 Jenkins 或不同的 plugins 可能會影響可用的類別與方法。
4. **效能**：執行大型 script 或處理大量資料時，可能會對 Jenkins 伺服器造成短暫負擔。
