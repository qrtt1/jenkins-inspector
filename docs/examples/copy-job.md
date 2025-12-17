# copy-job - 複製 Job

## 用途

複製現有的 Jenkins job 為新 job，保留原 job 的所有配置設定。這個工具可以幫助你快速建立相似的 jobs，特別適合用於建立新環境或複製 template。

## 基本語法

```bash
jks copy-job <source-job> <destination-job>
```

參數說明：
- `source-job` (必填)：來源 job 名稱
- `destination-job` (必填)：目標 job 名稱（必須是新的名稱）

## 功能說明

此指令會：
1. 驗證 Jenkins 認證設定
2. 複製來源 job 的完整配置（包含所有參數、建置步驟、觸發器等）
3. 建立新的 job
4. 如果目標 job 已存在，操作會失敗

## 執行範例

### 複製 Job

```bash
$ jks copy-job shield-console-deploy-staging shield-console-deploy-staging-test
✓ Successfully copied job 'shield-console-deploy-staging' to 'shield-console-deploy-staging-test'
```

### 驗證複製結果

```bash
$ jks list-jobs --all | grep "shield-console-deploy-staging"
shield-console-deploy-staging
shield-console-deploy-staging-test
```

### 缺少必要參數

```bash
$ jks copy-job source-job
Error: Source and destination job names are required.
Usage: jks copy-job <source-job> <destination-job>
```

### 來源 Job 不存在

```bash
$ jks copy-job non-existent-job new-job
Error: Failed to copy job 'non-existent-job' to 'new-job'

ERROR: No such job 'non-existent-job'; perhaps you meant 'spider-shield-console-deploy-staging'?
```

### 目標 Job 已存在

```bash
$ jks copy-job source-job existing-job
Error: Failed to copy job 'source-job' to 'existing-job'

ERROR: Job 'existing-job' already exists
```

## 常見使用情境

### 建立新環境的 Pipeline

從現有環境複製 jobs 到新環境：

```bash
# 複製 staging 環境的 jobs 到 staging 環境
jks copy-job spider-app-production-deploy-staging spider-app-production-deploy-staging
jks copy-job spider-app-production-release-image-staging spider-app-production-release-image-staging

# 將新 jobs 加入 view
jks add-job-to-view AVENGERS spider-app-production-deploy-staging spider-app-production-release-image-staging
```

### 建立 Job Template

複製現有 job 作為 template 基礎：

```bash
# 複製一個穩定的 job 作為 template
jks copy-job stable-deploy-job template-deploy-job

# 之後可以基於 template 建立新的 jobs
jks copy-job template-deploy-job my-new-service-deploy
```

### 建立測試 Job

在修改重要 job 前，先複製一份用於測試：

```bash
# 複製 productionuction job
jks copy-job critical-job critical-job-test

# 在 test job 上進行修改測試
jks get-job critical-job-test > /tmp/job.xml
# 編輯 /tmp/job.xml
# jks update-job critical-job-test < /tmp/job.xml

# 確認無誤後，將變更套用到正式 job
```

### 批次複製相關 Jobs

複製一組相關的 jobs：

```bash
# 定義要複製的 jobs
JOBS=(
  "myproject-release-image-auto"
  "myproject-release-image-staging"
  "myproject-deploy-staging"
)

# 批次複製並重新命名
for job in "${JOBS[@]}"; do
  NEW_JOB=$(echo $job | sed 's/staging/staging/')
  jks copy-job "$job" "$NEW_JOB"
done
```

### 跨專案複製配置

從另一個專案複製類似的 job 配置：

```bash
# 從 project-a 複製到 project-b
jks copy-job project-a-deploy project-b-deploy

# 之後使用 get-job 取得配置並修改專案特定的參數
jks get-job project-b-deploy > /tmp/project-b.xml
# 編輯 XML 檔案調整專案特定設定
```

## 輸出格式

成功時：
```
✓ Successfully copied job 'source-job' to 'destination-job'
```

失敗時：
```
Error: Failed to copy job 'source-job' to 'destination-job'
<Jenkins CLI error message>
```

## 相關指令

- `jks get-job <job>` - 取得 job XML 配置
- `jks list-jobs --all` - 列出所有 jobs
- `jks add-job-to-view <view> <job>` - 將複製的 job 加入 view
- `jks job-status <job>` - 檢查複製後的 job 狀態

## 注意事項

1. 目標 job 名稱必須是新的，不能覆寫現有 job
2. 複製的 job 會保留所有配置，包含：
   - 建置參數
   - 建置步驟
   - 觸發器設定
   - SCM 配置
   - Credentials 參考
3. 複製後的 job 不會自動加入任何 view，需手動使用 `add-job-to-view` 加入
4. 複製後的 job 預設為啟用狀態
5. Build 歷史記錄不會被複製
6. 如果來源 job 引用的 credentials 不存在，複製的 job 仍會建立但可能無法正常執行

## 最佳實踐

### 複製後立即調整配置

```bash
# 1. 複製 job
jks copy-job source-job new-job

# 2. 取得配置
jks get-job new-job > /tmp/new-job.xml

# 3. 編輯配置（修改環境變數、參數等）
vim /tmp/new-job.xml

# 4. 更新配置 (目前尚未實作 update-job)
# jks update-job new-job < /tmp/new-job.xml
```

### 使用命名規則

建立一致的命名規則，方便批次操作：

```bash
# 好的命名規則
{project}-{service}-{type}-{env}

# 範例
spider-app-production-api-deploy-staging
spider-app-production-api-deploy-staging
spider-app-production-api-deploy-production
```

### 驗證複製結果

複製後立即驗證：

```bash
# 複製
jks copy-job source-job new-job

# 驗證存在
jks list-jobs --all | grep new-job

# 檢查狀態
jks job-status new-job

# 比較配置
jks job-diff source-job new-job
```

## 工作流程整合

### 自動化建立新環境 Pipeline

```bash
#!/bin/bash
# setup-new-env.sh - 為新環境建立完整 pipeline

SOURCE_ENV=$1  # staging
TARGET_ENV=$2  # staging
PROJECT=$3     # spider-app-production-api

if [ -z "$SOURCE_ENV" ] || [ -z "$TARGET_ENV" ] || [ -z "$PROJECT" ]; then
  echo "Usage: $0 <source-env> <target-env> <project>"
  exit 1
fi

# 找出所有來源環境的 jobs
SOURCE_JOBS=$(jks list-jobs --all | grep "${PROJECT}.*-${SOURCE_ENV}")

# 複製每個 job
for source_job in $SOURCE_JOBS; do
  target_job=$(echo $source_job | sed "s/-${SOURCE_ENV}/-${TARGET_ENV}/")

  echo "Copying: $source_job -> $target_job"
  jks copy-job "$source_job" "$target_job"

  # 加入 view
  VIEW_NAME=$(echo $PROJECT | tr '[:lower:]' '[:upper:]')
  jks add-job-to-view "$VIEW_NAME" "$target_job"
done

echo "✓ New environment setup complete!"
```

使用方式：
```bash
./setup-new-env.sh staging staging spider-app-production-api
```
