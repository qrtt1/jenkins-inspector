# domain

管理 Jenkins credentials domains，包含列出、建立、更新、刪除與查看詳細資訊。

## 用法

### List - 列出所有 domains

```bash
jenkee domain list
```

### Create - 建立新 domain

```bash
jenkee domain create <domain-name> [--description=<text>] [--yes-i-really-mean-it]
```

### Update - 更新 domain

```bash
jenkee domain update <domain-name> [--description=<text>] [--new-name=<name>] [--yes-i-really-mean-it]
```

### Delete - 刪除 domain

```bash
jenkee domain delete <domain-name> [--yes-i-really-mean-it] [--force]
```

若 domain 內有 credentials，必須加上 `--force` 才能刪除。

### Describe - 查看 domain 詳細資訊

```bash
jenkee domain describe <domain-name>
```

顯示 domain 的名稱、描述與所有 credentials 清單。

**危險操作：** 建立、更新與刪除 domain 都需要確認，請謹慎執行。

## 輸出範例

```
Available domains:
  (global)   Global credentials domain (3 credentials)
  staging    Staging environment credentials (1 credential)
  production Production environment credentials (0 credentials)

Total: 3 domains
```

## 使用範例

### 建立 domain

```bash
jenkee domain create staging --description="Staging credentials" --yes-i-really-mean-it
```

### 更新 domain 描述

```bash
jenkee domain update staging --description="Updated staging credentials" --yes-i-really-mean-it
```

### 重新命名 domain

```bash
jenkee domain update staging --new-name=staging-v2 --yes-i-really-mean-it
```

### 同時更新名稱和描述

```bash
jenkee domain update staging --new-name=staging-v2 --description="Version 2 staging credentials" --yes-i-really-mean-it
```

### 查看 domain 詳細資訊

```bash
jenkee domain describe staging
```

輸出範例：
```
=== Domain: staging ===
Name: staging
Description: Staging environment credentials
Credentials: 2

Credentials in this domain:
  - staging-db-password (StringCredentialsImpl)
  - staging-api-key (UsernamePasswordCredentialsImpl)
```

### 刪除空的 domain

```bash
jenkee domain delete old-staging --yes-i-really-mean-it
```

### 刪除有 credentials 的 domain

需要加上 `--force` 旗標：

```bash
jenkee domain delete staging --yes-i-really-mean-it --force
```

**警告：** 刪除 domain 時，該 domain 內的所有 credentials 也會一併刪除，請謹慎操作。
