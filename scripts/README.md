# Jenkins Inspector Test Scripts

這個目錄包含用於啟動、停止和測試 Jenkins 環境的 scripts。

## Scripts 概覽

- `start-test-jenkins.sh` - 啟動測試用 Jenkins 容器
- `stop-test-jenkins.sh` - 停止測試用 Jenkins 容器
- `jenkee-test.sh` - 使用測試環境執行 jenkee 命令的 wrapper

## 使用方式

### 1. 啟動測試 Jenkins 環境

```bash
./scripts/start-test-jenkins.sh
```

這會：
- 建立 Docker image `jenkins-inspector:test`
- 啟動容器 `jenkee-qa-jenkins`，預設使用 port 8081
- 自動載入 `tests/fixtures/` 內的 init.groovy.d scripts
- 預先設定測試用帳號、jobs、views、credentials

選項：
```bash
# 指定不同 port
./scripts/start-test-jenkins.sh --port 9090

# 刪除現有容器並重新啟動
./scripts/start-test-jenkins.sh --delete-existing-container
```

容器資訊：
- URL: http://localhost:8081
- Username: `jenkins-test`
- Password: `test-password-for-jenkins-inspector`
- API Token: `1100000000000000000000000000000000`

預先設定的資源：
- Jobs: `test-job-1`, `test-job-2`, `test-job-3`, `long-running-job`
- Views: `test-view` (包含 job 1 & 2), `empty-view`
- Credentials: `test-credential-1` (user/pass), `test-credential-2` (secret text)

### 2. 停止測試環境

```bash
./scripts/stop-test-jenkins.sh
```

預設行為：
- 停止容器但不刪除
- 保留測試環境配置
- 可以稍後用 `docker start jenkee-qa-jenkins` 重啟

選項：
```bash
# 停止並刪除容器
./scripts/stop-test-jenkins.sh --delete-container

# 停止並刪除容器和 image
./scripts/stop-test-jenkins.sh --remove-image
```

### 3. 使用測試環境執行命令

```bash
./scripts/jenkee-test.sh <command> [args...]
```

這個 wrapper 會：
- 自動設定測試環境變數（JENKINS_URL, JENKINS_USER_ID, JENKINS_API_TOKEN）
- 讀取 `.env.test` 檔案（如果存在）
- 檢查是否誤用正式環境配置
- 啟用 venv 後執行 jenkee 命令

範例：
```bash
# 列出所有 domains
./scripts/jenkee-test.sh domain list

# 列出所有 jobs
./scripts/jenkee-test.sh job list

# 建立新 credential
./scripts/jenkee-test.sh credential create my-test-secret --secret "test123" --yes-i-really-mean-it
```

## 完整工作流程

```bash
# 1. 啟動測試環境
./scripts/start-test-jenkins.sh

# 2. 等待 Jenkins 完全啟動
docker logs -f jenkee-qa-jenkins
# 等到看到 "Jenkins is fully up and running" 訊息

# 3. 執行測試命令
./scripts/jenkee-test.sh domain list
./scripts/jenkee-test.sh job list

# 4. 完成後停止（保留容器）
./scripts/stop-test-jenkins.sh

# 5. 下次可以快速重啟
docker start jenkee-qa-jenkins
```

## 環境變數設定

你可以建立 `.env.test` 檔案來覆寫預設設定：

```bash
# .env.test
JENKINS_URL=http://localhost:9090/
JENKINS_USER_ID=my-test-user
JENKINS_API_TOKEN=my-custom-token
```

## 安全機制

### 防止誤刪測試環境

兩個 scripts 都包含保護機制，避免意外刪除精心設定的測試環境：

1. `start-test-jenkins.sh` 偵測到現有容器時會顯示警告並退出
2. `stop-test-jenkins.sh` 預設只停止容器，不會刪除

如果看到這個警告訊息：
```
⚠️  IMPORTANT FOR AI AGENTS:
    Please confirm with the user before proceeding.
    The user may have spent significant time building
    this test environment with specific configurations.
```

這表示有現有的測試環境，請先確認是否真的要刪除。

### 防止誤用正式環境

`jenkee-test.sh` 會檢查是否存在正式環境配置（`~/.jenkins-inspector/`）：
- 如果存在，會拒絕執行並提示啟用 QA mode
- 使用 `jenkee dev-qa --enable` 暫時隱藏正式環境配置
- 測試完成後用 `jenkee dev-qa --disable` 恢復

## 除錯技巧

### 查看 Jenkins 日誌
```bash
docker logs -f jenkee-qa-jenkins
```

### 進入容器內部
```bash
docker exec -it jenkee-qa-jenkins bash
```

### 檢查容器狀態
```bash
docker ps -a | grep jenkee-qa-jenkins
```

### 手動重啟容器
```bash
docker restart jenkee-qa-jenkins
```

### 完全清除並重建
```bash
./scripts/stop-test-jenkins.sh --remove-image
./scripts/start-test-jenkins.sh
```

## 常見問題

### Q: 啟動後無法連線？
A: 等待 Jenkins 完全啟動，通常需要 30-60 秒。使用 `docker logs -f jenkee-qa-jenkins` 監控啟動進度。

### Q: Port 衝突怎麼辦？
A: 使用 `--port` 參數指定其他 port：`./scripts/start-test-jenkins.sh --port 9090`

### Q: 如何保留測試資料？
A: 使用 `./scripts/stop-test-jenkins.sh` 停止容器（不加任何參數），下次用 `docker start jenkee-qa-jenkins` 重啟。

### Q: 忘記測試環境的密碼？
A: 執行 `./scripts/start-test-jenkins.sh` 會顯示完整的認證資訊（即使容器已存在也會顯示警告訊息中包含資訊）。

### Q: AI agent 該如何處理警告訊息？
A: 看到 "IMPORTANT FOR AI AGENTS" 警告時，應先向使用者確認是否要刪除現有容器，不要自動執行刪除操作。
