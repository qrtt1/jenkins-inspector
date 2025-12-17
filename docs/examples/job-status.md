# job-status - 查看 Job 狀態與觸發關係

## 用途

查看 Jenkins job 的完整狀態資訊，包含建置健康度、最近的 builds、以及與其他 jobs 的觸發關係。

## 基本語法

```bash
jks job-status <job-name>
```

## 功能說明

此指令會顯示：
1. Job 基本狀態（啟用/停用、是否可建置）
2. 建置健康度評分與描述
3. 最近 builds 的快速連結（permalinks）
4. Downstream Projects（此 job 會觸發的下游 jobs）
5. Upstream Projects（會觸發此 job 的上游 jobs）

## 執行範例

### 查看 Auto Job 狀態

```bash
$ jks job-status spider-shield-console-release-image-auto
=== Job: spider-shield-console-release-image-auto ===

Status: ENABLED
Buildable: true

=== Health ===
Score: 100%
Description: Build stability: No recent builds failed.

=== Last Builds ===
Last Build: #130
Last Stable Build: #130
Last Successful Build: #130
Last Failed Build: #115
Last Unsuccessful Build: #115
Last Completed Build: #130

=== Downstream Projects ===
  - spider-shield-console-release-image-staging
  - spider-shield-console-release-image-productionuction

=== Upstream Projects ===
  (none)
```

**說明**：
- Status 為 ENABLED 表示 job 啟用中
- Health Score 100% 表示最近的 builds 都成功
- Downstream Projects 顯示此 auto job 會觸發 staging 和 production 兩個 release jobs
- Upstream Projects 為 (none) 表示沒有其他 job 觸發它（由 GitLab webhook 觸發）

### 查看 Release Job 狀態

```bash
$ jks job-status spider-shield-console-release-image-staging
=== Job: spider-shield-console-release-image-staging ===

Status: ENABLED
Buildable: true

=== Health ===
Score: 100%
Description: Build stability: No recent builds failed.

=== Last Builds ===
Last Build: #115
Last Stable Build: #115
Last Successful Build: #115
Last Failed Build: #106
Last Unsuccessful Build: #106
Last Completed Build: #115

=== Downstream Projects ===
  (none)

=== Upstream Projects ===
  - spider-shield-console-release-image-auto
```

**說明**：
- Downstream Projects 為 (none) 表示此 job 不會自動觸發其他 jobs
- Upstream Projects 顯示此 job 會被 auto job 觸發
- 可清楚看出 pipeline 的觸發鏈：auto → release-image-staging

### 缺少參數

```bash
$ jks job-status
Error: Missing job name
Usage: jks job-status <job-name>
```

### Job 不存在

```bash
$ jks job-status non-existent-job
Error: Job 'non-existent-job' not found
```

## 常見使用情境

### 理解 Pipeline Flow

快速了解 job 在整個 pipeline 中的位置：

```bash
# 從 auto job 開始
$ jks job-status spider-shield-console-release-image-auto
# 看到 downstream: release-image-staging, release-image-production

# 檢查下游 job
$ jks job-status spider-shield-console-release-image-staging
# 看到 upstream: release-image-auto
# 確認觸發關係
```

### 檢查 Job 健康狀態

批次檢查多個 jobs 的健康度：

```bash
# 使用 view 內的 jobs 清單
jks list-jobs AVENGERS | while read job; do
  echo "=== $job ==="
  jks job-status "$job" | grep -A 2 "=== Health ==="
  echo ""
done
```

輸出範例：
```
=== spider-shield-console-release-image-auto ===
=== Health ===
Score: 100%
Description: Build stability: No recent builds failed.

=== spider-shield-console-release-image-staging ===
=== Health ===
Score: 100%
Description: Build stability: No recent builds failed.
```

### 找出最近失敗的 Build

```bash
$ jks job-status my-job | grep "Last Failed"
Last Failed Build: #115
```

### 追蹤 Pipeline 觸發鏈

從任一 job 往上或往下追蹤：

```bash
# 往下追蹤（找出會影響哪些 jobs）
$ jks job-status auto-job | grep -A 10 "Downstream Projects"

# 往上追蹤（找出被誰影響）
$ jks job-status deploy-job | grep -A 10 "Upstream Projects"
```

### 比對環境差異

檢查 staging 和 production 的 job 配置是否一致：

```bash
# 比對 upstream 設定
echo "Beta upstream:"
jks job-status spider-shield-console-release-image-staging | grep -A 5 "Upstream"

echo "Prod upstream:"
jks job-status spider-shield-console-release-image-productionuction | grep -A 5 "Upstream"
```

### 快速找到可用的 Build Number

```bash
# 取得最新成功的 build number
jks job-status my-job | grep "Last Successful" | awk '{print $NF}' | tr -d '#'
```

可配合其他命令使用：
```bash
# 取得最新成功 build 的 console 輸出
BUILD=$(jks job-status my-job | grep "Last Successful" | awk '{print $NF}' | tr -d '#')
jks console my-job $BUILD
```

## 輸出格式

輸出分為五個區塊：

### 1. Job 基本資訊
- Job 完整名稱
- 狀態（ENABLED/DISABLED）
- 是否可建置（Buildable）

### 2. Health Report
- 健康度評分（0-100%）
- 健康度描述（如：build stability）

### 3. Last Builds (Permalinks)
- Last Build：最新的 build
- Last Stable Build：最新的穩定 build
- Last Successful Build：最新的成功 build
- Last Failed Build：最新的失敗 build
- Last Unsuccessful Build：最新的不成功 build（包含 unstable）
- Last Completed Build：最新的完成 build

### 4. Downstream Projects
此 job 會觸發的下游 jobs 清單，若無則顯示 (none)

### 5. Upstream Projects
會觸發此 job 的上游 jobs 清單，若無則顯示 (none)

## 相關指令

- `jks list-jobs <view>` - 列出 view 中的所有 jobs
- `jks get-job <job>` - 取得 job 的完整 XML 配置
- `jks list-builds <job>` - 列出 job 的所有 build numbers
- `jks console <job> [build]` - 查看 build 的 console 輸出

## 注意事項

1. Job 名稱區分大小寫
2. Downstream/Upstream 關係來自 Jenkins 的 job 配置（如 Parameterized Trigger Plugin）
3. 手動執行的 jobs 不會出現在 Upstream Projects 中
4. Health Score 基於最近的 build 歷史計算
5. 使用 Groovy script 實作，執行需要幾秒鐘
