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

## 單次覆蓋：--profile flag

不想動到持久設定時，可以在指令前面加上全域 `--profile` flag，只對這一次呼叫生效：

```bash
jenkee --profile <name> <command>
```

這跟設定 `JENKEE_PROFILE=<name>` 環境變數效果完全相同（實作上就是同一條路徑），優先權也相同。

## Profile 解析順序

jenkee 依下列順序決定要用哪個 profile，第一個有值的就贏：

1. `--profile <name>` flag 或 `JENKEE_PROFILE` 環境變數
2. `jenkee profile use <name>` 設定的持久狀態（存在 `~/.jenkins-inspector/current_profile`）
3. 都沒有 → 使用預設的 `~/.jenkins-inspector/.env`

**重要：指定的 profile 不存在時不會靜默 fallback 到 default**，而是直接報錯並結束（exit code 1），提示要跑 `jenkee profile list` 確認可用的 profile，或建立對應的檔案。這是刻意設計：不希望一個打錯字的 profile 名稱，讓指令默默地打到別的 Jenkins 站台。

## Profile 名稱限制

`jenkee profile use <name>` 的 `<name>` 只能包含英數字、`-`、`_`，且不能是 `default`（保留給內建的預設 profile）。不符合規則會直接報錯，不會嘗試建立或切換。
