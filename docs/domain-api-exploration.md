# Jenkins Domain API Exploration Results

探索日期：2026-01-03
測試環境：Local Jenkins (Docker container)

## 測試環境設定

```bash
# 啟動測試 Jenkins
./scripts/start-test-jenkins.sh

# 連線資訊
URL: http://localhost:8081
Username: jenkins-test
Password: test-password-for-jenkins-inspector
API Token: 1100000000000000000000000000000000
```

## Domain API 基本操作

### 1. 列出所有 Domains

```groovy
import com.cloudbees.plugins.credentials.SystemCredentialsProvider
import com.cloudbees.plugins.credentials.domains.Domain
import jenkins.model.Jenkins

def jenkins = Jenkins.get()
def store = SystemCredentialsProvider.getInstance().getStore()

println "=== All Domains ==="
store.getDomains().each { domain ->
    println "Domain name: ${domain.getName() ?: '(global)'}"
    println "  Description: ${domain.getDescription() ?: '(no description)'}"
    println "  Specifications count: ${domain.getSpecifications().size()}"
    println ""
}
println "Total domains: ${store.getDomains().size()}"
```

輸出範例：
```
=== All Domains ===
Domain name: (global)
  Description: (no description)
  Specifications count: 0

Total domains: 1
```

### 2. 建立新 Domain

```groovy
import com.cloudbees.plugins.credentials.SystemCredentialsProvider
import com.cloudbees.plugins.credentials.domains.Domain
import jenkins.model.Jenkins

def jenkins = Jenkins.get()
def store = SystemCredentialsProvider.getInstance().getStore()

def domainName = "production"
def domainDesc = "Production environment credentials"

// Check if domain already exists
def existing = store.getDomains().find { it.getName() == domainName }
if (existing) {
    println "ERROR: Domain '${domainName}' already exists"
    return
}

// Create domain (with empty specifications list)
def domain = new Domain(domainName, domainDesc, Collections.emptyList())

// Add domain to store
if (store.addDomain(domain)) {
    jenkins.save()
    println "SUCCESS: Created domain '${domainName}'"
} else {
    println "ERROR: Failed to create domain '${domainName}'"
}
```

測試結果：✅ 成功建立 domain

### 3. 更新 Domain

Jenkins Domain API 不支援直接更新 domain，需要先刪除舊的再建立新的：

```groovy
import com.cloudbees.plugins.credentials.SystemCredentialsProvider
import com.cloudbees.plugins.credentials.domains.Domain
import jenkins.model.Jenkins

def jenkins = Jenkins.get()
def store = SystemCredentialsProvider.getInstance().getStore()

def oldName = "production"
def newName = "prod"
def newDesc = "Production env (renamed)"

// Find existing domain
def oldDomain = store.getDomains().find { it.getName() == oldName }
if (!oldDomain) {
    println "ERROR: Domain '${oldName}' not found"
    return
}

// Create new domain with updated info (preserve specifications)
def newDomain = new Domain(newName, newDesc, oldDomain.getSpecifications())

// Remove old and add new
if (store.removeDomain(oldDomain) && store.addDomain(newDomain)) {
    jenkins.save()
    println "SUCCESS: Updated domain from '${oldName}' to '${newName}'"
} else {
    println "ERROR: Failed to update domain"
}
```

測試結果：✅ 成功更新 domain（透過刪除 + 新增實現）

**注意事項**：
- 更新時需要保留原 domain 的 specifications
- 如果 domain 中有 credentials，需要一併處理（credentials 會隨著 domain 一起移除）

### 4. 刪除 Domain

```groovy
import com.cloudbees.plugins.credentials.SystemCredentialsProvider
import com.cloudbees.plugins.credentials.domains.Domain
import jenkins.model.Jenkins

def jenkins = Jenkins.get()
def store = SystemCredentialsProvider.getInstance().getStore()

def domainName = "prod"

// Find domain
def domain = store.getDomains().find { it.getName() == domainName }
if (!domain) {
    println "ERROR: Domain '${domainName}' not found"
    return
}

// Check if it's global domain
if (domain.isGlobal()) {
    println "ERROR: Cannot delete global domain"
    return
}

// Remove domain
if (store.removeDomain(domain)) {
    jenkins.save()
    println "SUCCESS: Deleted domain '${domainName}'"
} else {
    println "ERROR: Failed to delete domain '${domainName}'"
}
```

測試結果：✅ 成功刪除 domain

**安全檢查**：
- Global domain 無法刪除（`domain.isGlobal()` 檢查）
- 刪除 domain 會同時刪除其中的所有 credentials

## Domain 物件屬性

從測試中確認的 Domain 物件方法：

- `getName()` - 取得 domain 名稱（global domain 會回傳 null，需處理為 "(global)"）
- `getDescription()` - 取得 domain 描述
- `getSpecifications()` - 取得 domain specifications（用於限定 domain 適用範圍，一般為空）
- `isGlobal()` - 檢查是否為 global domain

**注意**：Domain 物件沒有 `getDisplayName()` 方法

## Store 物件方法

SystemCredentialsProvider store 提供的方法：

- `getDomains()` - 取得所有 domains
- `addDomain(domain)` - 新增 domain
- `removeDomain(domain)` - 刪除 domain
- `updateDomain(oldDomain, newDomain)` - 更新 domain（但實測發現使用 remove + add 更可靠）

## 實作建議

基於探索結果，實作 domain management 時的建議：

### 1. Domain List
- 使用 `store.getDomains()` 取得所有 domains
- Global domain 的 `getName()` 回傳 null，需要特別處理顯示為 "(global)"
- 可以統計每個 domain 中的 credentials 數量

### 2. Domain Create
- 建立前檢查 domain 是否已存在
- 使用空的 specifications list（一般不需要設定 domain 限定條件）
- 建立後呼叫 `jenkins.save()` 持久化

### 3. Domain Update
- 先找到舊的 domain
- 保留原 domain 的 specifications
- 使用 `removeDomain()` + `addDomain()` 組合實現更新
- 如果 domain 中有 credentials，需要警告使用者（更新過程中 credentials 會暫時消失）
- 建議實作時提供 `--preserve-credentials` 選項，在更新前備份 credentials

### 4. Domain Delete
- 檢查是否為 global domain（`domain.isGlobal()`）
- 檢查 domain 中是否有 credentials
- 如果有 credentials，需要明確警告並要求確認
- 刪除後呼叫 `jenkins.save()` 持久化

## 與 Credentials 整合

### 在指定 Domain 建立 Credential

修改現有的 GCP credential 建立 script 範例：

```groovy
// 原本硬編碼
def domain = Domain.global()

// 改為支援指定 domain
def domainName = "production"  // 從參數取得
def domain = store.getDomains().find { it.getName() == domainName }
if (!domain) {
    domain = Domain.global()  // fallback to global
}

// 或者：如果 domain 不存在就建立
if (!domain) {
    domain = new Domain(domainName, "Auto-created domain", Collections.emptyList())
    store.addDomain(domain)
}
```

## Jenkins CLI 原生支援

經過測試，Jenkins CLI 本身就提供了 domain 管理命令：

### 1. create-credentials-domain-by-xml
```
java -jar jenkins-cli.jar create-credentials-domain-by-xml STORE
Create Credentials Domain by XML
 STORE : Store Id
```

使用範例：
```bash
cat domain.xml | jenkee-cli create-credentials-domain-by-xml system::system::jenkins
```

XML 格式：
```xml
<com.cloudbees.plugins.credentials.domains.Domain>
  <name>staging</name>
  <description>Staging environment credentials</description>
  <specifications/>
</com.cloudbees.plugins.credentials.domains.Domain>
```

### 2. get-credentials-domain-as-xml
```
java -jar jenkins-cli.jar get-credentials-domain-as-xml STORE DOMAIN
Get a Credentials Domain as XML
 STORE  : Store Id
 DOMAIN : Domain Name
```

### 3. update-credentials-domain-by-xml
```
java -jar jenkins-cli.jar update-credentials-domain-by-xml STORE DOMAIN
Update Credentials Domain by XML
 STORE  : Store Id
 DOMAIN : Domain Name
```

### 4. delete-credentials-domain
```
java -jar jenkins-cli.jar delete-credentials-domain STORE DOMAIN
Delete a Credentials Domain
 STORE  : Store Id
 DOMAIN : Domain Name
```

## 實作決策

### 優先使用 Jenkins CLI
- 所有 domain CRUD 操作使用 Jenkins CLI 原生命令
- 只在需要額外資訊時才使用 Groovy（例如：列出 domain 並顯示 credential 數量）

### 安全性考量
- 所有 domain 操作都列為 dangerous commands
- 需要 `--yes-i-really-mean-it` flag 確認
- domain create, update, delete 都需要確認

### Store ID
- 預設使用 `system::system::jenkins`
- 一般情況下不需要使用者指定

## 後續工作

- [ ] 實作 `domain list` command（使用 Groovy 顯示詳細資訊）
- [ ] 實作 `domain create` command（wrapper for create-credentials-domain-by-xml）
- [ ] 實作 `domain update` command（wrapper for update-credentials-domain-by-xml）
- [ ] 實作 `domain delete` command（wrapper for delete-credentials-domain）
- [ ] 實作 `domain describe` command（使用 Groovy 或 get-credentials-domain-as-xml）
- [ ] 更新 GCP credential commands 支援 `--domain` 參數
- [ ] 新增測試案例
- [ ] 撰寫使用範例文件
