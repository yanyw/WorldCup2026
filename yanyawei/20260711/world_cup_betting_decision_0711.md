# 2026-07-11 最新下注决策：双向修正版

决策快照：2026-07-11 23:20:50，北京时间

目标比赛：未来24小时内两场世界杯四分之一决赛

固定门槛：费用、滑点和模型不确定性扣除后 `robust_edge >= 1.5pp`

合约口径：仅计算常规时间90分钟及伤停补时，不含加时赛和点球大战

## 1. 最终结论

当前只有一个价格上达到正式门槛的方向：

| 比赛 | 盘口 | 动作 | 价格条件 | 模型仓位 |
|---|---|---|---:|---:|
| Norway vs England | 全场两队合计进球 `Under 2.5` | `POST-ONLY BUY Under` | 42.25c挂单，不吃42.50c ask | 每1000 USDC本金约1.17 USDC |
| Argentina vs Switzerland | 全部直接1X2和O/U 2.5 | `NO BET` | 无 | 0 |

`Under 2.5`指两队在90分钟和伤停补时内合计进球为0、1或2球时盈利；合计3球及以上亏损。它不是挪威或英格兰任一队的单队进球盘口。

执行规则：当前42.50c taker在5%费率后的Edge只有0.32pp，不下注；只允许在42.25c挂post-only maker单。挂单未成交不算持仓，不得为了成交改成吃单。临场首发、外部赔率或费用结构变化时必须重算。

## 2. 新概率规则

1X2中心概率采用：

```text
p_sportsbook = BetMGM与Oddschecker分别去水后的均值
p_external   = 75% * p_sportsbook + 25% * p_opta
p_center     = 75% * p_external + 25% * p_internal
```

对应名义权重为博彩赔率56.25%、Opta 18.75%、内部模型25%。

O/U 2.5没有Opta直接概率，因此采用：

```text
p_external = p_sportsbook
p_center   = 75% * p_sportsbook + 25% * p_internal
```

动态不确定性：

```text
u = max(
  0.5pp,
  0.5 * 博彩来源分歧
  + 0.1 * |内部概率 - 外部概率|
  + 0.25pp 数据质量惩罚
)

p_trade = p_center - u
```

内部模型可以双向修正中心概率，但模型分歧同时提高不确定性。Polymarket价格不参与公平概率，只用于计算成交成本和Edge。

## 3. 正式下注的完整决策链

候选：`Norway vs England: O/U 2.5 - Under`。

### 3.1 内部模型

| 中间层 | Norway | England | 说明 |
|---|---:|---:|---|
| P1 lambda | 0.9006 | 1.6999 | 长期90分钟攻防Poisson |
| P1 1X2 | 19.80% | 56.25% | 平局23.95% |
| P2 Elo | 1808.5 | 1913.6 | P2 1X2为22.36% / 23.83% / 53.81% |
| P3 lambda | 1.3603 | 1.8325 | 当前赛事最少5场，权重23.81% |
| 最终lambda | 1.0120 | 1.7294 | 总lambda 2.7415 |

最终内部结果：Norway/Draw/England为22.05% / 23.74% / 54.21%；Over/Under 2.5为51.65% / 48.35%。

### 3.2 外部数据与双向融合

| 项目 | Under 2.5概率 |
|---|---:|
| BetMGM去水 | 45.3230% |
| Oddschecker实时区去水 | 43.7211% |
| 博彩共识 | 44.5221% |
| 内部模型 | 48.3523% |
| 内部权重 | 25% |
| `p_center` | 45.4796% |

本盘口没有Opta直接O/U概率，因此Opta没有被虚构映射到大小球。Opta的1X2预测只用于同场1X2：Norway/Draw/England为25.8% / 24.7% / 49.5%。

### 3.3 不确定性与保守概率

| 扣减项 | 数值 |
|---|---:|
| 博彩来源分歧 | 1.6020pp |
| 0.5倍来源分歧惩罚 | 0.8010pp |
| 内外模型分歧 | 3.8303pp |
| 0.1倍模型分歧惩罚 | 0.3830pp |
| 数据质量惩罚 | 0.2500pp |
| 最低不确定性 | 0.5000pp |
| 最终动态不确定性 `u` | 1.4340pp |
| 保守交易概率 `p_trade` | 44.0456% |

内部模型把中心概率相对博彩共识提高0.9576pp；动态不确定性再扣1.4340pp。Oddschecker实时区和BetMGM出现1.60pp分歧后，规则自动显著提高了风险扣减；这笔交易并没有直接把48.35%的内部概率当成真实概率下注。

### 3.4 成交成本、Edge与仓位

| 指标 | 数值 |
|---|---:|
| 最新best bid / ask | 42.25c / 42.50c |
| 7.5 USDC测试订单VWAP | 42.50c |
| 市场 `feeSchedule.rate` | 0.05 |
| 每股taker fee | 1.2219c |
| 每股有效成本 | 43.7219c |
| `p_trade` | 44.0456% |
| taker robust Edge | **+0.3237pp，SKIP** |
| 固定门槛 | +1.5000pp |
| post-only挂单价 | **42.25c** |
| maker robust Edge | **+1.7956pp，ACTIONABLE** |
| maker full Kelly | 3.1093% |
| 实际缩放 | 5% Kelly，再乘0.75相关性系数 |
| 每1000 USDC模型仓位 | **约1.17 USDC** |

maker Edge只比门槛高0.296pp，对一个tick和外部赔率更新非常敏感。42.25c是当前best bid，可以挂post-only；42.50c会立即跨到ask并产生taker费，不允许。挂单存在无法成交风险，不能把挂单写成已下注。

## 4. 其他直接候选

下表Edge均已计入当前taker费：

| 方向 | `p_trade` | ask | robust Edge | 结论 |
|---|---:|---:|---:|---|
| Switzerland 90分钟胜 | 16.97% | 16.25c | +0.04pp | SKIP |
| Argentina 90分钟不胜 | 43.05% | 42.25c | -0.42pp | SKIP |
| Argentina-Switzerland 非平局 | 73.39% | 73.25c | -0.84pp | SKIP |
| Argentina-Switzerland Over 2.5 | 41.25% | 41.25c | -1.22pp | SKIP |
| Norway-England 非平局 | 73.67% | 74.50c | -1.78pp | SKIP |
| England 90分钟胜 | 48.25% | 50.25c | -3.25pp | SKIP |
| Argentina 90分钟胜 | 54.88% | 58.00c | -4.33pp | SKIP |

每场三个1X2合约的Yes和No均已同时评估，不存在漏掉互补token的情况。1X2先构造和为100%的中心概率，再对每个交易方向施加保守下界。

## 5. 临场执行日程

| 北京时间 | 动作 |
|---|---|
| 当前 | Under 2.5只在42.25c挂post-only；不吃42.50c ask |
| 7月12日04:00，T-60 | 检查首发、Reece James/Declan Rice/Marc Guehi状态、天气、CLOB和费率 |
| 7月12日04:45，T-15 | 最终刷新；重新计算，不以本报告旧价格直接下单 |
| 7月12日08:00，T-60 | 刷新Argentina-Switzerland全部输入 |
| 7月12日08:45，T-15 | 最终刷新；当前结论仍为不下注，除非重算后超过1.5pp |

England三名此前有疑问的球员已恢复训练，但首发仍可能改变比赛节奏；该信息暂时通过不确定性处理，没有主观硬改lambda。Argentina-Switzerland方面，Manzambi确认缺席，但临场博彩赔率已经是主要信息锚，避免在外部概率之外重复加权。

## 6. 证据门槛与限制

本轮扫描40个Polymarket市场、80个outcome：16个直接1X2或直接O/U 2.5 outcome完成估值；其余64个因缺少直接基准或经过历史验证的盘口投影器而明确排除。两场事件均未发现可执行角球市场。

当前仍未完成嵌套walk-forward、盘口家族经验校准、相邻盘口投影回测、maker成交概率与CLV模型。动态权重和惩罚系数属于有明确结构的先验规则，并非已经从大样本中学习出的最优参数。因此仓位保持极小，且每次临场必须重算。

## 7. 主要来源

- Polymarket Norway-England: https://polymarket.com/sports/world-cup/fifwc-nor-eng-2026-07-11
- Polymarket Argentina-Switzerland: https://polymarket.com/sports/world-cup/fifwc-arg-che-2026-07-11
- Polymarket fees: https://docs.polymarket.com/trading/fees
- BetMGM Norway-England: https://sports.betmgm.com/en/blog/world-cup/england-vs-norway-prediction-odds-preview-world-cup-july-11-bm16/
- BetMGM Argentina-Switzerland: https://sports.betmgm.com/en/blog/world-cup/argentina-vs-switzerland-prediction-odds-preview-world-cup-july-11-bm16/
- Opta Norway-England: https://theanalyst.com/articles/norway-vs-england-prediction-world-cup-2026-match-preview
- Opta Argentina-Switzerland: https://theanalyst.com/articles/argentina-vs-switzerland-prediction-world-cup-2026-match-preview
- Sky Sports England team news: https://www.skysports.com/football/news/12016/13562422/world-cup-2026-englands-declan-rice-marc-guehi-and-reece-james-train-ahead-of-quarter-final-with-norway

本报告不保证盈利。边际很薄时，遵守价格上限和仓位纪律比“必须下一笔”更重要。
