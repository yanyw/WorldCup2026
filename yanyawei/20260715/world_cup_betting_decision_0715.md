# 2026-07-15 最新世界杯下注决策

决策快照：2026-07-15 21:29:26，北京时间<br>
目标比赛：England vs Argentina，世界杯半决赛<br>
开球：2026-07-16 03:00，北京时间<br>
合约口径：仅常规时间 90 分钟及伤停补时，不含加时赛和点球大战<br>
固定门槛：费用、滑点和不确定性之后 `robust_edge >= 1.5pp`

## 1. 最终结论

**当前价正式空仓，不提交任何 taker 或能排到当前 best bid 的 maker 订单。**

| 候选 | 当前 bid / ask | `p_trade` | taker 有效成本 | taker edge | 结论 |
|---|---:|---:|---:|---:|---|
| Draw `No`，即 90 分钟内任一队获胜 | 66.50c / 66.75c | 67.64% | 67.86c | -0.22pp | 不下注 |
| Argentina 90 分钟胜 `Yes` | 31.50c / 31.75c | 32.33% | 32.83c | -0.50pp | 不下注 |
| England 90 分钟胜 `No` | 64.25c / 64.50c | 64.17% | 65.64c | -1.48pp | 不下注 |
| 两队合计进球 `Under 2.5` | 60.50c / 60.75c | 59.02% | 61.94c | -2.92pp | 不下注 |

`Under 2.5` 指两队在 90 分钟和伤停补时内合计进 0、1 或 2 球时盈利；合计 3 球及以上亏损。它不是任一球队的单队进球盘口。

本场没有发现 Polymarket 可执行角球市场，因此角球没有进入正式候选。其余让球、相邻总进球、BTTS 和球队总进球盘口缺少直接外部基准或经过历史验证的投影器，按证据门槛剔除，不能用同一个 Poisson 输出无限扩展下注数量。

## 2. 内部模型完整链条

本轮继续使用 P1/P2/P3，而不是另建不可比较的新模型。

| 模型层 | England | Argentina | 作用 |
|---|---:|---:|---|
| P1 进球 `lambda` | 0.8686 | 1.0634 | 四年半衰期、ridge=2 的长期攻防 Poisson |
| P1 1X2 | 29.19% | 39.52% | 平局 31.29% |
| P2 Elo | 1908.8 | 1971.4 | 仅校验相对强弱，不改变总进球 |
| P2 1X2 | 28.63% | 46.34% | 平局 25.03% |
| P3 当前赛事 xG `lambda` | 1.4109 | 1.4825 | 最少 4 场，融合权重 20%，上限 25% |
| 最终 `lambda` | 0.9623 | 1.1619 | 总 `lambda=2.1242` |

最终内部概率：

| 市场 | England | Draw | Argentina |
|---|---:|---:|---:|
| 90 分钟 1X2 | 30.13% | 29.55% | 40.31% |

| 总进球 | Over 2.5 | Under 2.5 |
|---|---:|---:|
| 内部 Poisson | 35.69% | 64.31% |

最可能比分依次为 `0-1` 13.89%、`1-1` 13.36%、`0-0` 11.95%、`1-0` 11.50%、`0-2` 8.07%。

### 90 分钟数据清洗

两队四分之一决赛都进入加时：Norway-England 和 Argentina-Switzerland 的训练比分均按 `1-1` 记录，而不是数据库中的 `1-2`、`3-1` 赛后总比分。两份 FIFA 报告没有可验证的 90 分钟 xG 切片，因此整场 120 分钟汇总 xG 从 P3 剔除，不做线性缩放。

本轮 49,506 条原始记录清洗后保留 48,665 条；841 条加时或点球口径不清记录剔除，6 场关键加时比赛由独立来源确认 90 分钟比分。P1 单一时间 holdout 的 1X2 log loss 为 0.8568、Brier 为 0.5008、RPS 为 0.1671；嵌套 walk-forward 尚未完成，因此这些只是研究诊断，不是假装精确的生产置信区间。

## 3. 外部概率层

### 3.1 1X2

BetMGM 最新公开投注更新为 `England +160 / Draw +185 / Argentina +200`；Oddschecker 实时 header 为 `+175 / +190 / +200`。分别去水后：

| 来源 | England | Draw | Argentina |
|---|---:|---:|---:|
| BetMGM 去水 | 35.98% | 32.83% | 31.19% |
| Oddschecker 去水 | 34.90% | 33.10% | 32.00% |
| 博彩共识，二者均值 | 35.44% | 32.96% | 31.59% |
| Opta 90 分钟预测 | 37.30% | 30.70% | 32.00% |
| 外部融合 | 35.91% | 32.40% | 31.69% |

规则为：

```text
p_external = 75% * sportsbook_consensus + 25% * Opta
p_center   = 75% * p_external + 25% * p_internal
```

名义中心权重是博彩 56.25%、Opta 18.75%、内部模型 25%。融合后的 `p_center` 为 England 34.47%、Draw 31.69%、Argentina 33.85%。内部模型可以双向修正，但其与外部层的分歧也会提高不确定性，不能只拿有利方向。

### 3.2 O/U 2.5

原始 BetMGM 7 月 12 日文章的 `-105/-120` 已废弃。本轮采用较新的 BetMGM 盘口移动记录 `Over +130 / Under -165`；Oddschecker 当前为 `Over +148 / Under -175`。

| 来源 | Over 2.5 | Under 2.5 |
|---|---:|---:|
| BetMGM 去水 | 41.12% | 58.88% |
| Oddschecker 去水 | 38.79% | 61.21% |
| 博彩共识 | 39.95% | 60.05% |
| 内部模型 | 35.69% | 64.31% |
| `p_center` | 38.89% | 61.11% |

Opta 没有给出直接 O/U 2.5 概率，因此没有把 Opta 1X2 虚构映射为大小球概率。BetMGM 与 Oddschecker 不是同一分钟快照，totals 额外保留 0.25pp 数据质量惩罚。

## 4. 不确定性、费用与 Edge

```text
u = max(
  0.5pp,
  0.5 * 博彩来源分歧
  + 0.1 * |内部概率 - 外部概率|
  + 数据质量惩罚
)

p_trade = p_center - u
```

每个方向都在一致的基础分布上构造后再扣 `u`。Yes/No 并不是各自独立估计；例如 Draw `No` 的中心概率严格等于 `1 - p_center(Draw)`，随后才做方向性保守扣减。

Polymarket 体育市场当前 `feeSchedule.rate=0.05`，taker 每股费用为：

```text
fee_per_share = 0.05 * price * (1 - price)
effective_taker_cost = VWAP + fee_per_share
```

maker 为零费用，但必须 post-only，且价格不能跨过 ask。固定 `1.5pp` 是在上述费用和不确定性之后的独立门槛。

### 最接近候选：Argentina 90 分钟胜

```text
博彩共识                 31.5914%
Opta                     32.0000%
p_external               31.6936%
内部模型                 40.3148%
p_center                 33.8489%
来源分歧惩罚              0.4046pp
内外模型分歧惩罚          0.8621pp
数据质量惩罚              0.2500pp
u                         1.5167pp
p_trade                  32.3322%
ask                       31.7500c
taker fee                  1.0835c/股
有效成本                  32.8335c
taker robust edge         -0.5013pp
```

不计费用和不确定性时，Argentina 看起来有约 2.10pp 原始优势；但这正是容易误下单的地方。动态不确定性和体育 taker fee 合计消耗约 2.60pp，最终没有优势。

## 5. 条件价格，不是当前下注

以下价格是在输入概率不变时满足 1.5pp 的最高 post-only 价格。它们均低于当前 best bid，不能写成当前可执行下注；只有市场跌到相应价格并重新刷新首发、外部盘和模型后才能考虑。

| 条件方向 | 最高 maker 价 | 当前 best bid | 当前状态 |
|---|---:|---:|---|
| Draw `No` | 66.00c | 66.50c | 等待，不挂追价单 |
| Argentina 胜 `Yes` | 30.75c | 31.50c | 等待 |
| England 胜 `No` | 62.50c | 64.25c | 等待 |
| Under 2.5 | 57.50c | 60.50c | 等待 |

不建议现在把低于 best bid 的条件单长期留在盘口里，因为首发和最终外部赔率出来后，概率本身会变化。更安全的做法是设价格提醒并在 T-60、T-15 重算。

## 6. 临场日程

| 北京时间 | 操作 |
|---|---|
| 当前 | 不下单；记录空仓和条件价 |
| 7 月 16 日 01:45，T-75 | 核对正式首发、Messi/Saka/Reece James、Rice 恢复情况和任何临时伤停 |
| 02:00，T-60 | 刷新 BetMGM/Oddschecker、Opta 页面和 Polymarket CLOB，重新去水并运行全部 8 个直接 outcome |
| 02:45，T-15 | 最终刷新；只执行重新计算后 `robust_edge >= 1.5pp` 的方向 |
| 02:50 后 | 不因“必须有下注”而追价；没有边际继续空仓 |

当前确认的 England 缴员信息是 Declan Rice 可以首发，Jarell Quansah 停赛，Jordan Henderson 受伤缺阵。新闻只通过市场与不确定性层进入，除非有可量化且未被赔率吸收的新信息，否则不主观硬改 `lambda`。

## 7. 审核结论与限制

第一轮审核复算确认费用、Yes/No 互补和空仓方向正确，但提出把 BetMGM 平局 `+185` 改为 `+188`。分析端拒绝：`+188` 是 VegasInsider 记录的周一 21:00 较早盘口，而 `+185` 来自 BetMGM 7 月 14 日更晚的公开投注更新。拒绝意见有明确时间戳和来源依据，并非为了维持原结论。

仍未完成的事项包括嵌套 walk-forward、各盘口族的经验校准、角球专门模型、maker 成交概率和真实 CLV。当前仓位因此保持为零；这比为增加下注数量而放松证据门槛更符合既定工作流。

## 8. 主要来源

- [Polymarket England vs Argentina](https://polymarket.com/sports/world-cup/fifwc-eng-arg-2026-07-15)
- [Polymarket fees](https://docs.polymarket.com/trading/fees)
- [Opta England vs Argentina prediction](https://theanalyst.com/articles/england-vs-argentina-prediction-world-cup-2026-match-preview)
- [BetMGM public betting update](https://sports.betmgm.com/en/blog/world-cup/world-cup-public-betting-data-consensus-predictions-bm16/)
- [BetMGM totals line movement via VegasInsider](https://www.vegasinsider.com/soccer/england-argentina-odds-world-cup-2026/)
- [Oddschecker live match page](https://www.oddschecker.com/us/soccer/world-cup/england-v-argentina)
- [England official team update](https://www.englandfootball.com/articles/2026/Jul/14/thomas-tuchel-argentina-world-cup-press-conference-20261507)
- [AP Norway-England extra-time report](https://apnews.com/article/f246f138c3a8563cb5a0e3f4037e930a)
- [FIFA Argentina-Switzerland report](https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/argentina-switzerland-match-report-highlights)

本报告不保证盈利。执行时必须使用最新价格重新计算，不能把研究概率当作确定事实。
