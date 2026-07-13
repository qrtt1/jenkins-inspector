# jenkee

[![PyPI version](https://badge.fury.io/py/jenkee.svg)](https://pypi.org/project/jenkee/)
[![Python Support](https://img.shields.io/pypi/pyversions/jenkee.svg)](https://pypi.org/project/jenkee/)
[![Tests](https://github.com/qrtt1/jenkins-inspector/actions/workflows/test.yml/badge.svg)](https://github.com/qrtt1/jenkins-inspector/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> [!NOTE]
> **讓 AI Agent 幫你探索和管理 Jenkins 的 CLI 工具**
>
> Jenkins CLI 工具，提供命令列介面來管理和探索 Jenkins jobs、builds、credentials 等資源。主要 CLI 命令為 `jenkee`（保留 `jks` 作為相容 alias）。

## 為什麼需要 jenkee？

我對 Jenkins Web UI 不太在行。每次要看 job 的設定，都得展開一堆選單才能找到資訊。更麻煩的是，很多重要的配置細節藏在 XML 裡，不下載回來根本看不清楚。

最初，我只是想做一個簡單的工具：用命令列出 jobs、抓下 XML、然後自己 diff 比對。那時候我直接呼叫 `jenkins-cli.jar`，還特地寫了 prompt 來教 AI agent 怎麼用。 但很快就發現問題了。AI agent 常常搞錯 `jenkins-cli.jar` 的參數格式，明明教過還是會出錯。我開始思考：與其一直教它用複雜的工具，不如直接把工具改簡單一點？ 於是我把常用的操作包裝成簡單的 CLI 命令。神奇的事情發生了：AI agent 幾乎不用特別教，看看 help 就能正確使用。原來簡化介面真的能讓 AI 更好發揮。

後來工具慢慢長大了。從最初的 list、get、diff，擴展到完整的 Jenkins 管理功能。現在有 24 個命令和完整的測試覆蓋，但核心理念沒變：讓 AI agent 幫你探索和管理 Jenkins。

一開始我們專注在唯讀操作：列出 jobs、抓配置、看 console。這些操作很安全，不會改變 Jenkins 的任何東西。這也是為什麼專案的 repository 名稱叫 `jenkins-inspector`，因為那時候真的只有檢視、探索資料的功能。後來才慢慢加入管理功能：建立 job、觸發 build、刪除資源。這些會變更 Jenkins 內容的操作，我們都加上了特別的提醒和確認機制。

## 特色

- 🚀 24 個完整的 Jenkins CLI 命令
- 🧪 完整的測試覆蓋所有功能
- 🤖 專為 AI Agent 設計的互動模式
- 🔒 支援多種 Jenkins credentials 類型
- 📦 透過 PyPI 輕鬆安裝
- 💬 清晰的 help 訊息，AI agent 容易理解

## 快速開始

```bash
# 安裝
pip install jenkee

# 設定認證
mkdir -p ~/.jenkins-inspector
cat > ~/.jenkins-inspector/.env << EOF
JENKINS_URL=http://your-jenkins-server:8080/
JENKINS_USER_ID=your_email@example.com
JENKINS_API_TOKEN=your_api_token
EOF

# 驗證連線
jenkee auth

# 列出所有 jobs
jenkee list-jobs --all

# 觸發 build
jenkee build my-job
```

## 安裝

### 從 PyPI 安裝（推薦）

```bash
pip install jenkee
```

或使用 pipx（建議用於 CLI 工具）：

```bash
pipx install jenkee
```

### 開發模式安裝

如果想要參與開發或修改程式碼：

```bash
# Clone repository
git clone https://github.com/qrtt1/jenkins-inspector
cd jenkins-inspector

# 啟用虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 以 editable 模式安裝
pip install -e ".[dev]"
```

> [!WARNING]
> **使用 AI Agent 的重要提醒**
>
> jenkee 設計來讓 AI agent 幫你操作 Jenkins。但有些操作會真的改變你的 Jenkins 環境，像是建立 job、觸發 build、刪除資源。
> 危險命令需要互動式確認；若要用在自動化腳本，請加上 `--yes-i-really-mean-it` 以跳過確認。
>
> **強烈建議你在「需要逐一授權」的模式下使用 AI agent。** 每次 AI 要執行命令時，你都應該先看過才放行。特別是那些會寫入或刪除的操作。
>
> 安全的做法：
> - 讓 AI agent 在每個命令執行前先告訴你它要做什麼
> - 自己檢查命令的參數和影響範圍
> - 確認沒問題後才讓它執行
> - 對於危險操作（刪除、更新配置），一定要親自確認
>
> 查看哪些命令需要特別注意：
> ```bash
> jenkee help --all
> ```
>
> 詳細的危險命令說明請參考 [README.advanced.md](README.advanced.md)。

## 與 AI Agent 協作

jenkee 從一開始就是設計給 AI agent 用的。命令結構很簡單：`jenkee <command> [options]`，不需要記憶複雜的參數組合。

每個命令都有詳細的 help 說明和範例（`jenkee help <command>`）。AI agent 看一眼就知道怎麼用。輸出格式也很規律，方便它解析和理解。

如果你想讓 Claude Code 幫你操作 Jenkins，直接安裝下面的 `jenkins-helper` skill 即可，不需要額外準備 prompt 文字。

### Claude Code Skill

如果你使用 [Claude Code CLI](https://github.com/anthropics/claude-code)，可以透過 marketplace 安裝 `jenkins-helper` plugin，它整合了 jenkee 的完整功能和最佳實踐，並附帶一個攔截危險 jenkee 指令、提醒確認目標站台的 PreToolUse hook。

```bash
/plugin marketplace add qrtt1/jenkins-inspector
/plugin install jenkins-helper@jenkins-inspector
```

plugin 原始碼位於 [`plugins/jenkins-helper/`](plugins/jenkins-helper/)。

## 設定認證

```bash
# 建立設定檔目錄
mkdir -p ~/.jenkins-inspector

# 編輯 .env 檔案
cat > ~/.jenkins-inspector/.env << EOF
JENKINS_URL=http://your-jenkins-server:8080/
JENKINS_USER_ID=your_email@example.com
JENKINS_API_TOKEN=your_api_token
EOF

# 驗證認證
jenkee auth
```

## 可用命令

### 一般命令

| 命令 | 說明 | 範例 |
|------|------|------|
| `help` | 顯示命令說明 | `jenkee help [command]` |
| `auth` | 驗證 Jenkins 認證 | `jenkee auth` |
| `list-views` | 列出所有 views | `jenkee list-views` |
| `list-jobs` | 列出 view 中的 jobs | `jenkee list-jobs AVENGERS` |
| `get-job` | 取得 job XML 配置 | `jenkee get-job <job-name>` |
| `list-builds` | 列出 job 的 build 歷史 | `jenkee list-builds <job-name>` |
| `console` | 取得 build console 輸出 | `jenkee console <job-name> [build]` |
| `job-status` | 查看 job 狀態與觸發關係 | `jenkee job-status <job-name>` |
| `job-diff` | 比較兩個 job 配置差異 | `jenkee job-diff <job1> <job2>` |
| `list-credentials` | 列出 Jenkins credentials metadata | `jenkee list-credentials [domain]` |
| `describe-credentials` | 查看特定 credential 詳細資訊 | `jenkee describe-credentials <id> [--show-secret]` |
| `add-job-to-view` | 將 jobs 加入到 view | `jenkee add-job-to-view <view> <job> [job ...]` |
| `copy-job` | 複製 job 為新 job | `jenkee copy-job <source> <destination>` |
| `update-job` | 更新 job 配置 | `jenkee update-job <job> < config.xml` |
| `build` | 觸發 job build | `jenkee build <job> [-p key=value] [-s] [-f]` |
| `stop-builds` | 停止執行中的 builds | `jenkee stop-builds <job> [job ...]` |
| `create-job` | 建立新 job | `jenkee create-job <job> < config.xml` |
| `profile` | 管理多組 Jenkins 連線 profile（多站台） | `jenkee profile list\|use\|current` |

詳細使用說明請參考 [docs/examples/](docs/examples/) 目錄下的各命令文件。

進階與危險命令請參考 [README.advanced.md](README.advanced.md)。

## 主要功能

### 1. 探索 Jenkins 架構
- 列出所有 views 和 jobs
- 查看 job 配置與狀態
- 追蹤 job 觸發關係

### 2. Build 管理
- 觸發 job builds（支援參數、同步與追蹤模式）
- 停止執行中的 builds
- 查看 build 歷史與 console 輸出

### 3. Job 管理
- 建立、複製、更新 job 配置
- 比較 job 配置差異
- 將 jobs 加入 views

### 4. Credentials 管理
- 列出所有 credentials metadata
- 查看 credentials 類型與相關資訊
- 驗證 credentials 配置

## 文件

- [README.advanced.md](README.advanced.md) - 進階與危險命令
- [CODING_GUIDE.md](CODING_GUIDE.md) - 專案開發指南
- [docs/examples/](docs/examples/) - 各命令使用範例

## 開發指引

如果你是 AI agent 正在開發此專案，請**務必先閱讀 [CODING_GUIDE.md](CODING_GUIDE.md)**。

該文件包含：
- 專案架構原則與設計模式
- 新增 command 的完整流程
- 程式碼格式化規範（Black）
- AI Agent 開發 checklist

遵循 CODING_GUIDE 可確保：
- 程式碼風格一致
- 功能完整實作（包含 help、example 文件）
- 通過所有整合測試
