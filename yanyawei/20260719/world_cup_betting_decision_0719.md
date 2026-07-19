# 西班牙 vs 阿根廷：世界杯决赛下注决策

**外部概率证据时间**：2026-07-19 19:47 北京时间

**Polymarket 最终快照**：2026-07-19 20:07:59 北京时间

**适用域修订时间**：2026-07-19 20:40 北京时间

**开赛时间**：2026-07-20 03:00 北京时间

**结算口径**：90 分钟加伤停补时，不含加时和点球

**模型适用域**：`PARTIAL_OOD_FINAL_STAGE`

**固定门槛**：费用、VWAP 与不确定性后 `robust edge >= 1.5pp`

## 最终结论

**当前正式下注：0 笔，0 USDC。**

取消“内部/外部概率分歧惩罚”后，进一步复核发现决赛不能与普通淘汰赛完全等同：球队优化的是最终捧杯概率，而合约只结算前 90 分钟；当前内部模型没有通过验证的决赛阶段、加时选择权或比分状态风险偏好变量。因此本场按 `PARTIAL_OOD_FINAL_STAGE` 处理：有直接同盘口外部证据的市场仍可定价，但 P1/P2/P3 只作诊断，执行层内部权重统一降为 0。

这项分类是在初版定价后由适用域质疑触发，属于透明记录的方法纠错，而不是事前预注册规则。它只能用于本场保守执行，不能用于宣称策略历史收益改善。未来必须在抓取当期盘口前完成赛事阶段分类。

8 个直接 Yes/No 方向全部重算后，最接近当前价格的候选是：

| 优先级 | 合约 | 当前 bid / ask | `p_trade` | taker 有效成本 | robust edge | 决策 |
|---|---|---:|---:|---:|---:|---|
| 1 | 90 分钟不是平局 No | 68.25 / 68.50c | 68.078% | 69.579% | -1.501pp | 不下注 |
| 2 | 阿根廷 90 分钟胜 No | 73.25 / 73.50c | 72.791% | 74.474% | -1.683pp | 不下注 |
| U2.5 专项 | 两队 90 分钟合计小 2.5 | 58.75 / 59.00c | 58.266% | 60.210% | -1.943pp | 不下注 |

“小 2.5”指两队在 90 分钟加伤停补时内的**合计进球数**为 0、1 或 2；总进球达到 3 或以上即输，不含加时赛进球。

U2.5 的机构去水概率为 59.016%，扣除 0.75pp 数据质量项后，正式 `p_trade` 为 58.266%。它既低于 59.00c ask，也低于 60.210% 的费用后成本。空仓不是由已删除的分歧惩罚造成，而是外部直接概率本身不足以支持当前价格。

## 内部模型

内部模型完全独立于 Polymarket、机构赔率和 Opta。下列结果在本场保留用于研究和偏差诊断，但因决赛部分 OOD，**不进入正式 `p_center`**。

| 模型层 | 西班牙 | 阿根廷 | 中间解释 |
|---|---:|---:|---|
| P1 lambda | 1.0603 | 0.9603 | 时间衰减攻防 Poisson |
| P1 1X2 | 37.303% | 32.090% | 平局 30.608% |
| P2 Elo | 2008.950 | 1984.765 | 最近 Elo 轨迹 +36.999 / +12.649 |
| P2 1X2 | 43.453% | 31.372% | 平局 25.175%；只调整强弱比例 |
| P3 lambda | 1.3985 | 1.2092 | FIFA xG；最小样本 4，权重 20% |
| P1/P3 融合后 | 1.1279 | 1.0101 | P3 受 25% 上限约束 |
| 最终 lambda | 1.1400 | 0.9980 | P2 调整比例，总 lambda 保持 2.1380 |

最终内部概率：

| 市场 | 西班牙胜 | 平局 | 阿根廷胜 | 大 2.5 | 小 2.5 |
|---|---:|---:|---:|---:|---:|
| `p_internal` | 38.844% | 29.535% | 31.621% | 36.062% | 63.938% |

最可能比分依次为 1-0（13.439%）、1-1（13.413%）、0-0（11.789%）、0-1（11.766%）。这些是独立 Poisson 的点估计，不含红牌、首发和赛中状态相关性。

P3 的 FIFA xG 明细只更新到 7 月 7 日。半决赛真实赛果已进入 P1/P2，但没有把二手报道中的零散 xG 强行拼入 P3。

## 外部概率与新闻

1X2 使用两家完整三向报价各自去水后平均：

| 来源 | 原始常规时间报价 | 去水后：西班牙 / 平 / 阿根廷 |
|---|---|---:|
| BetMGM 实时事件页 | 2.25 / 3.00 / 3.50 | 41.791% / 31.343% / 26.866% |
| Oddschecker 实时页头 | +132 / +200 / +265 | 41.512% / 32.103% / 26.386% |
| 机构共识 | - | 41.651% / 31.723% / 26.626% |

Opta 的 90 分钟概率为西班牙 45.0%、平局 29.0%、阿根廷 26.0%。按固定规则：

```text
p_external(1X2) = 75% * 机构共识 + 25% * Opta
                 = 42.489% / 31.042% / 26.469%
```

Oddschecker 的 2.5 球完整报价为大球 +134、小球 -160，去水后为大 40.984%、小 59.016%。本轮没有同口径直接 Opta 总进球概率，因此不把 Opta 1X2 映射到大小球。

赛前新闻没有触发硬性 `SKIP`，但赛事结构本身触发 `PARTIAL_OOD_FINAL_STAGE`：

- [Sports Mole](https://www.sportsmole.co.uk/football/spain/world-cup-2026/team-news/spain-vs-argentina-injury-suspension-list-predicted-xis_601309.html)：西班牙无确认缺阵，Pedro Porro 肌肉问题存疑；阿根廷无列明伤停。
- [AS](https://as.com/futbol/mundial/alineacion-posible-de-argentina-hoy-en-la-final-del-mundial-contra-espana-el-once-probable-de-scaloni-f202607-n/)：阿根廷预计让 De Paul 回归首发并使用四中场，但第四名中场仍不确定。
- [FIFA 决赛前瞻](https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/spain-v-argentina-live-stream-team-news-tickets-and-more)：预测西班牙使用 Porro，阿根廷由 Messi 和 Alvarez 搭档；均不是确认首发。
- [BetMGM 赛前背景](https://sports.betmgm.com/en/blog/world-cup/spain-vs-argentina-prediction-odds-preview-world-cup-july-19-bm16/)：阿根廷本届 19 个进球来自 14.6 xG，并提示炎热潮湿环境；这些只作风险检查，不临时转成方向系数。

决赛与季军赛的处理不同：季军赛的动机、轮换和开放程度使通用模型与执行层均失效，属于硬 OOD；决赛仍有最强阵容和直接同盘口机构/Opta证据，因此外部层可用，但未校准的内部模型不能方向性修正执行概率。

## 全部直接候选

| 买入方向 | `p_internal`（诊断） | `p_external` | `p_center` | 内部权重 | `u` | `p_trade` | ask | 费用后成本 | edge | maker 最高价 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 平局 No | 70.465% | 68.958% | 68.958% | 0% | 0.880pp | 68.078% | 68.50c | 69.579% | -1.501pp | 66.50c |
| 阿根廷胜 No | 68.379% | 73.531% | 73.531% | 0% | 0.740pp | 72.791% | 73.50c | 74.474% | -1.683pp | 71.25c |
| 西班牙胜 Yes | 38.844% | 42.489% | 42.489% | 0% | 0.640pp | 41.849% | 42.50c | 43.722% | -1.873pp | 40.25c |
| 小 2.5 | 63.938% | 59.016% | 59.016% | 0% | 0.750pp | 58.266% | 59.00c | 60.210% | -1.943pp | 56.75c |
| 阿根廷胜 Yes | 31.621% | 26.469% | 26.469% | 0% | 0.740pp | 25.729% | 26.75c | 27.730% | -2.001pp | 24.00c |
| 西班牙胜 No | 61.156% | 57.511% | 57.511% | 0% | 0.640pp | 56.872% | 57.75c | 58.970% | -2.098pp | 55.25c |
| 大 2.5 | 36.062% | 40.984% | 40.984% | 0% | 0.750pp | 40.234% | 41.25c | 42.462% | -2.228pp | 38.50c |
| 平局 Yes | 29.535% | 31.042% | 31.042% | 0% | 0.880pp | 30.163% | 31.75c | 32.833% | -2.671pp | 28.50c |

`u` 只含机构来源离散度和数据质量项。内部模型与外部概率的差异仍记录在 JSON 中，但不参与减法，也不参与本场 `p_center`。

## 关键候选的完整链条

### 90 分钟不是平局 No

```text
内部概率（仅诊断）              70.4651%
外部中心                       68.9578%
决赛 OOD 内部权重               0%
p_center                       68.9578%
0.5 * 机构来源范围              0.3796pp
数据质量项                      0.5000pp
u                              0.8796pp
p_trade                        68.0782%
ask / 计划VWAP                  68.5000%
taker fee                       1.0789pp
有效成本                        69.5789%
robust edge                    -1.5007pp
```

这是当前最接近价格的方向，但 `p_trade` 已低于 ask，费用后更不存在正 edge。66.50c 是零手续费 post-only maker 的最高限价，不是 taker 触发价，也不是当前下单建议。

### 两队 90 分钟合计小 2.5

```text
内部概率（仅诊断）              63.9381%
机构去水                       59.0164%
决赛 OOD 内部权重               0%
p_center                       59.0164%
机构来源范围                    0.0000pp（仅一条完整直接报价）
基础 + totals数据质量项          0.7500pp
u                              0.7500pp
p_trade                        58.2664%
ask / 计划VWAP                  59.0000%
taker fee                       1.2095pp
有效成本                        60.2095%
robust edge                    -1.9431pp
```

内部模型给出 63.938%，但这主要来自没有决赛阶段变量的 Poisson 结构，不能用于把机构概率向小球方向抬高。正式判断只使用机构去水概率；内外差异没有被“惩罚”，而是内部模型因部分 OOD 被整体移出执行融合。结论仍为不买 U2.5。

## 其余盘口与覆盖

本轮抓取 20 个 Polymarket 市场、40 个 outcome。四个直接市场的本地快照同时保存结算描述、FIFA 结算来源、`condition_id`、`fees_enabled` 与 CLOB 费用详情。8 个 outcome 有同盘口直接机构证据并完成双向计算；其余 32 个均有明确否决原因：

- 8 个让球 outcome：`SKIP_NO_DIRECT_SPREAD_BENCHMARK`。
- 10 个相邻总进球 outcome：`SKIP_UNVALIDATED_ADJACENT_LINE_PROJECTION`。
- 2 个 BTTS outcome：`SKIP_NO_DIRECT_BTTS_BENCHMARK`。
- 12 个球队总进球 outcome：`SKIP_NO_DIRECT_TEAM_TOTAL_BENCHMARK`。

事件市场集中未发现可执行角球盘口。以上不是遗漏；它们缺少同口径直接基准或已回测的投影器，不能因为内部 Poisson 能算出数值就进入下注层。

## 条件观察与临场动作

条件价格不是当前挂单建议。maker 最高价假设 post-only 零手续费；taker 最高价按单档成交并计入当前非线性费用，两者不能混用：

| 合约 | post-only maker 最高价 | taker 最高单档价 | 当前 bid / ask | 说明 |
|---|---:|---:|---:|---|
| 平局 No | 66.50c | 65.25c | 68.25 / 68.50c | 触价后重新核对首发、Opta、机构赔率与 fee |
| 小 2.5 | 56.75c | 55.50c | 58.75 / 59.00c | 触价后重新核对 totals、天气和首发 |
| 阿根廷胜 Yes | 24.00c | 23.25c | 26.50 / 26.75c | 触价后重新核对首发、Opta、机构赔率与 fee |

建议在开赛前 75 至 45 分钟、确认首发后重跑三段脚本。若数据不变且价格没有达到重算触发区间，继续空仓；不能为了“决赛必须下注”降低 1.5pp 门槛。

## 主要数据源

- [Polymarket 决赛市场](https://polymarket.com/sports/world-cup/fifwc-esp-arg-2026-07-19)
- [Polymarket 费用规则](https://docs.polymarket.com/trading/fees)
- [Polymarket CLOB 市场信息接口](https://docs.polymarket.com/api-reference/markets/get-clob-market-info)
- [BetMGM 实时常规时间 1X2](https://www.betmgm.com/en/sports/events/spain-argentina-2%3A7832367)
- [Oddschecker 实时 1X2 与 O/U 2.5](https://www.oddschecker.com/us/soccer/world-cup/spain-v-argentina)
- [Opta 决赛 90 分钟概率转述](https://www.clarosports.com/futbol/mundial-2026/pronosticos-final-mundial-espana-argentina/)
- [FIFA 双方赛事统计](https://www.fifa.com/en/articles/tournament-stats-how-spain-argentina-perform)
