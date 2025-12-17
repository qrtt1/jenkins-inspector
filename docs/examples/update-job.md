# update-job - 更新 Job 配置

## 用途

從 XML 檔案更新現有 Jenkins job 的配置。這個工具可以幫助你批次修改 job 設定，或將某個 job 的配置同步到其他 jobs。

## 基本語法

```bash
jks update-job <job-name> < config.xml
```

或透過 pipe：

```bash
jks get-job <job-name> | jks update-job <job-name>
```

參數說明：
- `job-name` (必填)：要更新的 job 名稱
- XML 配置必須從 stdin 提供

## 功能說明

此指令會：
1. 驗證 Jenkins 認證設定
2. 從 stdin 讀取 XML 配置
3. 使用新的 XML 配置更新指定的 job
4. 更新會立即生效，不需要重新載入 Jenkins

## 執行範例

### 實際案例：加入 Downstream Job

這個範例展示如何為 `shield-console-release-image-auto` 加入新的 downstream job。

**背景**：這個 auto job 使用 conditional build steps 根據 Git tag 中的服務名稱來觸發對應的 release job。我們需要加入 `service-b` 的支援。

#### 步驟 1: 備份原始配置

```bash
$ mkdir -p /tmp/jenkins-test && cd /tmp/jenkins-test
$ jks get-job shield-console-release-image-auto > original.xml
$ cp original.xml backup-$(date +%Y%m%d-%H%M%S).xml
```

#### 步驟 2: 準備要插入的 XML 片段

創建新的 conditional build step：

```bash
$ cat > service-b-step.xml << 'EOF'
    <org.jenkinsci.plugins.conditionalbuildstep.singlestep.SingleConditionalBuilder plugin="conditional-buildstep@1.5.0">
      <condition class="org.jenkins_ci.plugins.run_condition.core.StringsMatchCondition" plugin="run-condition@243.v3c3f94e46a_8b_">
        <arg1>$SERVICE</arg1>
        <arg2>service-b</arg2>
        <ignoreCase>false</ignoreCase>
      </condition>
      <buildStep class="hudson.plugins.parameterizedtrigger.TriggerBuilder" plugin="parameterized-trigger@873.v8b_e37dd8418f">
        <configs>
          <hudson.plugins.parameterizedtrigger.BlockableBuildTriggerConfig>
            <configs>
              <hudson.plugins.parameterizedtrigger.PredefinedBuildParameters>
                <properties>tag=${gitlabSourceBranch}</properties>
                <textParamValueOnNewLine>false</textParamValueOnNewLine>
              </hudson.plugins.parameterizedtrigger.PredefinedBuildParameters>
            </configs>
            <projects>shield-console-service-b-release-image</projects>
            <condition>ALWAYS</condition>
            <triggerWithNoParameters>false</triggerWithNoParameters>
            <triggerFromChildProjects>false</triggerFromChildProjects>
            <buildAllNodesWithLabel>false</buildAllNodesWithLabel>
          </hudson.plugins.parameterizedtrigger.BlockableBuildTriggerConfig>
        </configs>
      </buildStep>
      <runner class="org.jenkins_ci.plugins.run_condition.BuildStepRunner$Fail" plugin="run-condition@243.v3c3f94e46a_8b_"/>
    </org.jenkinsci.plugins.conditionalbuildstep.singlestep.SingleConditionalBuilder>
EOF
```

#### 步驟 3: 使用 awk 插入新內容

在 `</builders>` 標籤之前插入新的 conditional build step：

```bash
$ awk '
  /  <\/builders>/ {
    while ((getline line < "service-b-step.xml") > 0) {
      print line
    }
    close("service-b-step.xml")
  }
  { print }
' original.xml > modified.xml
```

#### 步驟 4: 使用 update-job 更新配置

```bash
$ jks update-job shield-console-release-image-auto < modified.xml
✓ Successfully updated job 'shield-console-release-image-auto'
```

#### 步驟 5: 驗證更新結果

```bash
$ jks job-status shield-console-release-image-auto
=== Job: shield-console-release-image-auto ===

Status: ENABLED
Buildable: true

=== Health ===
Score: 100%
Description: Build stability: No recent builds failed.

=== Downstream Projects ===
  - shield-console-service-a-release-image
  - shield-console-service-b-release-image  ← ✓ 新增成功
  - shield-console-release-image-staging
  - shield-console-release-image-production

=== Upstream Projects ===
  (none)
```

成功！Downstream projects 從原本的 3 個增加到 4 個。

### 基本更新範例

```bash
# 取得配置
$ jks get-job my-job > /tmp/my-job.xml

# 編輯配置
$ vim /tmp/my-job.xml

# 更新 job
$ jks update-job my-job < /tmp/my-job.xml
✓ Successfully updated job 'my-job'
```

### 使用 sed 批次修改

```bash
# 修改某個設定值並更新
$ jks get-job my-job | sed 's/old-value/new-value/g' | jks update-job my-job
✓ Successfully updated job 'my-job'
```

### 缺少必要參數

```bash
$ jks update-job
Error: Job name is required.
Usage: jks update-job <job-name> < config.xml
```

### 沒有提供 XML 輸入

```bash
$ jks update-job my-job
Error: No XML input provided.
Usage: jks update-job <job-name> < config.xml
   or: jks get-job <job> | jks update-job <job>
```

### XML 輸入為空

```bash
$ echo "" | jks update-job my-job
Error: XML input is empty.
```

### Job 不存在

```bash
$ jks get-job existing-job | jks update-job non-existent-job
Error: Failed to update job 'non-existent-job'

ERROR: No such job 'non-existent-job'
```

## 常見使用情境

### 修改單一 Job 配置

```bash
# 1. 取得現有配置
jks get-job my-job > /tmp/my-job.xml

# 2. 編輯配置檔案
vim /tmp/my-job.xml

# 3. 更新 job
jks update-job my-job < /tmp/my-job.xml
```

### 使用 sed 批次修改

```bash
# 修改 job 中的某個值並更新
jks get-job my-job | sed 's/old-value/new-value/g' | jks update-job my-job
```

### 複製配置到另一個 Job

```bash
# 取得 job-a 的配置並套用到 job-b
jks get-job job-a | jks update-job job-b
```

### 批次更新多個 Jobs

```bash
# 將相同的修改套用到多個 jobs
for job in $(jks list-jobs AVENGERS | grep deploy); do
  jks get-job $job | sed 's/old-value/new-value/g' | jks update-job $job
done
```

### 更新特定環境的所有 Jobs

```bash
# 批次更新 staging 環境的 jobs
jks list-jobs --all | grep "staging" | while read job; do
  jks get-job $job | sed 's/old-setting/new-setting/g' | jks update-job $job
  echo "Updated: $job"
done
```

### 同步配置檔案

```bash
# 從版本控制系統更新 job
git pull
jks update-job my-job < configs/my-job.xml
```

## 輸出格式

成功時：
```
✓ Successfully updated job 'job-name'
```

失敗時：
```
Error: Failed to update job 'job-name'
<Jenkins CLI error message>
```

## 相關指令

- `jks get-job <job>` - 取得 job XML 配置
- `jks copy-job <source> <dest>` - 複製 job
- `jks job-diff <job1> <job2>` - 比較兩個 job 的配置差異
- `jks job-status <job>` - 檢查更新後的 job 狀態

## 注意事項

1. 更新會立即生效，無需重新載動 Jenkins
2. 更新操作無法復原，建議先備份原始配置
3. 如果 XML 格式錯誤，更新會失敗
4. 更新後的 job 會保留 build 歷史記錄
5. 更新不會影響正在執行中的 builds
6. 確保 XML 中引用的 credentials 和其他資源存在

## 安全性建議

### 更新前備份

```bash
# 更新前先備份
jks get-job my-job > backup/my-job-$(date +%Y%m%d-%H%M%S).xml

# 執行更新
jks update-job my-job < new-config.xml
```

### 驗證更新結果

```bash
# 更新後立即驗證
jks update-job my-job < new-config.xml
jks job-status my-job
jks get-job my-job > /tmp/verify.xml
diff /tmp/new-config.xml /tmp/verify.xml
```

### 測試後再套用到正式環境

```bash
# 1. 在測試 job 上先測試
jks copy-job production-job test-job
jks update-job test-job < new-config.xml

# 2. 驗證測試 job
jks job-status test-job

# 3. 確認無誤後套用到正式 job
jks update-job production-job < new-config.xml
```

## 批次操作範例

### 版本控制 Job 配置

```bash
#!/bin/bash
# sync-jobs.sh - 從 git repository 同步 job 配置

CONFIG_DIR="jenkins-configs"

# 拉取最新配置
git pull

# 更新所有 jobs
for config in $CONFIG_DIR/*.xml; do
  job_name=$(basename $config .xml)
  echo "Updating: $job_name"
  jks update-job $job_name < $config
done

echo "✓ All jobs synchronized"
```

### 批次修改腳本

```bash
#!/bin/bash
# batch-update.sh - 批次修改 jobs 的某個設定

PATTERN=$1  # 搜尋的 jobs pattern
OLD_VALUE=$2
NEW_VALUE=$3

if [ -z "$PATTERN" ] || [ -z "$OLD_VALUE" ] || [ -z "$NEW_VALUE" ]; then
  echo "Usage: $0 <job-pattern> <old-value> <new-value>"
  exit 1
fi

# 找出符合的 jobs 並更新
jks list-jobs --all | grep "$PATTERN" | while read job; do
  echo "Processing: $job"

  # 備份
  jks get-job $job > "backup/${job}.xml"

  # 更新
  jks get-job $job | sed "s/$OLD_VALUE/$NEW_VALUE/g" | jks update-job $job

  if [ $? -eq 0 ]; then
    echo "✓ Updated: $job"
  else
    echo "✗ Failed: $job"
  fi
done
```

使用方式：
```bash
./batch-update.sh "spider-app-production" "old-server" "new-server"
```

## 最佳實踐

1. **永遠先備份**
   ```bash
   mkdir -p backup
   jks get-job my-job > backup/my-job-$(date +%Y%m%d).xml
   ```

2. **使用版本控制**
   ```bash
   # 將 job 配置納入版本控制
   jks get-job my-job > configs/my-job.xml
   git add configs/my-job.xml
   git commit -m "Update my-job configuration"
   ```

3. **小步驟修改**
   - 一次只修改一個設定
   - 修改後立即測試
   - 確認無誤再進行下一個修改

4. **使用 job-diff 驗證**
   ```bash
   # 更新前後比較
   jks get-job my-job > /tmp/before.xml
   jks update-job my-job < new-config.xml
   jks get-job my-job > /tmp/after.xml
   diff /tmp/before.xml /tmp/after.xml
   ```

5. **在非尖峰時段更新**
   - 避免在 builds 執行時更新
   - 選擇使用率較低的時段進行批次更新

## 技術細節

### Jenkins CLI 命令

此工具封裝了 Jenkins CLI 的 `update-job` 命令：

```bash
java -jar jenkins-cli.jar update-job JOB < config.xml
```

### XML 格式要求

- 必須是有效的 Jenkins job 配置 XML
- 根元素通常是 `<project>` 或特定的 job 類型
- 必須包含所有必要的配置元素

### 與 get-job 的配合

`update-job` 是 `get-job` 的相反操作：
```bash
jks get-job my-job > config.xml  # 匯出
jks update-job my-job < config.xml  # 匯入
```
