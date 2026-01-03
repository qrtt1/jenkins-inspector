# domain

管理 Jenkins credentials domains，包含列出、建立與更新 domain。

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

建立與更新 domain 都是危險操作，請確認目標後再執行。

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
