# list-views - 列出所有 Jenkins Views

## 用途

列出 Jenkins 伺服器上的所有 views（視圖）。Views 用來組織和分類 Jenkins jobs。

## 基本語法

```bash
jks list-views
```

## 功能說明

此指令會：
1. 檢查認證設定
2. 使用 Groovy script 查詢 Jenkins instance
3. 列出所有 views 並依名稱排序
4. 輸出 view 名稱列表（每行一個）

## 執行範例

### 成功案例

```bash
$ jks list-views
AVENGERS
all
avengers-locator
shield-console
stark-gateway
```

**說明**：
- 列出所有可用的 views
- 按字母順序排列
- `all` 是預設的 view，包含所有 jobs
- 其他 views 用來組織不同專案或團隊的 jobs

### 未設定認證

```bash
$ jks list-views
Error: Jenkins credentials not configured.
Run 'jks auth' to configure credentials.
```

**說明**：
- 需要先設定認證才能執行
- 使用 `jks auth` 檢查認證設定

## 常見使用情境

### 探索 Jenkins 結構

第一次接觸 Jenkins 伺服器時，先列出所有 views 了解專案組織：

```bash
# 列出所有 views
jks list-views

# 選擇感興趣的 view，查看其中的 jobs
jks list-jobs AVENGERS
```

### 尋找特定專案

當不確定專案在哪個 view 時：

```bash
# 列出所有 views
jks list-views

# 從結果中找到相關的 view 名稱
# 例如看到 AVENGERS，再查看該 view 的 jobs
```

### 確認 View 存在

在執行其他操作前，確認 view 是否存在：

```bash
# 列出所有 views
jks list-views | grep -i spider

# 確認 AVENGERS view 存在後，再進行後續操作
```

## 技術說明

此指令使用 Groovy script 透過 Jenkins CLI 執行：

```groovy
println hudson.model.Hudson.instance.views*.name.sort().join('\n')
```

- 存取 Jenkins instance 的 views 集合
- 取得所有 view 的名稱
- 排序後以換行分隔輸出

## 相關指令

- `jks list-jobs <view-name>` - 列出特定 view 中的所有 jobs
- `jks auth` - 驗證 Jenkins 認證設定

## 注意事項

1. 需要有效的 Jenkins 認證才能執行
2. 列出的是所有使用者可見的 views（依權限而定）
3. Groovy script 執行需要幾秒鐘時間
4. 輸出已依名稱排序，方便查找
