# profile

管理多組 Jenkins 連線設定（multi-site support），可在不同 Jenkins 站台間切換。

## 用法

### list - 列出所有 profiles，標示目前使用中的那個

```bash
jenkee profile list
```

### use - 切換目前使用的 profile

```bash
jenkee profile use <name>
jenkee profile use --default
```

### current - 顯示目前使用中的 profile 詳細資訊

```bash
jenkee profile current
```

## 建立 profile

Profile 檔案放在 `~/.jenkins-inspector/profiles/<name>.env`：

```bash
mkdir -p ~/.jenkins-inspector/profiles
cat > ~/.jenkins-inspector/profiles/<name>.env << 'EOF'
JENKINS_URL=http://your-jenkins-server:8080/
JENKINS_USER_ID=your_email@example.com
JENKINS_API_TOKEN=your_api_token
EOF
```

也可以用 `JENKEE_PROFILE=<name>` 環境變數暫時覆蓋，優先權高於 `profile use` 設定的持久狀態。
