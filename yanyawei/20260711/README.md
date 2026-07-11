# 20260711 决策运行总览

本目录保存2026-07-11对未来24小时世界杯盘口的完整、可复核运行。它继承0709的P1/P2/P3框架，重点升级概率融合、90分钟数据口径、动态不确定性、maker/taker裁决和独立审核。

## 最终决策

唯一正式方向：

```text
Norway vs England
全场90分钟两队合计进球 Under 2.5
POST-ONLY BUY @ 42.25c
不得改为42.50c taker
模型仓位约1.17 USDC / 1000 USDC本金
```

核心数字：`p_trade=44.0456%`，42.25c maker Edge为`+1.7956pp`，超过固定`1.5pp`门槛；42.50c taker计入费用后的Edge只有`+0.3237pp`，不合格。其余15个直接评估outcome全部不下注。

## 本轮决策逻辑改动

### 旧规则

```text
p_center = 外部概率 + 少量内部模型修正
p_trade  = min(较低外部概率, p_center)
           - 1.5pp来源缓冲
           - 0.5pp筛选缓冲
```

旧规则只能让内部模型否决交易，几乎不能正向贡献；逐outcome取较低来源还可能选中陈旧或异常报价，并与固定缓冲重复惩罚。

### 新规则

1X2：

```text
p_sportsbook = BetMGM与Oddschecker分别去水后的均值
p_external   = 75% * p_sportsbook + 25% * p_opta
p_center     = 75% * p_external + 25% * p_internal
```

名义中心权重为博彩赔率56.25%、Opta 18.75%、内部模型25%。三个1X2概率先组成和为100%的分布，再评估各Yes/No方向。

O/U 2.5没有Opta直接概率时：

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
  + 0.25pp数据质量惩罚
)

p_trade = p_center - u
```

内部模型现在允许双向修正，但内外分歧越大，不确定性扣减也越大。固定`1.5pp`是费用、滑点和上述不确定性之后的独立下注门槛，不再与固定2pp缓冲重复。

执行层进一步区分：

- taker：使用VWAP加单市场 `feeSchedule` 计算有效成本。
- maker：使用post-only限价和零maker费用；挂单未成交不算持仓。
- Kelly：taker必须使用费用后成本，不能用裸成交价高估仓位。

## 本轮关键返修

第一轮分析误读Oddschecker页面下方的旧静态正文，将Norway-England O/U记录为`-130/+114`。独立审核发现页面顶部实时市场区已更新为`-138/+122`。返修后，42.50c taker从合格变为不合格。

审核同时发现旧maker判断会在 `maker_max >= ask` 时遗漏合法挂单。修复为：

```python
maker_price = min(maker_max, floor_to_tick(ask - tick))
```

因此最终结论不是42.50c taker，也不是完全空仓，而是42.25c post-only maker挂单。第二轮独立审核复算后给出`ACCEPT`。

以后采集Oddschecker必须优先读取页面顶部实时市场区，并保存抓取时间；正文说明只能作背景，不能直接作为当前价格。

## 文件索引

- `world_cup_betting_decision_0711.md`：最终报告、下注链条和完整中间结果。
- `workflow_notes_0711.md`：相对0709的工作流升级与未完成项。
- `audit_rounds_0711.md`：两轮独立审核、返修和最终裁决。
- `data/polymarket_snapshot_0711.json`：冻结的Gamma/CLOB市场与订单簿。
- `data/external_evidence_0711.json`：BetMGM、Oddschecker、Opta和新闻证据。
- `data/model_results_0711.json`：P1/P2/P3及最终概率。
- `data/model_backtest_0711.json`：时间留出验证和限制。
- `data/extra_time_verification_0711.json`：加时比赛90分钟比分的第二来源核验。
- `data/candidate_evaluation_0711.json`：全部直接候选、费用、Edge和Kelly结果。
- `data/run_manifest_0711.json`：冻结时间、最终裁决和SHA256清单。
- `scripts/`：市场刷新、内部模型和候选估值脚本。
- `data/raw/`：本轮模型使用的原始比赛结果、射手和点球数据。

## 仍需继续验证

新权重和惩罚系数是结构化先验，不是已经从大样本学习出的最优参数。后续应通过严格时间切分的walk-forward，对Brier Score、Log Loss、校准曲线、CLV和实际ROI联合调参；maker成交概率也需要真实订单日志。未完成这些验证前，维持小仓位和临场重算。
