# groovy - 執行 Groovy Script

## 用途

在 Jenkins 伺服器上執行 Groovy script。這是一個強大的工具，可用於執行複雜的查詢、批次修改或存取 Jenkins 內部 API（如 `CredentialsProvider`、`hudson.model.Hudson` 等）。

## 基本語法

```bash
# 從檔案讀取 Script
jks groovy <script-file.groovy>

# 從標準輸入 (stdin) 讀取 Script
echo "println hudson.model.Hudson.instance.pluginManager.plugins*.shortName" | jks groovy
```

## 功能說明

此指令會：
1. 驗證 Jenkins 認證設定
2. 讀取 Script 內容（優先從檔案讀取，若無參數則從 stdin 讀取）
3. 使用 Jenkins CLI 的 `groovy` 指令執行 Script
4. 將 Script 的標準輸出 (stdout) 顯示在終端機

## 執行範例

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
