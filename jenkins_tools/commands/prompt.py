"""Prompt command - AI Agent guidance for using jenkee"""

import os
import sys
from pathlib import Path

from jenkins_tools.core import Command


class PromptCommand(Command):
    """Display AI agent guidance for using jenkee CLI tool"""

    def __init__(self, args=None):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
                  Can include --all flag to show dangerous commands guidance
                  Can include --ignore-override flag to ignore custom prompt files
        """
        self.args = args or []
        self.show_dangerous = "--all" in self.args
        self.ignore_override = "--ignore-override" in self.args

    def execute(self) -> int:
        """Execute prompt command - show AI agent guidance"""
        # If --ignore-override is set, skip custom prompt and use default
        if self.ignore_override:
            return self._show_default_prompt()

        # Check for custom prompt file from environment variable or default location
        custom_prompt_file = os.getenv("JENKINS_INSPECTOR_PROMPT_FILE")

        if custom_prompt_file:
            # Environment variable is set - must use this file
            custom_prompt_path = Path(custom_prompt_file)

            if not custom_prompt_path.exists():
                print(f"Error: Custom prompt file not found: {custom_prompt_file}", file=sys.stderr)
                return 1

            try:
                prompt_text = custom_prompt_path.read_text()
                if not prompt_text.strip():
                    print(f"Error: Custom prompt file is empty: {custom_prompt_file}", file=sys.stderr)
                    return 1
                print(prompt_text.strip())
                return 0
            except Exception as e:
                print(f"Error reading custom prompt file: {e}", file=sys.stderr)
                return 1

        # Check default location
        default_prompt_path = Path.home() / ".jenkins-inspector" / "prompt.md"
        if default_prompt_path.exists():
            try:
                prompt_text = default_prompt_path.read_text()
                if not prompt_text.strip():
                    print(f"Error: Custom prompt file is empty: {default_prompt_path}", file=sys.stderr)
                    return 1
                print(prompt_text.strip())
                return 0
            except Exception as e:
                print(f"Error reading custom prompt file: {e}", file=sys.stderr)
                return 1

        # Use default prompt
        return self._show_default_prompt()

    def _show_default_prompt(self) -> int:
        """Display the default built-in prompt"""
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
  domain list                       列出所有 credential domains
  domain create <name>              建立新 domain (需確認)
  copy-job <source> <dest>          複製 job 為新 job
  update-job <job>                  更新 job 配置 (從 stdin)
  groovy <script>                   執行 Groovy script
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

### 情境 2: 管理 Credentials 與 Domains

管理 credential domains 並查找 credentials：

```bash
# 1. 驗證認證
jenkee auth

# 2. 列出所有 credential domains
jenkee domain list

# 3. 建立新 domain（需確認）
jenkee domain create staging --description="Staging credentials" --yes-i-really-mean-it

# 4. 列出所有 credentials
jenkee list-credentials

# 5. 列出特定 domain 的 credentials
jenkee list-credentials <domain-name>

# 6. 查看特定 credential 的詳細資訊
jenkee describe-credentials <credential-id>

# 7. 如需查看 secret 內容（請注意安全性）
jenkee describe-credentials <credential-id> --show-secret
```

**使用時機：**
- 組織 credentials 到不同 domains（依環境、團隊或專案）
- 設定新環境時，建立對應的 domain
- 驗證 credentials 是否正確設定
- 排查因 credential 錯誤導致的部署失敗

### 情境 2.1: 建立 GCP credential 並套用到 job

建立 GCP credential，套用到使用 GCloudBuildWrapper 的 job：

```bash
# 1. 建立 GCP credential（建議用清楚的 ID，會顯示在 Jenkins 選單）
jenkee gcp credential create bugfix-sa /path/to/service-account.json

# 2. 複製範本 job
jenkee copy-job aaa-sa-test bugfix-sa-job

# 3. 取出 job XML 並更新 credentialsId
jenkee get-job bugfix-sa-job > job-config.xml
# 將 <credentialsId>aaa-sa</credentialsId> 改成 <credentialsId>bugfix-sa</credentialsId>
jenkee update-job bugfix-sa-job < job-config.xml

# 4. 觸發 build 並檢查 console
jenkee build bugfix-sa-job
jenkee console bugfix-sa-job
```

期望 console 看到：
- `Activated service account credentials for: [<service-account-email>]`

### 情境 3: 比較 Jobs 配置差異

比較環境間的配置差異：

```bash
# 1. 找到要比較的 jobs（通常是不同環境的同一服務）
jenkee list-jobs <view-name>

# 2. 比較兩個 job 的配置差異
jenkee job-diff <job-staging> <job-production>

# 3. 從 diff 結果中找到 credentialsId
# 可以用 describe-credentials 確認 credential 詳細資訊
```

**使用時機：**
- 確認 staging 和 production 環境的配置差異
- 找出環境間的設定不一致

### 情境 4: Job 管理操作

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

## ⚠️ groovy 命令 - 特別警告

`groovy` 命令是**最高風險**的命令，可以在 Jenkins server 上執行任意操作。

### AI Agent 必須遵守的使用規則：

**1. 優先檢查替代命令（必須）**

在考慮使用 groovy 前，必須先確認是否有專用命令：
- 列出 jobs → `jenkee list-jobs --all`
- 取得 job 配置 → `jenkee get-job <job>`
- 列出 credentials → `jenkee list-credentials`
- 觸發 build → `jenkee build <job>`
- 查看 build 歷史 → `jenkee list-builds <job>`
- 停止 builds → `jenkee stop-builds <job>`
- 建立 job → `jenkee create-job <job>`

**只有在確認沒有任何專用命令可以完成任務時，才考慮使用 groovy**

**2. 必須向使用者確認（必須）**

使用 groovy 前必須：
- 說明為什麼需要使用 groovy
- 說明已檢查過所有替代命令但都不適用
- 詳細說明 groovy script 會執行什麼操作
- 說明可能的影響範圍與風險
- **等待使用者明確同意後才執行**

**3. 必須詳細說明 Script 內容（必須）**

提供的說明必須包含：
- Script 會執行什麼操作（讀取 vs 修改）
- 會存取哪些資料或資源
- 會對系統造成什麼影響
- 操作是否可逆

### Groovy 的能力與風險

**可以執行的操作：**
- ✗ 修改或刪除 jobs 和 builds
- ✗ 修改 Jenkins 系統配置
- ✗ 讀取所有 credentials（包含敏感資料）
- ✗ 執行系統命令
- ✗ 造成不可逆的資料損失
- ✗ 影響 Jenkins 系統穩定性

### 正確與錯誤示範

**❌ 錯誤示範：**
```
User: 幫我列出所有 jobs
AI: 好的，我使用 groovy 列出
[直接執行 groovy script]  ← 錯誤！應該使用 list-jobs
```

**✓ 正確示範 1：**
```
User: 幫我列出所有 jobs
AI: 我使用 `jenkee list-jobs --all` 命令列出所有 jobs。
[執行 list-jobs --all]  ← 正確！使用專用命令
```

**✓ 正確示範 2（需要 groovy 的情況）：**
```
User: 幫我找出所有使用 azure-spn credential 的 jobs
AI: 這個需求沒有專用命令可以完成。我需要使用 groovy script 來查詢。

我打算執行以下 groovy script：
[顯示完整 script]

這個 script 會：
- 遍歷所有 jobs
- 檢查每個 job 的 XML 配置
- 找出使用 azure-spn credential 的 jobs
- 只執行讀取操作，不會修改任何資料

這是唯一的解決方式。可以執行嗎？
[等待使用者確認]
```

**詳細說明請執行：** `jenkee help groovy`

---

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

        # 如果有 --all flag，顯示危險命令的說明
        if self.show_dangerous:
            dangerous_commands = """

---

## ⚠️ 危險命令（需要確認）

以下命令會對 Jenkins 進行不可逆或影響重大的操作，預設需要互動式確認。
若要用在自動化腳本，可加上 `--yes-i-really-mean-it` 跳過確認。

- **delete-job**: 刪除 job（不可逆，會刪除所有 build 歷史）
- **disable-job**: 停用 job（會影響 job 的可用性）
- **enable-job**: 啟用 job（會恢復 job 的可用性）
- **delete-builds**: 刪除 build 記錄（不可逆，會永久刪除 build 記錄）
- **groovy**: 執行 Groovy script（最高風險）

這些命令使用前都必須：
1. 向使用者說明操作內容與影響
2. 取得使用者明確同意
3. 確認操作的必要性

---
"""
            print(dangerous_commands)

        return 0
