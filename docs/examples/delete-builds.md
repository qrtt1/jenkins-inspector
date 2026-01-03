# delete-builds - 刪除 Build 記錄

## ⚠️ 警告

**這是一個危險且不可逆的操作！**

- 刪除 build 記錄會永久移除指定的 build 歷史
- 此操作無法復原
- Build artifacts、logs 和測試結果都會被刪除
- 建議謹慎使用，只刪除確實不需要的舊 builds

## AI Agent 使用限制

AI agent 在使用此命令前**必須**：
1. 向使用者說明將要刪除的 job 名稱和 build 範圍
2. 說明刪除的影響（build 記錄永久移除）
3. 建議保留最近的 builds，只刪除舊的 builds
4. 取得使用者明確同意後才執行

## 用途

刪除指定 Jenkins job 的 build 記錄。可以刪除單一 build 或指定範圍的 builds。

## 基本語法

```bash
# 刪除單一 build
jenkee delete-builds <job-name> <build-number>

# 刪除 build 範圍
jenkee delete-builds <job-name> <start-number>-<end-number>
```

## 參數說明

| 參數 | 說明 | 必填 |
|------|------|------|
| `<job-name>` | Job 名稱 | 是 |
| `<build-number>` | 單一 build 編號 | 是（擇一） |
| `<start>-<end>` | Build 範圍（包含起終點） | 是（擇一） |
| `--yes-i-really-mean-it` | 跳過互動式確認，直接執行（適合自動化腳本） | 否 |

## 功能說明

此指令會：
1. 驗證 Jenkins 認證設定
2. 刪除指定的 build 記錄
3. 同時刪除 build artifacts、logs 和測試結果
4. 操作不可逆

## 執行範例

### 互動式確認（預設行為）

```bash
$ jenkee delete-builds my-job 100
Are you sure you want to delete build(s) 100 for job 'my-job'? (y/N): y
✓ Successfully deleted build(s) 100 for job 'my-job'
```

### 取消刪除

```bash
$ jenkee delete-builds my-job 1-50
Are you sure you want to delete build(s) 1-50 for job 'my-job'? (y/N): n
Operation cancelled.
```

### 使用確認 Flag（自動化腳本）

```bash
# 跳過互動式確認，直接執行
$ jenkee delete-builds my-job 1-50 --yes-i-really-mean-it
✓ Successfully deleted build(s) 1-50 for job 'my-job'
```

### 缺少必要參數

```bash
$ jenkee delete-builds my-job
Error: Missing required arguments
Usage: jenkee delete-builds <job-name> <build-range>

Build range can be:
  - Single build number: 123
  - Build range: 100-150
```

### Build 不存在

```bash
$ jenkee delete-builds my-job 9999
Error: Failed to delete build(s) 9999 for job 'my-job'
ERROR: No such build #9999
```

## 常見使用情境

### 清理舊的 Build 記錄

```bash
#!/bin/bash
# 只保留最近 100 個 builds，刪除其他舊 builds

JOB_NAME="my-job"
KEEP_LAST=100

# 取得最新 build 編號
LATEST=$(jenkee list-builds "$JOB_NAME" | head -1 | awk '{print $1}' | tr -d '#')

# 計算要刪除的範圍
DELETE_END=$((LATEST - KEEP_LAST))

if [ $DELETE_END -gt 0 ]; then
  echo "Deleting builds 1-$DELETE_END for $JOB_NAME..."
  jenkee delete-builds "$JOB_NAME" "1-$DELETE_END"
else
  echo "No old builds to delete"
fi
```

### 刪除失敗的 Builds

```bash
#!/bin/bash
# 找出並刪除所有失敗的 builds（謹慎使用！）

JOB_NAME="test-job"

# 列出所有失敗的 builds
FAILED_BUILDS=$(jenkee list-builds "$JOB_NAME" | grep "FAILURE" | awk '{print $1}' | tr -d '#')

echo "Failed builds found:"
echo "$FAILED_BUILDS"

read -p "Delete all failed builds? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
  # 逐個刪除（因為可能不連續）
  echo "$FAILED_BUILDS" | while read build_num; do
    jenkee delete-builds "$JOB_NAME" "$build_num"
  done
else
  echo "Cancelled"
fi
```

### 定期清理維護腳本

```bash
#!/bin/bash
# 定期清理超過 90 天的 builds

JOB_NAME="my-job"
DAYS_TO_KEEP=90

# 計算日期門檻（Unix timestamp）
CUTOFF_DATE=$(date -d "$DAYS_TO_KEEP days ago" +%s)

# 找出需要刪除的 builds
# 注意：這需要解析每個 build 的時間戳記
# 實際使用時可能需要更複雜的邏輯

# 簡化版：只保留最近 200 個 builds
LATEST=$(jenkee list-builds "$JOB_NAME" | head -1 | awk '{print $1}' | tr -d '#')
DELETE_END=$((LATEST - 200))

if [ $DELETE_END -gt 0 ]; then
  jenkee delete-builds "$JOB_NAME" "1-$DELETE_END"
fi
```

### 清理特定範圍的測試 Builds

```bash
# 刪除實驗性測試的 builds
jenkee delete-builds experimental-feature 50-100

# 確認刪除結果
jenkee list-builds experimental-feature | head -20
```

### 錯誤刪除後的處理

```bash
#!/bin/bash
# 雖然刪除不可逆，但可以記錄刪除動作

JOB_NAME="$1"
BUILD_RANGE="$2"

# 記錄刪除動作
echo "$(date): Deleting builds $BUILD_RANGE from $JOB_NAME" >> deletion-log.txt

# 執行刪除
jenkee delete-builds "$JOB_NAME" "$BUILD_RANGE"

# 觸發新 build 補充
# jenkee build "$JOB_NAME"
```

## 輸出格式

### 成功
```
✓ Successfully deleted build(s) 1-50 for job 'job-name'
```

### 失敗
```
Error: Failed to delete build(s) 100 for job 'job-name'
[Jenkins error message]
```

## 相關指令

- `jenkee list-builds <job>` - 查看 build 歷史
- `jenkee console <job> [build]` - 查看 build console 輸出
- `jenkee delete-job <job>` - 刪除整個 job（包含所有 builds）
- `jenkee build <job>` - 觸發新 build

## 注意事項

1. **操作不可逆**
   - 刪除後無法復原
   - Build artifacts 和 logs 都會被刪除
   - 測試結果和報告也會消失

2. **Build 編號不會重置**
   - 刪除 builds 後，新 build 的編號會繼續遞增
   - 不會填補被刪除的編號

3. **範圍包含起終點**
   - `1-50` 會刪除 build #1 到 #50（包含兩端）

4. **不存在的 Build**
   - 如果範圍中某些 build 不存在，命令可能部分成功
   - 建議先用 `list-builds` 確認 build 編號

5. **權限需求**
   - 需要有刪除 build 的權限

6. **影響趨勢圖表**
   - 刪除 builds 會影響 Jenkins 的趨勢圖表
   - 可能導致圖表出現斷點

## 最佳實踐

### 刪除前備份重要資訊

```bash
#!/bin/bash
# 刪除前備份 build logs

JOB_NAME="my-job"
BUILD_RANGE="1-50"
BACKUP_DIR="build-logs-backup"

mkdir -p "$BACKUP_DIR/$JOB_NAME"

# 備份要刪除的 builds 的 logs
for i in $(seq 1 50); do
  echo "Backing up build #$i..."
  jenkee console "$JOB_NAME" "$i" > "$BACKUP_DIR/$JOB_NAME/build-$i.log" 2>/dev/null
done

echo "Backup completed"

# 確認後刪除
read -p "Proceed with deletion? (yes/no): " confirm
if [ "$confirm" = "yes" ]; then
  jenkee delete-builds "$JOB_NAME" "$BUILD_RANGE"
fi
```

### 設定保留策略

```bash
#!/bin/bash
# 自動保留策略：保留最近 N 個成功的 builds

JOB_NAME="production-deploy"
KEEP_SUCCESS=10

# 找出成功的 builds
SUCCESS_BUILDS=$(jenkee list-builds "$JOB_NAME" | grep "SUCCESS" | head -$KEEP_SUCCESS | awk '{print $1}' | tr -d '#')

# 取得最小的成功 build 編號
MIN_KEEP=$(echo "$SUCCESS_BUILDS" | tail -1)

if [ ! -z "$MIN_KEEP" ] && [ "$MIN_KEEP" -gt 1 ]; then
  DELETE_END=$((MIN_KEEP - 1))
  if [ $DELETE_END -gt 0 ]; then
    echo "Keeping builds >= #$MIN_KEEP"
    echo "Deleting builds 1-$DELETE_END"
    jenkee delete-builds "$JOB_NAME" "1-$DELETE_END"
  fi
fi
```

### 分批刪除大量 Builds

```bash
#!/bin/bash
# 分批刪除避免一次刪太多

JOB_NAME="high-frequency-job"
TOTAL_DELETE=1000
BATCH_SIZE=100

for start in $(seq 1 $BATCH_SIZE $TOTAL_DELETE); do
  end=$((start + BATCH_SIZE - 1))
  if [ $end -gt $TOTAL_DELETE ]; then
    end=$TOTAL_DELETE
  fi

  echo "Deleting builds $start-$end..."
  jenkee delete-builds "$JOB_NAME" "$start-$end"

  # 間隔一下避免負載過高
  sleep 2
done
```

### 只刪除非關鍵 Job 的 Builds

```bash
#!/bin/bash
# 定義關鍵 jobs，只清理非關鍵的

CRITICAL_JOBS=(
  "production-deploy"
  "hotfix-deploy"
  "security-scan"
)

ALL_JOBS=$(jenkee list-jobs --all)

for job in $ALL_JOBS; do
  # 檢查是否為關鍵 job
  is_critical=false
  for critical in "${CRITICAL_JOBS[@]}"; do
    if [ "$job" = "$critical" ]; then
      is_critical=true
      break
    fi
  done

  if [ "$is_critical" = false ]; then
    echo "Cleaning non-critical job: $job"
    # 只保留最近 50 個 builds
    latest=$(jenkee list-builds "$job" | head -1 | awk '{print $1}' | tr -d '#')
    if [ ! -z "$latest" ] && [ "$latest" -gt 50 ]; then
      delete_end=$((latest - 50))
      jenkee delete-builds "$job" "1-$delete_end"
    fi
  else
    echo "Skipping critical job: $job"
  fi
done
```
