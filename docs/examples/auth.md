# auth - 驗證 Jenkins 連線

## 用途

驗證使用者的 Jenkins 認證設定是否正確，確保可以成功連線到 Jenkins 伺服器。

## 基本語法

```bash
jks auth
```

## 功能說明

此指令會：
1. 檢查 `~/.jenkins-inspector/.env` 是否存在且包含必要的認證資訊
2. 自動下載 `jenkins-cli.jar`（如果不存在）
3. 使用 `who-am-i` 指令驗證與 Jenkins 伺服器的連線
4. 顯示認證結果與使用者權限

## 執行範例

### 成功案例

當認證設定正確時：

```bash
$ jks auth
Verifying authentication...
✓ Authenticated as: user@example.com
Authorities:
  authenticated
```

**說明**：
- 顯示已成功認證的使用者帳號
- 列出使用者擁有的權限

### 未設定認證

當 `.env` 檔案不存在或未設定時：

```bash
$ jks auth
Error: Jenkins credentials not configured.

Please create a .env file at: /Users/username/.jenkins-inspector/.env

Content:
  JENKINS_URL=http://your-jenkins-server:8080/
  JENKINS_USER_ID=your_email@example.com
  JENKINS_API_TOKEN=your_api_token

You can get your API token from:
  Jenkins > User > Configure > API Token
```

**說明**：
- 提示使用者建立 `.env` 檔案
- 顯示完整的檔案路徑
- 說明如何取得 API Token

### 認證失敗

當認證資訊錯誤時：

```bash
$ jks auth
Verifying authentication...
✗ Authentication failed
java.io.IOException: Server returned HTTP response code: 401 for URL: http://jenkins.example.com:8080/cli?remoting=false
...
```

**說明**：
- 顯示認證失敗訊息
- 包含詳細的錯誤資訊（401 表示認證失敗）

## 常見使用情境

### 初次設定

第一次使用 `jks` 工具時，建議先執行 `jks auth` 確認設定：

```bash
# 1. 建立設定目錄
mkdir -p ~/.jenkins-inspector

# 2. 建立 .env 檔案
cat > ~/.jenkins-inspector/.env <<EOF
JENKINS_URL=http://your-jenkins-server:8080/
JENKINS_USER_ID=your_email@example.com
JENKINS_API_TOKEN=your_api_token_here
EOF

# 3. 驗證設定
jks auth
```

### 更新 API Token

當 API Token 更新後，使用 `jks auth` 驗證新的 token 是否正確：

```bash
# 1. 編輯 .env 更新 token
vi ~/.jenkins-inspector/.env

# 2. 驗證新的設定
jks auth
```

### 除錯連線問題

當其他 command 執行失敗時，先用 `jks auth` 確認基本連線：

```bash
# 如果其他指令失敗，先確認連線
jks auth

# 連線成功後再執行其他操作
jks <other-command>
```

## 注意事項

1. API Token 不是密碼，需要從 Jenkins 網頁介面產生
2. `.env` 檔案位於使用者 home 目錄，不在專案目錄
3. 首次執行會自動下載 `jenkins-cli.jar` 到 `/tmp/jenkins-inspector/`
4. 認證使用 HTTP 模式（`-http`）而非 WebSocket
