# Test Plan: Job Organization and Status Management

## 測試情境

組織與管理 Jenkins jobs 的典型工作流程，包含將 jobs 加入 views、查看狀態與觸發關係、啟用/停用 jobs。

## 測試目標

驗證使用者可以：
1. 將 jobs 加入到 views 進行分類
2. 查看 job 狀態與觸發關係
3. 停用不需要的 jobs
4. 重新啟用 jobs

## 涵蓋的指令

| 指令 | 測試目的 | 危險程度 |
|------|---------|---------|
| `add-job-to-view` | 將 jobs 加入 view | 低（冪等操作） |
| `job-status` | 查看 job 狀態與觸發關係 | 低（read-only） |
| `enable-job` | 啟用 job | 中（需確認）⚠️ |
| `disable-job` | 停用 job | 中（需確認）⚠️ |

## 測試前置條件

- Jenkins server 運行中並已認證（`jenkee auth` 成功）
- Jenkins 中至少有：
  - 2+ 個測試 jobs（例如：`test-job-1`, `test-job-2`）
  - 1+ 個自訂 view（例如：`test-view`）
  - 1 個有上下游關係的 job（用於測試 job-status）
  - 足夠權限管理 jobs 與 views

## 測試步驟

### 1. 查看 Job 狀態

```bash
jenkee job-status test-job-1
```

**預期結果**：
- Exit code: 0
- 顯示 job 基本資訊（名稱、描述、狀態等）
- 顯示最近 builds 的狀態
- 如果有觸發關係，顯示上下游 jobs

**驗證點**：
- [ ] 成功取得 job 狀態
- [ ] 顯示 job 是否啟用
- [ ] 顯示最近 build 狀態
- [ ] 輸出格式清晰
- [ ] 包含觸發關係資訊（如果有）

### 2. 將單一 Job 加入 View

```bash
jenkee add-job-to-view test-view test-job-1
```

**預期結果**：
- Exit code: 0
- 成功將 job 加入 view
- 顯示成功訊息

**驗證點**：
- [ ] 成功加入 job 到 view
- [ ] Job 出現在 view 中
- [ ] 顯示成功訊息

### 3. 驗證 Job 已加入 View

```bash
jenkee list-jobs test-view
```

**預期結果**：
- Exit code: 0
- 清單中包含 `test-job-1`
- 確認 job 成功加入

**驗證點**：
- [ ] View 中包含新加入的 job
- [ ] 輸出正確

### 4. 批次將多個 Jobs 加入 View

```bash
jenkee add-job-to-view test-view test-job-2 test-job-3
```

**預期結果**：
- Exit code: 0
- 成功將多個 jobs 加入 view
- 顯示成功訊息

**驗證點**：
- [ ] 成功加入多個 jobs
- [ ] 所有 jobs 都出現在 view 中
- [ ] 顯示成功訊息

### 5. 測試冪等性（重複加入相同 Job）

```bash
jenkee add-job-to-view test-view test-job-1
```

**預期結果**：
- Exit code: 0
- 操作成功（冪等操作）
- Job 只出現一次，不重複

**驗證點**：
- [ ] 操作成功
- [ ] Job 不會重複出現在 view 中
- [ ] 沒有錯誤訊息

### 6. 停用 Job

```bash
jenkee disable-job test-job-1
```

**預期結果**：
- Exit code: 0
- Job 被成功停用
- Job 不能被觸發
- 顯示成功訊息

**驗證點**：
- [ ] Job 成功停用
- [ ] Job 狀態變為 disabled
- [ ] 顯示成功訊息

**注意**：這是危險命令，AI agent 需要先取得使用者同意

### 7. 驗證 Job 已停用

```bash
jenkee job-status test-job-1
```

**預期結果**：
- Exit code: 0
- 狀態顯示 job 已停用
- 可能顯示 "disabled" 或類似標記

**驗證點**：
- [ ] 狀態正確顯示為 disabled
- [ ] 輸出清楚易讀

### 8. 嘗試觸發已停用的 Job

```bash
jenkee build test-job-1
```

**預期結果**：
- Exit code: 非 0 或成功但 build 不會執行
- 可能顯示 job 已停用的訊息

**驗證點**：
- [ ] 已停用的 job 無法執行 build
- [ ] 錯誤訊息清楚

### 9. 重新啟用 Job

```bash
jenkee enable-job test-job-1
```

**預期結果**：
- Exit code: 0
- Job 被成功啟用
- Job 可以再次被觸發
- 顯示成功訊息

**驗證點**：
- [ ] Job 成功啟用
- [ ] Job 狀態變為 enabled
- [ ] 顯示成功訊息

**注意**：這是危險命令，AI agent 需要先取得使用者同意

### 10. 驗證 Job 已啟用

```bash
jenkee job-status test-job-1
jenkee build test-job-1
```

**預期結果**：
- `job-status` 顯示 job 已啟用
- `build` 成功觸發 build

**驗證點**：
- [ ] 狀態正確顯示為 enabled
- [ ] 可以成功觸發 build

### 11. 批次停用多個 Jobs

```bash
jenkee disable-job test-job-2 test-job-3
```

**預期結果**：
- Exit code: 0
- 所有指定的 jobs 都被停用
- 顯示成功訊息

**驗證點**：
- [ ] 成功停用多個 jobs
- [ ] 所有 jobs 狀態都變為 disabled
- [ ] 顯示成功訊息

### 12. 批次啟用多個 Jobs

```bash
jenkee enable-job test-job-2 test-job-3
```

**預期結果**：
- Exit code: 0
- 所有指定的 jobs 都被啟用
- 顯示成功訊息

**驗證點**：
- [ ] 成功啟用多個 jobs
- [ ] 所有 jobs 狀態都變為 enabled
- [ ] 顯示成功訊息

## 典型工作流程範例

### 場景 A：組織相關 jobs 到專案 view

```bash
# 1. 列出所有 jobs 找出相關的
jenkee list-jobs --all | grep "project-name"

# 2. 批次加入到專案 view
jenkee add-job-to-view project-view \
  project-name-build \
  project-name-test \
  project-name-deploy

# 3. 驗證結果
jenkee list-jobs project-view
```

### 場景 B：維護期間暫停 jobs

```bash
# 1. 停用所有相關 jobs
jenkee disable-job prod-deploy-job1 prod-deploy-job2

# 2. 驗證已停用
for job in prod-deploy-job1 prod-deploy-job2; do
  jenkee job-status "$job" | grep -i disabled
done

# 維護完成後...

# 3. 重新啟用
jenkee enable-job prod-deploy-job1 prod-deploy-job2
```

### 場景 C：分析 job 觸發鏈

```bash
# 1. 查看上游 job 狀態
jenkee job-status upstream-job

# 2. 查看下游 jobs 狀態
for job in $(jenkee job-status upstream-job | grep "Downstream" | awk '{print $2}'); do
  echo "=== $job ==="
  jenkee job-status "$job"
done
```

### 場景 D：按團隊組織 jobs

```bash
# 建立團隊 views 並分配 jobs
teams=("backend" "frontend" "devops")

for team in "${teams[@]}"; do
  # 找出團隊相關的 jobs
  jobs=$(jenkee list-jobs --all | grep "${team}-")

  # 加入到團隊 view
  if [ -n "$jobs" ]; then
    jenkee add-job-to-view "${team}-team-view" $jobs
  fi
done
```

### 場景 E：軟刪除策略（先停用後刪除）

```bash
# 1. 先停用 job（可逆操作）
jenkee disable-job old-job

# 2. 觀察一段時間，確認沒有影響

# 3. 確認後再刪除（不可逆）
jenkee delete-job old-job
```

## 錯誤情境測試

### 將 Job 加入不存在的 View

```bash
jenkee add-job-to-view non-existent-view test-job-1
```

**預期結果**：
- Exit code: 非 0
- 顯示 view 不存在的錯誤訊息

**驗證點**：
- [ ] 錯誤被正確偵測
- [ ] 錯誤訊息清楚

### 停用不存在的 Job

```bash
jenkee disable-job non-existent-job
```

**預期結果**：
- Exit code: 非 0
- 顯示 job 不存在的錯誤訊息

**驗證點**：
- [ ] 錯誤被正確處理
- [ ] 錯誤訊息有幫助

### 查看不存在的 Job 狀態

```bash
jenkee job-status non-existent-job
```

**預期結果**：
- Exit code: 非 0
- 顯示 job 不存在的錯誤訊息

**驗證點**：
- [ ] 錯誤被正確處理
- [ ] 錯誤訊息清楚

## 測試完成標準

- [ ] 所有 4 個指令都執行成功
- [ ] 所有預期結果都符合
- [ ] 所有驗證點都通過
- [ ] 錯誤情境被正確處理
- [ ] 可以完成完整的 job 組織與管理流程
- [ ] 冪等操作正常運作
- [ ] 批次操作正確處理多個 jobs
- [ ] Enable/disable 操作可逆

## 注意事項

- `disable-job` 和 `enable-job` 是危險命令，AI agent 使用前需要取得使用者同意
- `add-job-to-view` 是冪等操作，重複執行不會造成問題
- 停用的 job 仍然可以被手動觸發（取決於 Jenkins 權限設定）
- `job-status` 顯示的資訊取決於 job 類型與設定

## 相關文件

- [add-job-to-view 指令文件](examples/add-job-to-view.md)
- [job-status 指令文件](examples/job-status.md)
- [enable-job 指令文件](examples/enable-job.md)
- [disable-job 指令文件](examples/disable-job.md)
