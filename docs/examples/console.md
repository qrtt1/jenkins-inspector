# console - 取得 Build 的 Console 輸出

## 用途

取得指定 Jenkins job 的 build console 輸出，可用於檢視 build 執行的詳細日誌。

## 基本語法

```bash
# 取得最新 build 的 console 輸出
jks console <job-name>

# 取得指定 build number 的 console 輸出
jks console <job-name> <build-number>
```

## 功能說明

此指令會：
1. 檢查認證設定
2. 使用 Jenkins CLI 的 `console` 命令取得 console 輸出
3. 若未指定 build number，預設取得 lastBuild
4. 將完整 console 輸出到 stdout

## 執行範例

### 取得最新 Build 的 Console 輸出

```bash
$ jks console spider-shield-console-deploy-staging | tail -20
✅ Successfully initiated cache purge for register.html
Purging cache for register.js
Invalidation pending for [https://www.googleapis.com/compute/v1/projects/example-project-staging/global/urlMaps/static-assets-cdn-staging-lb]
Monitor its progress at [https://www.googleapis.com/compute/v1/projects/example-project-staging/global/operations/operation-1234567890]
✅ Successfully initiated cache purge for register.js
Purging cache for register.css
Invalidation pending for [https://www.googleapis.com/compute/v1/projects/example-project-staging/global/urlMaps/static-assets-cdn-staging-lb]
Monitor its progress at [https://www.googleapis.com/compute/v1/projects/example-project-staging/global/operations/operation-1234567891]
✅ Successfully initiated cache purge for register.css
Purging cache for publishers.json
Invalidation pending for [https://www.googleapis.com/compute/v1/projects/example-project-staging/global/urlMaps/static-assets-cdn-staging-lb]
Monitor its progress at [https://www.googleapis.com/compute/v1/projects/example-project-staging/global/operations/operation-1234567892]
✅ Successfully initiated cache purge for publishers.json
✨ All files uploaded successfully to gs://static-assets-staging/ and cache purge initiated
Public URLs:
https://storage.googleapis.com/static-assets-staging/register.html
https://storage.googleapis.com/static-assets-staging/register.js
https://storage.googleapis.com/static-assets-staging/register.css
https://storage.googleapis.com/static-assets-staging/publishers.json
Finished: SUCCESS
```

**說明**：
- 不指定 build number 時，預設取得 lastBuild 的 console 輸出
- 完整輸出可能很長，可配合 `tail`、`head`、`grep` 等工具處理

### 取得指定 Build Number 的 Console 輸出

```bash
$ jks console spider-shield-console-deploy-staging 107 | head -30
Started by user developer
Running as SYSTEM
[EnvInject] - Loading node environment variables.
Building remotely on jenkins-worker-01 (agent) in workspace /var/lib/jenkins/workspace/spider-shield-console-deploy-staging
The recommended git tool is: NONE
using credential fcc26b8a-ce9c-4ee0-9dff-dfab31a2393f
 > git rev-parse --resolve-git-dir /var/lib/jenkins/workspace/spider-shield-console-deploy-staging/.git # timeout=10
Fetching changes from the remote Git repository
 > git config remote.origin.url ssh://git@git.example.com:9527/team-alpha/sample-service.git # timeout=10
Fetching upstream changes from ssh://git@git.example.com:9527/team-alpha/sample-service.git
 > git --version # timeout=10
 > git --version # 'git version 1.8.3.1'
using GIT_SSH to set credentials jenkins-ssh-key
Verifying host key using manually-configured host key entries
 > git fetch --tags --progress ssh://git@git.example.com:9527/team-alpha/sample-service.git +refs/heads/*:refs/remotes/origin/* # timeout=10
 > git rev-parse refs/remotes/origin/staging/1.0.83^{commit} # timeout=10
 > git rev-parse staging/1.0.83^{commit} # timeout=10
Checking out Revision fd65f2ffe0bc17eaf84c97336f7b227a00224b42 (staging/1.0.83)
 > git config core.sparsecheckout # timeout=10
 > git checkout -f fd65f2ffe0bc17eaf84c97336f7b227a00224b42 # timeout=10
Commit message: "fix: adjust build steps"
First time build. Skipping changelog.
$ /usr/bin/gcloud auth activate-service-account jenkins@example-project-staging.iam.gserviceaccount.com --key-file /var/lib/jenkins/workspace/spider-shield-console-deploy-staging/gcloud.config1234567890/key.json
Activated service account credentials for: [jenkins@example-project-staging.iam.gserviceaccount.com]
[spider-shield-console-deploy-staging] $ /bin/bash -xe /tmp/jenkins16870481209062471273.sh
+ cd docker
+ ZONE=us-central1-a
+ PROJECT=example-project-staging
+ INSTANCE=spider-shield-console-staging
+ gcloud compute ssh spider-shield-console-staging --zone us-central1-a --project example-project-staging --tunnel-through-iap
```

**說明**：
- 指定 build number (107) 取得該次 build 的 console 輸出
- 可檢視 build 的詳細執行過程、git commit、執行指令等資訊

### 缺少參數

```bash
$ jks console
Error: Missing job name
Usage: jks console <job-name> [build-number]
```

### Job 不存在或 Build 不存在

```bash
$ jks console non-existent-job 999
Error: Failed to get console output for job 'non-existent-job' build 999
ERROR: No such job 'non-existent-job'; perhaps you meant 'existing-job'?
java.lang.IllegalArgumentException: No such job 'non-existent-job'; perhaps you meant 'existing-job'?
```

## 常見使用情境

### 檢查 Build 失敗原因

```bash
# 取得最新 build 的最後 50 行輸出
jks console my-job | tail -50

# 搜尋錯誤訊息
jks console my-job | grep -i error

# 搜尋特定關鍵字
jks console my-job 100 | grep "deployment"
```

### 比較不同 Build 的輸出

```bash
# 取得兩個 build 的輸出進行比較
jks console my-job 100 > build100.log
jks console my-job 101 > build101.log
diff build100.log build101.log
```

### 批次檢查最近的 Builds

結合 `list-builds` 批次檢查：

```bash
# 檢查最近 3 個 builds 的結束狀態
jks list-builds spider-shield-console-deploy-staging | head -3 | while read build; do
  echo "=== Build #$build ===="
  jks console spider-shield-console-deploy-staging $build | tail -1
  echo ""
done
```

### 即時監控 Build 進度

雖然此工具取得的是完整輸出，但可配合 shell 迴圈定期檢查：

```bash
# 每 10 秒檢查一次最新 build 的最後幾行
watch -n 10 "jks console my-job | tail -5"
```

### 擷取特定資訊

```bash
# 取得 git commit 資訊
jks console my-job | grep "Commit message"

# 取得部署的 tag 或版本
jks console my-job | grep "tag:"

# 取得執行時間相關資訊
jks console my-job | grep "Finished:"
```

## 輸出格式

- 完整的 console 文字輸出
- 包含 ANSI 控制碼（可能需要工具清理）
- 適合配合 pipe 和其他 Unix 工具處理
- 輸出到 stdout，錯誤訊息到 stderr

## 相關指令

- `jks list-builds <job>` - 列出 job 的所有 build numbers
- `jks list-jobs <view>` - 列出 view 中的所有 jobs

## 注意事項

1. Job 名稱區分大小寫
2. Build number 必須存在，否則會回報錯誤
3. 使用 `lastBuild` 會自動取得最新的 build（預設行為）
4. Console 輸出可能很大，建議配合 `head`、`tail`、`grep` 等工具過濾
5. 部分輸出包含 ANSI 控制碼，可能需要清理後再處理
