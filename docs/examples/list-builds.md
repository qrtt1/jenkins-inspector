# list-builds - 列出 Job 的 Build 歷史

## 用途

列出指定 Jenkins job 的 build 歷史，顯示所有 build numbers。

## 基本語法

```bash
jks list-builds <job-name>
```

## 功能說明

此指令會：
1. 檢查認證設定
2. 使用 Groovy script 查詢 job 的 build 歷史
3. 列出所有 build numbers（由新到舊）
4. 輸出到 stdout

## 執行範例

### 列出 Build 歷史

```bash
$ jks list-builds spider-shield-console-deploy-staging
107
106
105
104
103
102
101
100
...
```

**說明**：
- 列出所有的 build numbers
- 由最新到最舊排序
- 每行一個 build number

### 缺少參數

```bash
$ jks list-builds
Error: Missing job name
Usage: jks list-builds <job-name>
```

### Job 不存在

```bash
$ jks list-builds non-existent-job
Error: Job 'non-existent-job' not found
```

## 常見使用情境

### 查看最近的 Builds

取得最近的 5 個 builds：

```bash
$ jks list-builds spider-shield-console-deploy-staging | head -5
107
106
105
104
103
```

### 統計 Build 數量

```bash
$ jks list-builds spider-shield-console-deploy-staging | wc -l
107
```

**說明**：
- 顯示總共有多少個 builds

### 批次取得 Console Output

結合 `console` command 批次取得輸出：

```bash
# 取得最近 3 個 builds 的 console output
jks list-builds spider-shield-console-deploy-staging | head -3 | while read build; do
  echo "=== Build #$build ==="
  jks console spider-shield-console-deploy-staging $build | tail -20
  echo ""
done
```

### 找到最新成功的 Build

雖然此指令只列出 build numbers，但可以配合其他工具：

```bash
# 列出所有 builds
jks list-builds spider-shield-console-deploy-staging > builds.txt

# 手動檢查或配合 console 查看狀態
```

### 比較不同 Job 的 Build 數量

```bash
echo "Beta builds:"
jks list-builds spider-shield-console-deploy-staging | wc -l

echo "Prod builds:"
jks list-builds spider-shield-console-deploy-productionuction | wc -l
```

## 輸出格式

- 每行一個 build number
- 純數字，由新到舊排序
- 適合配合 pipe 和其他 Unix 工具處理

## 相關指令

- `jks console <job> [build]` - 取得特定 build 的 console 輸出
- `jks list-jobs <view>` - 列出 view 中的所有 jobs

## 注意事項

1. Job 名稱區分大小寫
2. 輸出包含所有歷史 builds（可能很多）
3. Build numbers 是遞增的正整數
4. 使用 Groovy script 實作，需要幾秒鐘執行時間
5. 適合配合 `head`、`tail`、`grep` 等工具過濾
