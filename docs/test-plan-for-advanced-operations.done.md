# Test Plan: Advanced Operations (Groovy Script Execution)

## ⚠️ 最高風險警告

**groovy 命令具有最高風險！**

- 擁有與 Jenkins 管理員相同的完整權限
- 可以執行任意程式碼
- 可以修改任何設定
- 可以刪除任何資料
- 可以造成系統不可用
- 操作通常不可逆

**在生產環境使用前必須極度謹慎！**

## 測試情境

使用 Groovy script 執行進階管理與自動化任務。這是最強大但也最危險的功能。

## 測試目標

驗證使用者可以：
1. 執行簡單的 Groovy script
2. 使用 script 查詢 Jenkins 資訊
3. 使用 script 執行批次操作
4. 理解操作的風險與影響

## 涵蓋的指令

| 指令 | 測試目的 | 危險等級 |
|------|---------|---------|
| `groovy` | 執行 Groovy script | 極高（完整權限）⚠️⚠️⚠️ |

## AI Agent 使用限制

AI agent 在使用此命令前**必須**：

1. **優先尋找替代方案**：
   - 檢查是否有其他更安全的 jenkee 命令可以達成目的
   - 只有在沒有替代方案時才使用 groovy

2. **向使用者說明**：
   - 說明為什麼需要使用 groovy（沒有其他命令可用）
   - 說明 script 將要執行的操作
   - 說明操作的影響與風險
   - 展示 script 內容讓使用者檢閱

3. **取得明確同意**：
   - 等待使用者檢閱 script
   - 取得使用者明確同意後才執行

4. **建議安全措施**：
   - 建議先在測試環境執行
   - 建議先備份重要資料
   - 建議使用 dry-run 模式（如果 script 支援）

## 測試前置條件

- **強烈建議在測試環境執行**
- Jenkins server 運行中並已認證（`jenkee auth` 成功）
- 使用者具有執行 Groovy script 的權限（通常需要管理員權限）
- 了解 Groovy 語言與 Jenkins API
- 準備好測試用的 scripts
- 完整備份（如果是重要環境）

## 測試步驟

### 1. 執行簡單的查詢 Script

```bash
jenkee groovy "println('Hello from Groovy')"
```

**預期結果**：
- Exit code: 0
- 輸出 "Hello from Groovy"
- Script 成功執行

**驗證點**：
- [ ] Script 執行成功
- [ ] 輸出正確
- [ ] 沒有錯誤

### 2. 查詢 Jenkins 版本

```bash
jenkee groovy "println(Jenkins.instance.version)"
```

**預期結果**：
- Exit code: 0
- 顯示 Jenkins 版本號
- 資訊正確

**驗證點**：
- [ ] 成功取得版本資訊
- [ ] 輸出格式正確

### 3. 列出所有 Jobs（使用 Groovy）

```bash
jenkee groovy "Jenkins.instance.items.each { println(it.name) }"
```

**預期結果**：
- Exit code: 0
- 列出所有 job 名稱
- 與 `list-jobs --all` 結果一致

**驗證點**：
- [ ] 成功列出 jobs
- [ ] 輸出正確
- [ ] 與其他命令結果一致

### 4. 從檔案執行 Script

建立測試 script 檔案 `test-script.groovy`：
```groovy
import jenkins.model.Jenkins

def jenkins = Jenkins.instance
println("Jenkins URL: ${jenkins.rootUrl}")
println("Total jobs: ${jenkins.items.size()}")
```

執行：
```bash
jenkee groovy < test-script.groovy
```

**預期結果**：
- Exit code: 0
- 顯示 Jenkins URL 和 job 總數
- 資訊正確

**驗證點**：
- [ ] 從檔案載入 script 成功
- [ ] Script 執行正確
- [ ] 輸出符合預期

### 5. 執行批次查詢操作

建立 `batch-query.groovy`：
```groovy
import jenkins.model.Jenkins

def jenkins = Jenkins.instance

println("=== Jenkins Statistics ===")
println("Version: ${jenkins.version}")
println("Total Jobs: ${jenkins.items.size()}")
println("Total Nodes: ${jenkins.nodes.size() + 1}") // +1 for master

println("\n=== Job Status ===")
jenkins.items.each { job ->
    def lastBuild = job.lastBuild
    def status = lastBuild ? lastBuild.result : "Never built"
    println("${job.name}: ${status}")
}
```

執行：
```bash
jenkee groovy < batch-query.groovy
```

**預期結果**：
- Exit code: 0
- 顯示完整的統計資訊
- 包含所有 jobs 的狀態

**驗證點**：
- [ ] Script 執行成功
- [ ] 統計資訊正確
- [ ] Job 狀態正確

### 6. 執行條件查詢（找出失敗的 Jobs）

```groovy
import jenkins.model.Jenkins

Jenkins.instance.items.findAll { job ->
    job.lastBuild?.result?.toString() == 'FAILURE'
}.each { job ->
    println("Failed job: ${job.name}")
    println("  Last build: #${job.lastBuild.number}")
    println("  URL: ${job.url}")
}
```

執行：
```bash
jenkee groovy < find-failed-jobs.groovy
```

**預期結果**：
- Exit code: 0
- 列出所有最後一次 build 失敗的 jobs
- 包含必要的資訊

**驗證點**：
- [ ] 成功找出失敗的 jobs
- [ ] 資訊正確完整

### 7. Dry-Run 模式範例（不實際修改）

建立 `dry-run-example.groovy`：
```groovy
import jenkins.model.Jenkins

def dryRun = true  // 設為 false 才會實際執行

Jenkins.instance.items.findAll { it.disabled }.each { job ->
    if (dryRun) {
        println("[DRY-RUN] Would enable job: ${job.name}")
    } else {
        job.enable()
        println("[EXECUTED] Enabled job: ${job.name}")
    }
}

if (dryRun) {
    println("\nThis was a dry-run. Set dryRun=false to execute.")
}
```

執行：
```bash
jenkee groovy < dry-run-example.groovy
```

**預期結果**：
- Exit code: 0
- 顯示會執行的操作（但不實際執行）
- 沒有修改任何設定

**驗證點**：
- [ ] Dry-run 模式運作正常
- [ ] 沒有實際修改設定
- [ ] 輸出清楚說明會執行的操作

## 典型工作流程範例

### 場景 A：批次查詢 Job 配置

```groovy
// query-job-configs.groovy
import jenkins.model.Jenkins

Jenkins.instance.items.each { job ->
    println("\n=== ${job.name} ===")
    println("Description: ${job.description}")
    println("Disabled: ${job.disabled}")
    println("Last build: ${job.lastBuild?.number ?: 'N/A'}")

    // 查詢 SCM 設定
    if (job.scm) {
        println("SCM: ${job.scm.class.simpleName}")
    }

    // 查詢 triggers
    if (job.triggers) {
        println("Triggers: ${job.triggers.keySet()}")
    }
}
```

### 場景 B：分析 Build 歷史

```groovy
// analyze-build-history.groovy
import jenkins.model.Jenkins

def jobName = "my-job"
def job = Jenkins.instance.getItem(jobName)

if (!job) {
    println("Job not found: ${jobName}")
    return
}

def stats = [SUCCESS: 0, FAILURE: 0, UNSTABLE: 0, ABORTED: 0, OTHER: 0]

job.builds.each { build ->
    def result = build.result?.toString() ?: 'OTHER'
    stats[result] = (stats[result] ?: 0) + 1
}

println("=== Build Statistics for ${jobName} ===")
stats.each { result, count ->
    println("${result}: ${count}")
}
```

### 場景 C：檢查無用的 Jobs（長時間未執行）

```groovy
// find-stale-jobs.groovy
import jenkins.model.Jenkins
import java.util.concurrent.TimeUnit

def daysThreshold = 90
def thresholdMillis = System.currentTimeMillis() - TimeUnit.DAYS.toMillis(daysThreshold)

println("=== Jobs not built in the last ${daysThreshold} days ===")

Jenkins.instance.items.each { job ->
    def lastBuild = job.lastBuild

    if (!lastBuild) {
        println("${job.name}: Never built")
    } else if (lastBuild.timeInMillis < thresholdMillis) {
        def daysSince = TimeUnit.MILLISECONDS.toDays(System.currentTimeMillis() - lastBuild.timeInMillis)
        println("${job.name}: ${daysSince} days ago (build #${lastBuild.number})")
    }
}
```

### 場景 D：審計權限設定

```groovy
// audit-permissions.groovy
import jenkins.model.Jenkins
import hudson.security.AuthorizationStrategy

def jenkins = Jenkins.instance
def strategy = jenkins.authorizationStrategy

println("=== Authorization Strategy ===")
println("Type: ${strategy.class.simpleName}")

// 這個範例依賴具體的 authorization strategy 類型
// 實際使用需要根據環境調整
```

### 場景 E：批次更新 Job 描述（謹慎使用）

```groovy
// update-job-descriptions.groovy
import jenkins.model.Jenkins

def dryRun = true  // 重要：預設為 true

def pattern = ~/test-.*/
def suffix = " [Test Job]"

Jenkins.instance.items.findAll { it.name =~ pattern }.each { job ->
    def newDescription = (job.description ?: "") + suffix

    if (dryRun) {
        println("[DRY-RUN] Would update ${job.name}")
        println("  Old: ${job.description}")
        println("  New: ${newDescription}")
    } else {
        job.description = newDescription
        job.save()
        println("[EXECUTED] Updated ${job.name}")
    }
}

if (dryRun) {
    println("\n⚠️  This was a dry-run. Set dryRun=false to execute.")
}
```

## 錯誤情境測試

### 執行無效的 Groovy Script

```bash
jenkee groovy "invalid groovy syntax {"
```

**預期結果**：
- Exit code: 非 0
- 顯示 Groovy 語法錯誤訊息

**驗證點**：
- [ ] 錯誤被正確偵測
- [ ] 錯誤訊息有幫助

### 存取不存在的 Job

```groovy
def job = Jenkins.instance.getItem("non-existent-job")
if (!job) {
    println("Job not found")
} else {
    println("Job found")
}
```

**預期結果**：
- Exit code: 0
- 輸出 "Job not found"
- Script 正確處理 null

**驗證點**：
- [ ] Null 檢查運作正常
- [ ] 沒有 NullPointerException

## 測試完成標準

- [ ] 簡單 script 執行成功
- [ ] 從檔案載入 script 成功
- [ ] 查詢操作正確回傳資訊
- [ ] Dry-run 模式運作正常
- [ ] 錯誤情境被正確處理
- [ ] 了解 groovy 命令的風險
- [ ] 測試環境沒有被意外修改

## 安全檢查清單

在使用 groovy 命令前，確認：

- [ ] 已尋找替代的 jenkee 命令
- [ ] 確實需要使用 groovy（沒有其他選擇）
- [ ] 在測試環境執行（不是生產環境）
- [ ] 已完整備份（如果是重要環境）
- [ ] 檢閱 script 內容，理解其作用
- [ ] 使用 dry-run 模式測試（如果 script 會修改設定）
- [ ] 取得必要的授權
- [ ] 了解操作的影響與風險
- [ ] 準備好復原計畫

## 最佳實踐

1. **優先使用專用命令**：
   - 能用 `jenkee list-jobs` 就不要用 groovy
   - 能用 `jenkee update-job` 就不要用 groovy
   - groovy 應該是最後手段

2. **Dry-Run 優先**：
   - 所有會修改設定的 script 都應該有 dry-run 模式
   - 先用 dry-run 驗證，確認無誤後才實際執行

3. **腳本審查**：
   - 所有 script 都應該經過檢閱
   - 理解每一行程式碼的作用
   - 特別注意刪除、修改操作

4. **錯誤處理**：
   - Script 中加入適當的 null 檢查
   - 處理可能的例外狀況
   - 提供清楚的錯誤訊息

5. **版本控制**：
   - 將常用的 scripts 納入版本控制
   - 記錄 script 的用途與執行歷史
   - 分享經過驗證的 scripts

6. **測試優先**：
   - 在測試環境先執行
   - 驗證結果正確後才在生產環境執行
   - 記錄執行結果

7. **權限最小化**：
   - 只給予必要的權限
   - 考慮使用受限的執行環境
   - 審計 script 執行記錄

## 替代方案對照表

在使用 groovy 前，檢查是否有替代命令：

| 需求 | 應該使用 | 而非 groovy |
|------|---------|-----------|
| 列出 jobs | `jenkee list-jobs` | ✗ |
| 取得 job 配置 | `jenkee get-job` | ✗ |
| 更新 job | `jenkee update-job` | ✗ |
| 觸發 build | `jenkee build` | ✗ |
| 刪除 job | `jenkee delete-job` | ✗ |
| 複雜批次操作 | ✓ groovy | 沒有其他選擇 |
| 自訂查詢 | ✓ groovy | 沒有其他選擇 |
| 系統管理操作 | ✓ groovy | 沒有其他選擇 |

## 注意事項

- `groovy` 命令具有完整的 Jenkins 管理員權限
- 錯誤的 script 可能導致資料遺失或系統不可用
- 某些操作無法復原
- Script 執行時會阻塞 Jenkins（避免長時間執行的操作）
- 不建議在 script 中執行耗時的外部命令
- Jenkins Groovy Sandbox 可能限制某些操作（取決於設定）

## Jenkins API 參考資源

- Jenkins JavaDoc: https://javadoc.jenkins.io/
- Groovy Script Console Wiki: https://www.jenkins.io/doc/book/managing/script-console/
- Jenkins CLI Reference: https://www.jenkins.io/doc/book/managing/cli/

## 相關文件

- [groovy 指令文件](examples/groovy.md)
