# 预测输出归档规则

`outputs/` 是需要长期跟踪的研究记录，不是缓存目录。已有版本应视为只读；重跑或新增信息集必须写到新目录，不能覆盖旧预测。

推荐的新运行结构：

```text
outputs/runs/YYYYMMDDTHHMMSSZ_<model>_<fixture>/
├── config_used.json
├── source_snapshot.txt
├── summary.json
├── recommendations.csv
└── report.md
```

每次运行至少保存：实际数据快照、UTC 截点、配置、随机种子、模拟次数、机器可读结果和人类可读报告。若涉及盘口，额外保存手续费、价差、流动性、最大入场价和执行状态。

版本关系见 [`docs/PREDICTION_HISTORY.md`](../docs/PREDICTION_HISTORY.md)。新增输出后运行全部测试，并用 `python scripts/build_repository_manifest.py` 更新文件清单。
