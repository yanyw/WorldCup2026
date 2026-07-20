# 新预测运行目录

新的预测和实验按以下格式建立子目录：

```text
YYYYMMDDTHHMMSSZ_<model>_<fixture>/
```

每个运行至少保存 `config_used.json`、`source_snapshot.txt`、机器可读结果和 Markdown 报告。已有 `model_v*`、`remaining_matches_v*` 等历史目录保持只读。
