# enable-job - 啟用 Job

## AI Agent 使用限制

AI agent 在使用此命令前**必須**：
1. 向使用者說明將要啟用的 job 名稱
2. 說明啟用的影響（job 將可以被觸發執行）
3. 取得使用者明確同意後才執行

## 用途

啟用已停用的 Jenkins job(s)。啟用後的 job 可以被手動或自動觸發執行。

## 基本語法

```bash
# 啟用單一 job
jenkee enable-job <job-name>

# 啟用多個 jobs
jenkee enable-job <job-name1> <job-name2> [job-name3 ...]
```

## 參數說明

| 參數 | 說明 | 必填 |
|------|------|------|
| `<job-name>` | Job 名稱（可指定多個） | 是 |
| `--yes-i-really-mean-it` | 跳過互動式確認，直接執行（適合自動化腳本） | 否 |

## 功能說明

此指令會：
1. 驗證 Jenkins 認證設定
2. 啟用指定的 job(s)
3. 啟用後 job 可以正常觸發執行
4. 恢復定時觸發和 upstream/downstream 關係

## 執行範例

### 互動式確認（預設行為）

```bash
$ jenkee enable-job production-deploy
Are you sure you want to enable job 'production-deploy'? (y/N): y
✓ Successfully enabled job 'production-deploy'
```

### 取消啟用

```bash
$ jenkee enable-job production-deploy
Are you sure you want to enable job 'production-deploy'? (y/N): n
Operation cancelled.
```

### 使用確認 Flag（自動化腳本）

```bash
# 跳過互動式確認，直接執行
$ jenkee enable-job production-deploy --yes-i-really-mean-it
✓ Successfully enabled job 'production-deploy'
```

### 啟用多個 Jobs

```bash
$ jenkee enable-job job-a job-b job-c
Are you sure you want to enable 3 job(s)? (y/N): y
✓ Successfully enabled 3 job(s)
  - job-a
  - job-b
  - job-c
```

### 缺少必要參數

```bash
$ jenkee enable-job
Error: Missing job name(s)
Usage: jenkee enable-job <job-name> [job-name ...]
```

### Job 不存在

```bash
$ jenkee enable-job non-existent-job
Error: Failed to enable job 'non-existent-job'
ERROR: No such job 'non-existent-job'
```

## 常見使用情境

### 維護完成後重新啟用

```bash
# 維護前停用
jenkee disable-job production-deploy

# 進行維護作業...
# 修改配置、更新 credentials 等

# 維護完成，重新啟用
jenkee enable-job production-deploy
```

### 批次啟用新版本 Jobs

```bash
# 啟用新版本的相關 jobs
jenkee enable-job \
  app-v2-build \
  app-v2-test \
  app-v2-deploy
```

### 啟用前確認配置

```bash
#!/bin/bash
# 檢查 job 配置後再啟用

JOB_NAME="$1"

echo "Checking job configuration..."
jenkee get-job "$JOB_NAME" > /tmp/check.xml

# 檢查配置是否包含必要設定
if grep -q "required-parameter" /tmp/check.xml; then
  echo "✓ Configuration looks good"
  jenkee enable-job "$JOB_NAME"
else
  echo "✗ Configuration incomplete, not enabling"
  exit 1
fi
```

### 版本切換

```bash
#!/bin/bash
# 從舊版本切換到新版本

OLD_VERSION="v1"
NEW_VERSION="v2"

# 停用舊版本
echo "Disabling $OLD_VERSION jobs..."
jenkee disable-job app-${OLD_VERSION}-deploy

# 啟用新版本
echo "Enabling $NEW_VERSION jobs..."
jenkee enable-job app-${NEW_VERSION}-deploy

echo "✓ Switched from $OLD_VERSION to $NEW_VERSION"
```

### 定期啟用排程任務

```bash
#!/bin/bash
# 只在特定時段啟用 nightly builds

HOUR=$(date +%H)

if [ $HOUR -ge 22 ] || [ $HOUR -lt 6 ]; then
  # 晚上 10 點到早上 6 點啟用 nightly builds
  jenkee enable-job nightly-build
  echo "Nightly builds enabled"
else
  # 其他時段停用
  jenkee disable-job nightly-build
  echo "Nightly builds disabled"
fi
```

## 輸出格式

### 成功（單一 job）
```
✓ Successfully enabled job 'job-name'
```

### 成功（多個 jobs）
```
✓ Successfully enabled 3 job(s)
  - job-a
  - job-b
  - job-c
```

### 失敗
```
Error: Failed to enable job 'job-name'
[Jenkins error message]
```

## 相關指令

- `jenkee disable-job <job>` - 停用 job
- `jenkee job-status <job>` - 查看 job 狀態（包含是否已停用）
- `jenkee build <job>` - 觸發 job build
- `jenkee list-jobs --all` - 列出所有 jobs

## 注意事項

1. **恢復所有觸發機制**
   - 手動觸發
   - 定時觸發（cron）
   - Upstream job 觸發
   - SCM 變更觸發

2. **Job 名稱區分大小寫**

3. **權限需求**
   - 需要有 configure job 的權限

4. **立即生效**
   - 啟用後馬上可以觸發 build
   - 如果有定時設定，也會立即恢復

5. **查看狀態**
   - 使用 `jenkee job-status <job>` 確認 Disabled 欄位為 false

## 最佳實踐

### 啟用後驗證

```bash
#!/bin/bash
# 啟用後立即驗證

JOB_NAME="$1"

# 啟用 job
jenkee enable-job "$JOB_NAME"

# 等待一下
sleep 2

# 驗證狀態
STATUS=$(jenkee job-status "$JOB_NAME" | grep "Disabled:" | awk '{print $2}')

if [ "$STATUS" = "false" ]; then
  echo "✓ Job enabled successfully"
else
  echo "✗ Job may not be enabled properly"
  exit 1
fi
```

### 啟用並觸發測試 Build

```bash
#!/bin/bash
# 啟用 job 並立即觸發測試 build

JOB_NAME="$1"

# 啟用 job
jenkee enable-job "$JOB_NAME"

# 觸發測試 build
echo "Triggering test build..."
jenkee build "$JOB_NAME" -s

if [ $? -eq 0 ]; then
  echo "✓ Test build successful, job is working"
else
  echo "✗ Test build failed, check job configuration"
  exit 1
fi
```

### 條件式啟用

```bash
#!/bin/bash
# 只在特定條件下啟用

JOB_NAME="production-deploy"

# 檢查環境
if [ "$ENVIRONMENT" = "production" ]; then
  echo "Production environment detected"
  jenkee enable-job "$JOB_NAME"
else
  echo "Not production environment, skipping"
fi
```
