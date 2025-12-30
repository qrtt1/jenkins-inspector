# Jenkins Inspector - 進階與危險命令

本文件包含需要謹慎使用的進階命令。這些命令可能會對 Jenkins 進行不可逆或影響重大的操作。

## 危險命令（需要使用者確認）

以下命令會對 Jenkins 進行不可逆或影響重大的操作，AI agent 在使用前必須向使用者確認：

| 命令 | 說明 | 範例 |
|------|------|------|
| `delete-job` ⚠️ | 刪除 job（不可逆） | `jenkee delete-job <job> [job ...]` |
| `disable-job` ⚠️ | 停用 job | `jenkee disable-job <job> [job ...]` |
| `enable-job` ⚠️ | 啟用 job | `jenkee enable-job <job> [job ...]` |
| `delete-builds` ⚠️ | 刪除 build 記錄（不可逆） | `jenkee delete-builds <job> <range>` |
| `groovy` ⚠️ | 執行 Groovy script（最高風險） | `jenkee groovy <script>` |

## 如何查看這些命令

這些危險命令預設不會顯示在 `jenkee help` 的命令列表中。

若要查看包含危險命令的完整命令列表，請使用：

```bash
jenkee help --ask-before-run-commands
```

## 使用注意事項

1. 執行前請確認操作的影響範圍
2. 建議在測試環境先行驗證
3. AI agent 使用這些命令前必須向使用者確認

## 詳細文件

各命令的詳細使用說明請參考 [docs/examples/](docs/examples/) 目錄下的對應文件。

## 主要功能

### Build 記錄管理
- 刪除舊的 build 記錄（不可逆，需確認）

### Job 管理
- 刪除 jobs（不可逆，需確認）
- 停用/啟用 jobs（需確認）

### 進階操作
- 執行 Groovy scripts（最高權限，需確認）
