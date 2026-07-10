# Test Plan: Profile Management

## 測試情境

使用者跨多個 Jenkins 站台工作，透過具名 profile 切換設定，而不必手動複製 `.env` 檔案。

## 測試目標

驗證使用者可以：
1. 列出目前有哪些 profile、哪個是 active
2. 持久切換 active profile，並在下次執行指令時繼續生效
3. 用 `--profile` 做單次覆蓋，不影響持久狀態
4. 在指到不存在的 profile 時得到清楚的錯誤訊息，而不是靜默使用錯的站台

## 涵蓋的指令

| 指令 | 測試目的 | 預期結果 |
|------|---------|---------|
| `profile list` | 列出所有 profile 與目前 active 的是誰 | 顯示 `default` 及所有具名 profile，標出 active |
| `profile use <name>` | 持久切換 active profile | 寫入 `current_profile` 狀態檔，之後的指令都套用 |
| `profile use --default` | 切回預設 `.env` | 清除 `current_profile` 狀態檔 |
| `profile current` | 顯示目前生效的 profile 與其來源 | 顯示 profile 名稱、來源、對應設定檔路徑 |
| `--profile <name>` | 單次覆蓋 | 只影響該次呼叫，不寫入任何狀態檔 |

## 測試前置條件

跟其他測試計畫不同，這裡不需要真的 Jenkins server 在跑 -- `profile` 系列指令都只是檔案系統操作。測試透過把 `HOME` 環境變數導向一個暫時目錄來隔離 `~/.jenkins-inspector`，不會碰到開發者本機的真實設定。

## 測試步驟

### 1. 沒有任何 profile 時列出清單

```bash
HOME=/tmp/fake-home jenkee profile list
```

**預期結果**：顯示 `default (active)`，不報錯。

### 2. 建立並切換 profile

```bash
mkdir -p /tmp/fake-home/.jenkins-inspector/profiles
cat > /tmp/fake-home/.jenkins-inspector/profiles/ops.env <<EOF
JENKINS_URL=http://ops.example.com/
JENKINS_USER_ID=u
JENKINS_API_TOKEN=t
EOF
HOME=/tmp/fake-home jenkee profile use ops
HOME=/tmp/fake-home jenkee profile list
```

**預期結果**：`profile use` 顯示切換成功；`profile list` 顯示 `ops (active)`。

### 3. 單次覆蓋不動持久狀態

```bash
HOME=/tmp/fake-home jenkee --profile ops profile current
cat /tmp/fake-home/.jenkins-inspector/current_profile  # 應該還是原本的狀態，沒被 --profile 覆蓋
```

### 4. 指到不存在的 profile

```bash
HOME=/tmp/fake-home jenkee profile use does-not-exist
```

**預期結果**：exit code 1，錯誤訊息包含建立 profile 的操作指引（`mkdir -p ...`）。
