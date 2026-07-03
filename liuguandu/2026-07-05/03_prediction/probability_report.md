# 概率预测报告

- 报告日期: 2026-07-05
- 比赛日期字段: 2026-07-04
- 模型模式: baseline_fallback / structural_edge
- 治理规则: 无证据，不编故事；有结构化盘口 edge 时允许小仓限价，而不是全部跳过。
- 已应用教训: 胜率与让分穿盘概率分开；保留弱势方进球路径；缺少确认首发/硬技术数据时限制仓位而不是压平所有预测。

## 覆盖审计
- 已解析请求数: 6
- 缺失请求数: 0
- 已选盘口类型数量: {"match_1x2": 6, "first_team_to_score": 6, "totals_lines": 30, "btts": 6, "team_total_lines": 28, "spread_lines": 20}

## 加拿大 vs 摩洛哥 [fifwc-can-mar-2026-07-04]

### 共享信息源
1. Canada and Morocco will play in Houston on July 4 for the city’s final World Cup match - Houston Public Media | Houston Public Media | https://news.google.com/rss/articles/CBMi0gFBVV95cUxNSWdJMFVTVnRVVTQ4YUItcmtpcS11LXVXaEtrVHdhMUUyYV9nNXJLRmlUN1Q0Y0tDOHN2UDl1UkZ0eHFKT3BZYWlDRWZEQTVjbDJaUldZdG40NzctVjR2SkVqZzFiWUp3czlvUUctUEN2WFlxOEMyUVpsNWZqZmpmajBCeEk1MEVGQU9nZEt2V0w2R1RidU1LTGZ5UkFoUjhrdTdKRk55aUpnQjZjMDVaOUU0U3dfMHB2X0paaDhyY21JTDUyMVBWT24tdHVfcG5fVlHSAdoBQVVfeXFMTmtUWTMyX2EwLXdlMHo0WHpXMzZtYjhmRXlVRlNhQjhTRkF2YUpGckxCdlprNWpuVTRlVDdndFQ1dEZOOVpfTERpdHBxSm04T0dpTHNjT1h4dGltVk9FOUVNTmNoaVRfRVdhak5YbzI5bWtrQlpuOUJyc3lZVmFJR3ItTzdWNERMVm9HT3hWVU8tcTFwSzUweTZJZkhYQXNBcmV4anZ3YTBOSlBkZG8yckZ6NExBRjFSeTJBalA3TjdfYkJlQktYdU03Yjl4cVhDeWd0ODFBV2JaSHc?oc=5
2. FIFA World Cup 2026: How to watch Canada vs Morocco in the round of 16 – head-to-head, full schedule - olympics.com | olympics.com | https://news.google.com/rss/articles/CBMinAFBVV95cUxOc1d5OVAxSUNLSTEtREJVMng3cnNxVFpkRk5VckV2eHdBSHpsc2ZCYVptN19JYXJLZFFRbUxOTjVrVjczWmpIbDBjR3E1RDNORU9rcjVvT1lkNWJudU44UVdyd0pvYV9WbWl4VzdNUzJFT09DalRZeU94S0l0ckxfZFBONlhzdkVIXzRHVS1EM3NObnhONHQzcHQ0N1Q?oc=5
3. How can Canada upset Morocco in the World Cup round of 16? - The Athletic - The New York Times | The New York Times | https://news.google.com/rss/articles/CBMimgFBVV95cUxNMWg5OUVHOFhaNVk2eTVoNVNrT3BfMTBSdm8tVWEwWlliMVZNS1dCclVtWGk4NWZ1d202bm81UzZsc2ljSWwwUU1zeTdZbFNxQm1WVEUyVXZxZzNLVXRXaWtNNHhYR29sblktdk05X3FZY1I1ZmJMN1M2QU1nV0ZYUk9IRGpYVlBMbFFoMzROcGZrMV9IMk40ejN3?oc=5
4. How to buy Morocco vs. Canada round of 16 World Cup soccer tickets - USA Today | USA Today | https://news.google.com/rss/articles/CBMi3AFBVV95cUxPYllKeGwtd0F0R3lOQ3JGdF9ENDBUanV0NVBGbUV1M3VNMEJTX1lTbXZnYzVuekl0dXpyYlliQjg4N29ZclZoVGU5aGhEcDBYYWp3T3kwZmVPM1VDX1VJaG5WQm5Ja2VaNWw0a29vS2pTZjc3aS1WaFg5bkRmR3lKeDdwbmpSTF9wYkN5NXNwMWlJc1B5YXdLLTNidkFSeUI2cDhoaC1PbE0wdTRpbDZLdXZzOHBCSUZCNmZtbzRfazhDMDJUUlNYUGZtaDhGdUZrcm54MkZ1WUszUTNp?oc=5
5. 2026 FIFA World Cup match schedule: Fixtures, results, features - ESPN | ESPN | https://news.google.com/rss/articles/CBMi0AFBVV95cUxNazBRZDFsYjkyM1lXUGRBZzU2c3FfaHdOTWNtTUZGMWZhR1FCdDd1LTJ5U0VBN1FHbFZWRndrMzZVUTNGUFZqa3A5U3pLT1lreXNMZllmU2pPQUFFOGhCTEJoZHlnWFM3VU1xM0ZxNWJiZG4zMTA5OTZqQUlzUGp3Zm1tSXpWeGViTEFvdUVaaTgtcVdUTnZqX2F3eFdKWnNsTHBFRUl3OVVxTF91TE5udTZlNVF5UTFoU2hpdjJjSDdKZE5JNV9XNENMS290NWtu?oc=5

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
| fifwc-can-mar-2026-07-04-draw | 加拿大 vs 摩洛哥 会打平吗？ | 是 | 27.5% | 27.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-mar | 摩洛哥 会在 2026-07-04 获胜吗？ | 是 | 54.5% | 54.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-can | 加拿大 会在 2026-07-04 获胜吗？ | 是 | 18.5% | 18.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |

### 让分盘
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-can-mar-2026-07-04-spread-home-1pt5 | 让分：加拿大 (-1.5) | 加拿大 | 5.5% | 5.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-spread-away-1pt5 | 让分：摩洛哥 (-1.5) | 摩洛哥 | 27.5% | 27.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-spread-home-2pt5 | 让分：加拿大 (-2.5) | 加拿大 | 1.4% | 3.4% | +2.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-can-mar-2026-07-04-spread-away-2pt5 | 让分：摩洛哥 (-2.5) | 摩洛哥 | 10.5% | 6.0% | -4.5% | 偏低+ | 仅观察 | baseline edge 需要首发确认 |
| fifwc-can-mar-2026-07-04-spread-home-3pt5 | 让分：加拿大 (-3.5) | 加拿大 | 0.5% | 2.6% | +2.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-can-mar-2026-07-04-spread-away-3pt5 | 让分：摩洛哥 (-3.5) | 摩洛哥 | 4.1% | 0.1% | -4.0% | 偏低+ | 仅观察 | baseline edge 需要首发确认 |
| fifwc-can-mar-2026-07-04-spread-home-4pt5 | 让分：加拿大 (-4.5) | 加拿大 | 0.5% | 2.6% | +2.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-can-mar-2026-07-04-spread-away-4pt5 | 让分：摩洛哥 (-4.5) | 摩洛哥 | 1.1% | 0.1% | -1.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-can-mar-2026-07-04-spread-home-5pt5 | 让分：加拿大 (-5.5) | 加拿大 | 0.1% | 2.1% | +2.0% | 低 | 跳过 | 价格过于极端 |
| fifwc-can-mar-2026-07-04-spread-away-5pt5 | 让分：摩洛哥 (-5.5) | 摩洛哥 | 0.5% | 0.1% | -0.4% | 偏低+ | 跳过 | 价格过于极端 |

### 总进球盘
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-can-mar-2026-07-04-total-3pt5 | 加拿大 vs 摩洛哥：总进球大小 3.5 | 大 | 20.5% | 20.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-total-4pt5 | 加拿大 vs 摩洛哥：总进球大小 4.5 | 大 | 8.5% | 8.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-total-6pt5 | 加拿大 vs 摩洛哥：总进球大小 6.5 | 大 | 1.5% | 0.1% | -1.4% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-can-mar-2026-07-04-total-8pt5 | 加拿大 vs 摩洛哥：总进球大小 8.5 | 大 | 0.4% | 0.1% | -0.2% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-can-mar-2026-07-04-total-0pt5 | 加拿大 vs 摩洛哥：总进球大小 0.5 | 大 | 90.0% | 92.0% | +2.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-total-1pt5 | 加拿大 vs 摩洛哥：总进球大小 1.5 | 大 | 67.5% | 69.5% | +2.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-total-2pt5 | 加拿大 vs 摩洛哥：总进球大小 2.5 | 大 | 40.5% | 40.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-total-5pt5 | 加拿大 vs 摩洛哥：总进球大小 5.5 | 大 | 3.1% | 0.1% | -3.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-total-7pt5 | 加拿大 vs 摩洛哥：总进球大小 7.5 | 大 | 0.5% | 0.1% | -0.4% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-can-mar-2026-07-04-first-half-total-0pt5 | 加拿大 vs 摩洛哥：上半场 大小 0.5 | 大 | 64.5% | 66.5% | +2.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-first-half-total-1pt5 | 加拿大 vs 摩洛哥：上半场 大小 1.5 | 大 | 28.0% | 30.0% | +2.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-first-half-total-2pt5 | 加拿大 vs 摩洛哥：上半场 大小 2.5 | 大 | 9.0% | 9.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-second-half-total-0pt5 | 加拿大 vs 摩洛哥：下半场 大小 0.5 | 大 | 73.0% | 75.0% | +2.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-second-half-total-1pt5 | 加拿大 vs 摩洛哥：下半场 大小 1.5 | 大 | 38.0% | 40.0% | +2.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-second-half-total-2pt5 | 加拿大 vs 摩洛哥：下半场 大小 2.5 | 大 | 15.0% | 15.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 双方均进球
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-can-mar-2026-07-04-btts | 加拿大 vs 摩洛哥: 双方均进球 | 是 | 45.5% | 49.0% | +3.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-btts-first-half | 加拿大 vs 摩洛哥: 上半场双方均进球 | 是 | 16.0% | 16.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-btts-second-half | 加拿大 vs 摩洛哥: 下半场双方均进球 | 是 | 23.5% | 23.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 首支进球队伍
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-can-mar-2026-07-04-first-to-score-home | 加拿大 会先于 摩洛哥 进球吗？ | 是 | 30.5% | 28.0% | -2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-first-to-score-away | 摩洛哥 会先于 加拿大 进球吗？ | 是 | 60.5% | 60.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-first-to-score-neither | 加拿大 vs 摩洛哥: 无球队先进球? | 是 | 10.0% | 6.5% | -3.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 球队进球数
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-can-mar-2026-07-04-second-half-team-total-home-1pt5 | 加拿大 vs 摩洛哥：加拿大 下半场 大小 1.5 | 大 | 9.0% | 9.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-second-half-team-total-away-0pt5 | 加拿大 vs 摩洛哥：摩洛哥 下半场 大小 0.5 | 大 | 58.5% | 61.0% | +2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-second-half-team-total-away-1pt5 | 加拿大 vs 摩洛哥：摩洛哥 下半场 大小 1.5 | 大 | 21.5% | 21.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-team-total-home-0pt5 | 加拿大 vs 摩洛哥：加拿大 大小 0.5 | 大 | 56.5% | 56.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-team-total-home-1pt5 | 加拿大 vs 摩洛哥：加拿大 大小 1.5 | 大 | 18.5% | 18.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-team-total-home-2pt5 | 加拿大 vs 摩洛哥：加拿大 大小 2.5 | 大 | 5.0% | 1.5% | -3.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-team-total-away-0pt5 | 加拿大 vs 摩洛哥：摩洛哥 大小 0.5 | 大 | 80.0% | 82.5% | +2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-team-total-away-1pt5 | 加拿大 vs 摩洛哥：摩洛哥 大小 1.5 | 大 | 45.0% | 45.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-team-total-away-2pt5 | 加拿大 vs 摩洛哥：摩洛哥 大小 2.5 | 大 | 20.0% | 16.5% | -3.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-first-half-team-total-home-0pt5 | 加拿大 vs 摩洛哥：加拿大 上半场 大小 0.5 | 大 | 31.5% | 31.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-first-half-team-total-home-1pt5 | 加拿大 vs 摩洛哥：加拿大 上半场 大小 1.5 | 大 | 5.0% | 5.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-first-half-team-total-away-0pt5 | 加拿大 vs 摩洛哥：摩洛哥 上半场 大小 0.5 | 大 | 50.0% | 52.5% | +2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-first-half-team-total-away-1pt5 | 加拿大 vs 摩洛哥：摩洛哥 上半场 大小 1.5 | 大 | 14.5% | 14.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-can-mar-2026-07-04-second-half-team-total-home-0pt5 | 加拿大 vs 摩洛哥：加拿大 下半场 大小 0.5 | 大 | 38.5% | 38.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

## 巴拉圭 vs 法国 [fifwc-par-fra-2026-07-04]

### 共享信息源
1. France vs. Paraguay in World Cup round of 16: Time, date, what to know - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMigwFBVV95cUxPZk9zUGUwSExTbFQxS1NrSm55VFRiS21qNmtDX1ltd0VHa2hKY2RtMFhtaFdoTVhUcjhQcG81MEZPV21CUmRZMWw5dk5kNE1nbmJRYm5lTzJKSmM1ZFg4OHFWQjVvcUFMX0FyS0wwNDRZeFBFOGs3cW4wLVBkSVFDbzlXWQ?oc=5
2. Philadelphia to host France and Paraguay for Round of 16 clash on July 4th - Philadelphia Union | Philadelphia Union | https://news.google.com/rss/articles/CBMiswFBVV95cUxQS1BRbGZQWDVwNE5UbV9keHdzeHFrMVBPNUtlQ0ZDM0pCY2Y1QjBJU1pQRmQxVmxwbnhKMlVETkQ4bEZsbjBneloyVURPYnVFTS1HcGdXS1BCQ3BLdkNlb1BlTEFoU3Z4YXkzZTJKZFpmb1hxUWhOMXQ5UzlHVnFXV09UXzZxUkRha1FSXzl4TjNyUmJwc2tjMmxOcW1uM3dNUE5iMlJNY0s3ZWlsamRJMUFwUQ?oc=5
3. How to buy France vs. Paraguay round of 16 World Cup soccer tickets - USA Today | USA Today | https://news.google.com/rss/articles/CBMi0wFBVV95cUxQRng4ZFJqb0ZHSkhtMnBFRGIxRGE3TzVsRjlsUm9HNEx0bFVvdHhQd2hueXZYX0ZIZnJjQnYtYW1aeFltOWNYSEd2RWlNaXlpZnBtRmNuZWtZbUt6Wllpc1ZJVi1yWkFVX1RnYjNaTnAwdk4xb2I5WEhZWkxRWng3QWowTEpwTXRSZ1pGSGhVM1NhTXhuQ3pUYWdnenVDX2VFck9FZEVuc2JydHNLaGV1Qk1INDQ4VGtLVnd5SjZqSmpMUFNxZHRLZF9pcU41MHp3TEEw?oc=5
4. Opening odds for Paraguay vs. France in the FIFA 2026 World Cup - DraftKings Network | DraftKings Network | https://news.google.com/rss/articles/CBMiqwFBVV95cUxPUVBacEo3YXVaRzZ2dVZhLU13RmFRenF6STZfbUNTT0Zpd1NMRnZkenpLM0dlNzdTYlh1bmRWUEdvREFGZGJ2aVV2TVRFWWk1NU1Va0l0QU96b0dQZGItQ2YyZEFNeUx5V2VoX1phenBQRVVuWTJQNnBKRWpVa05WRk45dmJjZGFoSFZPZTZmOVJJNE1jd01IZ1FCOWhWckxIMmR0MkctN0JMVUU?oc=5
5. Paraguay vs France: Date, kickoff time and venue for 2026 World Cup Round of 16 clash - World Soccer Talk | World Soccer Talk | https://news.google.com/rss/articles/CBMivwFBVV95cUxQc0t5SFRiUkpvVjdHckxMYVk5WUxrX0JNVk4yUTVQNlJUZkFCYmRQckZzVlhRd0Vhb250SkVxZXRGSDdfeGhjOGJ4am5vbVJkUGgwVFE3WFl3NTVlZVFxbDZjeWhPd0F4dEdINjBpM19fTHJGT2xJNU85RnhTSEF3RlNCM1NSOVJvUnk3Rms5XzE1ZjdFSWhHcEhISGdBWnhQdVhEQ2Y1WFczWWVBbjZRcjJXSEkyVmNYWXhzREdVONIBwwFBVV95cUxNeXdwNVdPLVRyRUw3SEI5M0IxWkd0UkFVRWdkQ3c5eS1kSXRLd3piLTZ0ZUJvWUhRbXJ5RTR3UFhkTk1NcnRlRTJsR0JuemJtejMyX2Y2OVE5a3p6ZXc1ajZReWo0ZnhmbmVrc1hJVFVIUmNOQTFQWUs5NTNPbGdnMUlvN2ZVSks1M1czOGNMRlNtXzhWYkd6OF9SU2FxVFVVdURvY3hZZXUyNlhRSkFKM2FRRW5KMHFYMU1GMVdhR1M4akU?oc=5

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
| fifwc-par-fra-2026-07-04-draw | 巴拉圭 vs 法国 会打平吗？ | 是 | 12.5% | 13.0% | +0.5% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-par | 巴拉圭 会在 2026-07-04 获胜吗？ | 是 | 4.5% | 2.0% | -2.5% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-fra | 法国 会在 2026-07-04 获胜吗？ | 是 | 83.5% | 86.0% | +2.5% | 中低 | 跳过 | edge 低于 4 个百分点 |

### 让分盘
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-par-fra-2026-07-04-spread-home-1pt5 | 让分：巴拉圭 (-1.5) | 巴拉圭 | 0.9% | 0.9% | +0.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-par-fra-2026-07-04-spread-away-1pt5 | 让分：法国 (-1.5) | 法国 | 61.5% | 67.0% | +5.5% | 中低 | 小仓限价 | 结构化 edge，小仓限价 |
| fifwc-par-fra-2026-07-04-spread-home-2pt5 | 让分：巴拉圭 (-2.5) | 巴拉圭 | 0.4% | 2.4% | +2.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-par-fra-2026-07-04-spread-away-2pt5 | 让分：法国 (-2.5) | 法国 | 37.5% | 33.0% | -4.5% | 中低 | 仅观察 | baseline edge 需要首发确认 |
| fifwc-par-fra-2026-07-04-spread-home-3pt5 | 让分：巴拉圭 (-3.5) | 巴拉圭 | 0.5% | 2.5% | +2.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-par-fra-2026-07-04-spread-away-3pt5 | 让分：法国 (-3.5) | 法国 | 18.5% | 13.4% | -5.1% | 偏低+ | 小仓限价 | 结构化 edge，小仓限价 |
| fifwc-par-fra-2026-07-04-spread-home-4pt5 | 让分：巴拉圭 (-4.5) | 巴拉圭 | 0.3% | 2.3% | +2.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-par-fra-2026-07-04-spread-away-4pt5 | 让分：法国 (-4.5) | 法国 | 8.5% | 2.8% | -5.7% | 偏低+ | 小仓限价 | 结构化 edge，小仓限价 |
| fifwc-par-fra-2026-07-04-spread-home-5pt5 | 让分：巴拉圭 (-5.5) | 巴拉圭 | 0.2% | 2.2% | +2.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-par-fra-2026-07-04-spread-away-5pt5 | 让分：法国 (-5.5) | 法国 | 4.0% | 0.1% | -3.9% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 总进球盘
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-par-fra-2026-07-04-total-0pt5 | 巴拉圭 vs 法国：总进球大小 0.5 | 大 | 96.0% | 96.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-total-1pt5 | 巴拉圭 vs 法国：总进球大小 1.5 | 大 | 81.5% | 81.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-total-2pt5 | 巴拉圭 vs 法国：总进球大小 2.5 | 大 | 58.5% | 56.0% | -2.5% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-total-3pt5 | 巴拉圭 vs 法国：总进球大小 3.5 | 大 | 36.5% | 36.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-total-4pt5 | 巴拉圭 vs 法国：总进球大小 4.5 | 大 | 19.0% | 19.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-total-5pt5 | 巴拉圭 vs 法国：总进球大小 5.5 | 大 | 8.5% | 4.0% | -4.5% | 偏低+ | 仅观察 | baseline edge 需要首发确认 |
| fifwc-par-fra-2026-07-04-total-6pt5 | 巴拉圭 vs 法国：总进球大小 6.5 | 大 | 3.0% | 0.1% | -2.9% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-total-7pt5 | 巴拉圭 vs 法国：总进球大小 7.5 | 大 | 1.5% | 0.1% | -1.4% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-par-fra-2026-07-04-total-8pt5 | 巴拉圭 vs 法国：总进球大小 8.5 | 大 | 0.5% | 0.1% | -0.4% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-par-fra-2026-07-04-first-half-total-0pt5 | 巴拉圭 vs 法国：上半场 大小 0.5 | 大 | 74.0% | 74.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-first-half-total-1pt5 | 巴拉圭 vs 法国：上半场 大小 1.5 | 大 | 37.5% | 37.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-first-half-total-2pt5 | 巴拉圭 vs 法国：上半场 大小 2.5 | 大 | 16.0% | 13.5% | -2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-second-half-total-0pt5 | 巴拉圭 vs 法国：下半场 大小 0.5 | 大 | 82.0% | 82.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-second-half-total-1pt5 | 巴拉圭 vs 法国：下半场 大小 1.5 | 大 | 51.0% | 51.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-second-half-total-2pt5 | 巴拉圭 vs 法国：下半场 大小 2.5 | 大 | 24.5% | 22.0% | -2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 双方均进球
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-par-fra-2026-07-04-btts | 巴拉圭 vs 法国: 双方均进球 | 是 | 36.5% | 36.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-btts-first-half | 巴拉圭 vs 法国: 上半场双方均进球 | 是 | 13.5% | 13.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-btts-second-half | 巴拉圭 vs 法国: 下半场双方均进球 | 是 | 20.5% | 20.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 首支进球队伍
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-par-fra-2026-07-04-first-to-score-home | 巴拉圭 会先于 法国 进球吗？ | 是 | 13.5% | 11.0% | -2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-first-to-score-away | 法国 会先于 巴拉圭 进球吗？ | 是 | 83.5% | 83.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-first-to-score-neither | 巴拉圭 vs 法国: 无球队先进球? | 是 | 4.2% | 0.6% | -3.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 球队进球数
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-par-fra-2026-07-04-team-total-home-0pt5 | 巴拉圭 vs 法国：巴拉圭 大小 0.5 | 大 | 38.0% | 38.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-team-total-home-1pt5 | 巴拉圭 vs 法国：巴拉圭 大小 1.5 | 大 | 7.5% | 7.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-team-total-home-2pt5 | 巴拉圭 vs 法国：巴拉圭 大小 2.5 | 大 | 2.2% | 0.1% | -2.1% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-team-total-away-0pt5 | 巴拉圭 vs 法国：法国 大小 0.5 | 大 | 93.0% | 93.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-team-total-away-1pt5 | 巴拉圭 vs 法国：法国 大小 1.5 | 大 | 74.0% | 74.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-team-total-away-2pt5 | 巴拉圭 vs 法国：法国 大小 2.5 | 大 | 48.0% | 44.5% | -3.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-first-half-team-total-home-0pt5 | 巴拉圭 vs 法国：巴拉圭 上半场 大小 0.5 | 大 | 20.0% | 20.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-first-half-team-total-home-1pt5 | 巴拉圭 vs 法国：巴拉圭 上半场 大小 1.5 | 大 | 2.3% | 2.3% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-first-half-team-total-away-0pt5 | 巴拉圭 vs 法国：法国 上半场 大小 0.5 | 大 | 68.5% | 71.0% | +2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-first-half-team-total-away-1pt5 | 巴拉圭 vs 法国：法国 上半场 大小 1.5 | 大 | 31.5% | 36.5% | +5.0% | 偏低+ | 小仓限价 | 结构化 edge，小仓限价 |
| fifwc-par-fra-2026-07-04-second-half-team-total-home-0pt5 | 巴拉圭 vs 法国：巴拉圭 下半场 大小 0.5 | 大 | 26.5% | 26.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-second-half-team-total-home-1pt5 | 巴拉圭 vs 法国：巴拉圭 下半场 大小 1.5 | 大 | 4.5% | 4.5% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-second-half-team-total-away-0pt5 | 巴拉圭 vs 法国：法国 下半场 大小 0.5 | 大 | 77.0% | 79.5% | +2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-par-fra-2026-07-04-second-half-team-total-away-1pt5 | 巴拉圭 vs 法国：法国 下半场 大小 1.5 | 大 | 42.5% | 47.5% | +5.0% | 偏低+ | 小仓限价 | 结构化 edge，小仓限价 |

## 策略观察项详细证据
### 巴拉圭 vs 法国 | fifwc-par-fra-2026-07-04-spread-away-4pt5
- 候选项：让分：法国 (-4.5) / 否；动作=小仓限价买入；参考方向=否；市场概率=91.5%；模型概率=97.2%；当前 edge=+5.7%；状态=小仓限价。
- 证据链：
  1. Polymarket market_slug=fifwc-par-fra-2026-07-04-spread-away-4pt5；参考方向市场概率=91.5%；模型概率=97.2%；edge=+5.7%。
  2. 同场盘口结构用于校验：市场类型=spread_lines；比赛=巴拉圭 vs 法国；候选方向=让分：法国 (-4.5) / 否。
  3. France vs. Paraguay in World Cup round of 16: Time, date, what to know - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMigwFBVV95cUxPZk9zUGUwSExTbFQxS1NrSm55VFRiS21qNmtDX1ltd0VHa2hKY2RtMFhtaFdoTVhUcjhQcG81MEZPV21CUmRZMWw5dk5kNE1nbmJRYm5lTzJKSmM1ZFg4OHFWQjVvcUFMX0FyS0wwNDRZeFBFOGs3cW4wLVBkSVFDbzlXWQ?oc=5
  4. Philadelphia to host France and Paraguay for Round of 16 clash on July 4th - Philadelphia Union | Philadelphia Union | https://news.google.com/rss/articles/CBMiswFBVV95cUxQS1BRbGZQWDVwNE5UbV9keHdzeHFrMVBPNUtlQ0ZDM0pCY2Y1QjBJU1pQRmQxVmxwbnhKMlVETkQ4bEZsbjBneloyVURPYnVFTS1HcGdXS1BCQ3BLdkNlb1BlTEFoU3Z4YXkzZTJKZFpmb1hxUWhOMXQ5UzlHVnFXV09UXzZxUkRha1FSXzl4TjNyUmJwc2tjMmxOcW1uM3dNUE5iMlJNY0s3ZWlsamRJMUFwUQ?oc=5
  5. How to buy France vs. Paraguay round of 16 World Cup soccer tickets - USA Today | USA Today | https://news.google.com/rss/articles/CBMi0wFBVV95cUxQRng4ZFJqb0ZHSkhtMnBFRGIxRGE3TzVsRjlsUm9HNEx0bFVvdHhQd2hueXZYX0ZIZnJjQnYtYW1aeFltOWNYSEd2RWlNaXlpZnBtRmNuZWtZbUt6Wllpc1ZJVi1yWkFVX1RnYjNaTnAwdk4xb2I5WEhZWkxRWng3QWowTEpwTXRSZ1pGSGhVM1NhTXhuQ3pUYWdnenVDX2VFck9FZEVuc2JydHNLaGV1Qk1INDQ4VGtLVnd5SjZqSmpMUFNxZHRLZF9pcU41MHp3TEEw?oc=5
- 推理链：
  1. fifwc-par-fra-2026-07-04-spread-away-4pt5 是 巴拉圭 vs 法国 的让分盘口；模型把胜平负优势和净胜球分布拆开处理，因此 让分：法国 (-4.5) / 否 的市场概率 91.5% 与模型概率 97.2% 出现偏差。
  2. 该信号 edge 为 +5.7%，核心判断是当前让分价格相对胜率分布偏离，而不是把胜率直接等同于穿盘率。
  3. 如果临场价格移动超过 4 个百分点或首发改变净胜球路径，fifwc-par-fra-2026-07-04-spread-away-4pt5 需要降级为观察。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 巴拉圭 vs 法国 | fifwc-par-fra-2026-07-04-spread-away-1pt5
- 候选项：让分：法国 (-1.5) / 法国；动作=小仓限价买入；参考方向=法国；市场概率=61.5%；模型概率=67.0%；当前 edge=+5.5%；状态=小仓限价。
- 证据链：
  1. Polymarket market_slug=fifwc-par-fra-2026-07-04-spread-away-1pt5；参考方向市场概率=61.5%；模型概率=67.0%；edge=+5.5%。
  2. 同场盘口结构用于校验：市场类型=spread_lines；比赛=巴拉圭 vs 法国；候选方向=让分：法国 (-1.5) / 法国。
  3. France vs. Paraguay in World Cup round of 16: Time, date, what to know - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMigwFBVV95cUxPZk9zUGUwSExTbFQxS1NrSm55VFRiS21qNmtDX1ltd0VHa2hKY2RtMFhtaFdoTVhUcjhQcG81MEZPV21CUmRZMWw5dk5kNE1nbmJRYm5lTzJKSmM1ZFg4OHFWQjVvcUFMX0FyS0wwNDRZeFBFOGs3cW4wLVBkSVFDbzlXWQ?oc=5
  4. Philadelphia to host France and Paraguay for Round of 16 clash on July 4th - Philadelphia Union | Philadelphia Union | https://news.google.com/rss/articles/CBMiswFBVV95cUxQS1BRbGZQWDVwNE5UbV9keHdzeHFrMVBPNUtlQ0ZDM0pCY2Y1QjBJU1pQRmQxVmxwbnhKMlVETkQ4bEZsbjBneloyVURPYnVFTS1HcGdXS1BCQ3BLdkNlb1BlTEFoU3Z4YXkzZTJKZFpmb1hxUWhOMXQ5UzlHVnFXV09UXzZxUkRha1FSXzl4TjNyUmJwc2tjMmxOcW1uM3dNUE5iMlJNY0s3ZWlsamRJMUFwUQ?oc=5
  5. How to buy France vs. Paraguay round of 16 World Cup soccer tickets - USA Today | USA Today | https://news.google.com/rss/articles/CBMi0wFBVV95cUxQRng4ZFJqb0ZHSkhtMnBFRGIxRGE3TzVsRjlsUm9HNEx0bFVvdHhQd2hueXZYX0ZIZnJjQnYtYW1aeFltOWNYSEd2RWlNaXlpZnBtRmNuZWtZbUt6Wllpc1ZJVi1yWkFVX1RnYjNaTnAwdk4xb2I5WEhZWkxRWng3QWowTEpwTXRSZ1pGSGhVM1NhTXhuQ3pUYWdnenVDX2VFck9FZEVuc2JydHNLaGV1Qk1INDQ4VGtLVnd5SjZqSmpMUFNxZHRLZF9pcU41MHp3TEEw?oc=5
- 推理链：
  1. fifwc-par-fra-2026-07-04-spread-away-1pt5 是 巴拉圭 vs 法国 的让分盘口；模型把胜平负优势和净胜球分布拆开处理，因此 让分：法国 (-1.5) / 法国 的市场概率 61.5% 与模型概率 67.0% 出现偏差。
  2. 该信号 edge 为 +5.5%，核心判断是当前让分价格相对胜率分布偏离，而不是把胜率直接等同于穿盘率。
  3. 如果临场价格移动超过 4 个百分点或首发改变净胜球路径，fifwc-par-fra-2026-07-04-spread-away-1pt5 需要降级为观察。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 巴拉圭 vs 法国 | fifwc-par-fra-2026-07-04-spread-away-3pt5
- 候选项：让分：法国 (-3.5) / 否；动作=小仓限价买入；参考方向=否；市场概率=81.5%；模型概率=86.6%；当前 edge=+5.1%；状态=小仓限价。
- 证据链：
  1. Polymarket market_slug=fifwc-par-fra-2026-07-04-spread-away-3pt5；参考方向市场概率=81.5%；模型概率=86.6%；edge=+5.1%。
  2. 同场盘口结构用于校验：市场类型=spread_lines；比赛=巴拉圭 vs 法国；候选方向=让分：法国 (-3.5) / 否。
  3. France vs. Paraguay in World Cup round of 16: Time, date, what to know - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMigwFBVV95cUxPZk9zUGUwSExTbFQxS1NrSm55VFRiS21qNmtDX1ltd0VHa2hKY2RtMFhtaFdoTVhUcjhQcG81MEZPV21CUmRZMWw5dk5kNE1nbmJRYm5lTzJKSmM1ZFg4OHFWQjVvcUFMX0FyS0wwNDRZeFBFOGs3cW4wLVBkSVFDbzlXWQ?oc=5
  4. Philadelphia to host France and Paraguay for Round of 16 clash on July 4th - Philadelphia Union | Philadelphia Union | https://news.google.com/rss/articles/CBMiswFBVV95cUxQS1BRbGZQWDVwNE5UbV9keHdzeHFrMVBPNUtlQ0ZDM0pCY2Y1QjBJU1pQRmQxVmxwbnhKMlVETkQ4bEZsbjBneloyVURPYnVFTS1HcGdXS1BCQ3BLdkNlb1BlTEFoU3Z4YXkzZTJKZFpmb1hxUWhOMXQ5UzlHVnFXV09UXzZxUkRha1FSXzl4TjNyUmJwc2tjMmxOcW1uM3dNUE5iMlJNY0s3ZWlsamRJMUFwUQ?oc=5
  5. How to buy France vs. Paraguay round of 16 World Cup soccer tickets - USA Today | USA Today | https://news.google.com/rss/articles/CBMi0wFBVV95cUxQRng4ZFJqb0ZHSkhtMnBFRGIxRGE3TzVsRjlsUm9HNEx0bFVvdHhQd2hueXZYX0ZIZnJjQnYtYW1aeFltOWNYSEd2RWlNaXlpZnBtRmNuZWtZbUt6Wllpc1ZJVi1yWkFVX1RnYjNaTnAwdk4xb2I5WEhZWkxRWng3QWowTEpwTXRSZ1pGSGhVM1NhTXhuQ3pUYWdnenVDX2VFck9FZEVuc2JydHNLaGV1Qk1INDQ4VGtLVnd5SjZqSmpMUFNxZHRLZF9pcU41MHp3TEEw?oc=5
- 推理链：
  1. fifwc-par-fra-2026-07-04-spread-away-3pt5 是 巴拉圭 vs 法国 的让分盘口；模型把胜平负优势和净胜球分布拆开处理，因此 让分：法国 (-3.5) / 否 的市场概率 81.5% 与模型概率 86.6% 出现偏差。
  2. 该信号 edge 为 +5.1%，核心判断是当前让分价格相对胜率分布偏离，而不是把胜率直接等同于穿盘率。
  3. 如果临场价格移动超过 4 个百分点或首发改变净胜球路径，fifwc-par-fra-2026-07-04-spread-away-3pt5 需要降级为观察。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 巴拉圭 vs 法国 | fifwc-par-fra-2026-07-04-first-half-team-total-away-1pt5
- 候选项：巴拉圭 vs 法国：法国 上半场 大小 1.5 / 大；动作=小仓限价买入；参考方向=大；市场概率=31.5%；模型概率=36.5%；当前 edge=+5.0%；状态=小仓限价。
- 证据链：
  1. Polymarket market_slug=fifwc-par-fra-2026-07-04-first-half-team-total-away-1pt5；参考方向市场概率=31.5%；模型概率=36.5%；edge=+5.0%。
  2. 同场盘口结构用于校验：市场类型=team_total_lines；比赛=巴拉圭 vs 法国；候选方向=巴拉圭 vs 法国：法国 上半场 大小 1.5 / 大。
  3. France vs. Paraguay in World Cup round of 16: Time, date, what to know - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMigwFBVV95cUxPZk9zUGUwSExTbFQxS1NrSm55VFRiS21qNmtDX1ltd0VHa2hKY2RtMFhtaFdoTVhUcjhQcG81MEZPV21CUmRZMWw5dk5kNE1nbmJRYm5lTzJKSmM1ZFg4OHFWQjVvcUFMX0FyS0wwNDRZeFBFOGs3cW4wLVBkSVFDbzlXWQ?oc=5
  4. Philadelphia to host France and Paraguay for Round of 16 clash on July 4th - Philadelphia Union | Philadelphia Union | https://news.google.com/rss/articles/CBMiswFBVV95cUxQS1BRbGZQWDVwNE5UbV9keHdzeHFrMVBPNUtlQ0ZDM0pCY2Y1QjBJU1pQRmQxVmxwbnhKMlVETkQ4bEZsbjBneloyVURPYnVFTS1HcGdXS1BCQ3BLdkNlb1BlTEFoU3Z4YXkzZTJKZFpmb1hxUWhOMXQ5UzlHVnFXV09UXzZxUkRha1FSXzl4TjNyUmJwc2tjMmxOcW1uM3dNUE5iMlJNY0s3ZWlsamRJMUFwUQ?oc=5
  5. How to buy France vs. Paraguay round of 16 World Cup soccer tickets - USA Today | USA Today | https://news.google.com/rss/articles/CBMi0wFBVV95cUxQRng4ZFJqb0ZHSkhtMnBFRGIxRGE3TzVsRjlsUm9HNEx0bFVvdHhQd2hueXZYX0ZIZnJjQnYtYW1aeFltOWNYSEd2RWlNaXlpZnBtRmNuZWtZbUt6Wllpc1ZJVi1yWkFVX1RnYjNaTnAwdk4xb2I5WEhZWkxRWng3QWowTEpwTXRSZ1pGSGhVM1NhTXhuQ3pUYWdnenVDX2VFck9FZEVuc2JydHNLaGV1Qk1INDQ4VGtLVnd5SjZqSmpMUFNxZHRLZF9pcU41MHp3TEEw?oc=5
- 推理链：
  1. fifwc-par-fra-2026-07-04-first-half-team-total-away-1pt5 是 巴拉圭 vs 法国 的球队进球数盘口；模型用胜平负、BTTS 和该队进球线交叉校验 巴拉圭 vs 法国：法国 上半场 大小 1.5 / 大，模型概率为 36.5%。
  2. 市场参考概率为 31.5%，edge 为 +5.0%；该信号来自球队进球线和比赛层面价格的结构差。
  3. 若该队 0.5/1.5 进球线或 BTTS 临场反向移动，fifwc-par-fra-2026-07-04-first-half-team-total-away-1pt5 需要取消。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 巴拉圭 vs 法国 | fifwc-par-fra-2026-07-04-second-half-team-total-away-1pt5
- 候选项：巴拉圭 vs 法国：法国 下半场 大小 1.5 / 大；动作=小仓限价买入；参考方向=大；市场概率=42.5%；模型概率=47.5%；当前 edge=+5.0%；状态=小仓限价。
- 证据链：
  1. Polymarket market_slug=fifwc-par-fra-2026-07-04-second-half-team-total-away-1pt5；参考方向市场概率=42.5%；模型概率=47.5%；edge=+5.0%。
  2. 同场盘口结构用于校验：市场类型=team_total_lines；比赛=巴拉圭 vs 法国；候选方向=巴拉圭 vs 法国：法国 下半场 大小 1.5 / 大。
  3. France vs. Paraguay in World Cup round of 16: Time, date, what to know - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMigwFBVV95cUxPZk9zUGUwSExTbFQxS1NrSm55VFRiS21qNmtDX1ltd0VHa2hKY2RtMFhtaFdoTVhUcjhQcG81MEZPV21CUmRZMWw5dk5kNE1nbmJRYm5lTzJKSmM1ZFg4OHFWQjVvcUFMX0FyS0wwNDRZeFBFOGs3cW4wLVBkSVFDbzlXWQ?oc=5
  4. Philadelphia to host France and Paraguay for Round of 16 clash on July 4th - Philadelphia Union | Philadelphia Union | https://news.google.com/rss/articles/CBMiswFBVV95cUxQS1BRbGZQWDVwNE5UbV9keHdzeHFrMVBPNUtlQ0ZDM0pCY2Y1QjBJU1pQRmQxVmxwbnhKMlVETkQ4bEZsbjBneloyVURPYnVFTS1HcGdXS1BCQ3BLdkNlb1BlTEFoU3Z4YXkzZTJKZFpmb1hxUWhOMXQ5UzlHVnFXV09UXzZxUkRha1FSXzl4TjNyUmJwc2tjMmxOcW1uM3dNUE5iMlJNY0s3ZWlsamRJMUFwUQ?oc=5
  5. How to buy France vs. Paraguay round of 16 World Cup soccer tickets - USA Today | USA Today | https://news.google.com/rss/articles/CBMi0wFBVV95cUxQRng4ZFJqb0ZHSkhtMnBFRGIxRGE3TzVsRjlsUm9HNEx0bFVvdHhQd2hueXZYX0ZIZnJjQnYtYW1aeFltOWNYSEd2RWlNaXlpZnBtRmNuZWtZbUt6Wllpc1ZJVi1yWkFVX1RnYjNaTnAwdk4xb2I5WEhZWkxRWng3QWowTEpwTXRSZ1pGSGhVM1NhTXhuQ3pUYWdnenVDX2VFck9FZEVuc2JydHNLaGV1Qk1INDQ4VGtLVnd5SjZqSmpMUFNxZHRLZF9pcU41MHp3TEEw?oc=5
- 推理链：
  1. fifwc-par-fra-2026-07-04-second-half-team-total-away-1pt5 是 巴拉圭 vs 法国 的球队进球数盘口；模型用胜平负、BTTS 和该队进球线交叉校验 巴拉圭 vs 法国：法国 下半场 大小 1.5 / 大，模型概率为 47.5%。
  2. 市场参考概率为 42.5%，edge 为 +5.0%；该信号来自球队进球线和比赛层面价格的结构差。
  3. 若该队 0.5/1.5 进球线或 BTTS 临场反向移动，fifwc-par-fra-2026-07-04-second-half-team-total-away-1pt5 需要取消。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 巴拉圭 vs 法国 | fifwc-par-fra-2026-07-04-total-5pt5
- 候选项：巴拉圭 vs 法国：总进球大小 5.5 / 否；动作=条件观察；参考方向=否；市场概率=91.5%；模型概率=96.0%；当前 edge=+4.5%；状态=仅观察。
- 证据链：
  1. Polymarket market_slug=fifwc-par-fra-2026-07-04-total-5pt5；参考方向市场概率=91.5%；模型概率=96.0%；edge=+4.5%。
  2. 同场盘口结构用于校验：市场类型=totals_lines；比赛=巴拉圭 vs 法国；候选方向=巴拉圭 vs 法国：总进球大小 5.5 / 否。
  3. France vs. Paraguay in World Cup round of 16: Time, date, what to know - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMigwFBVV95cUxPZk9zUGUwSExTbFQxS1NrSm55VFRiS21qNmtDX1ltd0VHa2hKY2RtMFhtaFdoTVhUcjhQcG81MEZPV21CUmRZMWw5dk5kNE1nbmJRYm5lTzJKSmM1ZFg4OHFWQjVvcUFMX0FyS0wwNDRZeFBFOGs3cW4wLVBkSVFDbzlXWQ?oc=5
  4. Philadelphia to host France and Paraguay for Round of 16 clash on July 4th - Philadelphia Union | Philadelphia Union | https://news.google.com/rss/articles/CBMiswFBVV95cUxQS1BRbGZQWDVwNE5UbV9keHdzeHFrMVBPNUtlQ0ZDM0pCY2Y1QjBJU1pQRmQxVmxwbnhKMlVETkQ4bEZsbjBneloyVURPYnVFTS1HcGdXS1BCQ3BLdkNlb1BlTEFoU3Z4YXkzZTJKZFpmb1hxUWhOMXQ5UzlHVnFXV09UXzZxUkRha1FSXzl4TjNyUmJwc2tjMmxOcW1uM3dNUE5iMlJNY0s3ZWlsamRJMUFwUQ?oc=5
  5. How to buy France vs. Paraguay round of 16 World Cup soccer tickets - USA Today | USA Today | https://news.google.com/rss/articles/CBMi0wFBVV95cUxQRng4ZFJqb0ZHSkhtMnBFRGIxRGE3TzVsRjlsUm9HNEx0bFVvdHhQd2hueXZYX0ZIZnJjQnYtYW1aeFltOWNYSEd2RWlNaXlpZnBtRmNuZWtZbUt6Wllpc1ZJVi1yWkFVX1RnYjNaTnAwdk4xb2I5WEhZWkxRWng3QWowTEpwTXRSZ1pGSGhVM1NhTXhuQ3pUYWdnenVDX2VFck9FZEVuc2JydHNLaGV1Qk1INDQ4VGtLVnd5SjZqSmpMUFNxZHRLZF9pcU41MHp3TEEw?oc=5
- 推理链：
  1. fifwc-par-fra-2026-07-04-total-5pt5 是 巴拉圭 vs 法国 的总进球盘口；模型用 BTTS、球队进球线和同场大小球阶梯检查总进球分布，得到 巴拉圭 vs 法国：总进球大小 5.5 / 否 模型概率 96.0%。
  2. 市场参考概率为 91.5%，结构化 edge 为 +4.5%；该 edge 来自同场盘口阶梯一致性，而不是外部硬统计断言。
  3. 如果 BTTS 或球队进球线临场反向移动，fifwc-par-fra-2026-07-04-total-5pt5 的总进球信号失效。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 加拿大 vs 摩洛哥 | fifwc-can-mar-2026-07-04-spread-away-2pt5
- 候选项：让分：摩洛哥 (-2.5) / 否；动作=条件观察；参考方向=否；市场概率=89.5%；模型概率=94.0%；当前 edge=+4.5%；状态=仅观察。
- 证据链：
  1. Polymarket market_slug=fifwc-can-mar-2026-07-04-spread-away-2pt5；参考方向市场概率=89.5%；模型概率=94.0%；edge=+4.5%。
  2. 同场盘口结构用于校验：市场类型=spread_lines；比赛=加拿大 vs 摩洛哥；候选方向=让分：摩洛哥 (-2.5) / 否。
  3. Canada and Morocco will play in Houston on July 4 for the city’s final World Cup match - Houston Public Media | Houston Public Media | https://news.google.com/rss/articles/CBMi0gFBVV95cUxNSWdJMFVTVnRVVTQ4YUItcmtpcS11LXVXaEtrVHdhMUUyYV9nNXJLRmlUN1Q0Y0tDOHN2UDl1UkZ0eHFKT3BZYWlDRWZEQTVjbDJaUldZdG40NzctVjR2SkVqZzFiWUp3czlvUUctUEN2WFlxOEMyUVpsNWZqZmpmajBCeEk1MEVGQU9nZEt2V0w2R1RidU1LTGZ5UkFoUjhrdTdKRk55aUpnQjZjMDVaOUU0U3dfMHB2X0paaDhyY21JTDUyMVBWT24tdHVfcG5fVlHSAdoBQVVfeXFMTmtUWTMyX2EwLXdlMHo0WHpXMzZtYjhmRXlVRlNhQjhTRkF2YUpGckxCdlprNWpuVTRlVDdndFQ1dEZOOVpfTERpdHBxSm04T0dpTHNjT1h4dGltVk9FOUVNTmNoaVRfRVdhak5YbzI5bWtrQlpuOUJyc3lZVmFJR3ItTzdWNERMVm9HT3hWVU8tcTFwSzUweTZJZkhYQXNBcmV4anZ3YTBOSlBkZG8yckZ6NExBRjFSeTJBalA3TjdfYkJlQktYdU03Yjl4cVhDeWd0ODFBV2JaSHc?oc=5
  4. FIFA World Cup 2026: How to watch Canada vs Morocco in the round of 16 – head-to-head, full schedule - olympics.com | olympics.com | https://news.google.com/rss/articles/CBMinAFBVV95cUxOc1d5OVAxSUNLSTEtREJVMng3cnNxVFpkRk5VckV2eHdBSHpsc2ZCYVptN19JYXJLZFFRbUxOTjVrVjczWmpIbDBjR3E1RDNORU9rcjVvT1lkNWJudU44UVdyd0pvYV9WbWl4VzdNUzJFT09DalRZeU94S0l0ckxfZFBONlhzdkVIXzRHVS1EM3NObnhONHQzcHQ0N1Q?oc=5
  5. How can Canada upset Morocco in the World Cup round of 16? - The Athletic - The New York Times | The New York Times | https://news.google.com/rss/articles/CBMimgFBVV95cUxNMWg5OUVHOFhaNVk2eTVoNVNrT3BfMTBSdm8tVWEwWlliMVZNS1dCclVtWGk4NWZ1d202bm81UzZsc2ljSWwwUU1zeTdZbFNxQm1WVEUyVXZxZzNLVXRXaWtNNHhYR29sblktdk05X3FZY1I1ZmJMN1M2QU1nV0ZYUk9IRGpYVlBMbFFoMzROcGZrMV9IMk40ejN3?oc=5
- 推理链：
  1. fifwc-can-mar-2026-07-04-spread-away-2pt5 是 加拿大 vs 摩洛哥 的让分盘口；模型把胜平负优势和净胜球分布拆开处理，因此 让分：摩洛哥 (-2.5) / 否 的市场概率 89.5% 与模型概率 94.0% 出现偏差。
  2. 该信号 edge 为 +4.5%，核心判断是当前让分价格相对胜率分布偏离，而不是把胜率直接等同于穿盘率。
  3. 如果临场价格移动超过 4 个百分点或首发改变净胜球路径，fifwc-can-mar-2026-07-04-spread-away-2pt5 需要降级为观察。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 巴拉圭 vs 法国 | fifwc-par-fra-2026-07-04-spread-away-2pt5
- 候选项：让分：法国 (-2.5) / 否；动作=条件观察；参考方向=否；市场概率=62.5%；模型概率=67.0%；当前 edge=+4.5%；状态=仅观察。
- 证据链：
  1. Polymarket market_slug=fifwc-par-fra-2026-07-04-spread-away-2pt5；参考方向市场概率=62.5%；模型概率=67.0%；edge=+4.5%。
  2. 同场盘口结构用于校验：市场类型=spread_lines；比赛=巴拉圭 vs 法国；候选方向=让分：法国 (-2.5) / 否。
  3. France vs. Paraguay in World Cup round of 16: Time, date, what to know - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMigwFBVV95cUxPZk9zUGUwSExTbFQxS1NrSm55VFRiS21qNmtDX1ltd0VHa2hKY2RtMFhtaFdoTVhUcjhQcG81MEZPV21CUmRZMWw5dk5kNE1nbmJRYm5lTzJKSmM1ZFg4OHFWQjVvcUFMX0FyS0wwNDRZeFBFOGs3cW4wLVBkSVFDbzlXWQ?oc=5
  4. Philadelphia to host France and Paraguay for Round of 16 clash on July 4th - Philadelphia Union | Philadelphia Union | https://news.google.com/rss/articles/CBMiswFBVV95cUxQS1BRbGZQWDVwNE5UbV9keHdzeHFrMVBPNUtlQ0ZDM0pCY2Y1QjBJU1pQRmQxVmxwbnhKMlVETkQ4bEZsbjBneloyVURPYnVFTS1HcGdXS1BCQ3BLdkNlb1BlTEFoU3Z4YXkzZTJKZFpmb1hxUWhOMXQ5UzlHVnFXV09UXzZxUkRha1FSXzl4TjNyUmJwc2tjMmxOcW1uM3dNUE5iMlJNY0s3ZWlsamRJMUFwUQ?oc=5
  5. How to buy France vs. Paraguay round of 16 World Cup soccer tickets - USA Today | USA Today | https://news.google.com/rss/articles/CBMi0wFBVV95cUxQRng4ZFJqb0ZHSkhtMnBFRGIxRGE3TzVsRjlsUm9HNEx0bFVvdHhQd2hueXZYX0ZIZnJjQnYtYW1aeFltOWNYSEd2RWlNaXlpZnBtRmNuZWtZbUt6Wllpc1ZJVi1yWkFVX1RnYjNaTnAwdk4xb2I5WEhZWkxRWng3QWowTEpwTXRSZ1pGSGhVM1NhTXhuQ3pUYWdnenVDX2VFck9FZEVuc2JydHNLaGV1Qk1INDQ4VGtLVnd5SjZqSmpMUFNxZHRLZF9pcU41MHp3TEEw?oc=5
- 推理链：
  1. fifwc-par-fra-2026-07-04-spread-away-2pt5 是 巴拉圭 vs 法国 的让分盘口；模型把胜平负优势和净胜球分布拆开处理，因此 让分：法国 (-2.5) / 否 的市场概率 62.5% 与模型概率 67.0% 出现偏差。
  2. 该信号 edge 为 +4.5%，核心判断是当前让分价格相对胜率分布偏离，而不是把胜率直接等同于穿盘率。
  3. 如果临场价格移动超过 4 个百分点或首发改变净胜球路径，fifwc-par-fra-2026-07-04-spread-away-2pt5 需要降级为观察。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 加拿大 vs 摩洛哥 | fifwc-can-mar-2026-07-04-spread-away-3pt5
- 候选项：让分：摩洛哥 (-3.5) / 否；动作=条件观察；参考方向=否；市场概率=95.9%；模型概率=99.9%；当前 edge=+4.0%；状态=仅观察。
- 证据链：
  1. Polymarket market_slug=fifwc-can-mar-2026-07-04-spread-away-3pt5；参考方向市场概率=95.9%；模型概率=99.9%；edge=+4.0%。
  2. 同场盘口结构用于校验：市场类型=spread_lines；比赛=加拿大 vs 摩洛哥；候选方向=让分：摩洛哥 (-3.5) / 否。
  3. Canada and Morocco will play in Houston on July 4 for the city’s final World Cup match - Houston Public Media | Houston Public Media | https://news.google.com/rss/articles/CBMi0gFBVV95cUxNSWdJMFVTVnRVVTQ4YUItcmtpcS11LXVXaEtrVHdhMUUyYV9nNXJLRmlUN1Q0Y0tDOHN2UDl1UkZ0eHFKT3BZYWlDRWZEQTVjbDJaUldZdG40NzctVjR2SkVqZzFiWUp3czlvUUctUEN2WFlxOEMyUVpsNWZqZmpmajBCeEk1MEVGQU9nZEt2V0w2R1RidU1LTGZ5UkFoUjhrdTdKRk55aUpnQjZjMDVaOUU0U3dfMHB2X0paaDhyY21JTDUyMVBWT24tdHVfcG5fVlHSAdoBQVVfeXFMTmtUWTMyX2EwLXdlMHo0WHpXMzZtYjhmRXlVRlNhQjhTRkF2YUpGckxCdlprNWpuVTRlVDdndFQ1dEZOOVpfTERpdHBxSm04T0dpTHNjT1h4dGltVk9FOUVNTmNoaVRfRVdhak5YbzI5bWtrQlpuOUJyc3lZVmFJR3ItTzdWNERMVm9HT3hWVU8tcTFwSzUweTZJZkhYQXNBcmV4anZ3YTBOSlBkZG8yckZ6NExBRjFSeTJBalA3TjdfYkJlQktYdU03Yjl4cVhDeWd0ODFBV2JaSHc?oc=5
  4. FIFA World Cup 2026: How to watch Canada vs Morocco in the round of 16 – head-to-head, full schedule - olympics.com | olympics.com | https://news.google.com/rss/articles/CBMinAFBVV95cUxOc1d5OVAxSUNLSTEtREJVMng3cnNxVFpkRk5VckV2eHdBSHpsc2ZCYVptN19JYXJLZFFRbUxOTjVrVjczWmpIbDBjR3E1RDNORU9rcjVvT1lkNWJudU44UVdyd0pvYV9WbWl4VzdNUzJFT09DalRZeU94S0l0ckxfZFBONlhzdkVIXzRHVS1EM3NObnhONHQzcHQ0N1Q?oc=5
  5. How can Canada upset Morocco in the World Cup round of 16? - The Athletic - The New York Times | The New York Times | https://news.google.com/rss/articles/CBMimgFBVV95cUxNMWg5OUVHOFhaNVk2eTVoNVNrT3BfMTBSdm8tVWEwWlliMVZNS1dCclVtWGk4NWZ1d202bm81UzZsc2ljSWwwUU1zeTdZbFNxQm1WVEUyVXZxZzNLVXRXaWtNNHhYR29sblktdk05X3FZY1I1ZmJMN1M2QU1nV0ZYUk9IRGpYVlBMbFFoMzROcGZrMV9IMk40ejN3?oc=5
- 推理链：
  1. fifwc-can-mar-2026-07-04-spread-away-3pt5 是 加拿大 vs 摩洛哥 的让分盘口；模型把胜平负优势和净胜球分布拆开处理，因此 让分：摩洛哥 (-3.5) / 否 的市场概率 95.9% 与模型概率 99.9% 出现偏差。
  2. 该信号 edge 为 +4.0%，核心判断是当前让分价格相对胜率分布偏离，而不是把胜率直接等同于穿盘率。
  3. 如果临场价格移动超过 4 个百分点或首发改变净胜球路径，fifwc-can-mar-2026-07-04-spread-away-3pt5 需要降级为观察。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。
