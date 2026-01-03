# domain

列出 Jenkins credentials domains，包含描述與 credential 數量，也可建立新 domain。

## 用法

```bash
jenkee domain list
```

```bash
jenkee domain create <domain-name> [--description=<text>] [--yes-i-really-mean-it]
```

建立 domain 是危險操作，請確認目標後再執行。

## 輸出範例

```
Available domains:
  (global)   Global credentials domain (3 credentials)
  staging    Staging environment credentials (1 credential)
  production Production environment credentials (0 credentials)

Total: 3 domains
```

## 建立範例

```bash
jenkee domain create staging --description="Staging credentials" --yes-i-really-mean-it
```
