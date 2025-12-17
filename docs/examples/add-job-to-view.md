# add-job-to-view - 將 Jobs 加入 View

## 用途

將一個或多個 Jenkins jobs 加入到指定的 view 中，幫助你快速組織新建立的 jobs 或批次調整 view 內容。

## 基本語法

```bash
jks add-job-to-view <view-name> <job-name> [job-name ...]
```

參數說明：
- `view-name` (必填)：目標 view 的名稱
- `job-name` (必填，可多個)：要加入的 job 名稱，可指定多個

## 功能說明

此指令會：
1. 驗證 Jenkins 認證設定
2. 使用 Jenkins CLI `add-job-to-view` 將指定的 jobs 加入到 view
3. 顯示操作結果與成功加入的 jobs 清單
4. 如果 job 已在 view 中，不會產生錯誤（冪等操作）

## 執行範例

### 加入單一 Job

```bash
$ jks add-job-to-view AVENGERS shield-console-deploy-staging
✓ Successfully added 1 job(s) to view 'AVENGERS'
  - shield-console-deploy-staging
```

### 一次加入多個 Jobs

```bash
$ jks add-job-to-view AVENGERS shield-console-deploy-staging shield-console-deploy-production
✓ Successfully added 2 job(s) to view 'AVENGERS'
  - shield-console-deploy-staging
  - shield-console-deploy-production
```

### 驗證 Jobs 已加入 View

```bash
$ jks list-jobs AVENGERS | grep shield-console
shield-console-deploy-staging
shield-console-deploy-production
```

### 缺少必要參數

```bash
$ jks add-job-to-view AVENGERS
Error: View name and at least one job name are required.
Usage: jks add-job-to-view <view-name> <job-name> [job-name ...]
```

### View 不存在

```bash
$ jks add-job-to-view NonExistentView some-job
Error: Failed to add jobs to view 'NonExistentView'

ERROR: No view named NonExistentView inside view Jenkins
```

### Job 不存在

```bash
$ jks add-job-to-view AVENGERS non-existent-job
Error: Failed to add jobs to view 'AVENGERS'

ERROR: No such job 'non-existent-job'; perhaps you meant 'spider-shield-console-deploy-staging'?
```

## 常見使用情境

### 新建 Pipeline 後組織到 View

為新專案建立一組 pipeline jobs 後，批次加入到 view：

```bash
jks add-job-to-view MyProject-CI \
  myproject-build-auto \
  myproject-release-image-staging \
  myproject-release-image-production \
  myproject-deploy-staging \
  myproject-deploy-production
```

### 找出未加入 View 的 Jobs

結合其他命令找出哪些 jobs 還沒被加入 view：

```bash
# 列出所有相關 jobs
jks list-jobs --all | grep shield-console > /tmp/all-jobs.txt

# 列出 view 中的 jobs
jks list-jobs AVENGERS > /tmp/view-jobs.txt

# 找出差異並加入
comm -23 <(sort /tmp/all-jobs.txt) <(sort /tmp/view-jobs.txt) | \
  xargs jks add-job-to-view AVENGERS
```

### 批次加入符合命名規則的 Jobs

```bash
# 將所有符合規則的 jobs 加入 view
jks list-jobs --all | grep "^spider-app-production.*-deploy$" | \
  xargs jks add-job-to-view AVENGERS
```

### 驗證 Pipeline 設定

檢查特定 pipeline 的所有 jobs 是否都在 view 中：

```bash
# 定義預期的 jobs
EXPECTED_JOBS=(
  "myproject-release-image-auto"
  "myproject-release-image-staging"
  "myproject-deploy-staging"
)

# 檢查並自動加入缺少的 jobs
VIEW_JOBS=$(jks list-jobs MyProject-CI)
for job in "${EXPECTED_JOBS[@]}"; do
  if ! echo "$VIEW_JOBS" | grep -q "^$job$"; then
    jks add-job-to-view MyProject-CI "$job"
  fi
done
```

## 輸出格式

成功時：
```
✓ Successfully added N job(s) to view 'VIEW_NAME'
  - job-name-1
  - job-name-2
```

失敗時：
```
Error: Failed to add jobs to view 'VIEW_NAME'
<Jenkins CLI error message>
```

## 相關指令

- `jks list-views` - 列出所有 views
- `jks list-jobs <view>` - 列出 view 中的 jobs
- `jks list-jobs --all` - 列出所有 jobs（不分 view）
- `jks get-job <job>` - 取得 job XML 配置

## 注意事項

1. View 名稱區分大小寫
2. Job 名稱必須完全匹配（不支援萬用字元）
3. 冪等操作 - 如果 job 已在 view 中，再次執行不會產生錯誤
4. 此命令只能加入 jobs，不會移除現有的 jobs
5. 需要有足夠的 Jenkins 權限才能修改 view
