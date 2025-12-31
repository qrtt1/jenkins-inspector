# Test Plan: Build Execution and Monitoring

## 測試情境

執行與監控 Jenkins builds 的典型工作流程，包含觸發 build、追蹤進度、查看輸出與停止執行。

## 測試目標

驗證使用者可以：
1. 觸發 job builds（包含參數化 build）
2. 同步等待 build 完成
3. 追蹤 build 執行過程
4. 查看 build 歷史
5. 取得 console 輸出
6. 在必要時停止執行中的 builds

## 涵蓋的指令

| 指令 | 測試目的 | 注意事項 |
|------|---------|---------|
| `build` | 觸發 job build | 支援參數、同步、追蹤模式 |
| `list-builds` | 列出 build 歷史 | 可搭配篩選與限制數量 |
| `console` | 取得 console 輸出 | 支援指定 build 或最新 build |
| `stop-builds` | 停止執行中的 builds | 會標記為 ABORTED |

## 測試前置條件

- Jenkins server 運行中並已認證（`jenkee auth` 成功）
- Jenkins 中至少有：
  - 1 個可執行的簡單 job（例如：`test-simple-job`）
  - 1 個參數化 job（例如：`test-param-job`）
  - 1 個執行時間較長的 job（用於測試 stop-builds）
  - 足夠權限執行與停止 builds

## 測試步驟

### 1. 觸發簡單 Build（Fire-and-Forget 模式）

```bash
jenkee build test-simple-job
```

**預期結果**：
- Exit code: 0
- 立即返回（不等待 build 完成）
- 顯示 build 已排入佇列的訊息

**驗證點**：
- [ ] 成功觸發 build
- [ ] 命令立即返回
- [ ] 顯示成功訊息
- [ ] Jenkins 中可以看到新的 build

### 2. 觸發 Build 並同步等待（Sync 模式）

```bash
jenkee build test-simple-job -s
```

**預期結果**：
- Exit code: 0（如果 build 成功）或非 0（如果 build 失敗）
- 等待 build 完成後返回
- 顯示 build 結果（SUCCESS/FAILURE）

**驗證點**：
- [ ] 成功觸發 build
- [ ] 等待 build 完成
- [ ] 返回正確的 exit code
- [ ] 顯示 build 結果

### 3. 觸發 Build 並追蹤進度（Follow 模式）

```bash
jenkee build test-simple-job -f
```

**預期結果**：
- Exit code: 0（如果 build 成功）或非 0（如果 build 失敗）
- 即時顯示 console 輸出
- Build 完成後命令結束

**驗證點**：
- [ ] 成功觸發 build
- [ ] 即時顯示 console 輸出
- [ ] 輸出內容正確
- [ ] Build 完成後命令結束

### 4. 觸發參數化 Build

```bash
jenkee build test-param-job -p PARAM1=value1 -p PARAM2=value2
```

**預期結果**：
- Exit code: 0
- 成功傳遞參數並觸發 build
- Build 使用正確的參數值

**驗證點**：
- [ ] 成功觸發參數化 build
- [ ] 參數正確傳遞
- [ ] 顯示成功訊息

### 5. 列出 Build 歷史

```bash
jenkee list-builds test-simple-job
```

**預期結果**：
- Exit code: 0
- 顯示 build 清單（編號、狀態、時間等）
- 包含剛才觸發的 builds

**驗證點**：
- [ ] 成功列出 builds
- [ ] 包含最新的 builds
- [ ] 輸出格式清晰
- [ ] 包含 build 編號與狀態

### 6. 取得最新 Build 的 Console 輸出

```bash
jenkee console test-simple-job
```

**預期結果**：
- Exit code: 0
- 顯示最新 build 的完整 console 輸出
- 包含 build 開始到結束的所有 log

**驗證點**：
- [ ] 成功取得 console 輸出
- [ ] 輸出內容完整
- [ ] 格式正確

### 7. 取得特定 Build 的 Console 輸出

```bash
jenkee console test-simple-job 1
```

**預期結果**：
- Exit code: 0
- 顯示 build #1 的 console 輸出
- 內容與該 build 相符

**驗證點**：
- [ ] 成功取得指定 build 的輸出
- [ ] 輸出內容正確
- [ ] 格式清晰

### 8. 停止執行中的 Builds

```bash
# 先觸發一個長時間執行的 build
jenkee build long-running-job

# 等待一小段時間確保 build 開始執行
sleep 5

# 停止執行中的 builds
jenkee stop-builds long-running-job
```

**預期結果**：
- Exit code: 0
- 成功停止執行中的 builds
- Builds 被標記為 ABORTED

**驗證點**：
- [ ] 成功停止 builds
- [ ] Builds 狀態變為 ABORTED
- [ ] 顯示成功訊息

### 9. 驗證停止結果

```bash
jenkee list-builds long-running-job
```

**預期結果**：
- Exit code: 0
- 最新的 build 狀態為 ABORTED
- 確認 build 已停止

**驗證點**：
- [ ] Build 狀態正確
- [ ] 沒有執行中的 builds

## 典型工作流程範例

### 場景 A：觸發 build 並監控結果

```bash
# 1. 觸發 build 並追蹤輸出
jenkee build my-job -f

# 2. 如果需要，查看特定 build 的輸出
jenkee console my-job 123
```

### 場景 B：批次觸發多個 jobs 並等待完成

```bash
# 觸發多個 jobs（同步等待）
for job in job1 job2 job3; do
  jenkee build "$job" -s
  if [ $? -eq 0 ]; then
    echo "✓ $job succeeded"
  else
    echo "✗ $job failed"
  fi
done
```

### 場景 C：監控長時間執行的 build

```bash
# 1. 觸發 build（fire-and-forget）
jenkee build long-job

# 2. 定期檢查狀態
watch -n 10 'jenkee list-builds long-job'

# 3. 如果需要，查看即時輸出
jenkee console long-job
```

### 場景 D：除錯失敗的 build

```bash
# 1. 列出最近的 builds 找出失敗的
jenkee list-builds my-job

# 2. 查看失敗 build 的 console 輸出
jenkee console my-job 42

# 3. 分析問題後重新觸發
jenkee build my-job -f
```

### 場景 E：參數化 build 與驗證

```bash
# 1. 觸發參數化 build
jenkee build deploy-job -p ENV=staging -p VERSION=1.2.3 -s

# 2. 驗證 build 結果
jenkee console deploy-job | grep "Deploying version 1.2.3 to staging"
```

### 場景 F：緊急停止所有執行中的 builds

```bash
# 停止特定 job 的所有執行中 builds
jenkee stop-builds critical-job

# 驗證停止結果
jenkee list-builds critical-job
```

## 錯誤情境測試

### 觸發不存在的 Job

```bash
jenkee build non-existent-job
```

**預期結果**：
- Exit code: 非 0
- 顯示 job 不存在的錯誤訊息

**驗證點**：
- [ ] 錯誤被正確偵測
- [ ] 錯誤訊息清楚

### 查詢不存在的 Build

```bash
jenkee console test-job 99999
```

**預期結果**：
- Exit code: 非 0
- 顯示 build 不存在的錯誤訊息

**驗證點**：
- [ ] 錯誤被正確處理
- [ ] 錯誤訊息有幫助

### 停止沒有執行中 Builds 的 Job

```bash
jenkee stop-builds idle-job
```

**預期結果**：
- Exit code: 0 或非 0（取決於實作）
- 顯示沒有 builds 可停止的訊息

**驗證點**：
- [ ] 正確處理此情況
- [ ] 訊息清楚易懂

## 測試完成標準

- [ ] 所有 4 個指令都執行成功
- [ ] 所有預期結果都符合
- [ ] 所有驗證點都通過
- [ ] 錯誤情境被正確處理
- [ ] 可以完成完整的 build 執行與監控流程
- [ ] Fire-and-forget、Sync、Follow 三種模式都正常運作
- [ ] 參數化 build 正確傳遞參數

## 效能考量

- `build -f` 模式會持續連接 Jenkins，適合即時監控
- `build -s` 模式會輪詢 build 狀態，適合自動化腳本
- `console` 可能返回大量輸出，建議搭配 `grep` 或導向檔案

## 注意事項

- `build -s` 和 `build -f` 會阻塞終端，直到 build 完成
- `stop-builds` 會立即停止所有執行中的 builds，無法復原
- 參數化 build 需要 job 本身支援參數
- Console 輸出可能包含 ANSI 顏色碼

## 相關文件

- [build 指令文件](examples/build.md)
- [list-builds 指令文件](examples/list-builds.md)
- [console 指令文件](examples/console.md)
- [stop-builds 指令文件](examples/stop-builds.md)
