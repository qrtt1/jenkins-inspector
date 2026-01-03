# Test Plan for Command Whitelist Configuration

## 功能目標

實作 command whitelist configuration 機制，允許使用者透過設定檔或環境變數控制可用的 command。
這是 runtime 層級的控制，未啟用的 command 不會被載入或執行。

## 設計原則

1. **只支援白名單或全開模式**：不提供黑名單功能
   - 全開模式：`{"enabled_commands": ["*"]}`
   - 白名單模式：明確列出允許的 command
   - 新增的 command 預設不會自動啟用，必須有意識地加入白名單

2. **使用 JSON 格式**：使用 Python 內建的 `json` module
   - 不需要額外依賴
   - 大多數人熟悉的格式
   - 支援結構化設定

## 使用情境

此功能主要應對以下需求：

1. **安全考量**：預設停用危險命令（delete-job, groovy, gcp 等）
2. **分階段導入**：初次使用時只開放少數基本指令，熟悉後再逐步開放
3. **環境限制**：在特定環境（如：CI/CD）只允許特定操作
4. **團隊管理**：不同成員有不同權限等級

## 測試範圍

### 1. Configuration Loading

#### 1.1 設定檔格式支援
- [ ] 支援 JSON 格式設定檔（`~/.jenkins-inspector/config.json`）
- [ ] 支援專案層級設定檔（`.jenkee.json` 在當前目錄）
- [ ] 設定檔優先順序：專案 `.jenkee.json` > 使用者 `~/.jenkins-inspector/config.json` > 預設值（全開）

#### 1.2 環境變數支援
- [ ] 支援 `JENKEE_ENABLED_COMMANDS` 環境變數（逗號分隔清單）
- [ ] 環境變數優先級高於設定檔
- [ ] 支援 `*` 表示全開：`JENKEE_ENABLED_COMMANDS="*"`

#### 1.3 預設行為
- [ ] 無設定檔且無環境變數時，所有 command 都可用（全開模式）
- [ ] 空白 `enabled_commands` 陣列視為「不允許任何 command」（除了 help/prompt）
- [ ] 設定檔格式錯誤時顯示錯誤訊息並退出
- [ ] 新增的 command 在白名單模式下預設不可用

### 2. Command Whitelist Control

#### 2.1 基本 Command 控制
- [ ] 只啟用部分 command（如：`auth, list-jobs, get-job`）
- [ ] 未在 whitelist 中的 command 執行時顯示錯誤訊息
- [ ] 錯誤訊息提示如何啟用該 command

#### 2.2 Subcommand 控制（如 GCP）
- [ ] 完全停用 `gcp` subcommand
- [ ] 部分啟用 GCP 功能（如：只允許 `gcp credential list`）
- [ ] Subcommand help 只顯示啟用的 actions

#### 2.3 特殊 Command 處理
- [ ] `help` command 永遠可用
- [ ] `help` 輸出只顯示已啟用的 command
- [ ] `prompt` command 永遠可用
- [ ] `prompt` 輸出只包含已啟用的 command
- [ ] `config` command 永遠可用（用於管理設定）

### 3. Configuration Examples

所有範例使用 JSON 格式，設定檔位置：
- `~/.jenkins-inspector/config.json` (使用者層級)
- `.jenkee.json` (專案層級，優先權較高)

#### 3.1 完全開放模式（預設）
```json
{
  "enabled_commands": ["*"]
}
```
或不建立設定檔（預設行為）

#### 3.2 最小權限模式（僅唯讀）
僅提供查詢功能，完全不允許任何變更操作
```json
{
  "enabled_commands": [
    "auth",
    "list-views",
    "list-jobs",
    "get-job",
    "list-builds",
    "console",
    "job-status",
    "job-diff",
    "list-credentials",
    "describe-credentials"
  ]
}
```
註：`help`、`prompt`、`config` 永遠可用，不需明確列出

#### 3.3 新手模式（只開放基本功能）
限制只能使用最基本的幾個 command
```json
{
  "enabled_commands": [
    "auth",
    "list-views",
    "list-jobs",
    "get-job",
    "console"
  ]
}
```

#### 3.4 安全管理模式（排除危險操作）
允許一般管理功能，但不包含刪除和高危操作
```json
{
  "enabled_commands": [
    "auth",
    "list-views",
    "list-jobs",
    "get-job",
    "list-builds",
    "console",
    "job-status",
    "job-diff",
    "list-credentials",
    "describe-credentials",
    "add-job-to-view",
    "copy-job",
    "update-job",
    "create-job",
    "build",
    "stop-builds",
    "disable-job",
    "enable-job"
  ]
}
```
註：不包含 `delete-job`、`delete-builds`、`groovy`、`gcp`

#### 3.5 環境變數快速設定
```bash
# 只啟用唯讀功能
export JENKEE_ENABLED_COMMANDS="auth,list-views,list-jobs,get-job,console"

# 完全開放
export JENKEE_ENABLED_COMMANDS="*"

# 新手模式
export JENKEE_ENABLED_COMMANDS="auth,list-jobs,get-job"
```

### 4. Config Command

新增 `jenkee config` command 用於管理設定

#### 4.1 列出所有可用 command
```bash
$ jenkee config list-commands
Available commands:
  auth                 Verify Jenkins authentication
  list-views           List all views
  list-jobs            List jobs in a view
  get-job              Get job XML configuration
  ...
  gcp                  Manage GCP resources
  groovy               Execute Groovy script
  delete-job           Delete a job
  delete-builds        Delete builds
```

#### 4.2 產生範例設定檔
```bash
$ jenkee config init
Created configuration file: ~/.jenkins-inspector/config.json
Mode: full (all commands enabled)

$ jenkee config init --mode=readonly
Created configuration file: ~/.jenkins-inspector/config.json
Mode: readonly (only read commands enabled)

$ jenkee config init --mode=safe
Created configuration file: ~/.jenkins-inspector/config.json
Mode: safe (management commands enabled, dangerous commands disabled)

$ jenkee config init --mode=basic
Created configuration file: ~/.jenkins-inspector/config.json
Mode: basic (only basic commands enabled)
```

#### 4.3 顯示當前設定
```bash
$ jenkee config show
Configuration source: ~/.jenkins-inspector/config.json
Enabled commands (10):
  - auth
  - list-views
  - list-jobs
  - get-job
  - console
  - job-status
  - job-diff
  - list-credentials
  - describe-credentials
  - build

Disabled commands (14):
  - copy-job
  - update-job
  - create-job
  - delete-job
  - ...

Special commands (always enabled): help, prompt, config
```

#### 4.4 驗證設定檔
```bash
$ jenkee config validate
✓ Configuration file is valid
✓ All enabled commands exist
✓ 10 commands enabled, 14 commands disabled

$ jenkee config validate
✗ Configuration file has errors:
  - Unknown command: 'invalid-command'
  - Syntax error at line 5
```

### 5. Error Handling

#### 5.1 執行未啟用的 Command
```bash
$ jenkee delete-job my-job
Error: Command 'delete-job' is not enabled.

To enable this command, add it to your configuration file:
  ~/.jenkins-inspector/config.json

Example:
  {
    "enabled_commands": ["auth", "list-jobs", "delete-job"]
  }

Or set the environment variable:
  export JENKEE_ENABLED_COMMANDS="auth,list-jobs,delete-job"

Run 'jenkee config init' to generate a configuration file.
Run 'jenkee config list-commands' to see all available commands.
```

#### 5.2 設定檔格式錯誤
```bash
$ jenkee list-jobs
Error: Failed to load configuration file: ~/.jenkins-inspector/config.json
  JSON syntax error at line 5: Expecting ',' delimiter

Please fix the configuration file or remove it to use default settings.
Run 'jenkee config validate' to check your configuration.
```

### 6. Integration Tests

#### 6.1 Configuration File Loading
- [ ] 正確載入並解析 JSON 設定檔
- [ ] 偵測設定檔語法錯誤
- [ ] 處理不存在的設定檔（使用預設值：全開）
- [ ] 專案層級設定檔優先於使用者層級設定檔

#### 6.2 Environment Variable Override
- [ ] 環境變數覆蓋設定檔
- [ ] 環境變數格式驗證（逗號分隔）
- [ ] 清除環境變數後回到設定檔行為
- [ ] `JENKEE_ENABLED_COMMANDS="*"` 啟用所有 command

#### 6.3 Command Dispatch
- [ ] 啟用的 command 正常執行
- [ ] 未啟用的 command 被拒絕執行
- [ ] Help 輸出正確反映已啟用的 command
- [ ] Prompt 輸出只包含已啟用的 command

#### 6.4 Config Command Tests
- [ ] `config list-commands` 列出所有 command
- [ ] `config init` 產生預設設定檔（全開模式）
- [ ] `config init --mode=readonly` 產生唯讀模式設定
- [ ] `config init --mode=safe` 產生安全模式設定
- [ ] `config init --mode=basic` 產生基本模式設定
- [ ] `config show` 正確顯示當前啟用/停用的 command
- [ ] `config validate` 驗證設定檔格式與內容

## 測試執行方式

### 手動測試
1. 建立測試用設定檔
2. 依序測試每個情境
3. 驗證錯誤訊息正確顯示

### 自動化測試
- 新增 `tests/test_config.py` 測試 configuration loading
- 新增 `tests/test_command_whitelist.py` 測試 whitelist 機制
- 更新現有測試確保 backward compatibility

## 實作架構

### 核心模組

1. **Configuration Loader** (`jenkins_tools/config.py`)
   - 載入與解析 JSON 設定檔
   - 處理環境變數
   - 設定檔優先順序管理
   - 驗證設定內容

2. **Command Registry** (`jenkins_tools/command_registry.py`)
   - 維護所有可用 command 的清單
   - 提供 command metadata（名稱、描述、分類）
   - 判斷 command 是否啟用

3. **CLI Dispatcher** (修改 `jenkins_tools/cli.py`)
   - 在 dispatch 前檢查 command 是否啟用
   - 顯示適當的錯誤訊息

4. **Config Command** (`jenkins_tools/commands/config.py`)
   - 實作 `list-commands`、`init`、`show`、`validate` 子命令

### Command 分類

為了方便產生預設設定，定義以下分類：

- **readonly**: 唯讀操作（auth, list-*, get-*, console, job-status, job-diff, describe-credentials）
- **safe_write**: 安全的寫入操作（copy-job, update-job, create-job, add-job-to-view, build, stop-builds）
- **management**: 管理操作（disable-job, enable-job）
- **dangerous**: 危險操作（delete-job, delete-builds, groovy, gcp）

## 相關文件

建立後需要新增的文件：
- [ ] `docs/examples/config.md` - 設定檔使用範例
- [ ] 更新 `README.md` - 加入 configuration 章節
- [ ] 更新 AI prompt - 說明 command 可能因設定而不可用
- [ ] 更新 `help` command 輸出 - 說明如何使用 config command

## 預期完成標準

- [ ] 所有測試案例通過
- [ ] 文件完整（範例、說明）
- [ ] Backward compatible（無設定時行為不變）
- [ ] 錯誤訊息清楚易懂
- [ ] Help 輸出正確反映實際可用的 command
