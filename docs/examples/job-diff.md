# job-diff - 比較兩個 Job 的配置差異

## 用途

比較兩個 Jenkins jobs 的 XML 配置，以 unified diff 格式顯示差異，方便找出環境間的配置差異或檢查設定是否一致。

## 基本語法

```bash
jks job-diff <job-name-1> <job-name-2>
```

## 功能說明

此指令會：
1. 使用 `get-job` 取得兩個 jobs 的 XML 配置
2. 使用 Python difflib 產生 unified diff
3. 以標準 diff 格式顯示差異

## 執行範例

### 比較 Beta 與 Prod 的 Release Job

```bash
$ jks job-diff spider-shield-console-release-image-staging spider-shield-console-release-image-productionuction
--- spider-shield-console-release-image-staging
+++ spider-shield-console-release-image-productionuction
@@ -20,10 +20,10 @@
       <parameterDefinitions>
         <net.uaznia.lukanus.hudson.plugins.gitparameter.GitParameterDefinition plugin="git-parameter@444.vca_b_84d3703c2">
           <name>tag</name>
-          <uuid>aed2be50-5d85-4b2b-9a11-c92ea3f2e5c3</uuid>
+          <uuid>4eacab23-1293-4ce7-be5e-8f3e5accf9e3</uuid>
           <type>PT_TAG</type>
           <branch></branch>
-          <tagFilter>staging/*</tagFilter>
+          <tagFilter>production/*</tagFilter>
           <branchFilter>.*</branchFilter>
           <sortMode>DESCENDING_SMART</sortMode>
           <defaultValue></defaultValue>
@@ -33,7 +33,7 @@
         </net.uaznia.lukanus.hudson.plugins.gitparameter.GitParameterDefinition>
         <hudson.model.StringParameterDefinition>
           <name>project</name>
-          <defaultValue>spider-app-staging</defaultValue>
+          <defaultValue>spider-app-production</defaultValue>
           <trim>false</trim>
         </hudson.model.StringParameterDefinition>
       </parameterDefinitions>
@@ -108,7 +108,7 @@
   <buildWrappers>
     <com.byclosure.jenkins.plugins.gcloud.GCloudBuildWrapper plugin="gcloud-sdk@0.0.3">
       <installation>google-cloud-sdk</installation>
-      <credentialsId>spider-app-staging-gcp-jenkins-sa</credentialsId>
+      <credentialsId>spider-app-production-gcp-jenkins-sa</credentialsId>
     </com.byclosure.jenkins.plugins.gcloud.GCloudBuildWrapper>
   </buildWrappers>
```

**說明**：
- `-` 開頭的行表示 staging job 的配置
- `+` 開頭的行表示 production job 的配置
- 主要差異：tag filter (`staging/*` vs `production/*`)、project 名稱、credentials ID

### 比較 Deploy Jobs

```bash
$ jks job-diff spider-shield-console-deploy-staging spider-shield-console-deploy-productionuction | head -50
--- spider-shield-console-deploy-staging
+++ spider-shield-console-deploy-productionuction
@@ -19,10 +19,10 @@
       <parameterDefinitions>
         <net.uaznia.lukanus.hudson.plugins.gitparameter.GitParameterDefinition plugin="git-parameter@0.9.6">
           <name>tag</name>
-          <uuid>ad12faaa-e846-4627-9613-669bcdff3ff8</uuid>
+          <uuid>2605042b-3851-424d-8520-4991d66c5f5a</uuid>
           <type>PT_TAG</type>
           <branch></branch>
-          <tagFilter>staging/*</tagFilter>
+          <tagFilter>production/*</tagFilter>
           <branchFilter>.*</branchFilter>
           <sortMode>DESCENDING_SMART</sortMode>
           <defaultValue></defaultValue>
@@ -32,12 +32,12 @@
         </net.uaznia.lukanus.hudson.plugins.gitparameter.GitParameterDefinition>
         <hudson.model.StringParameterDefinition>
           <name>instance</name>
-          <defaultValue>spider-shield-console-staging</defaultValue>
+          <defaultValue>spider-shield-console-production</defaultValue>
           <trim>false</trim>
         </hudson.model.StringParameterDefinition>
         <hudson.model.StringParameterDefinition>
           <name>project</name>
-          <defaultValue>spider-app-staging</defaultValue>
+          <defaultValue>spider-app-production</defaultValue>
           <trim>false</trim>
         </hudson.model.StringParameterDefinition>
```

**說明**：
- Deploy jobs 的差異包含：tag filter、instance 名稱、project 名稱
- 所有 credentials ID 也都有環境差異

### 兩個 Jobs 完全相同

```bash
$ jks job-diff job-a job-a
No differences found between 'job-a' and 'job-a'
```

### 缺少參數

```bash
$ jks job-diff job-a
Error: Missing job names
Usage: jks job-diff <job-name-1> <job-name-2>
```

### Job 不存在

```bash
$ jks job-diff job-a non-existent-job
Error: Failed to get job 'non-existent-job'
ERROR: No such job 'non-existent-job'
```

## 常見使用情境

### 驗證環境一致性

檢查 staging 和 production 環境的 jobs 配置是否遵循相同模式：

```bash
# 比較 release jobs
jks job-diff \
  spider-shield-console-release-image-staging \
  spider-shield-console-release-image-productionuction

# 比較 deploy jobs
jks job-diff \
  spider-shield-console-deploy-staging \
  spider-shield-console-deploy-productionuction
```

### 找出關鍵差異

使用 grep 過濾特定配置項目：

```bash
# 只看 tag filter 差異
jks job-diff job-staging job-production | grep -A 1 -B 1 tagFilter

# 只看 credentials 差異
jks job-diff job-staging job-production | grep -A 1 -B 1 credentialsId

# 只看 project/instance 參數差異
jks job-diff job-staging job-production | grep -A 1 -B 1 "defaultValue"
```

### 儲存 Diff 報告

將差異存成檔案供後續分析：

```bash
jks job-diff job-staging job-production > diff-report.txt
```

### 批次比對多組 Jobs

```bash
#!/bin/bash
# 比對所有環境對應的 jobs

JOBS=(
  "spider-app-production-shield-console-release-image"
  "spider-app-production-shield-console-deploy"
)

for job in "${JOBS[@]}"; do
  echo "=== Comparing $job-staging vs $job-production ==="
  jks job-diff "${job}-staging" "${job}-production" | grep "^[-+]" | head -20
  echo ""
done
```

### 檢查配置更新前後差異

在更新 job 配置前後進行比對：

```bash
# 更新前先匯出配置
jks get-job my-job > my-job-before.xml

# ... 透過 Jenkins UI 更新配置 ...

# 比對差異
jks get-job my-job > my-job-after.xml
diff my-job-before.xml my-job-after.xml
```

或直接使用兩個時間點的配置：

```bash
# 假設有舊版本的 job 名稱包含日期
jks job-diff my-job-old my-job
```

### 製作環境遷移清單

找出需要調整的配置項目：

```bash
# 列出所有差異行數
jks job-diff job-staging job-production | grep "^@@" | wc -l

# 製作完整差異報告
echo "## Beta to Prod Migration Checklist" > migration.md
echo "" >> migration.md
jks job-diff job-staging job-production | grep -E "^[-+].*<" >> migration.md
```

### 對比 Diff 輸出格式

```bash
# 使用外部 diff 工具比對
jks get-job job-a > /tmp/job-a.xml
jks get-job job-b > /tmp/job-b.xml
diff -u /tmp/job-a.xml /tmp/job-b.xml

# 或使用其他 diff 工具
vimdiff /tmp/job-a.xml /tmp/job-b.xml
```

## 輸出格式

使用標準的 unified diff 格式：

### Header
```
--- job-name-1
+++ job-name-2
```

### Change Blocks
```
@@ -20,10 +20,10 @@
```
- `-20,10`：從第一個檔案的第 20 行開始，共 10 行
- `+20,10`：從第二個檔案的第 20 行開始，共 10 行

### Diff Lines
- ` `（空格）：兩個檔案相同的行
- `-`：只存在於第一個檔案（job-1）
- `+`：只存在於第二個檔案（job-2）

## 與其他工具搭配

### 結合 grep 過濾

```bash
# 只看新增的行
jks job-diff job-a job-b | grep "^+"

# 只看刪除的行
jks job-diff job-a job-b | grep "^-"

# 忽略 UUID 和 secretToken 的差異
jks job-diff job-a job-b | grep -v -E "(uuid|secretToken)"
```

### 結合 wc 統計

```bash
# 統計差異行數
jks job-diff job-a job-b | grep -E "^[-+]" | wc -l

# 統計變更區塊數量
jks job-diff job-a job-b | grep "^@@" | wc -l
```

### 使用 colordiff 增加可讀性

```bash
# 如果有安裝 colordiff
jks job-diff job-a job-b | colordiff | less -R
```

## 相關指令

- `jks get-job <job>` - 取得 job 的 XML 配置
- `jks job-status <job>` - 查看 job 狀態
- 外部工具：`diff`、`vimdiff`、`colordiff`

## 注意事項

1. Job 名稱區分大小寫
2. 輸出為 unified diff 格式，可配合標準 Unix 工具處理
3. UUID 和 secretToken 的差異通常可忽略（每個 job 都不同）
4. 大型 XML 配置的 diff 輸出可能很長，建議使用 `head` 或 `grep` 過濾
5. 此命令基於 `get-job`，因此需要有讀取 job 配置的權限
