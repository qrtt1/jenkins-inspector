# Jenkins Studio Coding Guide

本文件記錄專案的設計原則與架構慣例。

## 專案架構原則

### 1. CLI Interface 設計

**檔案**: `jenkins_tools/cli.py`

- 只負責 CLI interface，不包含複雜實作
- 主要功能：
  - 解析命令列參數
  - Dispatch 到具體的 Command 實作
  - 顯示 usage 和錯誤訊息
- 保持簡潔，所有商業邏輯委派給 Command 類別

**範例**:
```python
def main():
    if len(sys.argv) < 2:
        # 顯示 usage
        sys.exit(1)

    command = sys.argv[1]

    # Dispatch to command
    if command == "auth":
        cmd = AuthCommand()
        sys.exit(cmd.execute())
```

### 2. Command 設計模式

**檔案**: `jenkins_tools/core.py`

使用抽象基礎類別定義 Command interface：

```python
class Command(ABC):
    @abstractmethod
    def execute(self) -> int:
        """執行命令，返回 exit code"""
        pass
```

每個具體 command 實作在 `jenkins_tools/commands/` 目錄下：
- 繼承 `Command` 基礎類別
- 實作 `execute()` 方法
- 返回 0 表示成功，非 0 表示失敗

### 3. 核心元件設計

**檔案**: `jenkins_tools/core.py`

#### Constants

- API URL 等常數直接定義在 `core.py` 中
- 使用大寫命名：`JENKINS_URL`, `JENKINS_CLI_JAR_PATH`

```python
JENKINS_URL = "http://jenkins.example.com:8080/"
JENKINS_CLI_JAR_PATH = Path("/tmp/jenkins-inspector/jenkins-cli.jar")
```

#### JenkinsConfig

- 管理認證設定
- 從 `~/.jenkins-inspector/.env` 讀取
- 使用 `override=True` 確保 .env 優先於環境變數

```python
class JenkinsConfig:
    def __init__(self):
        env_path = Path.home() / ".jenkins-inspector" / ".env"
        load_dotenv(env_path, override=True)
        self.username = os.getenv("JENKINS_USER_ID")
        self.api_token = os.getenv("JENKINS_API_TOKEN")
```

#### JenkinsCLI

- 封裝 jenkins-cli.jar 操作
- 自動下載 jar 檔到固定位置（如果不存在）
- 固定位置：`/tmp/jenkins-inspector/jenkins-cli.jar`
- 提供 `run()` 方法執行 Jenkins CLI 指令

```python
class JenkinsCLI:
    def ensure_cli_jar(self) -> None:
        """如果 jar 不存在則自動下載"""
        if not self.jar_path.exists():
            # 下載邏輯
            pass

    def run(self, command: str, *args: str) -> subprocess.CompletedProcess:
        """執行 jenkins-cli 指令"""
        self.ensure_cli_jar()
        # 執行邏輯
        pass
```

### 4. 認證機制

- 使用 `.env` 檔案儲存認證資訊
- 位置：`~/.jenkins-inspector/.env`（使用者 home 目錄）
- 不在專案目錄，方便跨專案共用

**環境變數**:
```bash
JENKINS_USER_ID=your_email@example.com
JENKINS_API_TOKEN=your_api_token
```

**jenkins-cli.jar 認證**:
- 有認證時使用 `-http` 模式配合 `-auth` 參數
- 無認證時使用 `-webSocket` 模式

## 第一個 Command: auth

### 功能

驗證使用者的 Jenkins 認證設定是否正確。

### 實作邏輯

1. 檢查 `.env` 是否存在且包含必要設定
   - 若未設定：顯示友善錯誤訊息，說明如何設定
   - 顯示 `.env` 完整路徑
2. 自動下載 `jenkins-cli.jar`（如果不存在）
3. 執行 `who-am-i` 指令驗證連線
4. 顯示認證結果
   - 成功：顯示使用者名稱和權限
   - 失敗：顯示錯誤訊息

### 使用方式

```bash
$ jks auth
Verifying authentication...
✓ Authenticated as: user@example.com
Authorities:
  authenticated
```

## 檔案結構

```
jenkins-inspector/
├── jenkins_tools/              # 主要 package（不在 src/ 下）
│   ├── __init__.py
│   ├── cli.py                 # CLI entry point（純 dispatch）
│   ├── core.py                # 核心元件與 Command 基礎類別
│   └── commands/              # 具體 command 實作
│       ├── __init__.py
│       ├── auth.py
│       ├── list_views.py
│       ├── list_jobs.py
│       └── ...
├── docs/
│   └── examples/              # Command 示範文件
│       ├── auth.md
│       ├── list-views.md
│       └── ...
├── pyproject.toml             # Package 設定
├── setup.py                   # 向後相容
├── CODING_GUIDE.md            # Coding 規範
└── README.md
```

## 開發流程

### 新增 Command

1. 在 `jenkins_tools/commands/` 建立新檔案
2. 繼承 `Command` 類別
3. 實作 `execute()` 方法
4. 在 `commands/__init__.py` 匯出
5. 在 `cli.py` 新增 dispatch 邏輯
6. **建立示範文件** `docs/examples/<command-name>.md`
7. **更新 help 命令** - 在 `commands/help.py` 的命令列表中加入新命令
8. **更新 prompt 命令** - 在 `commands/prompt.py` 的指引中加入新命令說明
9. **使用 Black 格式化程式碼** - 完成後執行 `black jenkins_tools/`

### 危險命令的開發

某些命令會對 Jenkins 進行不可逆或影響重大的操作，需要特別標記為「危險命令」：

**危險命令的定義**：
- 不可逆操作（如 delete-job、delete-builds）
- 會影響系統可用性（如 disable-job、enable-job）
- 具有最高權限可執行任意操作（如 groovy）

**開發危險命令時的額外步驟**：

1. **標記為危險命令**
   - 在 `commands/help.py` 的 `DANGEROUS_COMMANDS` 集合中加入命令名稱
   - 這會讓命令在一般 `help` 中隱藏，只在 `help --ask-before-run-commands` 顯示

2. **文件中加入警告區段**
   - 在 `docs/examples/<command>.md` 開頭加入 `⚠️ 警告` 區段
   - 明確說明操作的危險性與影響
   - 說明是否可逆

3. **AI Agent 使用限制**
   - 在文件中加入 `## AI Agent 使用限制` 區段
   - 列出 AI agent 在使用此命令前必須完成的步驟：
     1. 向使用者說明將要執行的操作
     2. 說明操作的影響
     3. 取得使用者明確同意

4. **最佳實踐建議**
   - 在文件中提供安全使用的最佳實踐
   - 如：刪除前先備份、使用軟刪除策略等

**範例**: 參考 `docs/examples/delete-job.md`、`docs/examples/groovy.md`

### Command 示範文件

每當完成一個 command 時，必須建立對應的示範文件。

**檔案位置**: `docs/examples/<command-name>.md`

**內容包含**:
1. Command 用途說明
2. 基本語法
3. 可用選項（如果有）
4. 實際執行範例與結果
5. 常見使用情境

**範例**: 參考 `docs/examples/auth.md`

### 開發模式安裝

```bash
# 啟用虛擬環境
source venv/bin/activate

# 以 editable 模式安裝
pip install -e .

# 測試指令
jks <command>
```

## 注意事項

### 設定檔位置

- **不要**將 `.env` 放在專案目錄
- **一定**使用 `~/.jenkins-inspector/.env`
- 這樣可以跨專案共用設定

### jenkins-cli.jar 管理

- 自動下載到固定位置 `/tmp/jenkins-inspector/jenkins-cli.jar`
- 檢查存在才下載，避免重複下載
- 不加入版本控制（放在 `/tmp` 下）

### 錯誤處理

- Command 執行失敗返回非 0 exit code
- 使用 `sys.stderr` 輸出錯誤訊息
- 提供友善且具體的錯誤說明

### 環境變數優先順序

- `.env` 檔案設定優先於 shell 環境變數
- 使用 `load_dotenv(override=True)` 確保此行為

### Import Style

使用 absolute import，不使用 relative import。

**正確** ✓
```python
from jenkins_tools.core import Command, JenkinsConfig, JenkinsCLI
from jenkins_tools.commands import AuthCommand
```

**錯誤** ✗
```python
from ..core import Command, JenkinsConfig, JenkinsCLI
from .commands import AuthCommand
```

**理由**：
- Absolute import 更清楚明確，容易追蹤模組來源
- 避免 relative import 在重構時造成的路徑問題
- 提升程式碼可讀性與維護性

### 程式碼格式化

**所有 Python 程式碼必須使用 Black 格式化**

在提交程式碼前，務必執行：

```bash
# 格式化所有 Python 檔案
black jenkins_tools/

# 檢查格式但不修改
black --check jenkins_tools/
```

**為什麼使用 Black？**
- 統一的程式碼風格，減少團隊討論
- 自動化格式調整，節省時間
- 提升程式碼可讀性與維護性
- 避免格式相關的 code review 爭議

**重要**：每次完成新功能或修改後，commit 前必須執行 Black。

## AI Agent 開發指引

如果你是 AI agent 正在開發此專案，請務必遵循以下原則：

### 開發前

1. **閱讀本文件** - 完整閱讀 `CODING_GUIDE.md` 了解專案架構與規範
2. **理解設計模式** - 熟悉 Command 模式與專案結構
3. **查看現有範例** - 參考 `jenkins_tools/commands/` 下的現有 command 實作

### 開發中

1. **遵循命名慣例** - 使用 snake_case 檔名，PascalCase 類別名稱
2. **保持一致性** - 參考現有 command 的實作風格
3. **完整實作** - 不要跳過任何步驟（help、prompt、example）
4. **測試功能** - 實際執行命令確認功能正常

### 完成時

1. **更新 help 命令** - 在 `commands/help.py` 加入新命令
2. **更新 prompt 命令** - 在 `commands/prompt.py` 加入新命令說明
3. **建立範例文件** - 在 `docs/examples/` 建立詳細文件
4. **執行 Black** - `black jenkins_tools/` 格式化所有程式碼
5. **測試整合** - 確認 `jks help`、`jks prompt` 和 `jks <new-command>` 都正常運作

### Checklist

新增 command 時的完整檢查清單：

- [ ] 建立 `jenkins_tools/commands/<command>.py`
- [ ] 實作 `Command` 類別與 `execute()` 方法
- [ ] 在 `commands/__init__.py` 匯出
- [ ] 在 `cli.py` 新增 dispatch
- [ ] 更新 `commands/help.py` 命令列表
- [ ] 更新 `commands/prompt.py` 命令說明
- [ ] 建立 `docs/examples/<command>.md`
- [ ] 執行 `black jenkins_tools/`
- [ ] 測試 `jks <command>` 功能
- [ ] 測試 `jks help <command>` 顯示
- [ ] 確認 `jks prompt` 包含新命令

**如果是危險命令，額外檢查**：

- [ ] 在 `commands/help.py` 的 `DANGEROUS_COMMANDS` 集合中加入
- [ ] 在文件中加入 `⚠️ 警告` 區段
- [ ] 在文件中加入 `## AI Agent 使用限制` 區段
- [ ] 提供安全使用的最佳實踐建議
- [ ] 測試 `jks help --ask-before-run-commands` 顯示危險命令
