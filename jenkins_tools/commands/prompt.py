"""Prompt command - AI Agent guidance for using jenkee"""

from jenkins_tools.core import Command


class PromptCommand(Command):
    """Display AI agent guidance for using jenkee CLI tool"""

    def execute(self) -> int:
        """Execute prompt command - show AI agent guidance"""
        prompt_text = """
# Jenkins Inspector (jenkee) - AI Agent Guide

## 關於 jenkee

Jenkins Inspector（CLI: `jenkee`）是一個 Jenkins CLI 工具，提供命令列介面來管理和探索 Jenkins 資源：
- 探索 Jenkins views 和 jobs 的架構
- 查看 job 配置、build 歷史與 console 輸出
- 管理 credentials metadata
- 比較不同 job 的配置差異
- 複製和更新 job 設定

註：為了相容舊用法，也提供 `jks` 作為 alias（功能相同）。

## 驗證流程

### Step 1: 驗證認證

首先執行 `jenkee auth` 驗證 Jenkins 連線：

```bash
jenkee auth
```

成功時會顯示：
```
Verifying authentication...
✓ Authenticated as: user@example.com
Authorities:
  authenticated
```

### Step 2: 認證失敗的處理

如果看到 "Error: Jenkins credentials not configured"，需要設定認證資訊：

```bash
# 1. 建立設定目錄
mkdir -p ~/.jenkins-inspector

# 2. 建立 .env 檔案
cat > ~/.jenkins-inspector/.env << EOF
JENKINS_URL=http://your-jenkins-server:8080/
JENKINS_USER_ID=your_email@example.com
JENKINS_API_TOKEN=your_api_token
EOF

# 3. 再次驗證
jenkee auth
```

**取得 API Token 的方式：**
Jenkins 網頁介面 > User > Configure > API Token

## 可用命令

執行 `jenkee help` 可查看所有命令列表，執行 `jenkee help <command>` 可查看特定命令的詳細說明與範例。

```
jenkee <command> [args]

Commands:
  help [command]                    顯示命令說明（可指定 command 查看詳細文件）
  auth                              驗證 Jenkins 認證
  list-views                        列出所有 views
  list-jobs <view>                  列出 view 中的 jobs
  get-job <job>                     取得 job XML 配置
  job-status <job>                  查看 job 狀態與觸發關係
  list-builds <job>                 列出 job 的 build 歷史
  console <job> [build]             取得 build console 輸出
  job-diff <job1> <job2>            比較兩個 job 配置差異
  list-credentials [domain]         列出 credentials metadata
  describe-credentials <id>         查看 credential 詳細資訊
  copy-job <source> <dest>          複製 job 為新 job
  update-job <job>                  更新 job 配置 (從 stdin)
  add-job-to-view <view> <job>...   將 jobs 加入 view

範例:
  jenkee help                          # 顯示所有命令
  jenkee help auth                     # 查看 auth 命令的詳細文件
  jenkee help job-status               # 查看 job-status 的使用範例
```

**重要：每個命令都有詳細的使用文件！**
使用 `jenkee help <command>` 可以看到：
- 命令的完整語法
- 參數說明
- 實際執行範例
- 輸出格式說明
- 常見使用情境

## 常見使用情境

### 情境 1: 探索 Jenkins 架構並檢查 Build 結果

完整的探索與除錯流程：

```bash
# 1. 驗證認證
jenkee auth

# 2. 列出所有 views
jenkee list-views

# 3. 列出特定 view 的 jobs
jenkee list-jobs <view-name>

# 4. 取得 job 的 XML 配置
jenkee get-job <job-name>

# 5. 查看 job 狀態與觸發關係
jenkee job-status <job-name>

# 6. 列出 build 歷史
jenkee list-builds <job-name>

# 7. 查看特定 build 的 console 輸出
jenkee console <job-name> <build-number>

# 或查看最新 build 的 console
jenkee console <job-name>
```

**使用時機：**
- 了解 Jenkins 的 job 組織結構
- 追蹤 build 失敗的原因
- 檢查 job 的觸發關係（upstream/downstream）
- 除錯 CI/CD pipeline 問題

### 情境 2: 比較 Jobs 與查找 Credentials

比較環境間的配置差異並確認 credentials：

```bash
# 1. 驗證認證
jenkee auth

# 2. 找到要比較的 jobs（通常是不同環境的同一服務）
jenkee list-jobs <view-name>

# 3. 比較兩個 job 的配置差異
jenkee job-diff <job-staging> <job-production>

# 4. 從 diff 結果中找到 credentialsId，列出所有 credentials
jenkee list-credentials

# 5. 列出特定 domain 的 credentials
jenkee list-credentials <domain-name>

# 6. 查看特定 credential 的詳細資訊
jenkee describe-credentials <credential-id>

# 7. 如需查看 secret 內容（請注意安全性）
jenkee describe-credentials <credential-id> --show-secret
```

**使用時機：**
- 設定新環境時，參考現有環境的配置
- 確認 staging 和 production 環境的差異
- 驗證 credentials 是否正確設定
- 排查因 credential 錯誤導致的部署失敗

### 情境 3: Job 管理操作

複製與更新 job 配置：

```bash
# 1. 複製現有 job 作為範本
jenkee copy-job <source-job> <new-job-name>

# 2. 取得 job 配置並修改
jenkee get-job <job-name> > job-config.xml
# 編輯 job-config.xml...

# 3. 更新 job 配置
jenkee update-job <job-name> < job-config.xml

# 4. 將 job 加入 view
jenkee add-job-to-view <view-name> <job-name>
```

**使用時機：**
- 為新專案建立 job（基於現有範本）
- 批次更新多個 job 的配置
- 組織 jobs 到不同的 views

## 提示

1. **所有 job 和 view 名稱都區分大小寫**
2. **使用 `jenkee help <command>` 查看命令的詳細說明**
3. **Credentials 的 secret 內容預設不會顯示，需要 `--show-secret` 參數**
4. **使用 `job-status` 可以看到 job 之間的觸發關係（upstream/downstream）**
5. **`console` 命令不帶 build number 時會顯示最新的 build**
6. **`job-diff` 輸出是 unified diff 格式，可以用標準工具處理**

## 快速參考

探索架構:
```bash
jenkee list-views
jenkee list-jobs <view>
jenkee job-status <job>
```

除錯 build:
```bash
jenkee list-builds <job>
jenkee console <job> [build]
```

管理 credentials:
```bash
jenkee list-credentials
jenkee describe-credentials <id>
```

比較與管理:
```bash
jenkee job-diff <job1> <job2>
jenkee copy-job <source> <dest>
```
"""
        print(prompt_text.strip())
        return 0
