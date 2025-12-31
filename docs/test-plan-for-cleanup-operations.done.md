# Test Plan: Cleanup Operations (Dangerous Commands)

## ⚠️ 警告

**本測試計畫包含危險且不可逆的操作！**

- 所有操作都會永久刪除資料
- 無法復原
- 僅應在測試環境中執行
- 生產環境使用前必須：
  1. 完整備份
  2. 取得明確授權
  3. 驗證刪除目標正確

## 測試情境

清理與維護 Jenkins 環境的工作流程，包含刪除舊的 build 記錄與不需要的 jobs。

## 測試目標

驗證使用者可以：
1. 刪除指定範圍的 build 記錄
2. 刪除不需要的 jobs
3. 操作前得到適當的警告與確認
4. 確認刪除操作正確執行

## 涵蓋的指令

| 指令 | 測試目的 | 危險等級 |
|------|---------|---------|
| `delete-builds` | 刪除 build 記錄 | 高（不可逆）⚠️ |
| `delete-job` | 刪除 jobs | 極高（不可逆）⚠️ |

## AI Agent 使用限制

AI agent 在使用這些命令前**必須**：
1. 向使用者說明將要刪除的內容
2. 說明刪除的影響（永久移除、無法復原）
3. 建議先備份重要資料
4. 取得使用者明確同意後才執行

## 測試前置條件

- **必須在測試環境執行**，不可在生產環境測試
- Jenkins server 運行中並已認證（`jenkee auth` 成功）
- Jenkins 中已準備：
  - 數個測試用 jobs（可以安全刪除的）
  - 每個 job 有數個 builds（可以安全刪除的）
  - 完整備份（如果是重要環境）
  - 足夠權限刪除 jobs 與 builds

## 測試步驟

### Phase 1: delete-builds 測試

#### 1. 準備測試資料

```bash
# 建立測試 job
echo '<project><builders/></project>' | jenkee create-job test-cleanup-job

# 觸發數個 builds
for i in {1..10}; do
  jenkee build test-cleanup-job
  sleep 2
done

# 等待 builds 完成
sleep 10

# 確認 builds 已建立
jenkee list-builds test-cleanup-job
```

**驗證點**：
- [ ] 測試 job 成功建立
- [ ] 至少有 10 個 builds
- [ ] Builds 狀態正常

#### 2. 刪除單一 Build

```bash
# 查看 build 清單
jenkee list-builds test-cleanup-job

# 刪除 build #1
jenkee delete-builds test-cleanup-job 1
```

**預期結果**：
- Exit code: 0
- 顯示成功訊息
- Build #1 被刪除

**驗證點**：
- [ ] 成功刪除 build
- [ ] 顯示成功訊息
- [ ] Build 不再出現在清單中

#### 3. 驗證 Build 已刪除

```bash
jenkee list-builds test-cleanup-job
jenkee console test-cleanup-job 1
```

**預期結果**：
- `list-builds` 不再顯示 build #1
- `console` 命令回報 build 不存在

**驗證點**：
- [ ] Build 確實被刪除
- [ ] 其他 builds 未受影響

#### 4. 刪除 Build 範圍

```bash
# 刪除 build #2-5
jenkee delete-builds test-cleanup-job 2-5
```

**預期結果**：
- Exit code: 0
- 顯示成功訊息
- Builds #2-5 都被刪除

**驗證點**：
- [ ] 成功刪除範圍內的 builds
- [ ] 顯示成功訊息
- [ ] 所有指定的 builds 都被刪除

#### 5. 驗證範圍刪除結果

```bash
jenkee list-builds test-cleanup-job
```

**預期結果**：
- Builds #2-5 不再出現
- Builds #6-10 仍然存在

**驗證點**：
- [ ] 範圍內的 builds 已刪除
- [ ] 範圍外的 builds 未受影響

#### 6. 刪除所有剩餘 Builds

```bash
jenkee delete-builds test-cleanup-job 6-10
```

**預期結果**：
- Exit code: 0
- 所有剩餘 builds 被刪除
- Job 沒有 build 歷史

**驗證點**：
- [ ] 所有 builds 成功刪除
- [ ] Job 仍然存在（只是沒有 builds）

### Phase 2: delete-job 測試

#### 7. 建立測試用 Jobs

```bash
# 建立數個測試 jobs
for i in {1..3}; do
  echo '<project><description>Test job for deletion</description><builders/></project>' | \
  jenkee create-job "test-delete-job-$i"
done

# 驗證 jobs 已建立
jenkee list-jobs --all | grep test-delete-job
```

**驗證點**：
- [ ] 成功建立 3 個測試 jobs
- [ ] Jobs 出現在清單中

#### 8. 刪除單一 Job

```bash
jenkee delete-job test-delete-job-1
```

**預期結果**：
- Exit code: 0
- 顯示成功訊息
- Job 被完全刪除（包含所有 builds）

**驗證點**：
- [ ] 成功刪除 job
- [ ] 顯示成功訊息
- [ ] Job 不再出現在清單中

#### 9. 驗證 Job 已刪除

```bash
jenkee list-jobs --all | grep test-delete-job-1
jenkee get-job test-delete-job-1
```

**預期結果**：
- `list-jobs` 不再顯示該 job
- `get-job` 回報 job 不存在

**驗證點**：
- [ ] Job 確實被刪除
- [ ] 無法再存取該 job

#### 10. 批次刪除多個 Jobs

```bash
jenkee delete-job test-delete-job-2 test-delete-job-3
```

**預期結果**：
- Exit code: 0
- 顯示成功訊息
- 兩個 jobs 都被刪除

**驗證點**：
- [ ] 成功刪除多個 jobs
- [ ] 顯示成功訊息
- [ ] 所有指定的 jobs 都被刪除

#### 11. 驗證批次刪除結果

```bash
jenkee list-jobs --all | grep test-delete-job
```

**預期結果**：
- 沒有任何 test-delete-job-* 出現
- 所有測試 jobs 都已清理

**驗證點**：
- [ ] 所有測試 jobs 已刪除
- [ ] 清單中沒有殘留

#### 12. 清理測試環境

```bash
# 刪除最初建立的測試 job
jenkee delete-job test-cleanup-job
```

**驗證點**：
- [ ] 測試環境完全清理

## 典型工作流程範例

### 場景 A：清理舊的 Build 記錄（保留最近的）

```bash
# 1. 查看 build 歷史
jenkee list-builds my-job

# 2. 找出 build 編號範圍（假設有 1-100，保留最近 20 個）
# 刪除 build #1-80
jenkee delete-builds my-job 1-80

# 3. 驗證結果
jenkee list-builds my-job
```

### 場景 B：軟刪除策略（先停用，觀察，再刪除）

```bash
# 1. 先停用 job（可逆操作）
jenkee disable-job old-job

# 2. 觀察數天或數週，確認沒有影響

# 3. 確認後再刪除 builds（節省空間）
jenkee delete-builds old-job 1-1000

# 4. 最後刪除 job（不可逆）
jenkee delete-job old-job
```

### 場景 C：批次清理專案相關 Jobs

```bash
# 1. 列出專案相關的 jobs
jobs=$(jenkee list-jobs --all | grep "old-project-")

# 2. 確認清單正確
echo "將要刪除的 jobs:"
echo "$jobs"

# 3. 取得使用者確認
read -p "確認刪除這些 jobs? (yes/no): " confirm

# 4. 執行刪除
if [ "$confirm" = "yes" ]; then
  jenkee delete-job $jobs
  echo "已刪除"
else
  echo "已取消"
fi
```

### 場景 D：定期清理舊 Builds（自動化腳本）

```bash
#!/bin/bash
# 每週執行，清理超過 100 個 builds 的 jobs

# 列出所有 jobs
jobs=$(jenkee list-jobs --all)

for job in $jobs; do
  # 取得 build 總數
  build_count=$(jenkee list-builds "$job" | wc -l)

  if [ "$build_count" -gt 100 ]; then
    # 保留最近 50 個，刪除其餘
    echo "清理 $job 的舊 builds..."
    jenkee delete-builds "$job" "1-$((build_count - 50))"
  fi
done
```

## 錯誤情境測試

### 刪除不存在的 Build

```bash
jenkee delete-builds test-job 99999
```

**預期結果**：
- Exit code: 非 0
- 顯示 build 不存在的錯誤訊息

**驗證點**：
- [ ] 錯誤被正確處理
- [ ] 錯誤訊息清楚

### 刪除不存在的 Job

```bash
jenkee delete-job non-existent-job
```

**預期結果**：
- Exit code: 非 0
- 顯示 job 不存在的錯誤訊息

**驗證點**：
- [ ] 錯誤被正確處理
- [ ] 錯誤訊息有幫助

### 使用無效的範圍格式

```bash
jenkee delete-builds test-job invalid-range
```

**預期結果**：
- Exit code: 非 0
- 顯示範圍格式錯誤訊息

**驗證點**：
- [ ] 錯誤被正確偵測
- [ ] 顯示正確的使用範例

## 測試完成標準

- [ ] 所有 2 個指令都執行成功
- [ ] 所有預期結果都符合
- [ ] 所有驗證點都通過
- [ ] 錯誤情境被正確處理
- [ ] 刪除操作正確執行
- [ ] 沒有意外刪除不該刪除的資料
- [ ] 測試環境完全清理

## 安全檢查清單

在執行這些命令前，確認：

- [ ] 在測試環境執行（不是生產環境）
- [ ] 已完整備份（如果是重要環境）
- [ ] 確認刪除目標正確
- [ ] 取得必要的授權
- [ ] 了解操作不可逆
- [ ] 準備好復原計畫（如：從備份還原）

## 最佳實踐

1. **漸進式刪除**：
   - 先刪除 builds，觀察影響
   - 確認無誤後再刪除 job

2. **備份優先**：
   - 使用 `get-job` 備份 job 配置
   - 記錄 build 歷史（如果需要）

3. **軟刪除策略**：
   - 先用 `disable-job` 停用
   - 觀察一段時間
   - 確認無影響後才刪除

4. **批次操作確認**：
   - 先列出目標
   - 人工確認清單
   - 再執行刪除

5. **自動化清理**：
   - 設定保留策略（如：保留最近 50 個 builds）
   - 定期執行清理腳本
   - 記錄清理 logs

## 注意事項

- `delete-builds` 會永久刪除 build 記錄、artifacts、logs 和測試結果
- `delete-job` 會永久刪除 job 及其所有 builds
- 這些操作無法復原
- 建議在執行前使用 `get-job` 備份 job 配置
- Jenkins 的 recycle bin 功能（如果有啟用）可能提供有限的復原能力
- 某些 Jenkins plugins 可能提供軟刪除功能

## 相關文件

- [delete-builds 指令文件](examples/delete-builds.md)
- [delete-job 指令文件](examples/delete-job.md)
- [disable-job 指令文件](examples/disable-job.md) - 軟刪除替代方案
