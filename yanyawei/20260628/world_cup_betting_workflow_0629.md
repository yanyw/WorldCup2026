# WC2026 0629 Polymarket 工作流与最终决策

- **覆盖窗口**: 北京时间 2026-06-29 至 2026-06-30
- **比赛数**: 4
- **Bankroll 假设**: 1000 USDC
- **结算口径**: 常规时间 90 分钟及补时，不含加时和点球
- **状态**: 最终复核版，可提交

## 1. 最终结论

当前盘口下不主动吃单，只保留一笔条件挂单：

| 北京时间截止 | 比赛 | 最终动作 | 价格条件 | 金额 |
|---|---|---|---:|---:|
| 6/29 02:40 | 南非 vs 加拿大 | 不下注 | 两队合计小于 2.5 球当前 57c | 0 |
| 6/30 00:40 | 巴西 vs 日本 | 不下注 | 无合格盘口 | 0 |
| 6/30 04:10 | 德国 vs 巴拉圭 | **BUY 两队合计进球小于 2.5** | **maker ≤44c** | **6 USDC** |
| 6/30 08:40 | 荷兰 vs 摩洛哥 | 不下注 | 摩洛哥胜当前 25c | 0 |

**盘口定义**：`BUY 两队合计进球小于 2.5` 是买入 Under 2.5 合约。德国和巴拉圭在常规时间 90 分钟及补时内的进球相加：合计 0、1、2 球时合约获胜，合计 3 球及以上时合约失败。例如 2:0 获胜，2:1 失败；加时赛和点球不计入。

该合约 44c 未成交就放弃，不改用 taker，不提高到 45c。本轮最大风险敞口为 6 USDC，占假设本金 0.6%。

## 2. 工作流

### 步骤一：固定市场与结算口径

先记录比赛时间、盘口、买价和市场规则。胜平负、让球和大小球必须针对同一 90 分钟事件，不能把晋级概率混入胜率。

本轮 Polymarket 快照：

| 比赛 | 胜平负 | ±1.5 | 两队合计进球大/小 2.5 |
|---|---|---|---|
| 南非-加拿大 | 16c / 26c / 59c | 南非 69c / 加拿大 32c | 44c / 57c |
| 巴西-日本 | 58c / 26c / 19c | 巴西 31c / 日本 70c | 49c / 52c |
| 德国-巴拉圭 | 74c / 19c / 9c | 德国 50c / 巴拉圭 51c | 57c / 44c |
| 荷兰-摩洛哥 | 44c / 31c / 25c | 荷兰 21c / 摩洛哥 80c | 44c / 57c |

### 步骤二：采集比赛数据

从 FIFA 官方赛后报告提取三场小组赛进球、xG、射门和射正；赛前 Elo/Kimi 报告仅作为长期先验；伤停和战术信息用于方向性修正，不直接拍概率。

| 球队 | 进球-失球 | xG-xGA | 射门-被射门 | 射正-被射正 |
|---|---:|---:|---:|---:|
| 南非 | 2-3 | 2.33-3.88 | 33-38 | 10-10 |
| 加拿大 | 8-3 | 7.00-2.64 | 59-16 | 22-7 |
| 巴西 | 7-1 | 6.19-2.28 | 40-35 | 18-11 |
| 日本 | 7-3 | 2.92-1.21 | 27-23 | 9-11 |
| 德国 | 10-4 | 7.38-2.96 | 53-24 | 22-7 |
| 巴拉圭 | 2-4 | 1.25-4.71 | 23-60 | 5-16 |
| 荷兰 | 10-4 | 4.67-2.40 | 40-35 | 20-14 |
| 摩洛哥 | 6-3 | 4.25-2.40 | 48-27 | 16-7 |

异常样本必须收缩：加拿大 6:0 卡塔尔发生在对方两张红牌后；德国 7:1 库拉索也不能按普通对手处理；日本 7 个进球来自 2.92 xG，终结效率需要向长期均值回归。

### 步骤三：建立统一比分分布

每场只估计一组主客队进球均值，再从同一个 Poisson 比分矩阵计算所有盘口：

`P(主队 i 球, 客队 j 球) = Poisson(i; λ主) × Poisson(j; λ客)`

| 比赛 | λ主-λ客 | 内部主/平/客 | 两队合计小于 2.5 球 |
|---|---:|---:|---:|
| 南非-加拿大 | 0.70-1.50 | 17.4% / 26.1% / 56.5% | 62.3% |
| 巴西-日本 | 1.65-0.90 | 55.1% / 24.5% / 20.5% | 53.1% |
| 德国-巴拉圭 | 2.05-0.55 | 72.7% / 18.5% / 8.8% | 51.8% |
| 荷兰-摩洛哥 | 1.25-1.10 | 39.7% / 27.9% / 32.4% | 58.3% |

一致性要求：每场胜平负之和为 100%，二元盘口两侧之和为 100%，让球和大小球都必须由同一比分矩阵积分得到。

### 步骤四：独立校验并处理模型分歧

点估计不能直接用于下注。优先采用独立强模型进行校验；若只有胜平负，则反推最接近该概率的 Poisson 进球均值，再检查大小球。

| 比赛 | 内部模型 | 独立校验 | 处理结果 |
|---|---|---|---|
| 南非-加拿大 | 两队合计小于 2.5 球 62.3% | Opta 1X2 反推约 52.3% | 初版小球被否决 |
| 巴西-日本 | 55.1% / 24.5% / 20.5% | Opta 57.3% / 23.0% / 19.7% | 与市场接近，跳过 |
| 德国-巴拉圭 | 两队合计小于 2.5 球 51.8% | 公开模型约 45%-48% | 保守概率下调至 48.5% |
| 荷兰-摩洛哥 | 摩洛哥胜 32.4% | Opta 摩洛哥胜 25.0% | 初版摩洛哥胜被否决 |

关键修正：内部模型不是多个“Agent”概率的简单平均。独立校验的作用是暴露参数偏差；出现明显冲突时使用保守端或放弃交易。

### 步骤五：计算可交易 Edge

maker Edge：

`edge_maker = 保守概率 - 限价`

taker 需加入 Polymarket 体育市场费用：

`fee/share = 0.03 × price × (1-price)`；`edge_taker = 保守概率 - price - fee/share`

筛选条件：maker 或费用后 taker Edge 至少 4 个百分点，且独立模型不能明确反对该方向。

| 市场 | 保守概率 | 买价 | Maker Edge | Taker Edge | 决策 |
|---|---:|---:|---:|---:|---|
| 南非-加拿大两队合计小于 2.5 球 | 约 56.3% | 57c | -0.7pp | -1.4pp | 不下注 |
| 巴西胜 | 约 56.4% | 58c | -1.6pp | -2.3pp | 不下注 |
| 德国-巴拉圭两队合计小于 2.5 球 | **约 48.5%** | **44c** | **+4.5pp** | +3.8pp | maker only |
| 摩洛哥胜 | 约 27.9% | 25c | +2.9pp | +2.3pp | 不下注 |

### 步骤六：一次 Kelly 与组合风控

只计算一次 Kelly，避免“Kelly 仓位被重复相乘”：

`full_kelly = (p - c) / (1 - c)`

德国-巴拉圭两队合计小于 2.5 球取 `p=0.485`、`c=0.44`，Full Kelly 约 8.0%；乘 0.20 fractional Kelly 后约 1.6%，再乘模型分歧折扣 0.4，得到约 0.64% bankroll，取整为 6 USDC。

风控规则：

- 单笔不超过 1.2% bankroll，单场不超过 1.5%，三日组合不超过 5%。
- 同场相关盘口只选一个，不把相关风险当成分散化。
- 盘口超过阈值不追价；没有成交也是正确执行。
- 临场首发改变核心进攻或防守强度时撤单并重算。

## 3. 最终执行清单

1. 德国-巴拉圭开赛前 60 分钟检查首发。
2. 盘口仍为两队合计进球小于 2.5，且价格不高于 44c 时，挂 maker 6 USDC。
3. 德国最强攻击组合全部首发，或巴拉圭关键中卫缺阵时撤单。
4. 订单未成交不切换 taker，45c 及以上不买。
5. 其余三场保持不下注，除非价格触发下表并重新运行模型。

| 市场 | 当前价 | 重新分析阈值 |
|---|---:|---:|
| 南非-加拿大两队合计小于 2.5 球 | 57c | ≤51c |
| 巴西胜 | 58c | ≤53c |
| 德国-巴拉圭两队合计小于 2.5 球 | 44c | ≤44c maker |
| 摩洛哥胜 | 25c | ≤23c |

## 4. 本轮经验与后续固化

本轮暴露的主要问题不是计算错误，而是初始参数对三场小样本过于敏感。最终工作流必须固定以下顺序：

`赛程 -> 市场快照 -> 官方比赛数据 -> 长期先验 -> 统一比分模型 -> 独立模型校验 -> 分歧折扣 -> 费用后 Edge -> 一次 Kelly -> 相关性限仓 -> 临场复核 -> 复盘评分`

下一版自动化范围：

- 每三日抓取未来三天赛程和 Gamma/CLOB 盘口，并保存时间戳。
- FIFA、WhoScored/SofaScore 抓取失败时使用明确的回退数据源。
- 用 Dixon-Coles、对手强度校正和 Monte Carlo 输出概率区间。
- 赛前 60 分钟自动二次运行，但只生成建议，不自动下单。
- 赛后记录成交价、closing line、Brier score、log-loss 和收益，避免只看盈亏评价模型。

本期结构化快照可运行 `python yanyawei/20260628/scripts/validate_snapshot.py` 复算内部概率，防止胜平负不等于 100% 或文档数值与模型漂移。

## 5. 来源

- [Polymarket World Cup 实时盘口](https://polymarket.com/sports/world-cup)
- [Polymarket sports fee formula](https://docs.polymarket.com/trading/fees)
- [Polymarket prices and order book](https://docs.polymarket.com/concepts/prices-orderbook)
- [FIFA Match Report Hub](https://www.fifatrainingcentre.com/en/fifa-world-cup-2026/match-report-hub.php)
- [Opta: South Africa vs Canada](https://theanalyst.com/articles/south-africa-vs-canada-prediction-world-cup-2026-match-preview)
- [Opta: Brazil vs Japan](https://theanalyst.com/articles/brazil-vs-japan-prediction-world-cup-2026-match-preview)
- [Opta: Netherlands vs Morocco](https://theanalyst.com/articles/netherlands-vs-morocco-prediction-world-cup-2026-match-preview)
- [Sports Mole: Germany vs Paraguay](https://www.sportsmole.co.uk/football/germany/world-cup-2026/preview/germany-vs-paraguay-prediction-team-news-lineups_600229.html)
- [xGscore: Germany vs Paraguay](https://xgscore.io/world-cup/germany-paraguay/preview)
- [The Playoffs: Germany vs Paraguay](https://theplayoffs.news/en/germany-vs-paraguay-prediction-and-odds-world-cup-29-06-2026/)
- [Football Bet Builder: Germany vs Paraguay](https://footballbetbuilder.co.uk/match/germany-vs-paraguay-2026-06-29)

> 本报告是概率研究记录，不保证收益。执行前必须复核价格、首发和市场规则。
