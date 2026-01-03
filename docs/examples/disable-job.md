# disable-job - 停用 Job

## AI Agent 使用限制

AI agent 在使用此命令前**必須**：
1. 向使用者說明將要停用的 job 名稱
2. 說明停用的影響（job 無法被觸發執行）
3. 取得使用者明確同意後才執行

## 用途

停用指定的 Jenkins job(s)。停用後的 job 無法被手動或自動觸發執行，但配置和歷史記錄都會保留。

## 基本語法

```bash
# 停用單一 job
jenkee disable-job <job-name>

# 停用多個 jobs
jenkee disable-job <job-name1> <job-name2> [job-name3 ...]
```

## 參數說明

| 參數 | 說明 | 必填 |
|------|------|------|
| `<job-name>` | Job 名稱（可指定多個） | 是 |
| `--yes-i-really-mean-it` | 跳過互動式確認，直接執行（適合自動化腳本） | 否 |

## 功能說明

此指令會：
1. 驗證 Jenkins 認證設定
2. 停用指定的 job(s)
3. 停用後 job 仍然存在，但無法被觸發
4. 配置和歷史記錄都會保留
5. 可以隨時使用 `enable-job` 重新啟用

## 執行範例

### 互動式確認（預設行為）

```bash
$ jenkee disable-job old-production-job
Are you sure you want to disable job 'old-production-job'? (y/N): y
✓ Successfully disabled job 'old-production-job'
```

### 取消停用

```bash
$ jenkee disable-job old-production-job
Are you sure you want to disable job 'old-production-job'? (y/N): n
Operation cancelled.
```

### 使用確認 Flag（自動化腳本）

```bash
# 跳過互動式確認，直接執行
$ jenkee disable-job old-production-job --yes-i-really-mean-it
✓ Successfully disabled job 'old-production-job'
```

### 停用多個 Jobs

```bash
$ jenkee disable-job job-a job-b job-c
Are you sure you want to disable 3 job(s)? (y/N): y
✓ Successfully disabled 3 job(s)
  - job-a
  - job-b
  - job-c
```

### 缺少必要參數

```bash
$ jenkee disable-job
Error: Missing job name(s)
Usage: jenkee disable-job <job-name> [job-name ...]
```

### Job 不存在

```bash
$ jenkee disable-job non-existent-job
Error: Failed to disable job 'non-existent-job'
ERROR: No such job 'non-existent-job'
```

## 常見使用情境

### 暫時停用維護中的 Job

```bash
# 停用需要維護的 job
jenkee disable-job production-deploy

# 進行維護作業...
# 修改配置、更新 credentials 等

# 完成後重新啟用
jenkee enable-job production-deploy
```

### 停用舊版本的 Jobs

```bash
# 停用舊版本，但保留配置作為參考
jenkee disable-job \
  app-v1-deploy \
  app-v1-test \
  app-v1-build
```

### 批次停用測試 Jobs

```bash
# 停用所有 nightly test jobs
jenkee list-jobs --all | grep "nightly-test" | xargs jenkee disable-job
```

### 停用前檢查狀態

```bash
#!/bin/bash
# 檢查 job 狀態後再停用

JOB_NAME="$1"

# 檢查 job 是否正在執行
if jenkee list-builds "$JOB_NAME" | head -1 | grep -q "In progress"; then
  echo "Warning: Job is currently running"
  read -p "Disable anyway? (yes/no): " confirm
  if [ "$confirm" != "yes" ]; then
    exit 1
  fi
fi

jenkee disable-job "$JOB_NAME"
```

### 軟刪除策略

```bash
# 與其直接刪除 job，先停用觀察一段時間
jenkee disable-job candidate-for-deletion

# 如果一週後確認沒問題，再執行刪除
# jenkee delete-job candidate-for-deletion
```

## 輸出格式

### 成功（單一 job）
```
✓ Successfully disabled job 'job-name'
```

### 成功（多個 jobs）
```
✓ Successfully disabled 3 job(s)
  - job-a
  - job-b
  - job-c
```

### 失敗
```
Error: Failed to disable job 'job-name'
[Jenkins error message]
```

## 相關指令

- `jenkee enable-job <job>` - 重新啟用 job
- `jenkee job-status <job>` - 查看 job 狀態（包含是否已停用）
- `jenkee delete-job <job>` - 刪除 job（永久移除）
- `jenkee list-jobs --all` - 列出所有 jobs

## 注意事項

1. **停用不等於刪除**
   - Job 配置和 build 歷史都會保留
   - 可以隨時重新啟用

2. **無法被觸發**
   - 停用後無法手動觸發 build
   - 定時觸發（cron）也會停止
   - Upstream job 也無法觸發此 job

3. **Job 名稱區分大小寫**

4. **權限需求**
   - 需要有 configure job 的權限

5. **Downstream 影響**
   - 如果其他 job 依賴此 job
   - 它們的 build 流程可能會受影響

6. **查看狀態**
   - 使用 `jenkee job-status <job>` 可以看到 Disabled 欄位

## 最佳實踐

### 停用前通知

```bash
#!/bin/bash
# 停用前通知相關團隊

JOB_NAME="critical-job"

# 停用 job
jenkee disable-job "$JOB_NAME"

# 發送通知（實際環境使用 Slack、Email 等）
echo "Job '$JOB_NAME' has been disabled" | \
  mail -s "Jenkins Alert" team@example.com
```

### 定期檢查停用的 Jobs

```bash
#!/bin/bash
# 列出所有已停用超過 30 天的 jobs

for job in $(jenkee list-jobs --all); do
  status=$(jenkee job-status "$job" 2>/dev/null | grep "Disabled:" | awk '{print $2}')
  if [ "$status" = "true" ]; then
    echo "$job is disabled"
    # 可以加入更多邏輯，如檢查停用時間
  fi
done
```

### 與 enable-job 搭配使用

```bash
# 快速切換 job 的啟用狀態

# 停用舊版本
jenkee disable-job app-v1-deploy

# 啟用新版本
jenkee enable-job app-v2-deploy
```
