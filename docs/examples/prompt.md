# prompt - AI Agent 使用指引

## 用途

`prompt` 命令輸出專為 AI agent 設計的完整使用指引，涵蓋：
- jenkee CLI 工具介紹
- 認證驗證流程
- 配置設定說明
- 所有可用命令概覽
- 常見使用情境與工作流程

## 基本語法

```bash
jenkee prompt
```

如需在輸出中包含危險命令提示，請加上 `--all`。
危險命令預設需要互動式確認，若要用在自動化腳本，可加上 `--yes-i-really-mean-it` 跳過確認。

## 功能說明

此命令會輸出一份結構化的指引文件，包含：

1. **工具介紹** - jenkee 的功能與用途
2. **驗證流程** - 如何使用 `jenkee auth` 驗證連線
3. **配置設定** - 當認證失敗時如何設定 `.env` 檔案
4. **命令列表** - 所有可用命令與簡要說明
5. **使用情境** - 常見的 workflow 範例與最佳實踐

## 執行範例

### 顯示完整指引

```bash
$ jenkee prompt
# Jenkins Inspector (jenkee) - AI Agent Guide

## 關於 jenkee

Jenkins Inspector（CLI: `jenkee`）是一個 Jenkins CLI 工具，提供命令列介面來管理和探索 Jenkins 資源：
- 探索 Jenkins views 和 jobs 的架構
- 查看 job 配置、build 歷史與 console 輸出
- 管理 credentials metadata
...
```

### 儲存指引到檔案

```bash
$ jenkee prompt > jenkee-guide.md
$ cat jenkee-guide.md
# Jenkins Inspector (jenkee) - AI Agent Guide
...
```

### 搜尋特定主題

```bash
# 搜尋 credentials 相關說明
$ jenkee prompt | grep -A 10 "credentials"

# 搜尋常見使用情境
$ jenkee prompt | grep -A 20 "常見使用情境"
```

### 顯示危險命令提示

```bash
$ jenkee prompt --all
```

## 輸出內容

### 1. 關於 jenkee

工具的基本介紹與主要功能。

### 2. 驗證流程

**Step 1: 驗證認證**
- 如何執行 `jenkee auth`
- 成功時的預期輸出

**Step 2: 認證失敗的處理**
- 如何建立 `~/.jenkins-inspector/.env`
- 必要的環境變數說明
- 如何取得 API Token

### 3. 可用命令

列出所有 jenkee 支援的命令：
- `help` - 命令說明
- `auth` - 驗證認證
- `list-views` - 列出 views
- `list-jobs` - 列出 jobs
- `get-job` - 取得 job 配置
- `job-status` - 查看 job 狀態
- `list-builds` - 列出 builds
- `console` - 查看 console 輸出
- `job-diff` - 比較 job 配置
- `list-credentials` - 列出 credentials
- `describe-credentials` - 查看 credential 詳情
- `copy-job` - 複製 job
- `update-job` - 更新 job
- `add-job-to-view` - 加入 job 到 view
- `groovy` - 執行 Groovy script

加上 `--all` 時，會額外列出危險命令提示與確認機制說明。

特別強調使用 `jenkee help <command>` 可查看每個命令的詳細文件。

### 4. 常見使用情境

#### 情境 1: 探索 Jenkins 架構並檢查 Build 結果

完整的工作流程：
```bash
jenkee auth
jenkee list-views
jenkee list-jobs <view-name>
jenkee get-job <job-name>
jenkee job-status <job-name>
jenkee list-builds <job-name>
jenkee console <job-name> <build-number>
```

**使用時機：**
- 了解 Jenkins 的 job 組織結構
- 追蹤 build 失敗的原因
- 檢查 job 的觸發關係
- 除錯 CI/CD pipeline 問題

#### 情境 2: 比較 Jobs 與查找 Credentials

比較環境配置並確認 credentials：
```bash
jenkee auth
jenkee list-jobs <view-name>
jenkee job-diff <job-staging> <job-production>
jenkee list-credentials
jenkee list-credentials <domain-name>
jenkee describe-credentials <credential-id>
```

**使用時機：**
- 設定新環境時參考現有配置
- 確認環境間的配置差異
- 驗證 credentials 設定
- 排查 credential 錯誤

#### 情境 3: Job 管理操作

複製與更新 job：
```bash
jenkee copy-job <source-job> <new-job-name>
jenkee get-job <job-name> > job-config.xml
jenkee update-job <job-name> < job-config.xml
jenkee add-job-to-view <view-name> <job-name>
```

**使用時機：**
- 為新專案建立 job
- 批次更新配置
- 組織 jobs 到 views

### 5. 重要提示

- 所有名稱區分大小寫
- 使用 `jenkee help <command>` 查看詳細說明
- Credentials secret 預設不顯示，需 `--show-secret`
- `job-status` 可查看觸發關係
- `console` 不帶 build number 顯示最新 build
- `job-diff` 輸出為 unified diff 格式

## 使用情境

### 1. AI Agent 初始化

當 AI agent 需要了解如何使用 jenkee 時：

```bash
# AI agent 執行此命令取得完整指引
jenkee prompt
```

Agent 可以從輸出中學習：
- 如何驗證連線
- 有哪些命令可用
- 常見的操作流程
- 如何處理錯誤情況

### 2. 生成使用文件

為團隊或專案生成 jenkee 使用指引：

```bash
# 生成 markdown 文件
jenkee prompt > team-guide.md

# 轉換為 PDF
jenkee prompt | pandoc -f markdown -o team-guide.pdf
```

### 3. 快速參考

當忘記某個 workflow 時：

```bash
# 查看探索架構的流程
jenkee prompt | grep -A 15 "情境 1"

# 查看 credentials 管理流程
jenkee prompt | grep -A 15 "情境 2"
```

### 4. 腳本集成

在自動化腳本中加入指引：

```bash
#!/bin/bash

# 檢查是否已安裝 jenkee
if ! command -v jenkee &> /dev/null; then
    echo "Error: jenkee not found"
    exit 1
fi

# 顯示使用指引
echo "=== jenkee Usage Guide ==="
jenkee prompt

# 執行實際操作...
```

## 與其他命令的關係

| 命令 | 關係 |
|------|------|
| `help` | `help` 顯示命令列表，`prompt` 提供完整使用指引 |
| `help <command>` | 查看特定命令的詳細文件 |
| `auth` | `prompt` 中包含 auth 的使用說明 |

`prompt` 提供的是總覽性的指引，而 `help <command>` 提供的是特定命令的深入文件。

## 自訂 Prompt

### 功能說明

從 0.2.0 版本開始，支援自訂 prompt 檔案。可以透過預設位置或環境變數指定自訂 prompt 的位置。

### 方式 1：使用預設位置

```bash
# 建立自訂 prompt 檔案
cat > ~/.jenkins-inspector/prompt.md << 'EOF'
# 我的使用指引

自訂的 prompt 內容...
EOF

# 執行 prompt 命令
jenkee prompt
```

### 方式 2：使用環境變數

```bash
# 建立自訂 prompt 檔案（可放在任意位置）
cat > /path/to/my-prompt.md << 'EOF'
# 我的使用指引

自訂的 prompt 內容...
EOF

# 設定環境變數
export JENKINS_INSPECTOR_PROMPT_FILE=/path/to/my-prompt.md

# 執行 prompt 命令
jenkee prompt
```

### 優先順序

當決定使用哪個 prompt 時，按以下順序檢查：

1. `--ignore-override` flag（如果設定，直接使用內建預設 prompt，忽略所有自訂）
2. 環境變數 `JENKINS_INSPECTOR_PROMPT_FILE` 指定的檔案
3. 預設位置 `~/.jenkins-inspector/prompt.md`
4. 內建的預設 prompt

### 暫時使用預設 Prompt

如果需要暫時使用預設 prompt 而不刪除自訂檔案：

```bash
# 使用 --ignore-override flag
jenkee prompt --ignore-override
```

這個 flag 會忽略所有自訂 prompt（環境變數和預設位置），直接使用內建的預設 prompt。

### 永久恢復預設 Prompt

```bash
# 方式 1：刪除預設位置的自訂檔案
rm ~/.jenkins-inspector/prompt.md

# 方式 2：取消設定環境變數
unset JENKINS_INSPECTOR_PROMPT_FILE

# 再次執行會看到預設內容
jenkee prompt
```

### 使用情境

**預設位置適合：**
- 個人使用者的長期自訂設定
- 穩定的團隊工作流程

**環境變數適合：**
- 測試不同的 prompt 內容
- CI/CD 環境中動態指定 prompt
- 多個專案使用不同的 prompt

**--ignore-override flag 適合：**
- 暫時查看預設 prompt 的內容
- 除錯自訂 prompt 的問題
- 比較自訂與預設的差異

### 注意事項

1. 自訂 prompt 會完全覆蓋預設內容
2. 檔案格式為 markdown，可以使用完整的 markdown 語法
3. 如果自訂檔案不存在、無法讀取或為空，命令會返回錯誤（不會 fallback 到預設 prompt）
4. 環境變數優先級高於預設位置

### 錯誤處理

當使用自訂 prompt 時，以下情況會返回錯誤：

```bash
# 檔案不存在
$ JENKINS_INSPECTOR_PROMPT_FILE=/path/not/exist.md jenkee prompt
Error: Custom prompt file not found: /path/not/exist.md

# 檔案為空
$ echo "" > /tmp/empty.md
$ JENKINS_INSPECTOR_PROMPT_FILE=/tmp/empty.md jenkee prompt
Error: Custom prompt file is empty: /tmp/empty.md

# 無法讀取（如：是目錄而非檔案）
$ mkdir /tmp/prompt-dir
$ JENKINS_INSPECTOR_PROMPT_FILE=/tmp/prompt-dir jenkee prompt
Error reading custom prompt file: ...
```

## 注意事項

1. **輸出格式** - 輸出為 markdown 格式，可用於文件生成
2. **內容更新** - 當有新命令加入時，prompt 輸出也會更新
3. **語言** - 目前輸出為繁體中文，專為中文使用者設計
4. **用途** - 主要設計給 AI agent 閱讀，但人類也可參考
5. **自訂支援** - 可透過 `~/.jenkins-inspector/prompt.md` 自訂 prompt 內容

## 設計理念

`prompt` 命令的設計目標：

1. **快速上手** - 讓 AI agent 能快速理解 jenkee 的使用方式
2. **完整覆蓋** - 包含從認證到實際操作的完整流程
3. **實用導向** - 提供真實的使用情境而非抽象說明
4. **結構化** - 清晰的章節劃分，便於快速定位資訊

## 相關命令

- `help` - 顯示命令列表
- `help <command>` - 查看特定命令的詳細文件
- `auth` - 驗證 Jenkins 認證

## 參考資料

- [README.md](../../README.md) - 專案總覽
- [CODING_GUIDE.md](../../CODING_GUIDE.md) - 開發指南
- [docs/examples/](../examples/) - 所有命令的詳細文件
