# 数据来源、归属与发布注意事项

本文件记录第三方数据的来源和发布边界。它不是法律意见；公开仓库前应再次核对源站当时的条款。

| 数据 | 本地位置 | 来源 | 本地用途 | 发布建议 |
|---|---|---|---|---|
| 男子国际比赛结果 | `data/raw/international/results.csv` | `martj42/international_results` | 历史强度、Elo、Poisson/DC 训练 | 保留来源、下载时间和上游许可证说明 |
| FIFA 2026 比赛表现报告 | `data/raw/fifa_performance_reports_2026/*.pdf` | FIFA Training Centre | 2026 逐场球队和球员特征 | 完整私有仓库可用 LFS；公开再分发前核对 FIFA 条款，不能仅因可下载就假设可再许可 |
| StatsBomb 世界杯事件 | `data/raw/statsbomb_world_cups/` | StatsBomb Open Data | 历史逐分钟事件、战术阶段和球员先验 | 遵守 StatsBomb Open Data 条款并保留 attribution；manifest 已保存原始 URL 和哈希 |
| EA SPORTS FC 26 评分 | `data/curated/fc26_eng_arg_20260715.json` | EA 官方国家评分页面 | 纯游戏引擎属性 | 将结果视为来源数据的研究性摘录；公开前保留来源链接，不宣称拥有原始评分版权 |
| Polymarket 市场和订单簿 | `data/raw/polymarket/` | Polymarket 公共市场/API 响应 | 历史价格、深度、合约规则和套利审计 | 保留抓取 UTC 时间；不得包含账户凭据、私有仓位或钱包信息 |
| 手工比赛输入 | `data/inputs/` | 公开伤停、阵容、赔率和研究判断 | 冻结赛前可获得状态 | 在报告中保留截止时间和来源；观点与事实分开 |

## 已有 provenance 文件

- `data/raw/international/README.md`
- `data/raw/fifa_performance_reports_2026/manifest.json`
- `data/raw/statsbomb_world_cups/manifest.json`
- `data/raw/polymarket/LATEST*.txt`
- `docs/FILE_MANIFEST.csv`

## 代码许可证与数据许可证必须分开

即使未来为本项目代码选择 MIT、Apache-2.0 或其他许可证，该许可证也只覆盖你有权许可的项目代码和原创文档，不会自动覆盖 FIFA、StatsBomb、EA、Polymarket 或其他第三方内容。

在许可证尚未确定时，不创建含糊的 `LICENSE` 文件。公开仓库仍允许他人查看和 fork，但默认版权规则继续适用。

## 推荐发布模式

### 完整档案仓库（推荐先采用 Private）

- 包含全部代码、配置、预测、PDF 和压缩事件数据。
- PDF 与 `.gz` 使用 Git LFS。
- 最适合个人备份、复现和受控协作。

### 公开研究仓库

- 包含代码、配置、curated 特征、inputs、outputs、manifest 和下载脚本。
- 若第三方条款不明确，可不提交 FIFA PDF，只保留 `manifest.json`、原始 URL、SHA-256 和构建脚本。
- StatsBomb 数据按其开放数据条款处理并保留署名。
