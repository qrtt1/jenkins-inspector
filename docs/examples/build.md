# build - 觸發 Jenkins Job Build

## 用途

觸發指定 Jenkins job 的 build，可選擇性地傳遞參數、等待完成或追蹤輸出。

## 基本語法

```bash
# 基本用法
jenkee build <job-name>

# 帶參數
jenkee build <job-name> -p key=value [-p key2=value2 ...]

# 等待完成
jenkee build <job-name> -s

# 追蹤執行（含輸出）
jenkee build <job-name> -f

# 組合使用
jenkee build <job-name> -p VERSION=1.0.0 -p ENV=staging -f
```

## 參數說明

| 參數 | 說明 | 必填 |
|------|------|------|
| `<job-name>` | Job 名稱 | 是 |
| `-p key=value` | Build 參數（可多次使用） | 否 |
| `-s` | 同步模式，等待 build 完成 | 否 |
| `-f` | 追蹤模式，等待完成並顯示進度（隱含 `-s`） | 否 |
| `-v` | 顯示 console 輸出（需配合 `-s` 或 `-f`） | 否 |

## 功能說明

此指令會：
1. 驗證 Jenkins 認證設定
2. 觸發指定 job 的 build
3. 可選擇性地：
   - 傳遞 build 參數
   - 等待 build 完成
   - 追蹤 build 進度
   - 顯示 console 輸出

## 執行範例

### 基本觸發 Build

```bash
$ jenkee build my-deployment-job
✓ Build triggered for job 'my-deployment-job'
```

### 帶參數觸發 Build

```bash
$ jenkee build release-job -p VERSION=2.1.0 -p ENVIRONMENT=production
✓ Build triggered for job 'release-job'
```

### 等待 Build 完成

```bash
$ jenkee build my-job -s
Started my-job #123
Completed my-job #123 : SUCCESS
```

**說明**：使用 `-s` 選項會等待 build 完成，exit code 會反映 build 結果（0 = 成功）

### 追蹤 Build 進度並顯示輸出

```bash
$ jenkee build my-job -f -v
Started my-job #124
Started by user Developer
Building in workspace /var/lib/jenkins/workspace/my-job
...
[build output]
...
Finished: SUCCESS
```

**說明**：
- `-f` 追蹤 build 進度（類似 `-s` 但不會傳遞中斷信號）
- `-v` 顯示 console 輸出

### 缺少必要參數

```bash
$ jenkee build
Error: Missing job name
Usage: jenkee build <job-name> [-p key=value ...] [-s] [-f] [-v]

Options:
  -p key=value  Build parameters (can be used multiple times)
  -s            Wait until build completion
  -f            Follow build progress (implies -s)
  -v            Print console output (use with -s or -f)
```

### Job 不存在

```bash
$ jenkee build non-existent-job
Error: Failed to build job 'non-existent-job'
ERROR: No such job 'non-existent-job'; perhaps you meant 'existing-job'?
```

## 常見使用情境

### 手動觸發 Production 部署

```bash
# 觸發 production 部署並追蹤結果
jenkee build prod-deploy -p VERSION=1.5.0 -p NOTIFY=true -f -v
```

### 批次觸發多個 Jobs

```bash
# 依序觸發一系列相關 jobs
for job in build-app build-api build-web; do
  echo "Triggering $job..."
  jenkee build $job -s
done
```

### 參數化 Build（從環境變數）

```bash
# 從環境變數讀取版本號
VERSION=$(cat version.txt)
jenkee build release-image -p VERSION=$VERSION -p PUSH=true
```

### 觸發並在背景等待

```bash
# 觸發 build 但不等待
jenkee build long-running-job &

# 或者使用 screen/tmux 追蹤長時間 build
screen -S mybuild jenkee build long-job -f -v
```

### CI/CD Pipeline 整合

```bash
#!/bin/bash
# deploy.sh - 完整部署流程

set -e  # Exit on error

echo "Building application..."
jenkee build app-build -p BRANCH=$GIT_BRANCH -s

echo "Building Docker image..."
jenkee build docker-image -p TAG=$VERSION -s

echo "Deploying to staging..."
jenkee build deploy-staging -p VERSION=$VERSION -f -v

echo "✓ Deployment completed successfully"
```

### 條件式觸發

```bash
# 只有在測試通過後才觸發部署
if jenkee build run-tests -s; then
  echo "Tests passed, deploying..."
  jenkee build deploy-staging -p VERSION=$VERSION
else
  echo "Tests failed, deployment cancelled"
  exit 1
fi
```

### 平行觸發多個 Builds

```bash
# 同時觸發多個獨立 builds
jenkee build service-a-build -p ENV=staging &
jenkee build service-b-build -p ENV=staging &
jenkee build service-c-build -p ENV=staging &

# 等待所有 builds 完成
wait

echo "All builds completed"
```

## 輸出格式

### 成功（異步模式）
```
✓ Build triggered for job 'job-name'
```

### 成功（同步模式 -s）
```
Started job-name #123
Completed job-name #123 : SUCCESS
```

### 成功（追蹤模式 -f -v）
```
Started job-name #124
[console output...]
Finished: SUCCESS
```

### 失敗
```
Error: Failed to build job 'job-name'
[Jenkins error message]
```

## 相關指令

- `jenkee list-builds <job>` - 查看 job 的 build 歷史
- `jenkee console <job> [build]` - 查看 build 的 console 輸出
- `jenkee job-status <job>` - 查看 job 狀態
- `jenkee stop-builds <job>` - 停止執行中的 builds

## 注意事項

1. **Job 名稱區分大小寫**
2. **參數格式**: `-p` 後面必須緊跟 `key=value` 格式
3. **同步模式 (-s) 的差異**:
   - Exit code 反映 build 結果（0=成功, 非0=失敗）
   - Ctrl+C 會中斷 build 本身
4. **追蹤模式 (-f) 的差異**:
   - Exit code 反映 build 結果
   - Ctrl+C 只中斷追蹤，不會中斷 build（exit code 125）
5. **參數化 Build**: Job 必須定義對應的 build 參數，否則參數會被忽略
6. **權限**: 需要有觸發 job build 的權限

## 最佳實踐

### 使用 -s 確保 Build 成功

```bash
# 在腳本中使用 -s 確保 build 成功才繼續
if jenkee build my-job -s; then
  echo "Build successful, proceeding..."
else
  echo "Build failed, stopping"
  exit 1
fi
```

### 記錄 Build 輸出

```bash
# 保存 build 輸出到檔案
jenkee build my-job -f -v 2>&1 | tee build-log-$(date +%Y%m%d-%H%M%S).txt
```

### 設定 Timeout

```bash
# 使用 timeout 避免永久等待
timeout 30m jenkee build long-job -s || {
  echo "Build timeout after 30 minutes"
  jenkee stop-builds long-job
  exit 1
}
```
