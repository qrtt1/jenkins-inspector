# Test Plan for Credential Domain Management

## 功能目標

實作 Jenkins credentials domain 管理功能，解決目前所有 credentials 都建立在 global domain 的問題。
提供完整的 domain CRUD 操作，並更新現有 credential commands 支援指定 domain。

## 背景

目前問題：
- GCP credential 建立時都硬編碼使用 `Domain.global()`
- 無法將 credentials 依專案、環境或團隊分類管理
- 缺乏 domain 管理的 CLI 介面

## 功能範圍

### 1. Domain Management Commands

新增 `jenkee domain` command group：

#### 1.1 列出所有 domains
```bash
jenkee domain list
```

預期輸出：
```
Available domains:
  (global)              Global credentials domain
  production            Production environment credentials
  staging               Staging environment credentials
  team-alpha            Team Alpha service accounts

Total: 4 domains
```

測試項目：
- [ ] 列出所有 domains（包含 global）
- [ ] 顯示 domain 名稱與描述
- [ ] 顯示每個 domain 中的 credential 數量
- [ ] 空 domain 也應正確顯示

#### 1.2 建立新 domain (DANGEROUS)
```bash
jenkee domain create <domain-name> [--description=<text>] [--yes-i-really-mean-it]
```

範例：
```bash
jenkee domain create production --description="Production environment credentials" --yes-i-really-mean-it
jenkee domain create team-alpha --yes-i-really-mean-it
```

測試項目：
- [ ] 建立有描述的 domain
- [ ] 建立無描述的 domain
- [ ] Domain 名稱驗證（不允許特殊字元）
- [ ] 檢查 domain 是否已存在（避免重複建立）
- [ ] 需要 `--yes-i-really-mean-it` flag 確認
- [ ] 成功訊息確認

#### 1.3 更新 domain (DANGEROUS)
```bash
jenkee domain update <domain-name> [--description=<text>] [--new-name=<name>] [--yes-i-really-mean-it]
```

範例：
```bash
jenkee domain update production --description="Updated description" --yes-i-really-mean-it
jenkee domain update old-name --new-name=new-name --yes-i-really-mean-it
jenkee domain update production --new-name=prod --description="Production env" --yes-i-really-mean-it
```

測試項目：
- [ ] 更新 domain 描述
- [ ] 重新命名 domain
- [ ] 同時更新名稱和描述
- [ ] 驗證 domain 存在
- [ ] 重新命名時檢查新名稱是否已被使用
- [ ] 無法更新 global domain
- [ ] 需要 `--yes-i-really-mean-it` flag 確認

#### 1.4 刪除 domain (DANGEROUS)
```bash
jenkee domain delete <domain-name> [--yes-i-really-mean-it] [--force]
```

範例：
```bash
jenkee domain delete staging --yes-i-really-mean-it
jenkee domain delete production --yes-i-really-mean-it --force  # 強制刪除有 credentials 的 domain
```

測試項目：
- [ ] 需要 `--yes-i-really-mean-it` flag 確認（危險操作）
- [ ] 無法刪除 global domain
- [ ] 有 credentials 的 domain 需要警告
- [ ] 成功刪除空 domain
- [ ] 強制刪除有 credentials 的 domain（加上 `--force` flag）

#### 1.5 查看 domain 詳細資訊
```bash
jenkee domain describe <domain-name>
```

預期輸出：
```
=== Domain: production ===
Name: production
Description: Production environment credentials
Credentials: 5

Credentials in this domain:
  - gcp-prod-sa-1 (FileCredentialsImpl)
  - gcp-prod-sa-2 (FileCredentialsImpl)
  - db-password (UsernamePasswordCredentialsImpl)
  - api-token (StringCredentialsImpl)
  - ssh-key (BasicSSHUserPrivateKey)
```

測試項目：
- [ ] 顯示 domain 基本資訊
- [ ] 列出該 domain 中的所有 credentials
- [ ] 顯示每個 credential 的類型
- [ ] 處理空 domain
- [ ] 處理 global domain

### 2. 更新現有 Credential Commands 支援 Domain

#### 2.1 GCP Credential Create
```bash
jenkee gcp credential create <id> <json-key-file> [--domain=<name>]
```

範例：
```bash
jenkee gcp credential create prod-sa-1 ~/key.json --domain=production
jenkee gcp credential create dev-sa-1 ~/key.json  # 預設使用 global domain
```

測試項目：
- [ ] 在指定 domain 建立 credential
- [ ] 無 `--domain` 參數時使用 global domain（保持向後相容）
- [ ] 驗證 domain 存在
- [ ] Domain 不存在時顯示錯誤訊息

#### 2.2 GCP Credential Update
```bash
jenkee gcp credential update <id> <json-key-file> [--domain=<name>]
```

測試項目：
- [ ] 在指定 domain 更新 credential
- [ ] 自動搜尋所有 domains（如果未指定 domain）
- [ ] 在正確的 domain 中找到並更新 credential

#### 2.3 GCP Credential Delete
```bash
jenkee gcp credential delete <id> [--domain=<name>] [--yes-i-really-mean-it]
```

測試項目：
- [ ] 從指定 domain 刪除 credential
- [ ] 自動搜尋所有 domains（如果未指定 domain）

#### 2.4 GCP Credential List
```bash
jenkee gcp credential list [--domain=<name>]
```

測試項目：
- [ ] 列出指定 domain 的 GCP credentials
- [ ] 列出所有 domains 的 GCP credentials（預設行為）
- [ ] 依 domain 分組顯示

#### 2.5 GCP Credential Describe
```bash
jenkee gcp credential describe <id> [--domain=<name>] [--show-secret]
```

測試項目：
- [ ] 在指定 domain 查詢 credential
- [ ] 自動搜尋所有 domains（如果未指定 domain）
- [ ] 顯示 credential 所屬的 domain

### 3. List Credentials Command 更新

```bash
jenkee list-credentials [domain] [--store=<store-id>]
```

目前已支援 domain 參數，但需要確保：
- [ ] 正確顯示各 domain 資訊
- [ ] `--domain` flag 作為替代語法
- [ ] 與新的 domain management 整合

### 4. Describe Credentials Command 更新

```bash
jenkee describe-credentials <id> [--domain=<name>] [--show-secret]
```

測試項目：
- [ ] 支援 `--domain` 參數
- [ ] 顯示 credential 所屬 domain
- [ ] 未指定 domain 時搜尋所有 domains

## Error Handling

### 4.1 Domain 不存在
```bash
$ jenkee gcp credential create test-sa ~/key.json --domain=nonexistent
Error: Domain 'nonexistent' does not exist.

Available domains:
  (global)
  production
  staging

Run 'jenkee domain create nonexistent' to create this domain.
```

### 4.2 重複的 Domain 名稱
```bash
$ jenkee domain create production
Error: Domain 'production' already exists.

Run 'jenkee domain list' to see all domains.
Run 'jenkee domain update production' to update this domain.
```

### 4.3 刪除有 Credentials 的 Domain
```bash
$ jenkee domain delete production --yes-i-really-mean-it
Warning: Domain 'production' contains 5 credentials.

Credentials in this domain:
  - gcp-prod-sa-1
  - gcp-prod-sa-2
  - db-password
  - api-token
  - ssh-key

Deleting this domain will also delete all credentials in it.
To proceed, add the --force flag:
  jenkee domain delete production --yes-i-really-mean-it --force
```

### 4.4 無法刪除 Global Domain
```bash
$ jenkee domain delete "(global)" --yes-i-really-mean-it
Error: Cannot delete the global domain.

The global domain is a system domain and cannot be removed.
```

### 4.5 無法更新 Global Domain
```bash
$ jenkee domain update "(global)" --description="New description"
Error: Cannot update the global domain.

The global domain is a system domain and cannot be modified.
```

## 實作架構

### 實作決策

**優先使用 Jenkins CLI 原生命令**：
- Jenkins CLI 本身提供完整的 domain 管理命令
- 只在需要額外資訊時才使用 Groovy（如：列出 domain 並顯示 credential 數量）

**安全性考量**：
- 所有 domain 操作都繼承 `DangerousCommandMixin`
- 需要 `--yes-i-really-mean-it` flag 確認
- 包含：create, update, delete（list 和 describe 不需要）

### 核心模組

1. **Domain Command** (`jenkins_tools/commands/domain.py`)
   - 繼承 `DangerousCommandMixin` 和 `Command`
   - 實作 `list`, `create`, `update`, `delete`, `describe` 子命令
   - **create/update/delete**: wrapper for Jenkins CLI 命令
   - **list/describe**: 使用 Groovy 提供詳細資訊

2. **更新 GCP Credential Command** (`jenkins_tools/commands/gcp/credential.py`)
   - 加入 `--domain` 參數支援
   - 修改 Groovy scripts 使用指定的 domain
   - 預設使用 global domain（向後相容）

3. **更新 CLI Dispatcher** (`jenkins_tools/cli.py`)
   - 註冊 `domain` command

### Jenkins CLI 命令

使用以下 Jenkins CLI 原生命令：

```bash
# Create domain (from stdin XML)
create-credentials-domain-by-xml STORE

# Get domain as XML
get-credentials-domain-as-xml STORE DOMAIN

# Update domain (from stdin XML)
update-credentials-domain-by-xml STORE DOMAIN

# Delete domain
delete-credentials-domain STORE DOMAIN
```

預設 STORE: `system::system::jenkins`

### Domain XML 格式

```xml
<com.cloudbees.plugins.credentials.domains.Domain>
  <name>domain-name</name>
  <description>Domain description</description>
  <specifications/>
</com.cloudbees.plugins.credentials.domains.Domain>
```

### Groovy Scripts（僅用於查詢）

Domain list/describe 使用 Groovy 提供額外資訊：

```groovy
import com.cloudbees.plugins.credentials.SystemCredentialsProvider
import com.cloudbees.plugins.credentials.domains.Domain
import jenkins.model.Jenkins

def jenkins = Jenkins.get()
def store = SystemCredentialsProvider.getInstance().getStore()

// List domains with credential counts
store.getDomains().each { domain ->
    println "Domain: ${domain.getName() ?: '(global)'}"
    println "  Description: ${domain.getDescription() ?: '(no description)'}"
    // ... show credentials in this domain
}
```

## 測試執行方式

### 手動測試流程

1. 建立測試 domains
2. 在不同 domain 建立 credentials
3. 測試 update, list, describe 操作
4. 測試錯誤處理
5. 測試刪除操作

### 自動化測試

- 新增 `tests/test_domain_commands.py`
- 更新 `tests/test_gcp_credential.py` 測試 domain 參數
- 整合測試確保向後相容

## 相關文件

建立後需要新增/更新的文件：
- [ ] `docs/examples/domain.md` - Domain 管理使用範例
- [ ] 更新 `docs/examples/gcp-credential.md` - 加入 domain 參數範例
- [ ] 更新 `README.md` - 加入 domain management 章節
- [ ] 更新 AI prompt - 加入 domain 相關命令說明

## 預期完成標準

- [ ] 所有測試案例通過
- [ ] 文件完整（範例、說明）
- [ ] 向後相容（預設使用 global domain）
- [ ] 錯誤訊息清楚易懂
- [ ] Help 輸出包含 domain 相關命令
- [ ] Prompt 輸出包含 domain 使用範例

## 優先順序

### Phase 1: Domain 基本管理（必要）
- [ ] `domain list`
- [ ] `domain create`
- [ ] `domain describe`
- [ ] `domain delete`
- [ ] `domain update`

### Phase 2: GCP Credential Domain 支援（必要）
- [ ] `gcp credential create --domain`
- [ ] `gcp credential update --domain`
- [ ] `gcp credential delete --domain`
- [ ] `gcp credential list --domain`
- [ ] `gcp credential describe --domain`

### Phase 3: 其他 Credential Commands 整合（可選）
- [ ] `list-credentials --domain`
- [ ] `describe-credentials --domain`

## Migration Guide

為了協助使用者將現有 credentials 組織到不同 domains，提供遷移指南：

```bash
# 1. 列出目前所有在 global domain 的 credentials
jenkee list-credentials "(global)"

# 2. 建立新的 domain
jenkee domain create production --description="Production credentials"
jenkee domain create staging --description="Staging credentials"

# 3. 重新建立 credentials 到新 domain（目前需要手動）
# 未來可能提供 credential move 命令
```

註：Credential 跨 domain 移動功能（`credential move`）可以作為 Phase 4 未來擴充功能。
