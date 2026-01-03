# delete-job - 刪除 Job

## ⚠️ 警告

**這是一個危險且不可逆的操作！**

- 刪除 job 會永久移除該 job 及其所有 build 歷史
- 此操作無法復原
- 建議在刪除前先備份 job 配置：`jenkee get-job <job> > backup.xml`

## AI Agent 使用限制

AI agent 在使用此命令前**必須**：
1. 向使用者說明將要刪除的 job 名稱
2. 說明刪除的影響（包含 build 歷史也會被刪除）
3. 建議使用者先備份 job 配置
4. 取得使用者明確同意後才執行

## 用途

刪除指定的 Jenkins job(s)。支援一次刪除多個 jobs。

## 基本語法

```bash
# 刪除單一 job
jenkee delete-job <job-name>

# 刪除多個 jobs
jenkee delete-job <job-name1> <job-name2> [job-name3 ...]
```

## 參數說明

| 參數 | 說明 | 必填 |
|------|------|------|
| `<job-name>` | Job 名稱（可指定多個） | 是 |
| `--yes-i-really-mean-it` | 跳過互動式確認，直接執行（適合自動化腳本） | 否 |

## 功能說明

此指令會：
1. 驗證 Jenkins 認證設定
2. 刪除指定的 job(s)
3. 同時刪除該 job 的所有 build 歷史記錄
4. 操作不可逆

## 執行範例

### 互動式確認（預設行為）

```bash
$ jenkee delete-job old-unused-job
Are you sure you want to delete job 'old-unused-job'? (y/N): y
✓ Successfully deleted job 'old-unused-job'
```

### 取消刪除

```bash
$ jenkee delete-job old-unused-job
Are you sure you want to delete job 'old-unused-job'? (y/N): n
Operation cancelled.
```

### 使用確認 Flag（自動化腳本）

```bash
# 跳過互動式確認，直接執行
$ jenkee delete-job old-unused-job --yes-i-really-mean-it
✓ Successfully deleted job 'old-unused-job'
```

### 刪除多個 Jobs

```bash
$ jenkee delete-job job-a job-b job-c
Are you sure you want to delete 3 job(s)? (y/N): y
✓ Successfully deleted 3 job(s)
  - job-a
  - job-b
  - job-c
```

### 缺少必要參數

```bash
$ jenkee delete-job
Error: Missing job name(s)
Usage: jenkee delete-job <job-name> [job-name ...]
```

### Job 不存在

```bash
$ jenkee delete-job non-existent-job
Error: Failed to delete job 'non-existent-job'
ERROR: No such job 'non-existent-job'; perhaps you meant 'existing-job'?
```

### 部分成功

```bash
$ jenkee delete-job job-a non-existent-job job-c
Error: Failed to delete job 'non-existent-job'
ERROR: No such job 'non-existent-job'
Warning: 2 job(s) deleted, 1 failed
```

## 常見使用情境

### 刪除前先備份

```bash
#!/bin/bash
# 安全刪除 job 的最佳實踐

JOB_NAME="old-job"
BACKUP_DIR="job-backups"

# 1. 建立備份目錄
mkdir -p "$BACKUP_DIR"

# 2. 備份 job 配置
echo "Backing up job configuration..."
jenkee get-job "$JOB_NAME" > "$BACKUP_DIR/${JOB_NAME}.xml"

# 3. 確認備份成功
if [ -f "$BACKUP_DIR/${JOB_NAME}.xml" ]; then
  echo "✓ Backup saved to $BACKUP_DIR/${JOB_NAME}.xml"

  # 4. 刪除 job
  echo "Deleting job..."
  jenkee delete-job "$JOB_NAME"
else
  echo "✗ Backup failed, job not deleted"
  exit 1
fi
```

### 批次刪除舊的測試 Jobs

```bash
#!/bin/bash
# 刪除所有以 test- 開頭的 jobs（謹慎使用！）

# 列出所有 test- 開頭的 jobs
TEST_JOBS=$(jenkee list-jobs --all | grep "^test-")

if [ -z "$TEST_JOBS" ]; then
  echo "No test jobs found"
  exit 0
fi

# 顯示將要刪除的 jobs
echo "The following jobs will be deleted:"
echo "$TEST_JOBS"
echo ""
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
  # 刪除所有 test jobs
  echo "$TEST_JOBS" | xargs jenkee delete-job
else
  echo "Cancelled"
fi
```

### 清理特定專案的 Jobs

```bash
#!/bin/bash
# 刪除特定專案的所有相關 jobs

PROJECT="old-project"

# 找出所有包含專案名稱的 jobs
JOBS=$(jenkee list-jobs --all | grep "$PROJECT")

if [ -z "$JOBS" ]; then
  echo "No jobs found for project: $PROJECT"
  exit 0
fi

# 先備份所有 jobs
echo "Backing up jobs..."
mkdir -p "backup-$PROJECT"
echo "$JOBS" | while read job; do
  jenkee get-job "$job" > "backup-$PROJECT/${job}.xml"
  echo "  Backed up: $job"
done

# 確認後刪除
echo ""
echo "Jobs to delete:"
echo "$JOBS"
echo ""
read -p "Delete all these jobs? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
  echo "$JOBS" | xargs jenkee delete-job
else
  echo "Cancelled"
fi
```

### 刪除失敗的實驗性 Jobs

```bash
# 刪除單一實驗性 job
jenkee delete-job experimental-feature-test

# 刪除多個實驗性 jobs
jenkee delete-job \
  experiment-1 \
  experiment-2 \
  experiment-3
```

### 條件式刪除

```bash
#!/bin/bash
# 只在 job 已停用時才刪除

JOB_NAME="candidate-for-deletion"

# 檢查 job 狀態
STATUS=$(jenkee job-status "$JOB_NAME" 2>/dev/null | grep "Disabled:" | awk '{print $2}')

if [ "$STATUS" = "true" ]; then
  echo "Job is disabled, safe to delete"
  jenkee delete-job "$JOB_NAME"
else
  echo "Job is still enabled, not deleting"
  echo "Run 'jenkee disable-job $JOB_NAME' first if you want to delete it"
fi
```

## 輸出格式

### 成功（單一 job）
```
✓ Successfully deleted job 'job-name'
```

### 成功（多個 jobs）
```
✓ Successfully deleted 3 job(s)
  - job-a
  - job-b
  - job-c
```

### 失敗
```
Error: Failed to delete job 'job-name'
[Jenkins error message]
```

### 部分成功
```
Error: Failed to delete job 'job-2'
[Jenkins error message]
Warning: 2 job(s) deleted, 1 failed
```

## 相關指令

- `jenkee get-job <job>` - 備份 job 配置
- `jenkee copy-job <source> <dest>` - 複製 job（保留原始 job）
- `jenkee disable-job <job>` - 停用 job（不刪除）
- `jenkee list-jobs --all` - 列出所有 jobs

## 注意事項

1. **操作不可逆**
   - 刪除後無法復原
   - 所有 build 歷史都會被刪除
   - 建議先備份 job 配置

2. **Job 名稱區分大小寫**

3. **權限需求**
   - 需要有刪除 job 的權限
   - 某些受保護的 job 可能無法刪除

4. **相依性**
   - 如果其他 jobs 依賴此 job（如 upstream/downstream 關係）
   - 刪除後這些關係會失效
   - 建議先用 `jenkee job-status <job>` 檢查相依性

5. **Pipeline 中使用**
   - 如果此 job 被其他 pipeline 呼叫
   - 刪除後那些 pipeline 會失敗

## 最佳實踐

### 刪除前檢查清單

```bash
#!/bin/bash
# 刪除 job 前的完整檢查

JOB_NAME="$1"

if [ -z "$JOB_NAME" ]; then
  echo "Usage: $0 <job-name>"
  exit 1
fi

echo "Pre-deletion checklist for: $JOB_NAME"
echo ""

# 1. 檢查 job 是否存在
echo "1. Checking if job exists..."
if ! jenkee list-jobs --all | grep -q "^$JOB_NAME$"; then
  echo "   ✗ Job not found"
  exit 1
fi
echo "   ✓ Job exists"

# 2. 檢查上下游關係
echo "2. Checking dependencies..."
jenkee job-status "$JOB_NAME" | grep -E "(Upstream|Downstream)" || echo "   No dependencies"

# 3. 備份配置
echo "3. Backing up configuration..."
mkdir -p job-backups
jenkee get-job "$JOB_NAME" > "job-backups/${JOB_NAME}.xml"
echo "   ✓ Saved to job-backups/${JOB_NAME}.xml"

# 4. 最後確認
echo ""
echo "Ready to delete job: $JOB_NAME"
read -p "Proceed with deletion? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
  jenkee delete-job "$JOB_NAME"
else
  echo "Cancelled"
fi
```

### 設定別名避免誤刪

```bash
# 在 ~/.bashrc 或 ~/.zshrc 中加入
alias jks-delete='echo "Use: jenkee delete-job <job> (requires confirmation)"'

# 強制需要明確指令
# 避免誤用簡短的別名
```

### 軟刪除策略

```bash
# 與其直接刪除，先停用 job 一段時間
jenkee disable-job old-job

# 等待一週後，確認沒問題再刪除
# jenkee delete-job old-job
```
