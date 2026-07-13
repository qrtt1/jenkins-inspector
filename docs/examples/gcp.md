# gcp

管理 GCP service account credentials，採用 git-style subcommand 結構。

## 用法

```bash
jenkee gcp credential create <credential-id> <path-to-service-account.json>
jenkee gcp credential list
jenkee gcp credential describe <credential-id>
jenkee gcp credential update <credential-id> <path-to-service-account.json>
jenkee gcp credential delete <credential-id> [--yes-i-really-mean-it]
```

完整說明（前置需求、Jenkins plugin 依賴、在 job 中使用方式）請參考 [docs/GCP_CREDENTIALS.md](../GCP_CREDENTIALS.md)。
