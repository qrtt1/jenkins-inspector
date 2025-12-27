# create-job - 建立新 Job

## 用途

從 XML 配置檔建立新的 Jenkins job。適用於快速複製現有 job 配置、批次建立相似 jobs 或從備份還原 job。

## 基本語法

```bash
# 從檔案建立
jenkee create-job <job-name> < config.xml

# 從現有 job 複製
jenkee get-job existing-job | jenkee create-job new-job

# 從備份還原
jenkee create-job restored-job < backup/job-config.xml
```

## 參數說明

| 參數 | 說明 | 必填 |
|------|------|------|
| `<job-name>` | 新 job 的名稱 | 是 |
| stdin | XML 配置（透過 stdin 輸入） | 是 |

## 功能說明

此指令會：
1. 驗證 Jenkins 認證設定
2. 從 stdin 讀取 XML 配置
3. 在 Jenkins 建立新 job
4. 如果 job 名稱已存在，操作會失敗

## 執行範例

### 從檔案建立 Job

```bash
$ jenkee create-job my-new-job < job-config.xml
✓ Successfully created job 'my-new-job'
```

### 複製現有 Job

```bash
$ jenkee get-job production-deploy | jenkee create-job staging-deploy
✓ Successfully created job 'staging-deploy'
```

### 批次建立 Jobs

```bash
#!/bin/bash
# 從 template 建立多個環境的 jobs

TEMPLATE="deployment-template"
ENVIRONMENTS=("dev" "staging" "production")

for env in "${ENVIRONMENTS[@]}"; do
  jenkee get-job $TEMPLATE | jenkee create-job "deploy-$env"
done
```

### 缺少必要參數

```bash
$ jenkee create-job
Error: Missing job name
Usage: jenkee create-job <job-name> < config.xml
   or: jenkee get-job existing-job | jenkee create-job new-job
```

### 未提供 XML 配置

```bash
$ jenkee create-job new-job
Error: No XML configuration provided via stdin
Usage: jenkee create-job <job-name> < config.xml
   or: jenkee get-job existing-job | jenkee create-job new-job
```

### Job 已存在

```bash
$ jenkee get-job old-job | jenkee create-job existing-job
Error: Failed to create job 'existing-job'
ERROR: Job 'existing-job' already exists
```

## 常見使用情境

### 快速複製並修改 Job

```bash
# 1. 複製現有 job
jenkee get-job prod-deploy > /tmp/new-job.xml

# 2. 編輯配置
vi /tmp/new-job.xml

# 3. 建立新 job
jenkee create-job test-deploy < /tmp/new-job.xml
```

### 建立多環境 Pipeline

```bash
#!/bin/bash
# 為不同環境建立 deployment jobs

BASE_JOB="app-deploy-template"

for env in dev staging production; do
  echo "Creating $env deployment job..."

  # 取得 template 並用 sed 替換環境變數
  jenkee get-job $BASE_JOB | \
    sed "s/ENVIRONMENT=template/ENVIRONMENT=$env/g" | \
    jenkee create-job "app-deploy-$env"
done
```

### 從備份還原

```bash
# 還原備份目錄中的所有 jobs
for config in backup/*.xml; do
  job_name=$(basename "$config" .xml)
  echo "Restoring $job_name..."
  jenkee create-job "$job_name" < "$config"
done
```

### 建立測試 Job

```bash
# 建立測試版本的 job 進行實驗
jenkee get-job critical-job | \
  sed 's/production/test/g' | \
  jenkee create-job critical-job-test
```

### 批次建立微服務 Jobs

```bash
#!/bin/bash
# 為所有微服務建立相同結構的 jobs

SERVICES=(
  "user-service"
  "order-service"
  "payment-service"
  "notification-service"
)

TEMPLATE_JOB="microservice-template"

for service in "${SERVICES[@]}"; do
  echo "Creating jobs for $service..."

  # Build job
  jenkee get-job $TEMPLATE_JOB | \
    sed "s/SERVICE_NAME=template/SERVICE_NAME=$service/g" | \
    jenkee create-job "${service}-build"

  # Deploy job
  jenkee get-job "${TEMPLATE_JOB}-deploy" | \
    sed "s/SERVICE_NAME=template/SERVICE_NAME=$service/g" | \
    jenkee create-job "${service}-deploy"
done
```

## 輸出格式

### 成功
```
✓ Successfully created job 'job-name'
```

### 失敗
```
Error: Failed to create job 'job-name'
[Jenkins error message]
```

## 相關指令

- `jenkee get-job <job>` - 取得 job XML 配置
- `jenkee copy-job <source> <dest>` - 直接複製 job（不需經過 XML）
- `jenkee update-job <job>` - 更新現有 job 配置
- `jenkee list-jobs --all` - 列出所有 jobs

## 注意事項

1. **Job 名稱必須是新的**
   - 不能覆寫現有 job
   - 使用 `update-job` 來更新現有 job

2. **XML 配置必須有效**
   - 格式錯誤會導致建立失敗
   - Jenkins 會驗證 XML schema

3. **Referenced 資源**
   - Credentials、nodes、views 等必須存在
   - 否則 job 會建立但可能無法正常運作

4. **權限需求**
   - 需要 CREATE 權限
   - 某些目錄可能有特殊限制

5. **Plugin 依賴**
   - 如果 XML 使用特定 plugin 功能
   - 該 plugin 必須在目標 Jenkins 安裝

6. **Build 歷史**
   - 新建立的 job 沒有 build 歷史
   - 只複製配置，不複製執行記錄

## 最佳實踐

### 驗證 XML 後再建立

```bash
# 先取得並檢查 XML
jenkee get-job source-job > /tmp/new-job.xml

# 檢查內容
cat /tmp/new-job.xml

# 確認無誤後建立
jenkee create-job new-job < /tmp/new-job.xml
```

### 使用版本控制

```bash
# 將 job 配置存入 git
mkdir -p jenkins-jobs
jenkee get-job my-job > jenkins-jobs/my-job.xml
git add jenkins-jobs/my-job.xml
git commit -m "Add my-job configuration"

# 需要時從 git 還原
jenkee create-job my-job < jenkins-jobs/my-job.xml
```

### 建立後驗證

```bash
# 建立 job
jenkee create-job new-job < config.xml

# 驗證建立成功
if jenkee list-jobs --all | grep -q "^new-job$"; then
  echo "✓ Job created successfully"

  # 檢查配置
  jenkee get-job new-job | head -20
else
  echo "✗ Job creation failed"
fi
```

### Template 管理

```bash
# 建立 templates 目錄
mkdir -p jenkins-templates

# 儲存常用 templates
jenkee get-job pipeline-template > jenkins-templates/pipeline.xml
jenkee get-job freestyle-template > jenkins-templates/freestyle.xml

# 從 template 建立新 job
cat jenkins-templates/pipeline.xml | \
  sed "s/PLACEHOLDER/$PROJECT_NAME/g" | \
  jenkee create-job "$PROJECT_NAME-build"
```

### 錯誤處理

```bash
#!/bin/bash
# 安全地建立 job

JOB_NAME="new-job"
CONFIG_FILE="config.xml"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Error: Config file not found: $CONFIG_FILE"
  exit 1
fi

if jenkee list-jobs --all | grep -q "^$JOB_NAME$"; then
  echo "Error: Job '$JOB_NAME' already exists"
  exit 1
fi

if jenkee create-job "$JOB_NAME" < "$CONFIG_FILE"; then
  echo "✓ Job created successfully"
else
  echo "✗ Failed to create job"
  exit 1
fi
```

## 與其他命令組合

### 複製並加入 View

```bash
# 複製 job 並加入到 view
jenkee get-job source-job | jenkee create-job new-job
jenkee add-job-to-view MY-VIEW new-job
```

### 建立並立即觸發

```bash
# 建立 job 並觸發第一次 build
jenkee create-job new-job < config.xml
jenkee build new-job
```

### 批次操作

```bash
# 複製多個 jobs 並重新命名
JOBS_TO_COPY=(
  "service-a-build"
  "service-a-deploy"
  "service-a-test"
)

for job in "${JOBS_TO_COPY[@]}"; do
  new_name="${job/service-a/service-b}"
  echo "Copying $job to $new_name..."
  jenkee get-job "$job" | \
    sed 's/service-a/service-b/g' | \
    jenkee create-job "$new_name"
done
```
