# Jenkins Inspector 測試基礎建設

本目錄包含 jenkins-inspector 專案的測試套件。測試使用 pytest 框架並透過 testcontainers 提供隔離的 Jenkins 測試環境。

## 目錄結構

```
tests/
├── README.md           # 本文件
├── conftest.py         # pytest fixtures 與測試基礎建設
├── fixtures/           # 測試用 Jenkins 初始化腳本
│   └── 00-create-test-user.groovy
├── test_auth.py        # auth 指令測試
└── test_example.py     # 範例測試（展示 fixture 用法）
```

## 測試基礎建設

### 核心 Fixtures (conftest.py)

#### 1. Jenkins 環境 Fixtures

- **`jenkins_init_dir`** (session scope)
  - 提供 Jenkins init scripts 目錄路徑（tests/fixtures/）
  - 用於初始化 Jenkins 測試環境（建立測試用戶等）

- **`jenkins_container`** (session scope)
  - 啟動 Jenkins Docker container
  - 整個測試 session 只啟動一次，多個測試共用
  - 使用 testcontainers 管理生命週期

- **`jenkins_instance`** (session scope)
  - 提供 `JenkinsTestInstance` 物件
  - 包含 Jenkins URL、認證資訊和實用方法
  - 自動等待 Jenkins 就緒並驗證健康狀態
  - **安全約束**：強制檢查 Jenkins 運行在 localhost

- **`jenkins_env`** (function scope)
  - 提供包含正確認證的環境變數字典
  - 適合需要透過 subprocess 執行的測試

- **`jenkins_bad_env`** (function scope)
  - 提供包含錯誤認證的環境變數字典
  - 用於測試認證失敗情境

#### 2. 命令執行 Fixtures

- **`run_jenkee`** (function scope)
  - 提供 `JenkeeRunner` 物件，用於執行 jenkee 指令
  - 自動帶入正確的 Jenkins 環境變數
  - 支援兩種使用方式：
    - **直接執行**：`run_jenkee.run("auth")`
    - **Builder 模式**：`run_jenkee.build_command("auth").with_timeout(30).run()`

- **`run_jenkee_authed`** (function scope)
  - 與 `run_jenkee` 相同，但會先驗證 auth 成功
  - 適合用於其他指令的測試，確保認證環境正常
  - 在返回 runner 前會執行 auth 並驗證通過

- **`run_jenkee_bad_auth`** (function scope)
  - 與 `run_jenkee` 相同，但使用錯誤的認證
  - 用於測試認證失敗情境

### JenkeeCommandBuilder API

Builder 提供以下方法串接：

```python
run_jenkee.build_command("auth")
    .with_timeout(30)        # 設定執行逾時（秒）
    .allow_failure()         # 允許失敗（不自動斷言）
    .must_fail()            # 斷言必須失敗（returncode != 0）
    .run()                  # 執行指令
```

### 安全約束

測試環境實施以下安全約束：

1. **Localhost 約束**
   - Jenkins 必須運行在 localhost 或 127.0.0.1
   - 在 fixture 層級檢查（jenkins_instance）
   - 在執行層級檢查（JenkeeCommandBuilder.run()）
   - 違反約束會立即 assert 失敗

2. **環境隔離**
   - 測試不依賴真實的 ~/.jenkins-inspector/.env
   - 環境變數優先於 .env 檔案（core.py: load_dotenv(override=False)）
   - 每個測試透過 fixture 取得獨立的環境變數

## 測試寫作慣例

### 1. 使用 3A Pattern (Arrange-Act-Assert)

所有測試應遵循 3A 模式，並用註解明確標示：

```python
def test_auth_success(run_jenkee):
    """測試成功的認證情境"""
    # Arrange: 使用正確的 Jenkins 認證資訊（由 fixture 提供）

    # Act: 執行 auth 指令
    result = run_jenkee.run("auth")

    # Assert: 驗證認證成功
    assert result.returncode == 0
    assert "Authenticated as:" in result.stdout or "✓" in result.stdout
```

#### 3A 階段說明

- **Arrange（準備）**
  - 說明測試資料/環境的設定
  - 如果由 fixture 提供，應註明
  - 如果需要額外準備，在此階段執行

- **Act（執行）**
  - 執行被測試的操作
  - 通常只有一個主要動作
  - 保持簡潔，不包含驗證邏輯

- **Assert（斷言）**
  - 驗證結果是否符合預期
  - 可以有多個 assert
  - 斷言應該明確且有意義

### 2. 命令執行方式選擇

根據測試需求選擇合適的執行方式：

#### 簡單情況（99%）- 直接執行
```python
def test_simple_command(run_jenkee):
    # Arrange: ...

    # Act: 直接執行
    result = run_jenkee.run("auth")

    # Assert: ...
    assert result.returncode == 0
```

#### 需要設定選項 - Builder 模式
```python
def test_with_timeout(run_jenkee):
    # Arrange: 設定 30 秒 timeout

    # Act: 使用 builder 設定選項
    result = run_jenkee.build_command("auth").with_timeout(30).run()

    # Assert: ...
    assert result.returncode == 0
```

#### 測試失敗情境 - must_fail()
```python
def test_auth_failure(run_jenkee_bad_auth):
    # Arrange: 使用錯誤的認證

    # Act: 執行並預期失敗
    result = run_jenkee_bad_auth.build_command("auth").must_fail().run()

    # Assert: 驗證失敗原因
    assert result.returncode != 0
    assert "failed" in result.stderr.lower()
```

### 3. 測試命名慣例

- 測試檔案：`test_<command>.py` (例如：test_auth.py)
- 測試函式：`test_<command>_<scenario>` (例如：test_auth_success)
- 使用描述性名稱，清楚表達測試目的

### 4. Docstring

每個測試都應該有中文 docstring 說明測試目的：

```python
def test_auth_success(run_jenkee):
    """測試成功的認證情境"""
    # ...
```

### 5. 測試覆蓋情境

為每個指令撰寫測試時，應涵蓋：

1. **成功情境** - 正常執行成功
2. **失敗情境** - 各種錯誤情況（認證失敗、參數錯誤等）
3. **輸出格式** - 驗證輸出包含必要資訊
4. **進階選項** - timeout、特殊參數等
5. **邊界情況** - 冪等性、重複執行、空輸入等

## 執行測試

### 執行全部測試
```bash
pytest -v
```

### 執行特定檔案
```bash
pytest -v tests/test_auth.py
```

### 執行特定測試
```bash
pytest -v tests/test_auth.py::test_auth_success
```

### 顯示輸出（除錯用）
```bash
pytest -v -s tests/test_auth.py
```

## 範例：撰寫新的測試檔案

```python
# tests/test_list_views.py

def test_list_views_success(run_jenkee):
    """測試成功列出 views"""
    # Arrange: 使用正確的認證（由 fixture 提供）

    # Act: 執行 list-views 指令
    result = run_jenkee.run("list-views")

    # Assert: 驗證執行成功
    assert result.returncode == 0
    assert result.stdout  # 應該有輸出


def test_list_views_with_format(run_jenkee):
    """測試 list-views 支援 format 參數"""
    # Arrange: 準備使用 --format 參數

    # Act: 執行帶參數的指令
    result = run_jenkee.run("list-views", "--format", "json")

    # Assert: 驗證輸出格式
    assert result.returncode == 0
    # 驗證 JSON 格式...


def test_list_views_with_wrong_auth(run_jenkee_bad_auth):
    """測試錯誤認證導致失敗"""
    # Arrange: 使用錯誤的認證

    # Act: 執行指令並預期失敗
    result = run_jenkee_bad_auth.build_command("list-views").must_fail().run()

    # Assert: 驗證失敗
    assert result.returncode != 0
```

## 注意事項

1. **不要硬編碼 URL**
   - 使用 fixture 提供的環境變數
   - 不要直接連接真實 Jenkins 環境

2. **測試隔離**
   - 每個測試應該獨立運行
   - 不依賴其他測試的執行順序或結果

3. **清理資源**
   - testcontainers 會自動清理 Docker containers
   - 如果建立臨時檔案，應在測試後清理

4. **效能考量**
   - Jenkins container 在 session 層級共用
   - 避免在測試中重複啟動 container

## 疑難排解

### 測試執行緩慢
- Jenkins container 首次啟動需要時間
- 考慮使用 session scope fixture 共用 container

### 認證失敗
- 確認使用正確的 fixture (run_jenkee vs run_jenkee_bad_auth)
- 檢查環境變數是否正確傳遞

### Localhost 約束錯誤
```
AssertionError: Security constraint: Jenkins must run on localhost
```
- 檢查 testcontainers 設定
- 確認 Docker 網路設定正確

## 參考資源

- pytest 文檔：https://docs.pytest.org/
- testcontainers-python：https://testcontainers-python.readthedocs.io/
- 3A Pattern：https://automationpanda.com/2020/07/07/arrange-act-assert-a-pattern-for-writing-good-tests/
