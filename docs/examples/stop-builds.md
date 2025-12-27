# stop-builds - 停止執行中的 Builds

## 用途

停止指定 Jenkins job(s) 的所有執行中 builds。適用於需要緊急終止錯誤 build、釋放資源或修正問題的情境。

## 基本語法

```bash
# 停止單一 job 的 builds
jenkee stop-builds <job-name>

# 停止多個 jobs 的 builds
jenkee stop-builds <job-name1> <job-name2> [job-name3 ...]
```

## 參數說明

| 參數 | 說明 | 必填 |
|------|------|------|
| `<job-name>` | Job 名稱（可指定多個） | 是 |

## 功能說明

此指令會：
1. 驗證 Jenkins 認證設定
2. 停止指定 job(s) 的所有執行中的 builds
3. 不影響 queue 中尚未開始的 builds
4. 不影響已完成的 builds

## 執行範例

### 停止單一 Job 的 Builds

```bash
$ jenkee stop-builds my-long-running-job
✓ Stopped all running builds for job 'my-long-running-job'
```

### 停止多個 Jobs 的 Builds

```bash
$ jenkee stop-builds job-a job-b job-c
✓ Stopped all running builds for 3 job(s)
  - job-a
  - job-b
  - job-c
```

### 缺少必要參數

```bash
$ jenkee stop-builds
Error: Missing job name(s)
Usage: jenkee stop-builds <job-name> [job-name ...]
```

### Job 不存在

```bash
$ jenkee stop-builds non-existent-job
Error: Failed to stop builds for job 'non-existent-job'
ERROR: No such job 'non-existent-job'; perhaps you meant 'existing-job'?
```

### 沒有執行中的 Builds

```bash
$ jenkee stop-builds idle-job
✓ Stopped all running builds for job 'idle-job'
```

**說明**：即使沒有執行中的 builds，命令也會成功返回。

## 常見使用情境

### 緊急終止錯誤的 Build

```bash
# 發現 build 有問題，立即終止
jenkee stop-builds production-deploy

# 修正問題後重新觸發
jenkee build production-deploy -p VERSION=1.5.1
```

### 批次停止相關 Jobs

```bash
# 停止所有 staging 環境的 builds
jenkee stop-builds \
  app-build-staging \
  api-build-staging \
  web-build-staging
```

### 使用 Grep 批次停止

```bash
# 找出所有執行中的特定類型 jobs 並停止
jenkee list-jobs --all | grep "nightly-test" | xargs jenkee stop-builds
```

### 在 Build 超時時停止

```bash
#!/bin/bash
# 監控並停止超時的 build

JOB_NAME="long-running-job"
TIMEOUT=3600  # 1 hour

# 觸發 build
jenkee build $JOB_NAME &
BUILD_PID=$!

# 等待指定時間
sleep $TIMEOUT

# 檢查 build 是否還在執行
if ps -p $BUILD_PID > /dev/null; then
  echo "Build timeout, stopping..."
  jenkee stop-builds $JOB_NAME
  kill $BUILD_PID
fi
```

### CI/CD Pipeline 錯誤處理

```bash
#!/bin/bash
# 部署腳本with錯誤處理

set -e

trap 'jenkee stop-builds deploy-staging deploy-production' ERR

# 執行部署
jenkee build pre-check -s
jenkee build deploy-staging -s
jenkee build deploy-production -s

echo "✓ Deployment completed"
```

### 清理卡住的 Builds

```bash
# 定期檢查並停止長時間執行的 builds
# (實際使用時需配合監控系統)

PROBLEMATIC_JOBS=(
  "occasional-hang-job"
  "resource-intensive-job"
)

for job in "${PROBLEMATIC_JOBS[@]}"; do
  echo "Stopping builds for $job..."
  jenkee stop-builds "$job"
done
```

### 維護視窗前停止所有 Builds

```bash
#!/bin/bash
# 維護前準備：停止所有執行中的 builds

echo "Stopping all running builds..."

# 取得所有 jobs
ALL_JOBS=$(jenkee list-jobs --all)

# 批次停止（小心使用！）
echo "$ALL_JOBS" | xargs jenkee stop-builds

echo "All builds stopped. Ready for maintenance."
```

**警告**：批次停止所有 jobs 的 builds 應該謹慎使用。

### 條件式停止

```bash
#!/bin/bash
# 只在特定條件下停止 builds

JOB_NAME="test-job"

# 檢查某個條件
if [ -f "/tmp/emergency_stop" ]; then
  echo "Emergency stop triggered"
  jenkee stop-builds $JOB_NAME
  rm /tmp/emergency_stop
fi
```

## 輸出格式

### 成功（單一 job）
```
✓ Stopped all running builds for job 'job-name'
```

### 成功（多個 jobs）
```
✓ Stopped all running builds for 3 job(s)
  - job-a
  - job-b
  - job-c
```

### 失敗
```
Error: Failed to stop builds for job 'job-name'
[Jenkins error message]
```

## 相關指令

- `jenkee build <job>` - 觸發 build
- `jenkee list-builds <job>` - 查看 build 歷史
- `jenkee console <job> [build]` - 查看 build console 輸出
- `jenkee job-status <job>` - 查看 job 狀態

## 注意事項

1. **Job 名稱區分大小寫**
2. **只影響執行中的 builds**
   - 不影響 queue 中的 builds
   - 不影響已完成的 builds
3. **Build 會被標記為 ABORTED**
   - 停止的 builds 在歷史記錄中狀態為 ABORTED
   - 可以在 Jenkins UI 中查看中止原因
4. **權限需求**
   - 需要有 cancel build 的權限
   - 部分 job 可能有特殊權限限制
5. **即使沒有執行中的 builds，命令也會成功**
   - 不會回報錯誤
   - 這是預期行為
6. **執行中的 Pipeline stages**
   - 對於 Pipeline jobs，會嘗試中止當前執行的 stage
   - 某些 stage 可能無法立即中止（如正在執行的外部命令）

## 最佳實踐

### 確認後再停止

```bash
# 先查看執行中的 builds
jenkee list-builds my-job | head -5

# 確認後再停止
echo "確定要停止 my-job 的所有 builds? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
  jenkee stop-builds my-job
fi
```

### 記錄停止動作

```bash
# 記錄誰在何時停止了 builds
{
  echo "$(date): Stopped builds for $JOB_NAME by $USER"
  jenkee stop-builds $JOB_NAME
} | tee -a /var/log/jenkins-stops.log
```

### 搭配通知

```bash
# 停止 builds 並發送通知
jenkee stop-builds critical-job

# 發送通知（實際環境中使用 Slack、Email 等）
echo "Stopped builds for critical-job at $(date)" | \
  mail -s "Jenkins Alert" team@example.com
```

### 避免誤操作

```bash
# 使用函數包裝，增加確認步驟
safe_stop_builds() {
  local job_name=$1
  echo "⚠️  About to stop all running builds for: $job_name"
  echo "Press ENTER to continue, Ctrl+C to cancel"
  read
  jenkee stop-builds "$job_name"
}

# 使用
safe_stop_builds my-important-job
```

## 與其他命令組合

### 停止後檢查狀態

```bash
# 停止 builds 並查看結果
jenkee stop-builds my-job
sleep 2
jenkee list-builds my-job | head -3
```

### 停止後重新觸發

```bash
# 停止舊的 builds 並觸發新的
jenkee stop-builds my-job
jenkee build my-job -p VERSION=new-version
```

### 清理並重建

```bash
#!/bin/bash
# 完整的清理與重建流程

JOB_NAME="my-job"

echo "1. Stopping running builds..."
jenkee stop-builds $JOB_NAME

echo "2. Waiting for builds to stop..."
sleep 5

echo "3. Triggering new build..."
jenkee build $JOB_NAME -s

echo "✓ Rebuild complete"
```
