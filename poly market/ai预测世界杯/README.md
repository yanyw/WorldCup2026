# FIFA World Cup 2026 × Polymarket 预测研究

这是一个从赛前概率模型逐步演化到真实比赛数据、逐分钟事件模拟、订单簿估值与套利审计的可复现研究项目。仓库保留了 2026-07-11 至 2026-07-19 的代码、冻结数据、模型配置、历史预测、复盘和最终两场比赛更新。

> 研究用途：项目不自动下单，不承诺盈利。严格套利、模型价值和方向预测在报告中被明确区分。

## 当前版本

- 最新配置：`config/world_cup_final_v8.json`
- 最新引擎：`src/simulate_remaining_matches_v6.py`（文件名沿用 v6，v8 行为由配置驱动）
- 最新结果：`outputs/world_cup_final_v8/`
- 模型演化历史：[`docs/PREDICTION_HISTORY.md`](docs/PREDICTION_HISTORY.md)
- 完整文件清单：[`docs/FILE_MANIFEST_SUMMARY.md`](docs/FILE_MANIFEST_SUMMARY.md)

最新 v8 使用 60 万条中央模拟路径、七组各 12 万条压力情景、本届世界杯逐场 FIFA 特征、历史国际比赛强度、StatsBomb 事件动态、预计阵容、伤病、裁判、天气、补时、加时和点球模块，并对 356 个决赛 Polymarket 合约逐一分类。

## 目录结构

```text
.
├── config/       # 版本化模型、比赛和风控配置
├── data/
│   ├── raw/      # 冻结原始快照；不得覆盖
│   ├── curated/  # 从原始数据构造的建模特征
│   ├── inputs/   # 阵容、赔率和比赛假设
│   └── processed/# 预留的中间处理层
├── docs/         # 研究方案、模型审计、路径与发布文档
├── outputs/      # 从早期模型到 v8 的全部预测与复盘
├── scripts/      # 仓库检查和文件清单工具
├── src/          # 数据采集、特征工程、模型、模拟和盘口估值
├── tests/        # 概率守恒、数据质量、路径和盘口覆盖测试
└── requirements.txt
```

根目录的 `walkforward_backtest_fast.py`、`club_results.csv`、`club_metrics.json`、`predictions_walkforward.csv` 和早期中文报告是项目最初阶段的历史工件，为保证研究链条完整而原位保留。

## 环境安装

建议 Python 3.11 或 3.12。不要在 README 或配置中写本机 Python 的绝对路径。

Windows PowerShell：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

macOS/Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 复现和检查

先检查仓库路径、配置指针和 GitHub 文件限制：

```powershell
python scripts/check_repository.py
python -m unittest discover -s tests -v
```

复现最终两场 v7：

```powershell
python src/simulate_remaining_matches_v6.py `
  --config config/remaining_matches_v7.json `
  --output-dir outputs/remaining_matches_v7_reproduced
```

Linux/macOS 将反引号续行改成反斜杠。为了保护历史结果，复现时应写入新目录，不要覆盖 `outputs/remaining_matches_v7/`。

其他主要入口：

```text
src/run_prediction_v2.py                 v2 国家队历史模型
src/validate_walkforward_v3.py           v3 Walk-Forward 验证
src/analyze_semifinals_v3.py             半决赛预测与全盘口估值
src/scan_orderbook_arbitrage.py          订单簿严格套利扫描
src/scan_dutch_book_lp.py                全状态线性规划扫描
src/simulate_match_game_engine.py        纯游戏属性逐分钟引擎
src/simulate_match_real_data_engine.py   真实数据逐分钟引擎
src/collect_remaining_markets.py         最新 Polymarket 订单簿采集
src/simulate_remaining_matches_v6.py     v6/v7 剩余比赛模拟与估值
```

## 路径约定

所有程序路径都必须相对仓库根目录解析。现有入口采用：

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
input_path = ROOT / "data" / "inputs" / "example.json"
```

配置文件和 `LATEST*.txt` 指针统一使用 `/` 分隔的仓库相对路径，例如：

```text
data/raw/polymarket/remaining_matches_normalized_20260718_161429Z.csv
```

详细规则、迁移方法和新增文件命名规范见 [`docs/PATH_MAINTENANCE.md`](docs/PATH_MAINTENANCE.md)。

## 数据与大文件

仓库约 220 MiB，其中 FIFA PDF 约 142 MiB，StatsBomb 压缩事件数据约 35 MiB。`.gitattributes` 已将 PDF、GZip 数据和 Polymarket 原始订单簿 JSON 配置为 Git LFS；首次添加文件前运行：

```powershell
git lfs install
```

数据来源、下载时间、SHA-256 和再分发注意事项见 [`docs/DATA_SOURCES_AND_LICENSES.md`](docs/DATA_SOURCES_AND_LICENSES.md)。公开仓库前，尤其要确认 FIFA 报告的源站条款。

## 发布到 GitHub

本目录目前只完成了 GitHub 就绪整理，没有擅自初始化远端、选择许可证或推送。完整的空仓库/已有仓库两套操作见 [`docs/GITHUB_PUBLISHING.md`](docs/GITHUB_PUBLISHING.md)。

## 免责声明与许可证状态

- 模型概率存在估计误差、阵容误差、数据修订和市场执行风险。
- 本项目不构成个性化投资或博彩建议。
- 项目代码尚未由所有者选择开源许可证；在添加 `LICENSE` 前，默认版权规则适用。
- 第三方数据仍受各自来源条款约束，项目许可证不会覆盖第三方数据。
