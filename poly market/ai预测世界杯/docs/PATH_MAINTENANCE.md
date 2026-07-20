# 路径维护与迁移规范

目标是让项目从当前含中文和空格的 Windows 路径迁移到任意 Windows、macOS、Linux 或 GitHub Actions 工作区后仍能运行。

## 1. 唯一根目录规则

入口脚本统一从自身位置推导仓库根目录：

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
```

随后所有文件均以 `ROOT / "data" / ...` 形式访问。禁止使用：

- 带盘符的个人目录绝对路径
- macOS 的个人主目录绝对路径
- Linux 的个人主目录绝对路径
- 依赖当前终端工作目录的裸相对路径，例如 `open("data.csv")`
- 为处理空格而手工拼接带引号的路径字符串

## 2. 配置文件路径

JSON 配置只存仓库相对路径，并统一用 `/`：

```json
{
  "data": {
    "lineups": "data/inputs/final_four_lineups_20260718.json"
  }
}
```

代码负责使用 `ROOT / value` 转换。不要把配置改成本机盘符路径。

## 3. Polymarket 最新指针

`data/raw/polymarket/LATEST*.txt` 每个文件只包含一行仓库相对路径。采集器写入时使用：

```python
str(csv_path.relative_to(ROOT)).replace("\\", "/")
```

移动整个仓库不需要修改指针；只要仓库内部目录结构不变即可。

## 4. 输出版本化

已有 `outputs/model_v2` 至 `outputs/remaining_matches_v7` 是历史记录，不应覆盖。新实验建议：

```text
outputs/runs/20260719T120000Z_v8_esp_arg/
├── config_used.json
├── source_snapshot.txt
├── summary.json
├── recommendations.csv
└── report.md
```

时间使用 UTC，格式为 `YYYYMMDDTHHMMSSZ`。代码、配置和输出版本分别记录，不用“final”“new”“latest2”一类不稳定名称。

## 5. 原始数据版本化

- `data/raw/`：只追加，绝不覆盖旧快照。
- `data/curated/`：由明确脚本生成，文件名包含赛事/样本/日期。
- `data/inputs/`：人工判断和阵容假设，必须带日期。
- `data/processed/`：可重建中间数据；若未来体积很大，可以不进 Git，但要保留构建脚本。

如果源站数据发生修订，保存新日期文件并更新 manifest；不要修改旧文件后沿用原名。

## 6. 重命名和移动文件

1. 先用 `rg "旧路径或文件名" .` 找到所有引用。
2. 使用 `git mv old new`，不要先在资源管理器中删除旧文件。
3. 同步更新配置、README、报告链接、测试和 `LATEST*.txt`。
4. 运行：

```powershell
python scripts/check_repository.py
python -m unittest discover -s tests -v
python scripts/build_repository_manifest.py
```

5. 用 `git diff --check` 检查空白和冲突标记。

## 7. 克隆到新位置后的检查

```powershell
git lfs pull
python scripts/check_repository.py
python -m unittest discover -s tests -v
```

项目目录可以改名，也可以放入不含中文的路径；不需要批量修改代码。若检查器报告 `local absolute path`，说明有新文件泄漏了开发者本机路径。

## 8. GitHub 链接和 Markdown

- 仓库内文档使用相对链接，如 `../outputs/model_v6/report.md`。
- 不把 Codex 生成的本机绝对可点击路径写入待发布文档。
- 外部来源使用完整 HTTPS URL。
- 文件名可保留中文，但脚本入口、配置键和机器生成目录优先使用 ASCII，减少跨工具兼容问题。
