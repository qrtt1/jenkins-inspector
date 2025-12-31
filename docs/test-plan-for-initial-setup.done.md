# Test Plan: Initial Setup and Environment Exploration

## 測試情境

初次設定 Jenkins Inspector 並探索 Jenkins 環境的典型工作流程。

## 測試目標

驗證使用者可以：
1. 成功連接並認證到 Jenkins server
2. 探索 Jenkins 環境結構（views, jobs, credentials）
3. 了解可用資源以便後續操作

## 涵蓋的指令

| 指令 | 測試目的 | 預期結果 |
|------|---------|---------|
| `auth` | 驗證 Jenkins 認證設定 | 成功認證並顯示使用者名稱 |
| `list-views` | 列出所有 views | 顯示 view 清單（至少包含 "All"） |
| `list-jobs` | 列出 jobs | 顯示 job 清單 |
| `list-credentials` | 列出 credentials | 顯示 credential metadata |

## 測試前置條件

- Jenkins server 運行中
- 設定好 `$HOME/.jenkins-inspector/.env` 檔案：
  ```
  JENKINS_URL=http://localhost:8080/
  JENKINS_USER_ID=jenkins-test
  JENKINS_API_TOKEN=1100000000000000000000000000000000
  ```
- Jenkins 中至少有：
  - 1 個 view（預設的 "All"）
  - 數個 test jobs
  - 數個 test credentials

## 測試步驟

### 1. 驗證 Jenkins 認證

```bash
jenkee auth
```

**預期結果**：
- Exit code: 0
- 輸出包含 "Authenticated as:" 或 "✓" 符號
- 顯示正確的使用者名稱（jenkins-test）

**驗證點**：
- [ ] 認證成功
- [ ] 顯示正確的使用者名稱
- [ ] 沒有錯誤訊息

### 2. 列出所有 Views

```bash
jenkee list-views
```

**預期結果**：
- Exit code: 0
- 至少顯示 "All" view
- 可能有其他自訂 views

**驗證點**：
- [ ] 成功列出 views
- [ ] 包含 "All" view
- [ ] 格式清晰易讀

### 3. 列出所有 Jobs

```bash
jenkee list-jobs --all
```

**預期結果**：
- Exit code: 0
- 顯示 Jenkins 中所有 jobs 的清單
- 每行一個 job 名稱

**驗證點**：
- [ ] 成功列出 jobs
- [ ] 輸出格式正確
- [ ] 沒有遺漏 jobs

### 4. 列出特定 View 的 Jobs

```bash
jenkee list-jobs All
```

**預期結果**：
- Exit code: 0
- 顯示 "All" view 中的 jobs
- 結果應與 `--all` 類似

**驗證點**：
- [ ] 成功列出指定 view 的 jobs
- [ ] 輸出格式正確

### 5. 列出所有 Credentials

```bash
jenkee list-credentials
```

**預期結果**：
- Exit code: 0
- 顯示 credentials metadata（不包含 secret 內容）
- 包含 ID、Name、Type 等資訊

**驗證點**：
- [ ] 成功列出 credentials
- [ ] 不洩漏 secret 內容
- [ ] 輸出格式清晰

## 典型工作流程範例

```bash
# 1. 驗證連線
jenkee auth

# 2. 探索環境結構
jenkee list-views
jenkee list-jobs --all

# 3. 查看可用的 credentials
jenkee list-credentials

# 4. 選擇特定 view 查看其 jobs
jenkee list-jobs "My View"
```

## 錯誤情境測試

### 錯誤的認證資訊

```bash
# 暫時修改環境變數測試
JENKINS_API_TOKEN=wrong_token jenkee auth
```

**預期結果**：
- Exit code: 非 0
- 顯示認證失敗錯誤訊息

**驗證點**：
- [ ] 認證失敗被正確偵測
- [ ] 錯誤訊息清楚

### 查詢不存在的 View

```bash
jenkee list-jobs "NonExistentView"
```

**預期結果**：
- Exit code: 非 0
- 顯示 view 不存在的錯誤訊息

**驗證點**：
- [ ] 錯誤被正確處理
- [ ] 錯誤訊息有幫助

## 測試完成標準

- [ ] 所有 4 個指令都執行成功
- [ ] 所有預期結果都符合
- [ ] 所有驗證點都通過
- [ ] 錯誤情境被正確處理
- [ ] 輸出格式清晰易讀
- [ ] 沒有洩漏敏感資訊（如 API tokens）

## 注意事項

- 此測試計畫中的所有指令都是 **read-only**，不會修改 Jenkins 狀態
- 適合作為新使用者的第一個測試流程
- 可以安全地重複執行

## 相關文件

- [auth 指令文件](examples/auth.md)
- [list-views 指令文件](examples/list-views.md)
- [list-jobs 指令文件](examples/list-jobs.md)
- [list-credentials 指令文件](examples/list-credentials.md)
