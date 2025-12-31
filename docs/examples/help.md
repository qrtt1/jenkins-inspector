# help - 顯示命令說明

## 用途

顯示 `jenkee` 工具的命令列表或特定命令的詳細說明文件。

註：`jks` 為相容 alias，功能相同（建議以 `jenkee` 為主）。

## 基本語法

```bash
jenkee help              # 顯示所有可用命令
jenkee help <command>    # 顯示特定命令的詳細說明
```

參數說明：
- 無參數：顯示所有可用命令的列表
- `command` (選填)：要查看詳細說明的命令名稱

## 功能說明

此指令會：
1. 不帶參數時：列出所有可用命令及其簡短說明
2. 帶命令名稱時：顯示該命令的完整文件（從內建文件讀取）
3. 命令不存在時：顯示錯誤訊息並提示使用 `jenkee help` 查看可用命令

## 執行範例

### 顯示所有命令

```bash
$ jenkee help
Jenkins Inspector CLI v0.2.1

Usage: jenkee <command> [options]
       jenkee help <command>  Show detailed help for a command

Available commands:

  add-job-to-view           Add jobs to a view
  auth                      Verify Jenkins authentication
  console                   Get console output of a build
  copy-job                  Copy a job to a new job
  describe-credentials      Describe a specific credential
  get-job                   Get job XML configuration
  help                      Show help information
  job-diff                  Compare two job configurations
  job-status                Show job status and triggers
  list-builds               List build history for a job
  list-credentials          List Jenkins credentials metadata
  list-jobs                 List jobs in a view or all jobs
  list-views                List all Jenkins views
  update-job                Update job configuration from XML

Run 'jenkee help <command>' for detailed information about a specific command.
```

### 顯示特定命令的詳細說明

```bash
$ jenkee help auth
# auth - 驗證 Jenkins 連線

## 用途

驗證使用者的 Jenkins 認證設定是否正確...
[顯示 auth 命令的完整文件]
```

### 查詢不存在的命令

```bash
$ jenkee help non-existent
Error: Unknown command 'non-existent'
Run 'jenkee help' to see available commands.
```

## 常見使用情境

### 初次使用

第一次使用 `jenkee` 工具時，查看所有可用命令：

```bash
$ jenkee help
# 查看命令列表，了解有哪些功能可用
```

### 學習特定命令

想要使用某個命令但不確定用法時：

```bash
# 查看 copy-job 命令的詳細說明
$ jenkee help copy-job

# 查看範例後執行
$ jenkee copy-job source-job destination-job
```

### 查閱命令選項

忘記命令的參數或選項時：

```bash
# 查看 list-credentials 的可用選項
$ jenkee help list-credentials

# 了解可以使用 --store 選項後執行
$ jenkee list-credentials --store system
```

### 快速參考

在編寫腳本時快速查閱命令語法：

```bash
# 查看 update-job 的正確用法
$ jenkee help update-job

# 確認需要從 stdin 提供 XML
$ jenkee get-job my-job | jenkee update-job my-job
```

## 文件來源

`jenkee help` 顯示的詳細文件來自：
- 安裝時打包的內建文件（`docs/examples/*.md`）
- 開發環境中直接讀取專案的文件檔案

這確保了無論是已安裝的版本還是開發版本都能正確顯示文件。

## 相關資源

- [README.md](../../README.md) - 專案總覽與安裝說明
- [CODING_GUIDE.md](../../CODING_GUIDE.md) - 專案開發指南
- [docs/examples/](../examples/) - 所有命令的詳細文件

## 注意事項

1. `jenkee` 不帶任何參數時會自動顯示命令列表（等同於 `jenkee help`）
2. 命令名稱必須完全匹配，不支援模糊搜尋
3. 所有命令的詳細文件都是 Markdown 格式
4. 如果找不到文件檔案，會顯示錯誤訊息
