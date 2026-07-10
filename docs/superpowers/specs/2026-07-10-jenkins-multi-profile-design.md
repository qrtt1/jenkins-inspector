# Jenkins Multi-Profile Support — Design

## 問題陳述

`JenkinsConfig`（`jenkins_tools/core.py:89`）目前寫死只讀 `~/.jenkins-inspector/.env` 這一份設定，代表一台機器同時間只能連一個 Jenkins 站台。但實際使用情境是同一人要跨多個真實站台工作（例如中央 ops、pchome prod），且切換頻率無法預期：可能一段時間只固定用一個站台，也可能同一個 session 內需要來回切換。

目前唯一解法是使用者自己土法手動備份/複製整份 `.env`（如 office-mbp 上的 `.env.ops.bak`、`.env.pchome-prod.bak` + 手動 `cp`），這件事沒有工具支援、也沒有留下「目前是哪個站台」的線索。

**核心風險**：`jenkee` 有 `delete-job`、`delete-builds`、`groovy` 這類破壞性命令。若使用者忘記目前 active 的是哪個 profile，可能對錯的站台下破壞性命令 — 這是本次設計最需要正面處理的風險，不只是「支援多組設定」而已。

## 範圍界線

已確認排除／限制的範圍：

- **不需相容舊檔案**：不必轉譯/沿用 office-mbp 現有的 `.env.*.bak` 檔案，新設計可以重新建立憑證，舊檔案使用者手動清理即可
- **不需跨機器同步**：每台機器各自建立自己的 profile，profile 定義與憑證都不跨機器同步
- **單人多站台**：使用情境是同一人跨多台自己的機器操作多個站台，不是多人共享同一份設定

已確認必須滿足的相容性限制：

- **對既有使用者零感知變更**：只用單一 `~/.jenkins-inspector/.env`、沒有 profile 概念的既有使用者，升級後所有指令、設定檔位置、輸出格式都必須原封不動繼續運作，不能要求先做任何遷移動作。Profile 是加法特性，疊加在現有單一 `.env` 之上，不是取代或重構它。「無 profile 設定」永遠是合法狀態，等同於現在的行為。

## 設計

### 1. 設定解析順序（Config Resolution）

`JenkinsConfig` 決定「這次要用哪份設定」時，依序檢查，第一個命中就用：

1. **`--profile <name>` CLI flag** — 單次覆蓋，最高優先
2. **`JENKEE_PROFILE` 環境變數** — session 範圍覆蓋，不動任何持久狀態（例如在某個 terminal tab 裡 `export JENKEE_PROFILE=pchome-prod`，該 tab 都用這個站台，關掉 tab 就沒了）
3. **`~/.jenkins-inspector/current_profile` 狀態檔** — 持久切換，`jenkee profile use <name>` 寫入這個檔案
4. **預設** — 都沒有命中時，讀 `~/.jenkins-inspector/.env`（今天的行為，完全不變）

這個順序刻意跟 AWS CLI 的 `--profile` > `AWS_PROFILE` > 預設 一致，對應「像 aws profile 那樣」的原始需求。

檔案佈局：

```
~/.jenkins-inspector/
├── .env                      # 現有預設 profile，原封不動
├── current_profile           # 純文字，內容是 profile 名稱；不存在 = 用預設
└── profiles/
    ├── ops.env
    └── pchome-prod.env       # 格式與 .env 完全相同
```

### 2. CLI wiring 與元件變動

**`cli.py`**：在 dispatch 前先攔截全域 `--profile <name>`（比照現有攔截 `--help`/`-h` 的手法），抽出來後 `os.environ["JENKEE_PROFILE"] = name` 並從 argv 移除這兩個 token，再繼續原本 dispatch。每個既有 Command 類別完全不用改建構子、不用感知 profile 概念 —— `--profile` 只是把「單次覆蓋」轉成跟 `JENKEE_PROFILE` 環境變數同一條處理路徑。

**`core.py` 的 `JenkinsConfig`**：`__init__` 內新增解析上述四層順序的邏輯，決定要 `load_dotenv` 哪個檔案路徑；同時記下 `self.profile_name`（`None` 代表用的是預設 `.env`）供後續指令顯示用。若 `current_profile` 狀態檔或 `--profile` 指到一個不存在的 profile 檔，`JenkinsConfig` 標記為不可用狀態，讓呼叫端用既有「找不到設定就印出清楚教學」的風格報錯。

**新增 `ProfileCommand`**（`jenkins_tools/commands/profile.py`，掛進 `cli.py` 跟 `commands/__init__.py`，風格比照 `dev_qa.py`/`auth.py`）：

- `jenkee profile list` — 掃 `profiles/` 目錄列出所有 profile，標出哪個是目前 active
- `jenkee profile use <name>` — 檢查 `profiles/<name>.env` 存在後，寫入 `current_profile` 狀態檔
- `jenkee profile use --default` — 刪掉/清空 `current_profile` 狀態檔，切回預設 `.env`
- `jenkee profile current` — 印出目前實際生效的 profile 與其來源（`--profile` / `JENKEE_PROFILE` / `current_profile` 檔 / 預設）

新建 profile 檔案本身沿用現有「機密不透過對話/CLI 參數輸入」的原則：`profile use` 找不到檔案時的錯誤訊息教使用者手動 `mkdir -p ~/.jenkins-inspector/profiles && cat > .../profiles/<name>.env`，不提供會把 token 當參數傳入的 `profile create` 指令。

### 3. 安全可見性

- **非破壞性指令**（`list-jobs`、`job-status`、`console` 等）：只有在「目前生效的不是預設 `.env`」時才印出一行 `Active profile: <name> (<jenkins_url>)` 到 stderr。預設單一 `.env` 的既有使用者輸出完全不變。
- **破壞性指令**（`delete-job`、`delete-builds`、`groovy`，目前用 `DangerousCommandMixin.require_confirmation()`）：不論是否為預設 profile，一律在確認提示裡帶入目前生效的站台名稱／URL，例如：

  ```
  ⚠ Active profile: pchome-prod (jenkins.prod.pchome.tenmax.tw)
  Delete job 'old-job' on pchome-prod? [y/N]
  ```

  這是既有 `DangerousCommandMixin` 的擴充（塞站台資訊進提示文字），不是新機制，`--yes-i-really-mean-it` 跳過確認的行為不變。

### 4. 錯誤處理

- `--profile <name>` 或 `JENKEE_PROFILE` 指到不存在的 profile：直接報錯並中止，不 silently fallback 到預設（否則會在錯的站台上跑指令而不自知）
- `current_profile` 狀態檔指到一個後來被刪除的 profile 檔：同樣報錯中止，提示 `jenkee profile use --default` 或 `jenkee profile use <existing-name>`
- `profiles/` 目錄不存在（從未建立過任何 profile）：`jenkee profile list` 印出「尚未建立任何 profile，目前使用預設 `~/.jenkins-inspector/.env`」，這是正常狀態，不是錯誤

### 5. 測試規劃

延續現有慣例（測試檔對應 `docs/test-plan-for-*.md`，並用 real Jenkins docker container 跑整合測試，見 `tests/conftest.py` + `scripts/start-test-jenkins.sh`），新功能拆兩層：

- **`JenkinsConfig` 解析邏輯的單元測試**（不需要真的 Jenkins container，純檔案系統操作）：驗證四層解析順序、`profiles/` 不存在時退回預設、`current_profile` 指向不存在檔案時的錯誤行為
- **`profile` 指令的整合測試**：新增 `tests/test_profile_command.py`，對應新的 `docs/test-plan-for-profile-management.md`，涵蓋 `profile list` / `use` / `use --default` / `current` 的實際 CLI 輸出
- **回歸驗證**：現有全部測試（`test_auth.py`、`test_initial_setup.py` 等）必須不做任何修改就能繼續通過 — 這是驗證「相容性」需求是否達成的直接證據，是設計核心承諾的驗收標準，不是額外加的
- **破壞性指令確認訊息**：在既有 `DangerousCommandMixin` 相關測試上，額外驗證確認提示裡有出現正確的 profile/site 名稱
