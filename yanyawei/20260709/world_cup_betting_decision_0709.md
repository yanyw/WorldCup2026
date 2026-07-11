# 2026-07-09 最新下注决策：未来 1 天

生成时间：2026-07-09 晚，北京时间。
执行范围：只预测未来约 24 小时内、Polymarket 已有可交易盘口的比赛。

## 1. 最终结论

| 比赛 | 最终动作 | 原因 |
|---|---|---|
| 法国 vs 摩洛哥 | 条件挂单：BUY 全场 Under 4.5 | 3pp 稳健边际阈值下，86¢ post-only maker 价满足要求；88¢ taker 不满足 |

最终入选项是 `France vs. Morocco: O/U 4.5 - Under`。这是两队合计总进球盘口：全场总进球 0、1、2、3、4 球则赢，5 球或更多则输。

`France O/U 1.5 - Under` 仍只作为观察项，不下注。这个盘口是法国单队总进球数，不是两队合计总进球。买 Under 的含义是：法国进 0 或 1 球则赢，法国进 2 球或更多则输。

执行纪律：

- 只挂 `全场 Under 4.5` 的 post-only maker 限价单，最高 86¢。
- 不吃 88¢ taker 卖单，因为加 taker fee 后有效成本约 88.32¢，taker 边际只有约 1.01pp，低于 3pp 阈值。
- 按 1000 USDC bankroll，建议下注 7.5 USDC；若 bankroll 不同，按 0.75% 等比例缩放。
- 未成交不追价。若盘口无法 post-only，取消而不是吃单。

## 2. 今日比赛范围

| 比赛 | Polymarket 开赛时间 UTC | 北京时间 | 是否纳入 |
|---|---:|---:|---|
| France vs Morocco | 2026-07-09 20:00 | 2026-07-10 04:00 | 纳入 |
| Spain vs Belgium | 2026-07-10 19:00 | 2026-07-11 03:00 | 超出严格未来 1 天，排除 |

角球盘口：已把角球纳入主流程搜索，但 Gamma/Polymarket 未找到 France-Morocco 可执行角球盘口，因此本版无角球下注。

## 3. 数据来源

- Polymarket 快照：`data/polymarket_snapshot_0709.json`，北京时间 2026-07-09 18:47:58。
- FIFA 技术报告/xG：`data/fifa_match_stats_0709.json`，用于 P3 当前赛事 xG 模型。
- 历史赛果：`data/raw/results.csv`，截止使用 2026-07-07 已完成比赛，不使用 2026-07-09 及之后未来数据。
- 外部同盘口/赔率证据：FanDuel Research 法国 vs 摩洛哥赛前赔率与阵容信息。
- Opta/The Analyst：仅作为同信息簇敏感性参考，不独立重复加权。
- Polymarket 费用：taker fee 按 `fee = feeRate * price * (1-price)` 每 share 计入；maker rebate 记为 0。

主要网页来源：

- FanDuel Research: https://www.fanduel.com/research/france-vs-morocco-prediction-picks-lineups-and-best-bets-world-cup-2026-quarterfinal
- Opta/The Analyst: https://theanalyst.com/articles/france-vs-morocco-prediction-world-cup-2026-match-preview
- Polymarket event: https://polymarket.com/sports/world-cup/fifwc-fra-mar-2026-07-09
- Polymarket fee docs: https://docs.polymarket.com/trading/fees

## 4. 内部模型中间结果

内部模型不读取 Polymarket、bookmaker odds 或 Opta 概率，只用历史赛果、Elo、FIFA xG 报告。

### P1：历史进球 Poisson

P1 是时间衰减、ridge 收缩的国家队攻防 Poisson 模型。

| 指标 | 法国 | 摩洛哥 |
|---|---:|---:|
| lambda | 1.0394 | 0.8339 |
| 1X2 | 法国 39.59% | 平 31.85%，摩洛哥 28.56% |

验证：2024-01-01 至 2026-07-09 前 holdout，P1 选择 half-life 1460 天、ridge 2.0，log loss 0.8645。

### P2：Elo 强弱校准

P2 只校准相对强弱和 1X2，不直接定价总进球、BTTS 或精确比分。

| 指标 | 法国 | 摩洛哥 |
|---|---:|---:|
| Elo | 1959.823 | 1893.911 |
| P2 1X2 | 法国 48.76% | 平 27.70%，摩洛哥 23.54% |

P2 使法国相对 P1 更强，但组合层只用 20% 权重调整进球比率，并保持总进球 lambda 不被 P2 单独拉动。

### P3：FIFA xG 当前赛事信号

| 队伍 | 样本 | xG for | xG against | xG for/场 | xG against/场 | 对手平均赛前 Elo |
|---|---:|---:|---:|---:|---:|---:|
| 法国 | 5 | 9.80 | 3.38 | 1.960 | 0.676 | 1729.41 |
| 摩洛哥 | 5 | 6.40 | 3.39 | 1.280 | 0.678 | 1753.89 |

P3 输出 lambda：法国 1.2441，摩洛哥 1.0306；因样本只有当前赛事 5 场，权重限制为 23.81%，上限 25%。

### 组合后独立概率

最终 lambda：法国 1.1018，摩洛哥 0.8672，总计 1.9689。

| 市场 | 内部中心概率 | p10 | p90 |
|---|---:|---:|---:|
| 法国胜 | 40.74% | 32.60% | 49.39% |
| 平局 | 30.84% | 26.83% | 35.62% |
| 摩洛哥胜 | 28.41% | 20.83% | 36.27% |
| BTTS No | 61.28% | 51.17% | 71.79% |
| 全场 Under 2.5 | 68.51% | 55.87% | 79.72% |
| 法国单队 Under 1.5 | 69.84% | 58.68% | 79.54% |

## 5. 外部基准与校正

FanDuel 1X2 devig 后：

| 结果 | 外部公平概率 |
|---|---:|
| 法国胜 | 60.65% |
| 平局 | 24.83% |
| 摩洛哥胜 | 14.52% |

Opta/The Analyst 给出法国 62.2%、平 22.1%、摩洛哥 15.7%，与 FanDuel 方向一致；最大差距约 2.73pp，因此它不构成新的独立强信号。

FanDuel 同盘口 devig 后：

| 盘口 | Over | Under |
|---|---:|---:|
| 全场 1.5 | 72.44% | 27.56% |
| 全场 2.5 | 47.64% | 52.36% |
| 全场 3.5 | 26.05% | 73.95% |
| BTTS | Yes 48.96% | No 51.04% |

关键影响：早先只用 1X2 拟合时，BTTS No 和全场 Under 会显得很有价值；加入同盘口 FanDuel totals/BTTS 后，这些边际消失，因此不下注。

## 6. 最终候选计算链条

### 入选：全场 Under 4.5

Polymarket 盘口：`France vs. Morocco: O/U 4.5`，选择 `Under`。
结算：两队合计总进球 0、1、2、3、4 球赢，5 球或更多输。

| 指标 | 数值 |
|---|---:|
| 内部模型中心概率 | 95.01% |
| 内部模型 p10 | 89.88% |
| 外部同盘口概率 | 92.60% |
| reliability | 10% |
| uncertainty buffer | 3pp |
| p_center | 92.84% |
| p_trade | 89.33% |
| Polymarket bid/ask | 87¢ / 88¢ |
| taker 有效成本 | 88.32¢ |
| taker 稳健边际 | +1.01pp |
| maker 最高价 | 86¢ |
| maker 价差边际 | p_trade - 86¢ = +3.33pp |
| 最终状态 | POST_ONLY_CONDITIONAL |

计算逻辑：

- 该盘口有 FanDuel 全场 3.5 同盘口，但没有 4.5 同盘口；4.5 外部概率来自 FanDuel 1X2 拟合比分分布，因此仍保守使用 10% reliability 和 3pp buffer。
- 内部模型认为总进球 lambda 为 1.9689，导致 Under 4.5 中心概率高达 95.01%。
- p_trade = 92.60% + 10% × (89.88% - 92.60%) - 3pp = 89.33%。
- 88¢ 吃单不够 3pp；86¢ maker 限价满足约 3.33pp，但必须 post-only，不能跨 spread 成为 taker。

风险说明：

- 这是高概率、低赔率盘口，对价格非常敏感；86¢ 和 88¢ 的差异足以改变结论。
- 若临场首发显示双方进攻配置明显强于预期，或盘口总进球价格快速下调，应取消挂单。
- 该下注是条件挂单，不是立即吃单。

### 观察项：法国单队 Under 1.5

Polymarket 盘口：`France vs. Morocco: France O/U 1.5`，选择 `Under`。
结算：法国进 0/1 球赢，法国进 2+ 球输。

| 指标 | 数值 |
|---|---:|
| 内部模型中心概率 | 69.84% |
| 内部模型 p10 | 58.68% |
| 外部簇概率 | 52.93% |
| reliability | 10% |
| uncertainty buffer | 3pp |
| p_center | 54.62% |
| p_trade | 50.51% |
| Polymarket bid/ask | 45¢ / 46¢ |
| taker 有效成本 | 46.75¢ |
| taker 稳健边际 | +3.76pp |
| 46¢ taker 是否达到 3pp | 是，但不入选 |
| 最终状态 | SKIP_NO_DIRECT_TEAM_TOTAL_BENCHMARK |

计算逻辑：

- 这个盘口没有找到同盘口 sportsbook team-total 赔率，所以外部簇概率来自 FanDuel 1X2 拟合出的比分分布，而不是直接盘口。
- 因此只给内部模型 10% reliability，并额外扣 3pp buffer。
- p_trade = 52.93% + 10% × (58.68% - 52.93%) - 3pp = 50.51%。
- 46¢ 吃单加 fee 后达到 3pp 阈值，但缺少同盘口 team-total 外部赔率，不能进入最终组合。

风险说明：

- 内部模型认为法国平均进球约 1.10，明显低于市场对法国优势的定价；这可能来自历史进球模型偏保守，也可能是市场高估法国。
- France team total 没有直接外部盘口校验，是足以否决下注的弱点。
- 审核后决定：不挂单，不下单，仅记录为观察项。

## 7. 放弃的主要候选

| 候选 | 放弃原因 |
|---|---|
| BTTS No | FanDuel BTTS devig 后 No 仅 51.04%；Polymarket No ask 51¢，加 fee 后无边际。 |
| 全场 Under 2.5 | FanDuel 全场 Under 2.5 devig 后 52.36%；Polymarket Under 53¢，加 fee 后无边际。 |
| 摩洛哥单队 Under 0.5 | 与法国 Under 1.5 同属低比分路径，高相关；且没有同盘口外部赔率，最终不叠加。 |
| 法国胜 / 摩洛哥胜 / 平局 | 外部市场与 Opta 明显更支持法国，内部模型分歧大但不足以逆市场下注。 |
| 法国单队 Under 1.5 | 虽然按 3pp 阈值边际足够，但没有同盘口 sportsbook team-total 外部赔率，标记为 `SKIP_NO_DIRECT_TEAM_TOTAL_BENCHMARK`。 |
| 角球盘口 | 未发现 Polymarket 可交易市场。 |

## 8. 执行清单

1. 当前结论：只挂全场 Under 4.5。
2. 最高买入价 86¢，必须 post-only maker。
3. 按 bankroll 0.75% 下单；1000 USDC bankroll 对应 7.5 USDC。
4. 不吃 88¢ 或更高价格。
5. 不下注 France team total Under 1.5，除非补到可靠的同盘口 team-total 外部赔率并重新计算。
6. BTTS、全场 1.5/2.5/3.5、1X2、让球和角球当前均无其他可执行下注。
