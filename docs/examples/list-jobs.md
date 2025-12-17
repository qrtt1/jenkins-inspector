# list-jobs - 列出 Jenkins Jobs

## 用途

列出 Jenkins 中的 jobs，可以指定特定 view 或列出所有 jobs。

## 基本語法

```bash
# 列出特定 view 中的 jobs
jks list-jobs <view-name>

# 列出所有 jobs
jks list-jobs --all
jks list-jobs -a
```

## 功能說明

此指令會：
1. 檢查認證設定
2. 根據參數列出對應的 jobs
3. 使用 Jenkins CLI 的 `list-jobs` 指令
4. 輸出 job 名稱列表（每行一個）

## 執行範例

### 列出特定 View 的 Jobs

```bash
$ jks list-jobs AVENGERS
spider-shield-console-deploy-staging
spider-shield-console-deploy-productionuction
spider-shield-console-release-image-auto
spider-shield-console-release-image-staging
spider-shield-console-release-image-productionuction
```

**說明**：
- 列出 `AVENGERS` view 中的所有 jobs
- 結果依 Jenkins 伺服器順序排列

### 列出所有 Jobs

使用 `--all` 或 `-a` 參數：

```bash
$ jks list-jobs --all
avengers-locator-deploy-production
avengers-locator-deploy-staging
shield-console-deploy-production
shield-console-deploy-staging
stark-gateway-deploy-production
stark-gateway-deploy-staging
...
(更多 jobs)
```

**說明**：
- 列出所有可見的 jobs
- 不限定特定 view
- 等同於 Jenkins CLI 的 `list-jobs` 不帶參數

### 缺少參數

```bash
$ jks list-jobs
Error: Missing argument
Usage: jks list-jobs <view-name>
       jks list-jobs --all | -a
```

**說明**：
- 必須指定 view 名稱或使用 `--all`/`-a`
- 顯示使用說明

### View 不存在或無 Jobs

```bash
$ jks list-jobs NonExistentView
No jobs found in view 'NonExistentView'
```

**說明**：
- 當 view 不存在或沒有 jobs 時的提示

### 未設定認證

```bash
$ jks list-jobs AVENGERS
Error: Jenkins credentials not configured.
Run 'jks auth' to configure credentials.
```

## 常見使用情境

### 查看專案的所有 Jobs

結合 `list-views` 和 `list-jobs` 查看專案結構：

```bash
# 1. 先列出所有 views
jks list-views

# 2. 選擇感興趣的 view
jks list-jobs AVENGERS

# 3. 查看具體 job 的命名模式
```

### 搜尋特定 Job

配合 grep 搜尋：

```bash
# 搜尋所有包含 "deploy" 的 jobs
jks list-jobs --all | grep deploy

# 搜尋特定專案的 productionuction jobs
jks list-jobs AVENGERS | grep production
```

### 確認命名慣例

根據 README.md 的命名慣例，檢查 jobs 是否符合規範：

```bash
# 列出 AVENGERS view 的 jobs
jks list-jobs AVENGERS

# 預期看到的模式：
# {project-name}-{job-type}-{environment}
# 例如：spider-shield-console-deploy-staging
```

### 統計 Jobs 數量

```bash
# 統計某個 view 有多少個 jobs
jks list-jobs AVENGERS | wc -l

# 統計所有 jobs 數量
jks list-jobs --all | wc -l
```

### 批次操作準備

在執行批次操作前，先確認要處理的 jobs：

```bash
# 列出要處理的 jobs
jks list-jobs AVENGERS > jobs.txt

# 檢查列表
cat jobs.txt

# 對每個 job 執行操作（示意）
# cat jobs.txt | xargs -I {} jks <some-operation> {}
```

## 參數說明

| 參數 | 說明 | 範例 |
|------|------|------|
| `<view-name>` | 指定 view 名稱 | `jks list-jobs AVENGERS` |
| `--all` | 列出所有 jobs | `jks list-jobs --all` |
| `-a` | `--all` 的簡寫 | `jks list-jobs -a` |

## 相關指令

- `jks list-views` - 列出所有 views
- `jks auth` - 驗證 Jenkins 認證設定

## 注意事項

1. View 名稱區分大小寫（如 `AVENGERS` 不等於 `spider-app-production`）
2. 需要有效的 Jenkins 認證才能執行
3. 列出的 jobs 依據使用者權限而定
4. 使用 `--all` 會列出大量 jobs，建議配合 `grep` 過濾
5. 空的 view 會顯示 "No jobs found" 訊息
