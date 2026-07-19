# 西班牙 vs 阿根廷：世界杯决赛下注决策

**外部概率证据时间**：2026-07-19 19:47 北京时间

**Polymarket 最终快照**：2026-07-19 20:07:59 北京时间

**开赛时间**：2026-07-20 03:00 北京时间

**结算口径**：90 分钟加伤停补时，不含加时和点球
**固定门槛**：费用、VWAP 与不确定性后 `robust edge >= 1.5pp`

## 最终结论

**当前正式下注：0 笔，0 USDC。**

取消“内部/外部概率分歧惩罚”后，所有 8 个有直接机构基准的 Yes/No 方向都已重算。最接近的两个候选是：

| 优先级 | 合约 | 当前 bid / ask | `p_trade` | taker 有效成本 | robust edge | 决策 |
|---|---|---:|---:|---:|---:|---|
| 1 | 阿根廷 90 分钟胜 Yes | 26.50 / 26.75c | 27.017% | 27.730% | -0.713pp | 不下注 |
| 2 | 两队 90 分钟合计小 2.5 | 58.75 / 59.00c | 59.497% | 60.210% | -0.713pp | 不下注 |

“小 2.5”指两队在 90 分钟加伤停补时内的**合计进球数**为 0、1 或 2；总进球达到 3 或以上即输，不含加时赛进球。

即使暂时忽略 taker fee，这两个候选相对 ask 的边际也只有 +0.267pp 和 +0.497pp，仍未达到固定 1.5pp 门槛。因此空仓不是由费用或已删除的分歧惩罚单独造成。

## 内部模型

内部模型完全独立于 Polymarket、机构赔率和 Opta。

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

赛前新闻检查没有触发模型适用域否决：

- [Sports Mole](https://www.sportsmole.co.uk/football/spain/world-cup-2026/team-news/spain-vs-argentina-injury-suspension-list-predicted-xis_601309.html)：西班牙无确认缺阵，Pedro Porro 肌肉问题存疑；阿根廷无列明伤停。
- [AS](https://as.com/futbol/mundial/alineacion-posible-de-argentina-hoy-en-la-final-del-mundial-contra-espana-el-once-probable-de-scaloni-f202607-n/)：阿根廷预计让 De Paul 回归首发并使用四中场，但第四名中场仍不确定。
- [FIFA 决赛前瞻](https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/spain-v-argentina-live-stream-team-news-tickets-and-more)：预测西班牙使用 Porro，阿根廷由 Messi 和 Alvarez 搭档；均不是确认首发。
- [BetMGM 赛前背景](https://sports.betmgm.com/en/blog/world-cup/spain-vs-argentina-prediction-odds-preview-world-cup-july-19-bm16/)：阿根廷本届 19 个进球来自 14.6 xG，并提示炎热潮湿环境；这些只作风险检查，不临时转成方向系数。

## 全部直接候选

| 买入方向 | `p_internal` | `p_external` | `p_center` | 内外差异（仅诊断） | `u` | `p_trade` | ask | 费用后成本 | edge | maker 最高价 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 阿根廷胜 Yes | 31.621% | 26.469% | 27.757% | 5.152pp | 0.740pp | 27.017% | 26.75c | 27.730% | -0.713pp | 25.50c |
| 小 2.5 | 63.938% | 59.016% | 60.247% | 4.922pp | 0.750pp | 59.497% | 59.00c | 60.210% | -0.713pp | 57.75c |
| 平局 No | 70.465% | 68.958% | 69.335% | 1.507pp | 0.880pp | 68.455% | 68.50c | 69.579% | -1.124pp | 66.75c |
| 西班牙胜 No | 61.156% | 57.511% | 58.423% | 3.644pp | 0.640pp | 57.783% | 57.75c | 58.970% | -1.187pp | 56.25c |
| 西班牙胜 Yes | 38.844% | 42.489% | 41.577% | 3.644pp | 0.640pp | 40.938% | 42.50c | 43.722% | -2.784pp | 39.25c |
| 阿根廷胜 No | 68.379% | 73.531% | 72.243% | 5.152pp | 0.740pp | 71.503% | 73.50c | 74.474% | -2.971pp | 70.00c |
| 平局 Yes | 29.535% | 31.042% | 30.665% | 1.507pp | 0.880pp | 29.786% | 31.75c | 32.833% | -3.048pp | 28.25c |
| 大 2.5 | 36.062% | 40.984% | 39.753% | 4.922pp | 0.750pp | 39.003% | 41.25c | 42.462% | -3.459pp | 37.50c |

`u` 只含机构来源离散度和数据质量项。内外差异列不参与任何一项减法。

## 两个最接近候选的完整链条

### 阿根廷 90 分钟胜 Yes

```text
内部概率                       31.6209%
机构共识                       26.6256%
Opta                           26.0000%
外部中心 = 75%机构 + 25%Opta    26.4692%
p_center = 75%外部 + 25%内部    27.7572%
机构来源范围                    0.4800pp
0.5 * 来源范围                  0.2400pp
数据质量项                      0.5000pp
u                              0.7400pp
p_trade                        27.0171%
ask / 计划VWAP                  26.7500%
taker fee                       0.9797pp
有效成本                        27.7297%
robust edge                    -0.7126pp
```

内部模型比外部高 5.152pp，但该差异不再被惩罚。取消前它会额外扣 0.515pp；新规则已把 `p_trade` 从约 26.502% 提高到 27.017%，仍不足以支付成本并保留 1.5pp edge。

### 两队 90 分钟合计小 2.5

```text
内部概率                       63.9381%
机构去水                       59.0164%
p_center = 75%外部 + 25%内部    60.2468%
机构来源范围                    0.0000pp（仅一条完整直接报价）
基础 + totals数据质量项          0.7500pp
u                              0.7500pp
p_trade                        59.4968%
ask / 计划VWAP                  59.0000%
taker fee                       1.2095pp
有效成本                        60.2095%
robust edge                    -0.7127pp
```

取消前内外差异会再扣 0.492pp；新规则已提高 `p_trade`，但毛边际仍仅 0.497pp，不到 1.5pp。

## 其余盘口与覆盖

本轮抓取 20 个 Polymarket 市场、40 个 outcome。四个直接市场的本地快照同时保存结算描述、FIFA 结算来源、`condition_id`、`fees_enabled` 与 CLOB 费用详情。8 个 outcome 有同盘口直接机构证据并完成双向计算；其余 32 个均有明确否决原因：

- 8 个让球 outcome：`SKIP_NO_DIRECT_SPREAD_BENCHMARK`。
- 10 个相邻总进球 outcome：`SKIP_UNVALIDATED_ADJACENT_LINE_PROJECTION`。
- 2 个 BTTS outcome：`SKIP_NO_DIRECT_BTTS_BENCHMARK`。
- 12 个球队总进球 outcome：`SKIP_NO_DIRECT_TEAM_TOTAL_BENCHMARK`。

事件市场集中未发现可执行角球盘口。以上不是遗漏；它们缺少同口径直接基准或已回测的投影器，不能因为内部 Poisson 能算出数值就进入下注层。

## 条件观察与临场动作

条件观察价不是当前挂单建议：

| 合约 | 重算触发价 | 当前 bid / ask | 说明 |
|---|---:|---:|---|
| 阿根廷胜 Yes | 25.50c 或更低 | 26.50 / 26.75c | 触价后重新核对首发、Opta、机构赔率与 fee |
| 小 2.5 | 57.75c 或更低 | 58.75 / 59.00c | 触价后重新核对 totals、天气和首发 |

建议在开赛前 75 至 45 分钟、确认首发后重跑三段脚本。若数据不变且价格没有达到重算触发区间，继续空仓；不能为了“决赛必须下注”降低 1.5pp 门槛。

## 主要数据源

- [Polymarket 决赛市场](https://polymarket.com/sports/world-cup/fifwc-esp-arg-2026-07-19)
- [Polymarket 费用规则](https://docs.polymarket.com/trading/fees)
- [Polymarket CLOB 市场信息接口](https://docs.polymarket.com/api-reference/markets/get-clob-market-info)
- [BetMGM 实时常规时间 1X2](https://www.betmgm.com/en/sports/events/spain-argentina-2%3A7832367)
- [Oddschecker 实时 1X2 与 O/U 2.5](https://www.oddschecker.com/us/soccer/world-cup/spain-v-argentina)
- [Opta 决赛 90 分钟概率转述](https://www.clarosports.com/futbol/mundial-2026/pronosticos-final-mundial-espana-argentina/)
- [FIFA 双方赛事统计](https://www.fifa.com/en/articles/tournament-stats-how-spain-argentina-perform)
