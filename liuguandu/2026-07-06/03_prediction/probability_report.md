# 概率预测报告

- 报告日期: 2026-07-06
- 比赛日期字段: 2026-07-05
- 模型模式: baseline_fallback / structural_edge
- 治理规则: 无证据，不编故事；有结构化盘口 edge 时允许小仓限价，而不是全部跳过。
- 已应用教训: 胜率与让分穿盘概率分开；保留弱势方进球路径；缺少确认首发/硬技术数据时限制仓位而不是压平所有预测。

## 覆盖审计
- 已解析请求数: 6
- 缺失请求数: 0
- 已选盘口类型数量: {"match_1x2": 6, "first_team_to_score": 6, "spread_lines": 20, "totals_lines": 30, "btts": 6, "team_total_lines": 28}

## 巴西 vs 挪威 [fifwc-bra-nor-2026-07-05]

### 共享信息源
1. Brazil vs. Norway in World Cup round of 16: Time, date, preview - USA Today | USA Today | https://news.google.com/rss/articles/CBMiuwFBVV95cUxQNmV4RHBsT2NwTi1nR2dkbUFxck81VXVIR0owaTNJT0JVWVRBd3pUSU5FVXg2RzBfaUxtY0x1TzIxT2NDXzZDRG12dU1NTTBFZmY5d3A3MGhoaUgzeGpiOVdoYVdMUTZNaUx5dzlVY1dNcHZJTUUza3p0V3RoM3NkdVM4ZUZaR3FzcjRQQ3N4emZYYmNWSl9zZnp2ekVFd1NmRjN4Y1ppXzFCc0xRQjQ0WF9mTTZoamI1cWpr?oc=5
2. 👀 Easy prey? Norway are a tough nut for Brazil: head-to-head - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMiigFBVV95cUxOV3BiZDE0ekRvRFdQWUw1eXZMOHBLcTgyZUpJay0ycHJjdUM1OGhWb1NYME9FTk11WXpPVldJdFkzdmxhT0ZBclR1NTZnREZZandzbkFGcWhkTUxacGYwNmNSWFZKNkF5UTFZTVpNanZwRVNjRU1USDZST01pR3dlaV9ZN3Q5Sl9kZkE?oc=5
3. Who Is Norway's Next World Cup Opponent? - FOX Sports | FOX Sports | https://news.google.com/rss/articles/CBMigAFBVV95cUxPWU5mcGJrcm5qeG5mLWd4NC1DeXZBT2djdnlZYVdHVjBrN2padnowWEhLOHpheGt2OUZxdnVKXzhiZ205RnZxZ0RSZkVEX3lfencwYUlfYWhLRXloT0s3TUZlVWFiRll2b1dwZEZPUC1pdTRUbl9fQ20yMXI0em4yYtIBgAFBVV95cUxPWlNNZnRBQmtWYTFCRlExUHlOMDlTTndIamh0SVBqbTFwQVlVeWFKNlo2S1ozVUlHS2dDaDF2RFc0NHlYQ2RnNG5obmpNenU3cmgyc3g5YnhDRW1kaWdnaEJ6aWZwaFBlWHAtX3VteHFoeS14bWpKcGx4eWJZLXBRYw?oc=5
4. Brazil is playing Norway in the World Cup at MetLife. Get discounted tickets - New York Post | New York Post | https://news.google.com/rss/articles/CBMiqAFBVV95cUxORXpBcWFNNDhPNlFnZHNra2VHUENmZHpTc2NRMFJfT1g4Zm9tcDZfeDBxbzhTR2FaTHM4QkxRYWVVNU1mOFU2c1Jta3E5Uld2aE1RQURQeUZlY21wdzNnaEJyY0l2RUswbDFiak1paU1XRTdDRzI4eVpLNEJyVVY3ejFidmU4Y3hCTGRkTXRsREhUM1pESTZIaXNMV0R5eEFZb1NZNW4tMzk?oc=5
5. Brazil vs Norway: Date, kickoff time and venue for 2026 World Cup Round of 16 clash - World Soccer Talk | World Soccer Talk | https://news.google.com/rss/articles/CBMivAFBVV95cUxPWjhZSDJvTjNYMU94TnlkT0F5YlBzUzMtRHJGc0x3dnhNTjdTYkdCVEJPeGNPRTNJVXZ4Nm96ZFBnYlhQclZIRVhvdnREYnh4bEJvTzFXSlNUUThjMjlSeDBoeWdFNlZEUU15ZlZ1NXFtOUR0Z2lzX0tqaXVacmhzTnY2UDFXOHFBM3hYa0tuUzRHN0RhRnhhY0FqYjdPdXF1U24wZ05WS0tDQVZnV1RveE53UXU1QkkzUzVjMdIBwAFBVV95cUxOWWdlWUxYaGJIVXdzeEstOXdlYW5NZWJGM3RCNldxSlVzMjhlSWtadHZuc3A4TGVCUWltWVdjSXdWRVRaa2ZKank5ZUFWSjB1WERYQ3huc1lpSE9BVDhDaGtwZDlaOE52dk1DcGRtak9BMFRvNWlfU0dZS2hwdERvaVlPOWY4ZDV4dVpweTk0NmlYZy1Gbzdqb2FkcVpXUWxucUZNWlJMMF9Vb0JPVDZjRGxDMmMydlpGbUY0WWZUUGM?oc=5

### 比赛层面解读
- 证据链：
  1. Polymarket 胜平负价格定义球队强弱和打平风险的基础先验。
  2. 让分、总进球、双方均进球、首支进球队伍和球队进球数盘口用于内部一致性校验。
  3. 已抓取的公开预览只能提供弱定性支持，因此置信度不会升到高档。
- 推理链：
  1. 对热门方，除非让分价格本身确认大比分分布，否则穿盘概率相对胜率打折。
  2. 不能因为一方更强就买双方均进球否或球队小球；必须明确否定弱势方进球路径。
  3. 4 个百分点以上结构化 edge 进入策略候选；5.0 个百分点以上进入小仓限价优先订单。
- 反证：信息源集合缺少确认首发、射门质量、压迫强度或 xG 拆分等硬数据。
- 失效观察：临场轮换、天气、战术变化，或价格移动超过 4 个百分点。

### 胜平负
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-bra-nor-2026-07-05-bra | 巴西 会在 2026-07-05 获胜吗？ | 是 | 51.5% | 51.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-draw | 巴西 vs 挪威 会打平吗？ | 是 | 26.5% | 26.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-nor | 挪威 会在 2026-07-05 获胜吗？ | 是 | 22.5% | 22.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |

### 让分盘
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-bra-nor-2026-07-05-spread-home-1pt5 | 让分：巴西 (-1.5) | 巴西 | 27.5% | 27.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-spread-away-1pt5 | 让分：挪威 (-1.5) | 挪威 | 8.5% | 8.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-spread-home-2pt5 | 让分：巴西 (-2.5) | 巴西 | 12.5% | 8.0% | -4.5% | 偏低+ | 仅观察 | baseline edge 需要首发确认 |
| fifwc-bra-nor-2026-07-05-spread-away-2pt5 | 让分：挪威 (-2.5) | 挪威 | 2.4% | 4.3% | +2.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-spread-home-3pt5 | 让分：巴西 (-3.5) | 巴西 | 4.5% | 0.1% | -4.4% | 偏低+ | 仅观察 | baseline edge 需要首发确认 |
| fifwc-bra-nor-2026-07-05-spread-away-3pt5 | 让分：挪威 (-3.5) | 挪威 | 0.5% | 2.6% | +2.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-bra-nor-2026-07-05-spread-home-4pt5 | 让分：巴西 (-4.5) | 巴西 | 4.6% | 0.1% | -4.5% | 低 | 仅观察 | baseline edge 需要首发确认 |
| fifwc-bra-nor-2026-07-05-spread-away-4pt5 | 让分：挪威 (-4.5) | 挪威 | 0.2% | 2.2% | +2.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-bra-nor-2026-07-05-spread-home-5pt5 | 让分：巴西 (-5.5) | 巴西 | 0.8% | 0.1% | -0.7% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-bra-nor-2026-07-05-spread-away-5pt5 | 让分：挪威 (-5.5) | 挪威 | 0.2% | 2.2% | +2.0% | 偏低+ | 跳过 | 价格过于极端 |

### 总进球盘
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-bra-nor-2026-07-05-total-0pt5 | 巴西 vs 挪威：总进球大小 0.5 | 大 | 94.0% | 96.0% | +2.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-total-1pt5 | 巴西 vs 挪威：总进球大小 1.5 | 大 | 78.5% | 80.5% | +2.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-total-2pt5 | 巴西 vs 挪威：总进球大小 2.5 | 大 | 54.5% | 58.5% | +4.0% | 中低 | 仅观察 | baseline edge 需要首发确认 |
| fifwc-bra-nor-2026-07-05-total-3pt5 | 巴西 vs 挪威：总进球大小 3.5 | 大 | 32.5% | 36.5% | +4.0% | 中低 | 仅观察 | baseline edge 需要首发确认 |
| fifwc-bra-nor-2026-07-05-total-4pt5 | 巴西 vs 挪威：总进球大小 4.5 | 大 | 16.5% | 16.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-total-5pt5 | 巴西 vs 挪威：总进球大小 5.5 | 大 | 6.5% | 2.0% | -4.5% | 中低 | 仅观察 | baseline edge 需要首发确认 |
| fifwc-bra-nor-2026-07-05-total-6pt5 | 巴西 vs 挪威：总进球大小 6.5 | 大 | 3.0% | 0.1% | -2.9% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-total-7pt5 | 巴西 vs 挪威：总进球大小 7.5 | 大 | 1.1% | 0.1% | -1.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-bra-nor-2026-07-05-total-8pt5 | 巴西 vs 挪威：总进球大小 8.5 | 大 | 0.5% | 0.1% | -0.4% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-bra-nor-2026-07-05-first-half-total-0pt5 | 巴西 vs 挪威：上半场 大小 0.5 | 大 | 72.0% | 74.0% | +2.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-first-half-total-1pt5 | 巴西 vs 挪威：上半场 大小 1.5 | 大 | 35.5% | 37.5% | +2.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-first-half-total-2pt5 | 巴西 vs 挪威：上半场 大小 2.5 | 大 | 12.5% | 16.5% | +4.0% | 偏低+ | 仅观察 | baseline edge 需要首发确认 |
| fifwc-bra-nor-2026-07-05-second-half-total-0pt5 | 巴西 vs 挪威：下半场 大小 0.5 | 大 | 78.0% | 80.0% | +2.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-second-half-total-1pt5 | 巴西 vs 挪威：下半场 大小 1.5 | 大 | 48.0% | 50.0% | +2.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-second-half-total-2pt5 | 巴西 vs 挪威：下半场 大小 2.5 | 大 | 21.0% | 25.0% | +4.0% | 偏低+ | 仅观察 | baseline edge 需要首发确认 |

### 双方均进球
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-bra-nor-2026-07-05-btts | 巴西 vs 挪威: 双方均进球 | 是 | 57.5% | 62.5% | +5.0% | 中低 | 小仓限价 | 结构化 edge，小仓限价 |
| fifwc-bra-nor-2026-07-05-btts-first-half | 巴西 vs 挪威: 上半场双方均进球 | 是 | 22.5% | 22.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-btts-second-half | 巴西 vs 挪威: 下半场双方均进球 | 是 | 30.5% | 30.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 首支进球队伍
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-bra-nor-2026-07-05-first-to-score-neither | 巴西 vs 挪威: 无球队先进球? | 是 | 5.5% | 2.0% | -3.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-first-to-score-home | 巴西 会先于 挪威 进球吗？ | 是 | 58.0% | 58.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-first-to-score-away | 挪威 会先于 巴西 进球吗？ | 是 | 37.0% | 34.5% | -2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 球队进球数
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-bra-nor-2026-07-05-team-total-home-0pt5 | 巴西 vs 挪威：巴西 大小 0.5 | 大 | 83.0% | 83.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-team-total-home-1pt5 | 巴西 vs 挪威：巴西 大小 1.5 | 大 | 52.5% | 52.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-team-total-home-2pt5 | 巴西 vs 挪威：巴西 大小 2.5 | 大 | 24.0% | 20.5% | -3.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-team-total-away-0pt5 | 巴西 vs 挪威：挪威 大小 0.5 | 大 | 68.0% | 68.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-team-total-away-1pt5 | 巴西 vs 挪威：挪威 大小 1.5 | 大 | 30.5% | 30.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-team-total-away-2pt5 | 巴西 vs 挪威：挪威 大小 2.5 | 大 | 10.0% | 6.5% | -3.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-first-half-team-total-home-0pt5 | 巴西 vs 挪威：巴西 上半场 大小 0.5 | 大 | 55.0% | 57.5% | +2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-first-half-team-total-home-1pt5 | 巴西 vs 挪威：巴西 上半场 大小 1.5 | 大 | 18.5% | 18.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-first-half-team-total-away-0pt5 | 巴西 vs 挪威：挪威 上半场 大小 0.5 | 大 | 38.0% | 42.0% | +4.0% | 偏低+ | 仅观察 | baseline edge 需要首发确认 |
| fifwc-bra-nor-2026-07-05-first-half-team-total-away-1pt5 | 巴西 vs 挪威：挪威 上半场 大小 1.5 | 大 | 9.5% | 9.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-second-half-team-total-home-0pt5 | 巴西 vs 挪威：巴西 下半场 大小 0.5 | 大 | 62.0% | 64.5% | +2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-bra-nor-2026-07-05-second-half-team-total-home-1pt5 | 巴西 vs 挪威：巴西 下半场 大小 1.5 | 大 | 48.0% | 48.0% | +0.0% | 低 | 跳过 | 流动性不足 |
| fifwc-bra-nor-2026-07-05-second-half-team-total-away-0pt5 | 巴西 vs 挪威：挪威 下半场 大小 0.5 | 大 | 46.5% | 50.5% | +4.0% | 低 | 仅观察 | baseline edge 需要首发确认 |
| fifwc-bra-nor-2026-07-05-second-half-team-total-away-1pt5 | 巴西 vs 挪威：挪威 下半场 大小 1.5 | 大 | 46.5% | 43.5% | -3.0% | 低 | 跳过 | 流动性不足 |

## 墨西哥 vs 英格兰 [fifwc-mex-eng-2026-07-05]

### 共享信息源
1. FIFA World Cup 2026: How to watch Mexico vs England in the round of 16 – head-to-head, full schedule - olympics.com | olympics.com | https://news.google.com/rss/articles/CBMiuwFBVV95cUxNTGt6TmladXBQeXh3eDJSZVdmODRmOWprSFlVSDNONmtOM1R5Q29NVElkN3VaWVFGOEZVaFlJZlA1cklGNktZVjU0ZGItbkFQbW1ITmhoc1BpV0Y1OTFmRnk3WUlITDd2SGU0NlpGakNLbEY4bkJkQWV3YUZwdGNoTmNLU29kcjBlM0dETURBT3l2NTZhYVM4QUo3REk0VEJmNjVaY0d6T003c3FYZENLdXVRTHh3aUdtRllN?oc=5
2. Mexico vs. England (Jul 5, 2026) Live Score - ESPN | ESPN | https://news.google.com/rss/articles/CBMickFVX3lxTE5XbEhNUVZxdGNvQ3NFX0dpeTBCMkIxWHIxZlNTTTJmOXNENnowS3pNcVU0SzZmRHlLUENvUlZfY1llVHdwU2dXOGxzdkN2a2FkM0pqTEJBSFBLRkd5bkF5d1JIMlZMNzVKY1FzQkRWSG00Zw?oc=5
3. England vs. Mexico: Everything To Know About The World Cup Round Of 16 Game - FOX Sports | FOX Sports | https://news.google.com/rss/articles/CBMipwFBVV95cUxQUmNYLTFnOXQ5NzFSRFRWd1hmR3ZhOHNmZm9qVWVfY0M5U3BXcXBWeFBVYi1pdkhRSkVDQ19RLXZvVTlabjVPcXdzdU9XWkRHSWpOZE4xcUY5U0pvVFNhNUxTYkJyZ1p1OWk4cUt0X3VBZEtUMEt4c2d4ZXVBNVFJU05wcVVub1E4bkVxVVFjTHdheHAwdlY1dUZJekFzUmNHNHpzUUFVZ9IBpwFBVV95cUxNSngxWjFxOC1NRU9Fby1zQ3VlbG55bllaUDB6WXBhMXYzVkNRN3N6LUVpaFlLcGRkYU9zZUtBck9fenJ2Mm1zQnMtWkcxQ29udU01QWoyQ3BvRHBYbkRYeE02VjhLQ0drSXNna2hPQzdieVdsM0U1Sm83YzZOVlNna09OMlJrY1VaazMySGVSUWhHTlQ0SEhyQ2ZkdnViejhGZjFFR1h4VQ?oc=5
4. When does Mexico play again in the World Cup? How to watch vs. England - El Paso Times | El Paso Times | https://news.google.com/rss/articles/CBMi0AFBVV95cUxNY0ZJUGVrSmF2SXExTkVXS3BRdkpyVTFfTmhMVnViNVE4MzlLY1Y2a1ZlT0tMZS02bm95OXF0cmZOeHVJSDZxcDRiU0hsUUI1MkRwY0JCcUk4Q2FURmJDbzB5ZzV0WlZETnl4NmpLMjBOc1doWnFzRlJoRE1WOWRVdE9FWHlERC1IWDB4Q0N2RXBBTUk3cXVUTUR3TU9pdHExT0lpRnZQaEtzNFVuNS1HYnIzaTBhUU1tQXB5ckxJMWNKY0l4SUk0V2d6ZzF6WmJw?oc=5
5. How to buy Mexico vs. England round of 16 World Cup soccer tickets - USA Today | USA Today | https://news.google.com/rss/articles/CBMi4gFBVV95cUxOYk4zRUtrM1Ixd2FaT25MT1JlRUFyeS1jQzE1dUJkUnJTX0N4ZnR6bk1UczF0WUtVb0k1a1VHNi0zbEhCU0VHdk1fdFNJRTJ5Yk1CWEZoaGxScjgxUkZHQWJncU5DWGtCbkZVQzlMZmlmRjZhWlYxMFY1Mk1teDRNRVdxNmFrWmZ4em5ZcFRSWFRaVmRJLU5LRnJhdXFvaG1YaHRUMDJIRk55WWZ2QkRZRVo3M3RNLXQxOFI2a19UaFBhM2p0WEZjM2haRWd0VTRydXpJQ283TVB0ZHYtelBid0lR?oc=5

### 比赛层面解读
- 证据链：
  1. Polymarket 胜平负价格定义球队强弱和打平风险的基础先验。
  2. 让分、总进球、双方均进球、首支进球队伍和球队进球数盘口用于内部一致性校验。
  3. 已抓取的公开预览只能提供弱定性支持，因此置信度不会升到高档。
- 推理链：
  1. 对热门方，除非让分价格本身确认大比分分布，否则穿盘概率相对胜率打折。
  2. 不能因为一方更强就买双方均进球否或球队小球；必须明确否定弱势方进球路径。
  3. 4 个百分点以上结构化 edge 进入策略候选；5.0 个百分点以上进入小仓限价优先订单。
- 反证：信息源集合缺少确认首发、射门质量、压迫强度或 xG 拆分等硬数据。
- 失效观察：临场轮换、天气、战术变化，或价格移动超过 4 个百分点。

### 胜平负
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-mex-eng-2026-07-05-mex | 墨西哥 会在 2026-07-05 获胜吗？ | 是 | 30.5% | 30.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-eng | 英格兰 会在 2026-07-05 获胜吗？ | 是 | 39.5% | 39.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-draw | 墨西哥 vs 英格兰 会打平吗？ | 是 | 29.5% | 34.0% | +4.5% | 中低 | 仅观察 | baseline edge 需要首发确认 |

### 让分盘
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-mex-eng-2026-07-05-spread-home-2pt5 | 让分：墨西哥 (-2.5) | 墨西哥 | 3.0% | 5.0% | +2.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-spread-away-2pt5 | 让分：英格兰 (-2.5) | 英格兰 | 5.0% | 0.5% | -4.5% | 偏低+ | 仅观察 | baseline edge 需要首发确认 |
| fifwc-mex-eng-2026-07-05-spread-home-3pt5 | 让分：墨西哥 (-3.5) | 墨西哥 | 0.6% | 2.6% | +2.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-mex-eng-2026-07-05-spread-away-3pt5 | 让分：英格兰 (-3.5) | 英格兰 | 1.5% | 0.1% | -1.4% | 低 | 跳过 | 价格过于极端 |
| fifwc-mex-eng-2026-07-05-spread-home-4pt5 | 让分：墨西哥 (-4.5) | 墨西哥 | 1.1% | 3.1% | +2.0% | 低 | 跳过 | 价格过于极端 |
| fifwc-mex-eng-2026-07-05-spread-away-4pt5 | 让分：英格兰 (-4.5) | 英格兰 | 1.1% | 0.1% | -1.0% | 低 | 跳过 | 价格过于极端 |
| fifwc-mex-eng-2026-07-05-spread-home-5pt5 | 让分：墨西哥 (-5.5) | 墨西哥 | 0.7% | 2.6% | +2.0% | 低 | 跳过 | 价格过于极端 |
| fifwc-mex-eng-2026-07-05-spread-away-5pt5 | 让分：英格兰 (-5.5) | 英格兰 | 1.1% | 0.1% | -1.0% | 低 | 跳过 | 价格过于极端 |
| fifwc-mex-eng-2026-07-05-spread-home-1pt5 | 让分：墨西哥 (-1.5) | 墨西哥 | 11.5% | 14.5% | +3.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-spread-away-1pt5 | 让分：英格兰 (-1.5) | 英格兰 | 16.5% | 16.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 总进球盘
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-mex-eng-2026-07-05-total-0pt5 | 墨西哥 vs 英格兰：总进球大小 0.5 | 大 | 89.0% | 91.0% | +2.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-total-1pt5 | 墨西哥 vs 英格兰：总进球大小 1.5 | 大 | 64.5% | 66.5% | +2.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-total-2pt5 | 墨西哥 vs 英格兰：总进球大小 2.5 | 大 | 37.5% | 37.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-total-3pt5 | 墨西哥 vs 英格兰：总进球大小 3.5 | 大 | 18.0% | 18.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-total-4pt5 | 墨西哥 vs 英格兰：总进球大小 4.5 | 大 | 7.5% | 7.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-total-5pt5 | 墨西哥 vs 英格兰：总进球大小 5.5 | 大 | 2.5% | 0.1% | -2.4% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-total-6pt5 | 墨西哥 vs 英格兰：总进球大小 6.5 | 大 | 1.1% | 0.1% | -1.0% | 低 | 跳过 | 价格过于极端 |
| fifwc-mex-eng-2026-07-05-total-7pt5 | 墨西哥 vs 英格兰：总进球大小 7.5 | 大 | 0.5% | 0.1% | -0.4% | 低 | 跳过 | 价格过于极端 |
| fifwc-mex-eng-2026-07-05-total-8pt5 | 墨西哥 vs 英格兰：总进球大小 8.5 | 大 | 0.5% | 0.1% | -0.4% | 低 | 跳过 | 价格过于极端 |
| fifwc-mex-eng-2026-07-05-first-half-total-0pt5 | 墨西哥 vs 英格兰：上半场 大小 0.5 | 大 | 62.5% | 64.5% | +2.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-first-half-total-1pt5 | 墨西哥 vs 英格兰：上半场 大小 1.5 | 大 | 26.5% | 28.5% | +2.0% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-first-half-total-2pt5 | 墨西哥 vs 英格兰：上半场 大小 2.5 | 大 | 8.0% | 8.0% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-second-half-total-0pt5 | 墨西哥 vs 英格兰：下半场 大小 0.5 | 大 | 71.0% | 73.0% | +2.0% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-second-half-total-1pt5 | 墨西哥 vs 英格兰：下半场 大小 1.5 | 大 | 35.0% | 37.0% | +2.0% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-second-half-total-2pt5 | 墨西哥 vs 英格兰：下半场 大小 2.5 | 大 | 13.0% | 13.0% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |

### 双方均进球
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-mex-eng-2026-07-05-btts | 墨西哥 vs 英格兰: 双方均进球 | 是 | 47.5% | 52.5% | +5.0% | 偏低+ | 小仓限价 | 结构化 edge，小仓限价 |
| fifwc-mex-eng-2026-07-05-btts-first-half | 墨西哥 vs 英格兰: 上半场双方均进球 | 是 | 14.5% | 14.5% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-btts-second-half | 墨西哥 vs 英格兰: 下半场双方均进球 | 是 | 22.0% | 22.0% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |

### 首支进球队伍
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-mex-eng-2026-07-05-first-to-score-home | 墨西哥 会先于 英格兰 进球吗？ | 是 | 41.0% | 41.0% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-first-to-score-away | 英格兰 会先于 墨西哥 进球吗？ | 是 | 48.5% | 48.5% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-first-to-score-neither | 墨西哥 vs 英格兰: 无球队先进球? | 是 | 9.5% | 6.0% | -3.5% | 低 | 跳过 | edge 低于 4 个百分点 |

### 球队进球数
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-mex-eng-2026-07-05-team-total-home-0pt5 | 墨西哥 vs 英格兰：墨西哥 大小 0.5 | 大 | 63.5% | 63.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-team-total-home-1pt5 | 墨西哥 vs 英格兰：墨西哥 大小 1.5 | 大 | 26.5% | 26.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-team-total-home-2pt5 | 墨西哥 vs 英格兰：墨西哥 大小 2.5 | 大 | 8.0% | 4.5% | -3.5% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-team-total-away-0pt5 | 墨西哥 vs 英格兰：英格兰 大小 0.5 | 大 | 70.0% | 72.5% | +2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-team-total-away-1pt5 | 墨西哥 vs 英格兰：英格兰 大小 1.5 | 大 | 34.5% | 34.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-team-total-away-2pt5 | 墨西哥 vs 英格兰：英格兰 大小 2.5 | 大 | 12.0% | 8.5% | -3.5% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-first-half-team-total-home-0pt5 | 墨西哥 vs 英格兰：墨西哥 上半场 大小 0.5 | 大 | 37.5% | 37.5% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-first-half-team-total-home-1pt5 | 墨西哥 vs 英格兰：墨西哥 上半场 大小 1.5 | 大 | 8.0% | 8.0% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-first-half-team-total-away-0pt5 | 墨西哥 vs 英格兰：英格兰 上半场 大小 0.5 | 大 | 40.5% | 43.0% | +2.5% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-first-half-team-total-away-1pt5 | 墨西哥 vs 英格兰：英格兰 上半场 大小 1.5 | 大 | 10.0% | 10.0% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-mex-eng-2026-07-05-second-half-team-total-home-0pt5 | 墨西哥 vs 英格兰：墨西哥 下半场 大小 0.5 | 大 | 50.0% | 50.0% | +0.0% | 低 | 跳过 | 流动性不足 |
| fifwc-mex-eng-2026-07-05-second-half-team-total-home-1pt5 | 墨西哥 vs 英格兰：墨西哥 下半场 大小 1.5 | 大 | 50.0% | 47.0% | -3.0% | 低 | 跳过 | 流动性不足 |
| fifwc-mex-eng-2026-07-05-second-half-team-total-away-0pt5 | 墨西哥 vs 英格兰：英格兰 下半场 大小 0.5 | 大 | 50.0% | 52.5% | +2.5% | 低 | 跳过 | 流动性不足 |
| fifwc-mex-eng-2026-07-05-second-half-team-total-away-1pt5 | 墨西哥 vs 英格兰：英格兰 下半场 大小 1.5 | 大 | 50.0% | 50.0% | +0.0% | 低 | 跳过 | 流动性不足 |

## 策略观察项详细证据
### 巴西 vs 挪威 | fifwc-bra-nor-2026-07-05-btts
- 候选项：巴西 vs 挪威: 双方均进球 / 是；动作=小仓限价买入；参考方向=是；市场概率=57.5%；模型概率=62.5%；当前 edge=+5.0%；状态=小仓限价。
- 证据链：
  1. Polymarket market_slug=fifwc-bra-nor-2026-07-05-btts；参考方向市场概率=57.5%；模型概率=62.5%；edge=+5.0%。
  2. 同场盘口结构用于校验：市场类型=btts；比赛=巴西 vs 挪威；候选方向=巴西 vs 挪威: 双方均进球 / 是。
  3. Brazil vs. Norway in World Cup round of 16: Time, date, preview - USA Today | USA Today | https://news.google.com/rss/articles/CBMiuwFBVV95cUxQNmV4RHBsT2NwTi1nR2dkbUFxck81VXVIR0owaTNJT0JVWVRBd3pUSU5FVXg2RzBfaUxtY0x1TzIxT2NDXzZDRG12dU1NTTBFZmY5d3A3MGhoaUgzeGpiOVdoYVdMUTZNaUx5dzlVY1dNcHZJTUUza3p0V3RoM3NkdVM4ZUZaR3FzcjRQQ3N4emZYYmNWSl9zZnp2ekVFd1NmRjN4Y1ppXzFCc0xRQjQ0WF9mTTZoamI1cWpr?oc=5
  4. 👀 Easy prey? Norway are a tough nut for Brazil: head-to-head - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMiigFBVV95cUxOV3BiZDE0ekRvRFdQWUw1eXZMOHBLcTgyZUpJay0ycHJjdUM1OGhWb1NYME9FTk11WXpPVldJdFkzdmxhT0ZBclR1NTZnREZZandzbkFGcWhkTUxacGYwNmNSWFZKNkF5UTFZTVpNanZwRVNjRU1USDZST01pR3dlaV9ZN3Q5Sl9kZkE?oc=5
  5. Who Is Norway's Next World Cup Opponent? - FOX Sports | FOX Sports | https://news.google.com/rss/articles/CBMigAFBVV95cUxPWU5mcGJrcm5qeG5mLWd4NC1DeXZBT2djdnlZYVdHVjBrN2padnowWEhLOHpheGt2OUZxdnVKXzhiZ205RnZxZ0RSZkVEX3lfencwYUlfYWhLRXloT0s3TUZlVWFiRll2b1dwZEZPUC1pdTRUbl9fQ20yMXI0em4yYtIBgAFBVV95cUxPWlNNZnRBQmtWYTFCRlExUHlOMDlTTndIamh0SVBqbTFwQVlVeWFKNlo2S1ozVUlHS2dDaDF2RFc0NHlYQ2RnNG5obmpNenU3cmgyc3g5YnhDRW1kaWdnaEJ6aWZwaFBlWHAtX3VteHFoeS14bWpKcGx4eWJZLXBRYw?oc=5
- 推理链：
  1. fifwc-bra-nor-2026-07-05-btts 是 巴西 vs 挪威 的双方均进球盘口；同场两队 0.5 球队进球线没有否定弱侧进球路径，因此 巴西 vs 挪威: 双方均进球 / 是 从市场概率 57.5% 上修到模型概率 62.5%。
  2. 该信号的 edge 为 +5.0%，来源是 BTTS 与球队进球数之间的结构差，不是因为单纯看好胜平负热门方。
  3. 若临场首发削弱任一方进球路径，fifwc-bra-nor-2026-07-05-btts 必须重新定价并取消小仓限价。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 墨西哥 vs 英格兰 | fifwc-mex-eng-2026-07-05-btts
- 候选项：墨西哥 vs 英格兰: 双方均进球 / 是；动作=小仓限价买入；参考方向=是；市场概率=47.5%；模型概率=52.5%；当前 edge=+5.0%；状态=小仓限价。
- 证据链：
  1. Polymarket market_slug=fifwc-mex-eng-2026-07-05-btts；参考方向市场概率=47.5%；模型概率=52.5%；edge=+5.0%。
  2. 同场盘口结构用于校验：市场类型=btts；比赛=墨西哥 vs 英格兰；候选方向=墨西哥 vs 英格兰: 双方均进球 / 是。
  3. FIFA World Cup 2026: How to watch Mexico vs England in the round of 16 – head-to-head, full schedule - olympics.com | olympics.com | https://news.google.com/rss/articles/CBMiuwFBVV95cUxNTGt6TmladXBQeXh3eDJSZVdmODRmOWprSFlVSDNONmtOM1R5Q29NVElkN3VaWVFGOEZVaFlJZlA1cklGNktZVjU0ZGItbkFQbW1ITmhoc1BpV0Y1OTFmRnk3WUlITDd2SGU0NlpGakNLbEY4bkJkQWV3YUZwdGNoTmNLU29kcjBlM0dETURBT3l2NTZhYVM4QUo3REk0VEJmNjVaY0d6T003c3FYZENLdXVRTHh3aUdtRllN?oc=5
  4. Mexico vs. England (Jul 5, 2026) Live Score - ESPN | ESPN | https://news.google.com/rss/articles/CBMickFVX3lxTE5XbEhNUVZxdGNvQ3NFX0dpeTBCMkIxWHIxZlNTTTJmOXNENnowS3pNcVU0SzZmRHlLUENvUlZfY1llVHdwU2dXOGxzdkN2a2FkM0pqTEJBSFBLRkd5bkF5d1JIMlZMNzVKY1FzQkRWSG00Zw?oc=5
  5. England vs. Mexico: Everything To Know About The World Cup Round Of 16 Game - FOX Sports | FOX Sports | https://news.google.com/rss/articles/CBMipwFBVV95cUxQUmNYLTFnOXQ5NzFSRFRWd1hmR3ZhOHNmZm9qVWVfY0M5U3BXcXBWeFBVYi1pdkhRSkVDQ19RLXZvVTlabjVPcXdzdU9XWkRHSWpOZE4xcUY5U0pvVFNhNUxTYkJyZ1p1OWk4cUt0X3VBZEtUMEt4c2d4ZXVBNVFJU05wcVVub1E4bkVxVVFjTHdheHAwdlY1dUZJekFzUmNHNHpzUUFVZ9IBpwFBVV95cUxNSngxWjFxOC1NRU9Fby1zQ3VlbG55bllaUDB6WXBhMXYzVkNRN3N6LUVpaFlLcGRkYU9zZUtBck9fenJ2Mm1zQnMtWkcxQ29udU01QWoyQ3BvRHBYbkRYeE02VjhLQ0drSXNna2hPQzdieVdsM0U1Sm83YzZOVlNna09OMlJrY1VaazMySGVSUWhHTlQ0SEhyQ2ZkdnViejhGZjFFR1h4VQ?oc=5
- 推理链：
  1. fifwc-mex-eng-2026-07-05-btts 是 墨西哥 vs 英格兰 的双方均进球盘口；同场两队 0.5 球队进球线没有否定弱侧进球路径，因此 墨西哥 vs 英格兰: 双方均进球 / 是 从市场概率 47.5% 上修到模型概率 52.5%。
  2. 该信号的 edge 为 +5.0%，来源是 BTTS 与球队进球数之间的结构差，不是因为单纯看好胜平负热门方。
  3. 若临场首发削弱任一方进球路径，fifwc-mex-eng-2026-07-05-btts 必须重新定价并取消小仓限价。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 巴西 vs 挪威 | fifwc-bra-nor-2026-07-05-total-5pt5
- 候选项：巴西 vs 挪威：总进球大小 5.5 / 否；动作=条件观察；参考方向=否；市场概率=93.5%；模型概率=98.0%；当前 edge=+4.5%；状态=仅观察。
- 证据链：
  1. Polymarket market_slug=fifwc-bra-nor-2026-07-05-total-5pt5；参考方向市场概率=93.5%；模型概率=98.0%；edge=+4.5%。
  2. 同场盘口结构用于校验：市场类型=totals_lines；比赛=巴西 vs 挪威；候选方向=巴西 vs 挪威：总进球大小 5.5 / 否。
  3. Brazil vs. Norway in World Cup round of 16: Time, date, preview - USA Today | USA Today | https://news.google.com/rss/articles/CBMiuwFBVV95cUxQNmV4RHBsT2NwTi1nR2dkbUFxck81VXVIR0owaTNJT0JVWVRBd3pUSU5FVXg2RzBfaUxtY0x1TzIxT2NDXzZDRG12dU1NTTBFZmY5d3A3MGhoaUgzeGpiOVdoYVdMUTZNaUx5dzlVY1dNcHZJTUUza3p0V3RoM3NkdVM4ZUZaR3FzcjRQQ3N4emZYYmNWSl9zZnp2ekVFd1NmRjN4Y1ppXzFCc0xRQjQ0WF9mTTZoamI1cWpr?oc=5
  4. 👀 Easy prey? Norway are a tough nut for Brazil: head-to-head - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMiigFBVV95cUxOV3BiZDE0ekRvRFdQWUw1eXZMOHBLcTgyZUpJay0ycHJjdUM1OGhWb1NYME9FTk11WXpPVldJdFkzdmxhT0ZBclR1NTZnREZZandzbkFGcWhkTUxacGYwNmNSWFZKNkF5UTFZTVpNanZwRVNjRU1USDZST01pR3dlaV9ZN3Q5Sl9kZkE?oc=5
  5. Who Is Norway's Next World Cup Opponent? - FOX Sports | FOX Sports | https://news.google.com/rss/articles/CBMigAFBVV95cUxPWU5mcGJrcm5qeG5mLWd4NC1DeXZBT2djdnlZYVdHVjBrN2padnowWEhLOHpheGt2OUZxdnVKXzhiZ205RnZxZ0RSZkVEX3lfencwYUlfYWhLRXloT0s3TUZlVWFiRll2b1dwZEZPUC1pdTRUbl9fQ20yMXI0em4yYtIBgAFBVV95cUxPWlNNZnRBQmtWYTFCRlExUHlOMDlTTndIamh0SVBqbTFwQVlVeWFKNlo2S1ozVUlHS2dDaDF2RFc0NHlYQ2RnNG5obmpNenU3cmgyc3g5YnhDRW1kaWdnaEJ6aWZwaFBlWHAtX3VteHFoeS14bWpKcGx4eWJZLXBRYw?oc=5
- 推理链：
  1. fifwc-bra-nor-2026-07-05-total-5pt5 是 巴西 vs 挪威 的总进球盘口；模型用 BTTS、球队进球线和同场大小球阶梯检查总进球分布，得到 巴西 vs 挪威：总进球大小 5.5 / 否 模型概率 98.0%。
  2. 市场参考概率为 93.5%，结构化 edge 为 +4.5%；该 edge 来自同场盘口阶梯一致性，而不是外部硬统计断言。
  3. 如果 BTTS 或球队进球线临场反向移动，fifwc-bra-nor-2026-07-05-total-5pt5 的总进球信号失效。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 巴西 vs 挪威 | fifwc-bra-nor-2026-07-05-spread-home-2pt5
- 候选项：让分：巴西 (-2.5) / 否；动作=条件观察；参考方向=否；市场概率=87.5%；模型概率=92.0%；当前 edge=+4.5%；状态=仅观察。
- 证据链：
  1. Polymarket market_slug=fifwc-bra-nor-2026-07-05-spread-home-2pt5；参考方向市场概率=87.5%；模型概率=92.0%；edge=+4.5%。
  2. 同场盘口结构用于校验：市场类型=spread_lines；比赛=巴西 vs 挪威；候选方向=让分：巴西 (-2.5) / 否。
  3. Brazil vs. Norway in World Cup round of 16: Time, date, preview - USA Today | USA Today | https://news.google.com/rss/articles/CBMiuwFBVV95cUxQNmV4RHBsT2NwTi1nR2dkbUFxck81VXVIR0owaTNJT0JVWVRBd3pUSU5FVXg2RzBfaUxtY0x1TzIxT2NDXzZDRG12dU1NTTBFZmY5d3A3MGhoaUgzeGpiOVdoYVdMUTZNaUx5dzlVY1dNcHZJTUUza3p0V3RoM3NkdVM4ZUZaR3FzcjRQQ3N4emZYYmNWSl9zZnp2ekVFd1NmRjN4Y1ppXzFCc0xRQjQ0WF9mTTZoamI1cWpr?oc=5
  4. 👀 Easy prey? Norway are a tough nut for Brazil: head-to-head - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMiigFBVV95cUxOV3BiZDE0ekRvRFdQWUw1eXZMOHBLcTgyZUpJay0ycHJjdUM1OGhWb1NYME9FTk11WXpPVldJdFkzdmxhT0ZBclR1NTZnREZZandzbkFGcWhkTUxacGYwNmNSWFZKNkF5UTFZTVpNanZwRVNjRU1USDZST01pR3dlaV9ZN3Q5Sl9kZkE?oc=5
  5. Who Is Norway's Next World Cup Opponent? - FOX Sports | FOX Sports | https://news.google.com/rss/articles/CBMigAFBVV95cUxPWU5mcGJrcm5qeG5mLWd4NC1DeXZBT2djdnlZYVdHVjBrN2padnowWEhLOHpheGt2OUZxdnVKXzhiZ205RnZxZ0RSZkVEX3lfencwYUlfYWhLRXloT0s3TUZlVWFiRll2b1dwZEZPUC1pdTRUbl9fQ20yMXI0em4yYtIBgAFBVV95cUxPWlNNZnRBQmtWYTFCRlExUHlOMDlTTndIamh0SVBqbTFwQVlVeWFKNlo2S1ozVUlHS2dDaDF2RFc0NHlYQ2RnNG5obmpNenU3cmgyc3g5YnhDRW1kaWdnaEJ6aWZwaFBlWHAtX3VteHFoeS14bWpKcGx4eWJZLXBRYw?oc=5
- 推理链：
  1. fifwc-bra-nor-2026-07-05-spread-home-2pt5 是 巴西 vs 挪威 的让分盘口；模型把胜平负优势和净胜球分布拆开处理，因此 让分：巴西 (-2.5) / 否 的市场概率 87.5% 与模型概率 92.0% 出现偏差。
  2. 该信号 edge 为 +4.5%，核心判断是当前让分价格相对胜率分布偏离，而不是把胜率直接等同于穿盘率。
  3. 如果临场价格移动超过 4 个百分点或首发改变净胜球路径，fifwc-bra-nor-2026-07-05-spread-home-2pt5 需要降级为观察。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 墨西哥 vs 英格兰 | fifwc-mex-eng-2026-07-05-spread-away-2pt5
- 候选项：让分：英格兰 (-2.5) / 否；动作=条件观察；参考方向=否；市场概率=95.0%；模型概率=99.5%；当前 edge=+4.5%；状态=仅观察。
- 证据链：
  1. Polymarket market_slug=fifwc-mex-eng-2026-07-05-spread-away-2pt5；参考方向市场概率=95.0%；模型概率=99.5%；edge=+4.5%。
  2. 同场盘口结构用于校验：市场类型=spread_lines；比赛=墨西哥 vs 英格兰；候选方向=让分：英格兰 (-2.5) / 否。
  3. FIFA World Cup 2026: How to watch Mexico vs England in the round of 16 – head-to-head, full schedule - olympics.com | olympics.com | https://news.google.com/rss/articles/CBMiuwFBVV95cUxNTGt6TmladXBQeXh3eDJSZVdmODRmOWprSFlVSDNONmtOM1R5Q29NVElkN3VaWVFGOEZVaFlJZlA1cklGNktZVjU0ZGItbkFQbW1ITmhoc1BpV0Y1OTFmRnk3WUlITDd2SGU0NlpGakNLbEY4bkJkQWV3YUZwdGNoTmNLU29kcjBlM0dETURBT3l2NTZhYVM4QUo3REk0VEJmNjVaY0d6T003c3FYZENLdXVRTHh3aUdtRllN?oc=5
  4. Mexico vs. England (Jul 5, 2026) Live Score - ESPN | ESPN | https://news.google.com/rss/articles/CBMickFVX3lxTE5XbEhNUVZxdGNvQ3NFX0dpeTBCMkIxWHIxZlNTTTJmOXNENnowS3pNcVU0SzZmRHlLUENvUlZfY1llVHdwU2dXOGxzdkN2a2FkM0pqTEJBSFBLRkd5bkF5d1JIMlZMNzVKY1FzQkRWSG00Zw?oc=5
  5. England vs. Mexico: Everything To Know About The World Cup Round Of 16 Game - FOX Sports | FOX Sports | https://news.google.com/rss/articles/CBMipwFBVV95cUxQUmNYLTFnOXQ5NzFSRFRWd1hmR3ZhOHNmZm9qVWVfY0M5U3BXcXBWeFBVYi1pdkhRSkVDQ19RLXZvVTlabjVPcXdzdU9XWkRHSWpOZE4xcUY5U0pvVFNhNUxTYkJyZ1p1OWk4cUt0X3VBZEtUMEt4c2d4ZXVBNVFJU05wcVVub1E4bkVxVVFjTHdheHAwdlY1dUZJekFzUmNHNHpzUUFVZ9IBpwFBVV95cUxNSngxWjFxOC1NRU9Fby1zQ3VlbG55bllaUDB6WXBhMXYzVkNRN3N6LUVpaFlLcGRkYU9zZUtBck9fenJ2Mm1zQnMtWkcxQ29udU01QWoyQ3BvRHBYbkRYeE02VjhLQ0drSXNna2hPQzdieVdsM0U1Sm83YzZOVlNna09OMlJrY1VaazMySGVSUWhHTlQ0SEhyQ2ZkdnViejhGZjFFR1h4VQ?oc=5
- 推理链：
  1. fifwc-mex-eng-2026-07-05-spread-away-2pt5 是 墨西哥 vs 英格兰 的让分盘口；模型把胜平负优势和净胜球分布拆开处理，因此 让分：英格兰 (-2.5) / 否 的市场概率 95.0% 与模型概率 99.5% 出现偏差。
  2. 该信号 edge 为 +4.5%，核心判断是当前让分价格相对胜率分布偏离，而不是把胜率直接等同于穿盘率。
  3. 如果临场价格移动超过 4 个百分点或首发改变净胜球路径，fifwc-mex-eng-2026-07-05-spread-away-2pt5 需要降级为观察。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 巴西 vs 挪威 | fifwc-bra-nor-2026-07-05-spread-home-4pt5
- 候选项：让分：巴西 (-4.5) / 否；动作=条件观察；参考方向=否；市场概率=95.4%；模型概率=99.9%；当前 edge=+4.5%；状态=仅观察。
- 证据链：
  1. Polymarket market_slug=fifwc-bra-nor-2026-07-05-spread-home-4pt5；参考方向市场概率=95.4%；模型概率=99.9%；edge=+4.5%。
  2. 同场盘口结构用于校验：市场类型=spread_lines；比赛=巴西 vs 挪威；候选方向=让分：巴西 (-4.5) / 否。
  3. Brazil vs. Norway in World Cup round of 16: Time, date, preview - USA Today | USA Today | https://news.google.com/rss/articles/CBMiuwFBVV95cUxQNmV4RHBsT2NwTi1nR2dkbUFxck81VXVIR0owaTNJT0JVWVRBd3pUSU5FVXg2RzBfaUxtY0x1TzIxT2NDXzZDRG12dU1NTTBFZmY5d3A3MGhoaUgzeGpiOVdoYVdMUTZNaUx5dzlVY1dNcHZJTUUza3p0V3RoM3NkdVM4ZUZaR3FzcjRQQ3N4emZYYmNWSl9zZnp2ekVFd1NmRjN4Y1ppXzFCc0xRQjQ0WF9mTTZoamI1cWpr?oc=5
  4. 👀 Easy prey? Norway are a tough nut for Brazil: head-to-head - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMiigFBVV95cUxOV3BiZDE0ekRvRFdQWUw1eXZMOHBLcTgyZUpJay0ycHJjdUM1OGhWb1NYME9FTk11WXpPVldJdFkzdmxhT0ZBclR1NTZnREZZandzbkFGcWhkTUxacGYwNmNSWFZKNkF5UTFZTVpNanZwRVNjRU1USDZST01pR3dlaV9ZN3Q5Sl9kZkE?oc=5
  5. Who Is Norway's Next World Cup Opponent? - FOX Sports | FOX Sports | https://news.google.com/rss/articles/CBMigAFBVV95cUxPWU5mcGJrcm5qeG5mLWd4NC1DeXZBT2djdnlZYVdHVjBrN2padnowWEhLOHpheGt2OUZxdnVKXzhiZ205RnZxZ0RSZkVEX3lfencwYUlfYWhLRXloT0s3TUZlVWFiRll2b1dwZEZPUC1pdTRUbl9fQ20yMXI0em4yYtIBgAFBVV95cUxPWlNNZnRBQmtWYTFCRlExUHlOMDlTTndIamh0SVBqbTFwQVlVeWFKNlo2S1ozVUlHS2dDaDF2RFc0NHlYQ2RnNG5obmpNenU3cmgyc3g5YnhDRW1kaWdnaEJ6aWZwaFBlWHAtX3VteHFoeS14bWpKcGx4eWJZLXBRYw?oc=5
- 推理链：
  1. fifwc-bra-nor-2026-07-05-spread-home-4pt5 是 巴西 vs 挪威 的让分盘口；模型把胜平负优势和净胜球分布拆开处理，因此 让分：巴西 (-4.5) / 否 的市场概率 95.4% 与模型概率 99.9% 出现偏差。
  2. 该信号 edge 为 +4.5%，核心判断是当前让分价格相对胜率分布偏离，而不是把胜率直接等同于穿盘率。
  3. 如果临场价格移动超过 4 个百分点或首发改变净胜球路径，fifwc-bra-nor-2026-07-05-spread-home-4pt5 需要降级为观察。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 墨西哥 vs 英格兰 | fifwc-mex-eng-2026-07-05-draw
- 候选项：墨西哥 vs 英格兰 会打平吗？ / 是；动作=条件观察；参考方向=是；市场概率=29.5%；模型概率=34.0%；当前 edge=+4.5%；状态=仅观察。
- 证据链：
  1. Polymarket market_slug=fifwc-mex-eng-2026-07-05-draw；参考方向市场概率=29.5%；模型概率=34.0%；edge=+4.5%。
  2. 同场盘口结构用于校验：市场类型=match_1x2；比赛=墨西哥 vs 英格兰；候选方向=墨西哥 vs 英格兰 会打平吗？ / 是。
  3. FIFA World Cup 2026: How to watch Mexico vs England in the round of 16 – head-to-head, full schedule - olympics.com | olympics.com | https://news.google.com/rss/articles/CBMiuwFBVV95cUxNTGt6TmladXBQeXh3eDJSZVdmODRmOWprSFlVSDNONmtOM1R5Q29NVElkN3VaWVFGOEZVaFlJZlA1cklGNktZVjU0ZGItbkFQbW1ITmhoc1BpV0Y1OTFmRnk3WUlITDd2SGU0NlpGakNLbEY4bkJkQWV3YUZwdGNoTmNLU29kcjBlM0dETURBT3l2NTZhYVM4QUo3REk0VEJmNjVaY0d6T003c3FYZENLdXVRTHh3aUdtRllN?oc=5
  4. Mexico vs. England (Jul 5, 2026) Live Score - ESPN | ESPN | https://news.google.com/rss/articles/CBMickFVX3lxTE5XbEhNUVZxdGNvQ3NFX0dpeTBCMkIxWHIxZlNTTTJmOXNENnowS3pNcVU0SzZmRHlLUENvUlZfY1llVHdwU2dXOGxzdkN2a2FkM0pqTEJBSFBLRkd5bkF5d1JIMlZMNzVKY1FzQkRWSG00Zw?oc=5
  5. England vs. Mexico: Everything To Know About The World Cup Round Of 16 Game - FOX Sports | FOX Sports | https://news.google.com/rss/articles/CBMipwFBVV95cUxQUmNYLTFnOXQ5NzFSRFRWd1hmR3ZhOHNmZm9qVWVfY0M5U3BXcXBWeFBVYi1pdkhRSkVDQ19RLXZvVTlabjVPcXdzdU9XWkRHSWpOZE4xcUY5U0pvVFNhNUxTYkJyZ1p1OWk4cUt0X3VBZEtUMEt4c2d4ZXVBNVFJU05wcVVub1E4bkVxVVFjTHdheHAwdlY1dUZJekFzUmNHNHpzUUFVZ9IBpwFBVV95cUxNSngxWjFxOC1NRU9Fby1zQ3VlbG55bllaUDB6WXBhMXYzVkNRN3N6LUVpaFlLcGRkYU9zZUtBck9fenJ2Mm1zQnMtWkcxQ29udU01QWoyQ3BvRHBYbkRYeE02VjhLQ0drSXNna2hPQzdieVdsM0U1Sm83YzZOVlNna09OMlJrY1VaazMySGVSUWhHTlQ0SEhyQ2ZkdnViejhGZjFFR1h4VQ?oc=5
- 推理链：
  1. fifwc-mex-eng-2026-07-05-draw 是 墨西哥 vs 英格兰 的胜平负盘口；模型根据主胜、平局、客胜之间的距离重新估计 墨西哥 vs 英格兰 会打平吗？ / 是，模型概率为 34.0%。
  2. 市场参考概率为 29.5%，edge 为 +4.5%；该信号主要来自比赛均衡度或热门程度，而不是新闻硬结论。
  3. 若临场胜平负三项价格重新拉开，fifwc-mex-eng-2026-07-05-draw 的结构化平衡信号需要取消。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 巴西 vs 挪威 | fifwc-bra-nor-2026-07-05-spread-home-3pt5
- 候选项：让分：巴西 (-3.5) / 否；动作=条件观察；参考方向=否；市场概率=95.5%；模型概率=99.9%；当前 edge=+4.4%；状态=仅观察。
- 证据链：
  1. Polymarket market_slug=fifwc-bra-nor-2026-07-05-spread-home-3pt5；参考方向市场概率=95.5%；模型概率=99.9%；edge=+4.4%。
  2. 同场盘口结构用于校验：市场类型=spread_lines；比赛=巴西 vs 挪威；候选方向=让分：巴西 (-3.5) / 否。
  3. Brazil vs. Norway in World Cup round of 16: Time, date, preview - USA Today | USA Today | https://news.google.com/rss/articles/CBMiuwFBVV95cUxQNmV4RHBsT2NwTi1nR2dkbUFxck81VXVIR0owaTNJT0JVWVRBd3pUSU5FVXg2RzBfaUxtY0x1TzIxT2NDXzZDRG12dU1NTTBFZmY5d3A3MGhoaUgzeGpiOVdoYVdMUTZNaUx5dzlVY1dNcHZJTUUza3p0V3RoM3NkdVM4ZUZaR3FzcjRQQ3N4emZYYmNWSl9zZnp2ekVFd1NmRjN4Y1ppXzFCc0xRQjQ0WF9mTTZoamI1cWpr?oc=5
  4. 👀 Easy prey? Norway are a tough nut for Brazil: head-to-head - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMiigFBVV95cUxOV3BiZDE0ekRvRFdQWUw1eXZMOHBLcTgyZUpJay0ycHJjdUM1OGhWb1NYME9FTk11WXpPVldJdFkzdmxhT0ZBclR1NTZnREZZandzbkFGcWhkTUxacGYwNmNSWFZKNkF5UTFZTVpNanZwRVNjRU1USDZST01pR3dlaV9ZN3Q5Sl9kZkE?oc=5
  5. Who Is Norway's Next World Cup Opponent? - FOX Sports | FOX Sports | https://news.google.com/rss/articles/CBMigAFBVV95cUxPWU5mcGJrcm5qeG5mLWd4NC1DeXZBT2djdnlZYVdHVjBrN2padnowWEhLOHpheGt2OUZxdnVKXzhiZ205RnZxZ0RSZkVEX3lfencwYUlfYWhLRXloT0s3TUZlVWFiRll2b1dwZEZPUC1pdTRUbl9fQ20yMXI0em4yYtIBgAFBVV95cUxPWlNNZnRBQmtWYTFCRlExUHlOMDlTTndIamh0SVBqbTFwQVlVeWFKNlo2S1ozVUlHS2dDaDF2RFc0NHlYQ2RnNG5obmpNenU3cmgyc3g5YnhDRW1kaWdnaEJ6aWZwaFBlWHAtX3VteHFoeS14bWpKcGx4eWJZLXBRYw?oc=5
- 推理链：
  1. fifwc-bra-nor-2026-07-05-spread-home-3pt5 是 巴西 vs 挪威 的让分盘口；模型把胜平负优势和净胜球分布拆开处理，因此 让分：巴西 (-3.5) / 否 的市场概率 95.5% 与模型概率 99.9% 出现偏差。
  2. 该信号 edge 为 +4.4%，核心判断是当前让分价格相对胜率分布偏离，而不是把胜率直接等同于穿盘率。
  3. 如果临场价格移动超过 4 个百分点或首发改变净胜球路径，fifwc-bra-nor-2026-07-05-spread-home-3pt5 需要降级为观察。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 巴西 vs 挪威 | fifwc-bra-nor-2026-07-05-total-2pt5
- 候选项：巴西 vs 挪威：总进球大小 2.5 / 大；动作=条件观察；参考方向=大；市场概率=54.5%；模型概率=58.5%；当前 edge=+4.0%；状态=仅观察。
- 证据链：
  1. Polymarket market_slug=fifwc-bra-nor-2026-07-05-total-2pt5；参考方向市场概率=54.5%；模型概率=58.5%；edge=+4.0%。
  2. 同场盘口结构用于校验：市场类型=totals_lines；比赛=巴西 vs 挪威；候选方向=巴西 vs 挪威：总进球大小 2.5 / 大。
  3. Brazil vs. Norway in World Cup round of 16: Time, date, preview - USA Today | USA Today | https://news.google.com/rss/articles/CBMiuwFBVV95cUxQNmV4RHBsT2NwTi1nR2dkbUFxck81VXVIR0owaTNJT0JVWVRBd3pUSU5FVXg2RzBfaUxtY0x1TzIxT2NDXzZDRG12dU1NTTBFZmY5d3A3MGhoaUgzeGpiOVdoYVdMUTZNaUx5dzlVY1dNcHZJTUUza3p0V3RoM3NkdVM4ZUZaR3FzcjRQQ3N4emZYYmNWSl9zZnp2ekVFd1NmRjN4Y1ppXzFCc0xRQjQ0WF9mTTZoamI1cWpr?oc=5
  4. 👀 Easy prey? Norway are a tough nut for Brazil: head-to-head - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMiigFBVV95cUxOV3BiZDE0ekRvRFdQWUw1eXZMOHBLcTgyZUpJay0ycHJjdUM1OGhWb1NYME9FTk11WXpPVldJdFkzdmxhT0ZBclR1NTZnREZZandzbkFGcWhkTUxacGYwNmNSWFZKNkF5UTFZTVpNanZwRVNjRU1USDZST01pR3dlaV9ZN3Q5Sl9kZkE?oc=5
  5. Who Is Norway's Next World Cup Opponent? - FOX Sports | FOX Sports | https://news.google.com/rss/articles/CBMigAFBVV95cUxPWU5mcGJrcm5qeG5mLWd4NC1DeXZBT2djdnlZYVdHVjBrN2padnowWEhLOHpheGt2OUZxdnVKXzhiZ205RnZxZ0RSZkVEX3lfencwYUlfYWhLRXloT0s3TUZlVWFiRll2b1dwZEZPUC1pdTRUbl9fQ20yMXI0em4yYtIBgAFBVV95cUxPWlNNZnRBQmtWYTFCRlExUHlOMDlTTndIamh0SVBqbTFwQVlVeWFKNlo2S1ozVUlHS2dDaDF2RFc0NHlYQ2RnNG5obmpNenU3cmgyc3g5YnhDRW1kaWdnaEJ6aWZwaFBlWHAtX3VteHFoeS14bWpKcGx4eWJZLXBRYw?oc=5
- 推理链：
  1. fifwc-bra-nor-2026-07-05-total-2pt5 是 巴西 vs 挪威 的总进球盘口；模型用 BTTS、球队进球线和同场大小球阶梯检查总进球分布，得到 巴西 vs 挪威：总进球大小 2.5 / 大 模型概率 58.5%。
  2. 市场参考概率为 54.5%，结构化 edge 为 +4.0%；该 edge 来自同场盘口阶梯一致性，而不是外部硬统计断言。
  3. 如果 BTTS 或球队进球线临场反向移动，fifwc-bra-nor-2026-07-05-total-2pt5 的总进球信号失效。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 巴西 vs 挪威 | fifwc-bra-nor-2026-07-05-first-half-total-2pt5
- 候选项：巴西 vs 挪威：上半场 大小 2.5 / 大；动作=条件观察；参考方向=大；市场概率=12.5%；模型概率=16.5%；当前 edge=+4.0%；状态=仅观察。
- 证据链：
  1. Polymarket market_slug=fifwc-bra-nor-2026-07-05-first-half-total-2pt5；参考方向市场概率=12.5%；模型概率=16.5%；edge=+4.0%。
  2. 同场盘口结构用于校验：市场类型=totals_lines；比赛=巴西 vs 挪威；候选方向=巴西 vs 挪威：上半场 大小 2.5 / 大。
  3. Brazil vs. Norway in World Cup round of 16: Time, date, preview - USA Today | USA Today | https://news.google.com/rss/articles/CBMiuwFBVV95cUxQNmV4RHBsT2NwTi1nR2dkbUFxck81VXVIR0owaTNJT0JVWVRBd3pUSU5FVXg2RzBfaUxtY0x1TzIxT2NDXzZDRG12dU1NTTBFZmY5d3A3MGhoaUgzeGpiOVdoYVdMUTZNaUx5dzlVY1dNcHZJTUUza3p0V3RoM3NkdVM4ZUZaR3FzcjRQQ3N4emZYYmNWSl9zZnp2ekVFd1NmRjN4Y1ppXzFCc0xRQjQ0WF9mTTZoamI1cWpr?oc=5
  4. 👀 Easy prey? Norway are a tough nut for Brazil: head-to-head - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMiigFBVV95cUxOV3BiZDE0ekRvRFdQWUw1eXZMOHBLcTgyZUpJay0ycHJjdUM1OGhWb1NYME9FTk11WXpPVldJdFkzdmxhT0ZBclR1NTZnREZZandzbkFGcWhkTUxacGYwNmNSWFZKNkF5UTFZTVpNanZwRVNjRU1USDZST01pR3dlaV9ZN3Q5Sl9kZkE?oc=5
  5. Who Is Norway's Next World Cup Opponent? - FOX Sports | FOX Sports | https://news.google.com/rss/articles/CBMigAFBVV95cUxPWU5mcGJrcm5qeG5mLWd4NC1DeXZBT2djdnlZYVdHVjBrN2padnowWEhLOHpheGt2OUZxdnVKXzhiZ205RnZxZ0RSZkVEX3lfencwYUlfYWhLRXloT0s3TUZlVWFiRll2b1dwZEZPUC1pdTRUbl9fQ20yMXI0em4yYtIBgAFBVV95cUxPWlNNZnRBQmtWYTFCRlExUHlOMDlTTndIamh0SVBqbTFwQVlVeWFKNlo2S1ozVUlHS2dDaDF2RFc0NHlYQ2RnNG5obmpNenU3cmgyc3g5YnhDRW1kaWdnaEJ6aWZwaFBlWHAtX3VteHFoeS14bWpKcGx4eWJZLXBRYw?oc=5
- 推理链：
  1. fifwc-bra-nor-2026-07-05-first-half-total-2pt5 是 巴西 vs 挪威 的总进球盘口；模型用 BTTS、球队进球线和同场大小球阶梯检查总进球分布，得到 巴西 vs 挪威：上半场 大小 2.5 / 大 模型概率 16.5%。
  2. 市场参考概率为 12.5%，结构化 edge 为 +4.0%；该 edge 来自同场盘口阶梯一致性，而不是外部硬统计断言。
  3. 如果 BTTS 或球队进球线临场反向移动，fifwc-bra-nor-2026-07-05-first-half-total-2pt5 的总进球信号失效。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 巴西 vs 挪威 | fifwc-bra-nor-2026-07-05-second-half-total-2pt5
- 候选项：巴西 vs 挪威：下半场 大小 2.5 / 大；动作=条件观察；参考方向=大；市场概率=21.0%；模型概率=25.0%；当前 edge=+4.0%；状态=仅观察。
- 证据链：
  1. Polymarket market_slug=fifwc-bra-nor-2026-07-05-second-half-total-2pt5；参考方向市场概率=21.0%；模型概率=25.0%；edge=+4.0%。
  2. 同场盘口结构用于校验：市场类型=totals_lines；比赛=巴西 vs 挪威；候选方向=巴西 vs 挪威：下半场 大小 2.5 / 大。
  3. Brazil vs. Norway in World Cup round of 16: Time, date, preview - USA Today | USA Today | https://news.google.com/rss/articles/CBMiuwFBVV95cUxQNmV4RHBsT2NwTi1nR2dkbUFxck81VXVIR0owaTNJT0JVWVRBd3pUSU5FVXg2RzBfaUxtY0x1TzIxT2NDXzZDRG12dU1NTTBFZmY5d3A3MGhoaUgzeGpiOVdoYVdMUTZNaUx5dzlVY1dNcHZJTUUza3p0V3RoM3NkdVM4ZUZaR3FzcjRQQ3N4emZYYmNWSl9zZnp2ekVFd1NmRjN4Y1ppXzFCc0xRQjQ0WF9mTTZoamI1cWpr?oc=5
  4. 👀 Easy prey? Norway are a tough nut for Brazil: head-to-head - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMiigFBVV95cUxOV3BiZDE0ekRvRFdQWUw1eXZMOHBLcTgyZUpJay0ycHJjdUM1OGhWb1NYME9FTk11WXpPVldJdFkzdmxhT0ZBclR1NTZnREZZandzbkFGcWhkTUxacGYwNmNSWFZKNkF5UTFZTVpNanZwRVNjRU1USDZST01pR3dlaV9ZN3Q5Sl9kZkE?oc=5
  5. Who Is Norway's Next World Cup Opponent? - FOX Sports | FOX Sports | https://news.google.com/rss/articles/CBMigAFBVV95cUxPWU5mcGJrcm5qeG5mLWd4NC1DeXZBT2djdnlZYVdHVjBrN2padnowWEhLOHpheGt2OUZxdnVKXzhiZ205RnZxZ0RSZkVEX3lfencwYUlfYWhLRXloT0s3TUZlVWFiRll2b1dwZEZPUC1pdTRUbl9fQ20yMXI0em4yYtIBgAFBVV95cUxPWlNNZnRBQmtWYTFCRlExUHlOMDlTTndIamh0SVBqbTFwQVlVeWFKNlo2S1ozVUlHS2dDaDF2RFc0NHlYQ2RnNG5obmpNenU3cmgyc3g5YnhDRW1kaWdnaEJ6aWZwaFBlWHAtX3VteHFoeS14bWpKcGx4eWJZLXBRYw?oc=5
- 推理链：
  1. fifwc-bra-nor-2026-07-05-second-half-total-2pt5 是 巴西 vs 挪威 的总进球盘口；模型用 BTTS、球队进球线和同场大小球阶梯检查总进球分布，得到 巴西 vs 挪威：下半场 大小 2.5 / 大 模型概率 25.0%。
  2. 市场参考概率为 21.0%，结构化 edge 为 +4.0%；该 edge 来自同场盘口阶梯一致性，而不是外部硬统计断言。
  3. 如果 BTTS 或球队进球线临场反向移动，fifwc-bra-nor-2026-07-05-second-half-total-2pt5 的总进球信号失效。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 巴西 vs 挪威 | fifwc-bra-nor-2026-07-05-total-3pt5
- 候选项：巴西 vs 挪威：总进球大小 3.5 / 否；动作=条件观察；参考方向=否；市场概率=67.5%；模型概率=63.5%；当前 edge=-4.0%；状态=仅观察。
- 证据链：
  1. Polymarket market_slug=fifwc-bra-nor-2026-07-05-total-3pt5；参考方向市场概率=67.5%；模型概率=63.5%；edge=-4.0%。
  2. 同场盘口结构用于校验：市场类型=totals_lines；比赛=巴西 vs 挪威；候选方向=巴西 vs 挪威：总进球大小 3.5 / 否。
  3. Brazil vs. Norway in World Cup round of 16: Time, date, preview - USA Today | USA Today | https://news.google.com/rss/articles/CBMiuwFBVV95cUxQNmV4RHBsT2NwTi1nR2dkbUFxck81VXVIR0owaTNJT0JVWVRBd3pUSU5FVXg2RzBfaUxtY0x1TzIxT2NDXzZDRG12dU1NTTBFZmY5d3A3MGhoaUgzeGpiOVdoYVdMUTZNaUx5dzlVY1dNcHZJTUUza3p0V3RoM3NkdVM4ZUZaR3FzcjRQQ3N4emZYYmNWSl9zZnp2ekVFd1NmRjN4Y1ppXzFCc0xRQjQ0WF9mTTZoamI1cWpr?oc=5
  4. 👀 Easy prey? Norway are a tough nut for Brazil: head-to-head - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMiigFBVV95cUxOV3BiZDE0ekRvRFdQWUw1eXZMOHBLcTgyZUpJay0ycHJjdUM1OGhWb1NYME9FTk11WXpPVldJdFkzdmxhT0ZBclR1NTZnREZZandzbkFGcWhkTUxacGYwNmNSWFZKNkF5UTFZTVpNanZwRVNjRU1USDZST01pR3dlaV9ZN3Q5Sl9kZkE?oc=5
  5. Who Is Norway's Next World Cup Opponent? - FOX Sports | FOX Sports | https://news.google.com/rss/articles/CBMigAFBVV95cUxPWU5mcGJrcm5qeG5mLWd4NC1DeXZBT2djdnlZYVdHVjBrN2padnowWEhLOHpheGt2OUZxdnVKXzhiZ205RnZxZ0RSZkVEX3lfencwYUlfYWhLRXloT0s3TUZlVWFiRll2b1dwZEZPUC1pdTRUbl9fQ20yMXI0em4yYtIBgAFBVV95cUxPWlNNZnRBQmtWYTFCRlExUHlOMDlTTndIamh0SVBqbTFwQVlVeWFKNlo2S1ozVUlHS2dDaDF2RFc0NHlYQ2RnNG5obmpNenU3cmgyc3g5YnhDRW1kaWdnaEJ6aWZwaFBlWHAtX3VteHFoeS14bWpKcGx4eWJZLXBRYw?oc=5
- 推理链：
  1. fifwc-bra-nor-2026-07-05-total-3pt5 是 巴西 vs 挪威 的总进球盘口；模型用 BTTS、球队进球线和同场大小球阶梯检查总进球分布，得到 巴西 vs 挪威：总进球大小 3.5 / 否 模型概率 63.5%。
  2. 市场参考概率为 67.5%，结构化 edge 为 -4.0%；该 edge 来自同场盘口阶梯一致性，而不是外部硬统计断言。
  3. 如果 BTTS 或球队进球线临场反向移动，fifwc-bra-nor-2026-07-05-total-3pt5 的总进球信号失效。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。
