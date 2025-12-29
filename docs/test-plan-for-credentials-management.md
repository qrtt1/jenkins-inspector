# Test Plan: Credentials Management

## 測試情境

查詢與驗證 Jenkins credentials 的典型工作流程。

## 測試目標

驗證使用者可以：
1. 列出所有 credentials 的 metadata
2. 查看特定 credential 的詳細資訊
3. 驗證 credentials 設定正確
4. 確認不會洩漏 secret 內容

## 涵蓋的指令

| 指令 | 測試目的 | 安全性 |
|------|---------|--------|
| `list-credentials` | 列出所有 credentials metadata | Read-only, 不洩漏 secrets |
| `describe-credentials` | 查看特定 credential 詳細資訊 | Read-only, 不洩漏 secrets |

## 測試前置條件

- Jenkins server 運行中並已認證（`jenkee auth` 成功）
- Jenkins 中至少有：
  - 數個不同類型的 credentials（如：Username/Password, SSH Key, Secret Text 等）
  - 足夠權限查看 credentials metadata

## 測試步驟

### 1. 列出所有 Credentials

```bash
jenkee list-credentials
```

**預期結果**：
- Exit code: 0
- 顯示所有 credentials 的 metadata
- 包含 ID、Name、Type、Scope 等資訊
- 不洩漏 secret 內容（如 password, private key 等）

**驗證點**：
- [ ] 成功列出 credentials
- [ ] 輸出包含必要的 metadata
- [ ] 不包含敏感資訊（passwords, tokens, keys）
- [ ] 格式清晰易讀
- [ ] 包含所有可用的 credentials

### 2. 確認輸出不洩漏 Secrets

```bash
jenkee list-credentials | grep -iE "(password|token|secret|key)" | grep -v "ID\|Type\|Name"
```

**預期結果**：
- 應該只找到欄位名稱，不應找到實際的 secret 值
- 輸出應為空或只有 metadata 標題

**驗證點**：
- [ ] 沒有洩漏實際的 passwords
- [ ] 沒有洩漏實際的 tokens
- [ ] 沒有洩漏實際的 private keys
- [ ] 只顯示 metadata 資訊

### 3. 查看特定 Credential 的詳細資訊

```bash
jenkee describe-credentials <credential-id>
```

**預期結果**：
- Exit code: 0
- 顯示該 credential 的詳細資訊
- 包含 Type、Scope、Description、使用情況等
- 不洩漏 secret 內容

**驗證點**：
- [ ] 成功取得 credential 資訊
- [ ] 資訊詳細且完整
- [ ] 不洩漏敏感內容
- [ ] 格式清晰

### 4. 測試不同類型的 Credentials

針對不同類型的 credentials 進行測試：

#### Username/Password Credential

```bash
jenkee describe-credentials username-password-cred-id
```

**驗證點**：
- [ ] 顯示 username（可見）
- [ ] 不顯示 password（隱藏）
- [ ] 顯示 credential type

#### SSH Key Credential

```bash
jenkee describe-credentials ssh-key-cred-id
```

**驗證點**：
- [ ] 顯示 username（如果有）
- [ ] 不顯示 private key（隱藏）
- [ ] 顯示 credential type

#### Secret Text Credential

```bash
jenkee describe-credentials secret-text-cred-id
```

**驗證點**：
- [ ] 不顯示 secret text（隱藏）
- [ ] 顯示 description（如果有）
- [ ] 顯示 credential type

### 5. 列出 Credentials 並搭配篩選

```bash
jenkee list-credentials | grep "ssh"
```

**預期結果**：
- Exit code: 0
- 只顯示 SSH 相關的 credentials
- 篩選功能正常運作

**驗證點**：
- [ ] 篩選結果正確
- [ ] 輸出格式不受影響

### 6. 驗證 Credential 存在性

```bash
jenkee list-credentials | grep -q "expected-cred-id" && echo "Found" || echo "Not found"
```

**預期結果**：
- 可以用於腳本中驗證 credential 是否存在
- 返回正確的結果

**驗證點**：
- [ ] 可以正確判斷 credential 存在與否
- [ ] 適合用於自動化腳本

## 典型工作流程範例

### 場景 A：驗證環境 Credentials 設定

```bash
# 1. 列出所有 credentials
jenkee list-credentials

# 2. 檢查必要的 credentials 是否存在
required_creds=("github-token" "docker-hub" "aws-creds")

for cred in "${required_creds[@]}"; do
  if jenkee list-credentials | grep -q "$cred"; then
    echo "✓ $cred exists"
  else
    echo "✗ $cred missing"
  fi
done

# 3. 查看詳細資訊確認設定
for cred in "${required_creds[@]}"; do
  echo "=== $cred ==="
  jenkee describe-credentials "$cred"
done
```

### 場景 B：審計 Credentials 使用情況

```bash
# 1. 列出所有 credentials
jenkee list-credentials > all-creds.txt

# 2. 對每個 credential 查看詳細資訊
while read -r cred_id; do
  echo "Checking $cred_id..."
  jenkee describe-credentials "$cred_id"
done < all-creds.txt
```

### 場景 C：找出特定類型的 Credentials

```bash
# 列出所有 SSH key credentials
jenkee list-credentials | grep -i "ssh"

# 列出所有 username/password credentials
jenkee list-credentials | grep -i "username"
```

### 場景 D：比對不同環境的 Credentials

```bash
# 開發環境
JENKINS_URL=https://dev.jenkins.example.com jenkee list-credentials > dev-creds.txt

# 生產環境
JENKINS_URL=https://prod.jenkins.example.com jenkee list-credentials > prod-creds.txt

# 比較差異
diff dev-creds.txt prod-creds.txt
```

## 錯誤情境測試

### 查詢不存在的 Credential

```bash
jenkee describe-credentials non-existent-credential-id
```

**預期結果**：
- Exit code: 非 0
- 顯示 credential 不存在的錯誤訊息

**驗證點**：
- [ ] 錯誤被正確偵測
- [ ] 錯誤訊息清楚

### 無權限查看 Credentials

```bash
# 使用無權限的帳號（如果測試環境支援）
JENKINS_USER_ID=readonly_user jenkee list-credentials
```

**預期結果**：
- Exit code: 非 0（如果沒有權限）或 0（但回傳空清單）
- 適當的權限錯誤訊息或空結果

**驗證點**：
- [ ] 權限控制正常運作
- [ ] 錯誤訊息清楚（如果有錯誤）

## 安全性驗證

### 確認不洩漏 Secrets

對所有指令的輸出進行安全檢查：

```bash
# 檢查 list-credentials 輸出
jenkee list-credentials | grep -iE "(password=|token=|key=|secret=)" && echo "SECURITY ISSUE!" || echo "Safe"

# 檢查 describe-credentials 輸出
jenkee describe-credentials <cred-id> | grep -iE "(password=|token=|key=|secret=)" && echo "SECURITY ISSUE!" || echo "Safe"
```

**驗證點**：
- [ ] 沒有 `password=<value>` 格式的輸出
- [ ] 沒有 `token=<value>` 格式的輸出
- [ ] 沒有實際的 private key 內容
- [ ] 沒有實際的 secret text 內容

### 測試 Log 輸出安全性

```bash
# 將輸出導向檔案並檢查
jenkee list-credentials > creds-output.txt
jenkee describe-credentials <cred-id> >> creds-output.txt

# 檢查檔案中是否有敏感資訊
grep -iE "BEGIN (RSA|DSA|EC) PRIVATE KEY" creds-output.txt && echo "SECURITY ISSUE!" || echo "Safe"
```

**驗證點**：
- [ ] Log 檔案不包含敏感資訊
- [ ] 可以安全地分享輸出內容

## 測試完成標準

- [ ] 所有 2 個指令都執行成功
- [ ] 所有預期結果都符合
- [ ] 所有驗證點都通過
- [ ] 錯誤情境被正確處理
- [ ] 安全性驗證全部通過
- [ ] 沒有洩漏任何 secret 內容
- [ ] 輸出格式清晰易讀
- [ ] 可以用於自動化腳本

## 注意事項

- 這些指令都是 **read-only**，不會修改 credentials
- 設計上不應該顯示任何 secret 內容（password, token, private key 等）
- 如果發現有洩漏 secrets 的情況，應立即報告為 security issue
- Credential ID 通常可以公開，但 secret 內容必須保密
- 某些環境可能限制查看 credentials 的權限

## 相關文件

- [list-credentials 指令文件](examples/list-credentials.md)
- [describe-credentials 指令文件](examples/describe-credentials.md)
