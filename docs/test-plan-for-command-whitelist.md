# Test Plan for Command Whitelist Configuration

## 功能目標

實作 command whitelist configuration 機制，允許使用者透過設定檔或環境變數控制可用的 command。
這是 runtime 層級的控制，未啟用的 command 不會被載入或執行。

## 使用情境

此功能主要應對以下需求：

1. **安全考量**：預設停用危險命令（delete-job, groovy, gcp 等）
2. **分階段導入**：初次使用時只開放少數基本指令，熟悉後再逐步開放
3. **環境限制**：在特定環境（如：CI/CD）只允許特定操作
4. **團隊管理**：不同成員有不同權限等級

## 測試範圍

### 1. Configuration Loading

#### 1.1 設定檔格式支援
- [ ] 支援 YAML 格式設定檔（`~/.jenkins-inspector/config.yaml`）
- [ ] 支援專案層級設定檔（`.jenkee.yaml` 在當前目錄）
- [ ] 設定檔優先順序：專案 > 使用者 home > 預設值

#### 1.2 環境變數支援
- [ ] 支援 `JENKEE_ENABLED_COMMANDS` 環境變數（逗號分隔清單）
- [ ] 環境變數優先級高於設定檔
- [ ] 支援 `JENKEE_DISABLED_COMMANDS` 環境變數（黑名單模式）

#### 1.3 預設行為
- [ ] 無設定檔時，所有 command 都可用
- [ ] 空白設定視為「允許全部」
- [ ] 設定檔格式錯誤時顯示錯誤訊息並退出

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

### 3. Configuration Examples

#### 3.1 最小權限模式（僅唯讀）
僅提供查詢功能，完全不允許任何變更操作
```yaml
enabled_commands:
  - auth
  - list-views
  - list-jobs
  - get-job
  - list-builds
  - console
  - job-status
  - job-diff
  - list-credentials
  - describe-credentials
  # help 和 prompt 永遠可用，不需明確列出
```

#### 3.2 排除危險命令模式
預設全部啟用，但明確停用危險操作
```yaml
disabled_commands:
  - delete-job
  - delete-builds
  - groovy
  - gcp
  # 其他所有 command 都可用
```

#### 3.3 新手模式（只開放基本功能）
限制只能使用最基本的幾個 command
```yaml
enabled_commands:
  - auth
  - list-views
  - list-jobs
  - get-job
  - console
```

#### 3.4 進階使用者模式（允許管理但不含 GCP）
```yaml
enabled_commands:
  - "*"  # 全部啟用

disabled_commands:
  - gcp  # 明確停用 GCP
```

#### 3.5 完全開放模式
```yaml
# 空檔案或不設定，所有 command 都可用
enabled_commands:
  - "*"
```

#### 3.6 細緻的 Command 分類控制
```yaml
# 使用 command 分組來管理
command_groups:
  readonly:
    - auth
    - list-views
    - list-jobs
    - get-job
    - list-builds
    - console
    - job-status
    - job-diff
    - list-credentials
    - describe-credentials

  safe_write:
    - copy-job
    - update-job
    - create-job
    - add-job-to-view
    - build

  dangerous:
    - delete-job
    - delete-builds
    - disable-job
    - enable-job
    - groovy

  cloud_integration:
    - gcp

# 只啟用特定群組
enabled_groups:
  - readonly
  - safe_write
  # dangerous 和 cloud_integration 未啟用
```

#### 3.7 環境變數快速設定
```bash
# 只啟用唯讀功能
export JENKEE_ENABLED_COMMANDS="auth,list-views,list-jobs,get-job,console"

# 停用危險命令
export JENKEE_DISABLED_COMMANDS="delete-job,delete-builds,groovy,gcp"
```

### 4. Error Handling

#### 4.1 執行未啟用的 Command
```bash
$ jenkee gcp credential create test-sa /path/to/key.json
Error: Command 'gcp' is not enabled.

To enable this command, add it to your configuration file:
  ~/.jenkins-inspector/config.yaml

Or set the environment variable:
  export JENKEE_ENABLED_COMMANDS="gcp,auth,list-jobs,..."

Run 'jenkee help config' for more information.
```

#### 4.2 執行未啟用的 Subcommand Action
```bash
$ jenkee gcp credential create test-sa /path/to/key.json
Error: GCP action 'create' is not enabled.

Enabled actions: list, describe

To enable this action, update your configuration file.
Run 'jenkee help config' for more information.
```

### 5. Integration Tests

#### 5.1 Configuration File Loading
- [ ] 正確載入並解析 YAML 設定檔
- [ ] 偵測設定檔語法錯誤
- [ ] 處理不存在的設定檔（使用預設值）

#### 5.2 Environment Variable Override
- [ ] 環境變數覆蓋設定檔
- [ ] 環境變數格式驗證
- [ ] 清除環境變數後回到設定檔行為

#### 5.3 Command Dispatch
- [ ] 啟用的 command 正常執行
- [ ] 未啟用的 command 被拒絕執行
- [ ] Help 輸出正確反映已啟用的 command

## 測試執行方式

### 手動測試
1. 建立測試用設定檔
2. 依序測試每個情境
3. 驗證錯誤訊息正確顯示

### 自動化測試
- 新增 `tests/test_config.py` 測試 configuration loading
- 新增 `tests/test_command_whitelist.py` 測試 whitelist 機制
- 更新現有測試確保 backward compatibility

## 相關文件

建立後需要新增的文件：
- [ ] `docs/examples/config.md` - 設定檔使用範例
- [ ] 更新 `README.md` - 加入 configuration 章節
- [ ] 更新 AI prompt - 說明 command 可能因設定而不可用

## 預期完成標準

- [ ] 所有測試案例通過
- [ ] 文件完整（範例、說明）
- [ ] Backward compatible（無設定時行為不變）
- [ ] 錯誤訊息清楚易懂
- [ ] Help 輸出正確反映實際可用的 command
