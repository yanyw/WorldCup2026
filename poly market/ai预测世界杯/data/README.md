# 数据分层与路径规则

本目录按可追溯性分为三层：

- `raw/`：原始数据与带 UTC 时间戳的市场快照，只追加、不覆盖。
- `inputs/`：赛前人工冻结的阵容、伤停、事件 slug 和结构假设，文件名带日期。
- `curated/`：由明确脚本从原始数据构造的模型特征。

配置和指针只允许使用仓库相对路径及 `/` 分隔符，例如：

```text
data/raw/polymarket/remaining_matches_normalized_20260718_161429Z.csv
```

`raw/polymarket/LATEST*.txt` 是采集入口指针，不是历史版本标识。预测报告必须记录解析后的具体时间戳快照。第三方数据的来源、哈希、许可与公开发布边界见 [`docs/DATA_SOURCES_AND_LICENSES.md`](../docs/DATA_SOURCES_AND_LICENSES.md)。

新增或移动数据后运行：

```powershell
python scripts/check_repository.py
python scripts/build_repository_manifest.py
```

