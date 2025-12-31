# Test Plan: Job Configuration Management

## 測試情境

管理 Jenkins job 配置的典型工作流程，包含建立、複製、更新與比較 jobs。

## 測試目標

驗證使用者可以：
1. 從既有 job 取得 XML 配置
2. 複製 job 為新的 job
3. 從 XML 建立全新的 job
4. 更新 job 配置
5. 比較兩個 jobs 的配置差異

## 涵蓋的指令

| 指令 | 測試目的 | 危險程度 |
|------|---------|---------|
| `get-job` | 取得 job XML 配置 | 低（read-only） |
| `copy-job` | 複製 job | 低 |
| `create-job` | 從 XML 建立新 job | 低 |
| `update-job` | 更新 job 配置 | 中（不可逆） |
| `job-diff` | 比較兩個 jobs 的配置 | 低（read-only） |

## 測試前置條件

- Jenkins server 運行中並已認證（`jenkee auth` 成功）
- Jenkins 中至少有：
  - 1 個現有的測試 job（例如：`test-job-original`）
  - 足夠權限建立、複製、更新 jobs

## 測試步驟

### 1. 取得 Job XML 配置

```bash
jenkee get-job test-job-original > original-config.xml
```

**預期結果**：
- Exit code: 0
- 成功將 XML 配置儲存到檔案
- XML 內容包含完整的 job 配置

**驗證點**：
- [ ] 成功取得 XML
- [ ] XML 格式正確
- [ ] 包含 job 的完整配置資訊
- [ ] 檔案可以用於後續操作

### 2. 複製 Job

```bash
jenkee copy-job test-job-original test-job-copy-1
```

**預期結果**：
- Exit code: 0
- 成功建立新 job `test-job-copy-1`
- 新 job 的配置與原始 job 相同

**驗證點**：
- [ ] 成功建立新 job
- [ ] 新 job 出現在 Jenkins 中
- [ ] 配置與原始 job 一致
- [ ] 顯示成功訊息

### 3. 驗證複製結果（使用 job-diff）

```bash
jenkee job-diff test-job-original test-job-copy-1
```

**預期結果**：
- Exit code: 0
- 沒有顯示差異（或僅有 job 名稱差異）
- 確認兩個 jobs 配置相同

**驗證點**：
- [ ] 命令執行成功
- [ ] 沒有重大配置差異
- [ ] diff 輸出格式清晰

### 4. 從 XML 建立新 Job

```bash
jenkee create-job test-job-from-xml < original-config.xml
```

**預期結果**：
- Exit code: 0
- 成功建立新 job `test-job-from-xml`
- 配置與 XML 內容一致

**驗證點**：
- [ ] 成功建立新 job
- [ ] 新 job 出現在 Jenkins 中
- [ ] 配置正確載入
- [ ] 顯示成功訊息

### 5. 修改 XML 並更新 Job

```bash
# 修改 XML（例如：更新描述）
sed 's/<description>.*<\/description>/<description>Updated description<\/description>/' original-config.xml > updated-config.xml

# 更新 job
jenkee update-job test-job-copy-1 < updated-config.xml
```

**預期結果**：
- Exit code: 0
- Job 配置成功更新
- 新配置立即生效

**驗證點**：
- [ ] 成功更新 job
- [ ] 配置變更已套用
- [ ] 顯示成功訊息

### 6. 驗證更新結果（使用 get-job）

```bash
jenkee get-job test-job-copy-1 > verify-config.xml
grep "Updated description" verify-config.xml
```

**預期結果**：
- Exit code: 0
- 新配置確實已套用
- 可以看到更新的描述

**驗證點**：
- [ ] 成功取得更新後的配置
- [ ] 確認變更已生效

### 7. 比較原始與更新後的 Job

```bash
jenkee job-diff test-job-original test-job-copy-1
```

**預期結果**：
- Exit code: 0
- 顯示描述欄位的差異
- diff 輸出清楚易讀

**驗證點**：
- [ ] 成功顯示差異
- [ ] 差異內容正確
- [ ] 輸出格式清晰

## 典型工作流程範例

### 場景 A：複製 job 到不同環境

```bash
# 1. 從開發環境取得配置
jenkee get-job dev-job > job-config.xml

# 2. 建立測試環境版本
jenkee create-job test-job < job-config.xml

# 3. 比較兩個環境的配置
jenkee job-diff dev-job test-job
```

### 場景 B：批次建立相似的 jobs

```bash
# 1. 取得範本 job 配置
jenkee get-job template-job > template.xml

# 2. 建立多個變體
for env in dev staging prod; do
  sed "s/template-job/${env}-job/" template.xml | \
  jenkee create-job "${env}-job"
done

# 3. 驗證建立結果
jenkee list-jobs --all | grep -E "(dev|staging|prod)-job"
```

### 場景 C：更新多個 jobs 的共同設定

```bash
# 1. 取得第一個 job 配置
jenkee get-job job-1 > config.xml

# 2. 修改配置（例如：更新 JDK 版本）
sed 's/jdk8/jdk11/' config.xml > updated.xml

# 3. 套用到多個 jobs
for job in job-1 job-2 job-3; do
  jenkee update-job "$job" < updated.xml
done

# 4. 驗證變更
jenkee get-job job-1 | grep jdk11
```

## 錯誤情境測試

### 複製已存在的 Job

```bash
jenkee copy-job test-job-original test-job-copy-1
```

**預期結果**：
- Exit code: 非 0
- 顯示 job 已存在的錯誤訊息

**驗證點**：
- [ ] 錯誤被正確偵測
- [ ] 錯誤訊息清楚

### 更新不存在的 Job

```bash
jenkee update-job non-existent-job < config.xml
```

**預期結果**：
- Exit code: 非 0
- 顯示 job 不存在的錯誤訊息

**驗證點**：
- [ ] 錯誤被正確處理
- [ ] 錯誤訊息有幫助

### 使用無效的 XML

```bash
echo "invalid xml" | jenkee create-job test-invalid-job
```

**預期結果**：
- Exit code: 非 0
- 顯示 XML 格式錯誤訊息

**驗證點**：
- [ ] 錯誤被正確偵測
- [ ] 不會建立部分設定的 job

## 測試完成標準

- [ ] 所有 5 個指令都執行成功
- [ ] 所有預期結果都符合
- [ ] 所有驗證點都通過
- [ ] 錯誤情境被正確處理
- [ ] 可以完成完整的 job 配置管理流程
- [ ] 所有測試用 jobs 在測試後被清理

## 清理步驟

測試完成後，清理建立的測試 jobs：

```bash
# 注意：delete-job 是危險命令，需要明確同意
jenkee delete-job test-job-copy-1 test-job-from-xml
```

## 注意事項

- `update-job` 操作不可逆，建議先用 `get-job` 備份原始配置
- `copy-job` 會複製所有配置，包含 build triggers 和 SCM 設定
- 使用 `job-diff` 可以避免意外覆蓋重要設定
- XML 修改建議使用專用工具（如 xmlstarlet）而非 sed

## 相關文件

- [get-job 指令文件](examples/get-job.md)
- [copy-job 指令文件](examples/copy-job.md)
- [create-job 指令文件](examples/create-job.md)
- [update-job 指令文件](examples/update-job.md)
- [job-diff 指令文件](examples/job-diff.md)
