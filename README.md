# Jenkins Inspector

Jenkins CLI 工具，提供命令列介面來管理和探索 Jenkins jobs、builds、credentials 等資源。

主要 CLI 命令為 `jenkee`（保留 `jks` 作為相容 alias）。

## 安裝

### 使用 pipx 安裝（推薦）

```bash
pipx install git+https://github.com/qrtt1/jenkins-inspector
```

### 開發模式安裝

如果想要參與開發或修改程式碼：

```bash
# Clone repository
git clone https://github.com/qrtt1/jenkins-inspector
cd jenkins-inspector

# 啟用虛擬環境
source venv/bin/activate

# 以 editable 模式安裝
pip install -e .
```

## 與 AI Agent 的互動

如果你不熟悉 Jenkins Inspector 的使用方式，或想讓 AI agent 協助你完成 Jenkins 相關任務，可以使用 `prompt` 命令：

```bash
jenkee prompt
```

這個命令會輸出專為 AI agent 設計的使用指引，包含：
- Jenkins Inspector 的功能說明
- 各命令的使用方式與情境
- AI agent 操作建議與最佳實踐

你可以將輸出的內容複製給你的 AI assistant（如 ChatGPT、Claude），讓它更了解如何協助你使用 Jenkins Inspector。

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
| `prompt` | 顯示 AI agent 使用指引 | `jenkee prompt` |
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

### 危險命令（需要使用者確認）

以下命令會對 Jenkins 進行不可逆或影響重大的操作，AI agent 在使用前必須向使用者確認：

| 命令 | 說明 | 範例 |
|------|------|------|
| `delete-job` ⚠️ | 刪除 job（不可逆） | `jenkee delete-job <job> [job ...]` |
| `disable-job` ⚠️ | 停用 job | `jenkee disable-job <job> [job ...]` |
| `enable-job` ⚠️ | 啟用 job | `jenkee enable-job <job> [job ...]` |
| `delete-builds` ⚠️ | 刪除 build 記錄（不可逆） | `jenkee delete-builds <job> <range>` |
| `groovy` ⚠️ | 執行 Groovy script（最高風險） | `jenkee groovy <script>` |

**注意**: 危險命令預設不會顯示在 `jenkee help` 中。使用 `jenkee help --ask-before-run-commands` 可以查看完整命令列表。

詳細使用說明請參考 [docs/examples/](docs/examples/) 目錄下的各命令文件。

## 主要功能

### 1. 探索 Jenkins 架構
- 列出所有 views 和 jobs
- 查看 job 配置與狀態
- 追蹤 job 觸發關係

### 2. Build 管理
- 觸發 job builds（支援參數、同步與追蹤模式）
- 停止執行中的 builds
- 查看 build 歷史與 console 輸出
- 刪除舊的 build 記錄（需確認）

### 3. Job 管理
- 建立、複製、更新 job 配置
- 刪除 jobs（需確認）
- 停用/啟用 jobs（需確認）
- 比較 job 配置差異
- 將 jobs 加入 views

### 4. Credentials 管理
- 列出所有 credentials metadata
- 查看 credentials 類型與相關資訊
- 驗證 credentials 配置

### 5. 進階操作
- 執行 Groovy scripts（需確認，最高權限）

## 文件

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
- 功能完整實作（包含 help、prompt、example 文件）
- 通過所有整合測試

