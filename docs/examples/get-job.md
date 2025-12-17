# get-job - 取得 Jenkins Job 配置

## 用途

取得指定 Jenkins job 的 XML 配置檔案，用於研究和分析 job 的完整設定。

## 基本語法

```bash
jks get-job <job-name>
```

## 功能說明

此指令會：
1. 檢查認證設定
2. 使用 Jenkins CLI 的 `get-job` 指令
3. 取得完整的 job XML 配置
4. 輸出到 stdout

## 執行範例

### 取得 Job 配置

```bash
$ jks get-job spider-shield-console-deploy-staging
<?xml version='1.1' encoding='UTF-8'?>
<project>
  <actions/>
  <description></description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.plugins.jira.JiraProjectProperty plugin="jira@3.3">
      <siteName>http://jira.example.com/</siteName>
    </hudson.plugins.jira.JiraProjectProperty>
    ...
  </properties>
  ...
</project>
```

**說明**：
- 輸出完整的 XML 配置
- 包含所有 job 設定：參數、觸發器、建置步驟等
- 可以重導向到檔案儲存

### 儲存到檔案

```bash
$ jks get-job spider-shield-console-deploy-staging > job-config.xml
```

**說明**：
- 將 XML 輸出儲存到檔案
- 方便後續分析或備份

### 缺少參數

```bash
$ jks get-job
Error: Missing job name
Usage: jks get-job <job-name>
```

### Job 不存在

```bash
$ jks get-job non-existent-job
Error: Failed to get config for job 'non-existent-job'
ERROR: No such job 'non-existent-job'
```

**說明**：
- 當 job 不存在時會顯示錯誤
- 確認 job 名稱是否正確（區分大小寫）

## 常見使用情境

### 研究現有配置

分析現有 job 的配置模式：

```bash
# 取得配置並用編輯器查看
jks get-job spider-shield-console-deploy-staging > deploy-staging.xml
code deploy-staging.xml

# 研究配置中的關鍵設定
# - 參數定義 (<parameterDefinitions>)
# - Git 配置 (<scm>)
# - 建置觸發器 (<triggers>)
# - 建置步驟 (<builders>)
```

### 比較不同環境的配置

比較 staging 和 production 環境的差異：

```bash
# 取得兩個環境的配置
jks get-job spider-shield-console-deploy-staging > deploy-staging.xml
jks get-job spider-shield-console-deploy-productionuction > deploy-production.xml

# 使用 diff 比較
diff deploy-staging.xml deploy-production.xml

# 或使用更友善的工具
code --diff deploy-staging.xml deploy-production.xml
```

### 批次備份配置

備份特定 view 的所有 jobs：

```bash
# 建立備份目錄
mkdir -p backups/spider-app-production

# 批次備份
jks list-jobs AVENGERS | while read job; do
  echo "Backing up: $job"
  jks get-job "$job" > "backups/spider-app-production/${job}.xml"
done
```

### 分析參數設定

提取 job 的參數定義：

```bash
# 使用 grep 提取參數相關設定
jks get-job spider-shield-console-deploy-staging | \
  grep -A 10 "<parameterDefinitions>"

# 使用 xmllint 格式化並查看
jks get-job spider-shield-console-deploy-staging | \
  xmllint --format - | less
```

### 搜尋特定配置

在配置中搜尋特定關鍵字：

```bash
# 檢查是否使用特定 plugin
jks get-job spider-shield-console-deploy-staging | \
  grep "git-parameter"

# 查看 Git repository 設定
jks get-job spider-shield-console-deploy-staging | \
  grep -A 5 "<url>"
```

## XML 配置結構

常見的重要區塊：

```xml
<project>
  <!-- Job 描述 -->
  <description>...</description>

  <!-- 參數定義 -->
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <!-- Git 參數、字串參數等 -->
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>

  <!-- Source Control 設定 -->
  <scm class="hudson.plugins.git.GitSCM">
    <userRemoteConfigs>
      <hudson.plugins.git.UserRemoteConfig>
        <url>...</url>
      </hudson.plugins.git.UserRemoteConfig>
    </userRemoteConfigs>
  </scm>

  <!-- 建置觸發器 -->
  <triggers>
    <!-- Webhook、定時建置等 -->
  </triggers>

  <!-- 建置步驟 -->
  <builders>
    <!-- Shell script、Docker 指令等 -->
  </builders>
</project>
```

## 相關指令

- `jks list-jobs <view>` - 列出可用的 job 名稱
- `jks list-views` - 列出所有 views

## 注意事項

1. Job 名稱區分大小寫
2. 輸出的 XML 包含完整配置，可能很長
3. 建議使用 `xmllint` 或 XML 編輯器查看
4. 可以搭配 `grep`、`xmllint` 等工具分析
5. 適合用於備份、比較、學習現有配置
