# 概率预测报告

- 报告日期: 2026-07-04
- 比赛日期字段: 2026-07-03
- 模型模式: baseline_fallback / structural_edge
- 治理规则: 无证据，不编故事；有结构化盘口 edge 时允许小仓限价，而不是全部跳过。
- 已应用教训: 胜率与让分穿盘概率分开；保留弱势方进球路径；缺少确认首发/硬技术数据时限制仓位而不是压平所有预测。

## 覆盖审计
- 已解析请求数: 9
- 缺失请求数: 0
- 已选盘口类型数量: {"match_1x2": 9, "first_team_to_score": 9, "spread_lines": 30, "totals_lines": 45, "btts": 9, "team_total_lines": 42}

## 阿根廷 vs 佛得角 [fifwc-arg-cvi-2026-07-03]

### 共享信息源
1. Cape Verde: All to know before FIFA World Cup knockout against Argentina - Al Jazeera | Al Jazeera | https://news.google.com/rss/articles/CBMirwFBVV95cUxPeWJFLWMwSXBfNzJ2NzFzWVFQMmFSS3NKdlZqUUE4XzM0eEFEa0xjcFRDMlR0QmpCaFNQc2VmZ1paakY1eDNYaWJiTThiWjJpMWpmSTBINUNLNVNTbGQyN3Q5Tnd0anFSek56TW9oNHVVa3BIcnJRR0htNUFJNDNsR0IxRV93UFFGNEJqNTRqTUJNZ2R6ZFNqSjQ3c0RxaUxmSVJ2ZWU3Y1VtZzRoWHhV0gG0AUFVX3lxTE15eTQxamM4Mk9PTHdrMXlSTDFmeEYxQVpBbmYwdjBZV3F6bTRGN2ZweTN3TU4wdlVIZlF6T1JqU2x5X05fdlJvMHEzWnQycm5wUXlQMjljc01FX0ZBS0I2VzZ5Sks4cXFzekJKRzZubHA5ZFNhaFQ5ckVNdVZ3UHV0cHM5TmhIWFBwczRTMkt3bkJsMXFWQnFfZThEYXAwZ2ROVkNpNHNDdjZXcDlqT0ZRWUpCZA?oc=5
2. Cape Verde are celebrating one of World Cup’s greatest feats. Can they shock Messi and Argentina next? - The Athletic - The New York Times | The New York Times | https://news.google.com/rss/articles/CBMioAFBVV95cUxPd240TjdZTXZxX2dvQTBYMmhkamFkQkRlVWtjNnlMN3UyVjlmaTlia1BuNmFLQ2JJaHA0QnZXaFJIMExMdUZhR3gwSkVuaVFRX2NodVZJTFV5RDc5U09kWWhqYnhXUUU1aUQyVEstQzNDRGVFbzVDQVo4ckh2aUZ0VEhhcmM0ek4tbkFnRDVIVF9BbnNTUUxWYXhxREdlbDc5?oc=5
3. World Cup 2026 R32 Argentina vs. Cape Verde Prediction: Knockout Preview & Best Bets - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMigwFBVV95cUxNT0lXWWRWbG5PSE84b3FYZmtreExnSW16T29JNXNheTlONXlnWU9fVXpQZmpsRzNVOVQ1LWdnVkpPLTVGV3FkRVlwS0dibWtrTzdpY1FEbjR5eEV6TWpRaWNaMktjeXRicGxMTlE5Vjk4eHRzclBobzBKNlB5U05XODNGUQ?oc=5
4. Who Will Lionel Messi And Argentina Play In The World Cup Round Of 32? - FOX Sports | FOX Sports | https://news.google.com/rss/articles/CBMingFBVV95cUxOOEZVamc0bmZPRjhpUzFrSXQ1Y1JGRDdlV0hMWWswNlY1akJfNWhQLXFPNUhwUGVHZnl4NndXV2IxOGo0cGF0WG93ZWFjVFNQaHh4VnRKS0R4NTNtRm5GYmU2ZFkydXNpNy0wS0tTeUNiX1JWeFdJZnFGOU9pSDFRN1A2cGtWQU5mZlVTQWI5ZWZmUWJFRk1zQTl6OXBfd9IBngFBVV95cUxQWUZJdFNkYkUxN25FMG9pMWVJT0pfc2lyZFRnWWlmLTdLRVVCa0FLQ1JPUTY0ODFpQ1owWU5FdEVFc0ItMC1FbmtRaXVVZ2w3RmtFc1dlMkE1UXFzSnVRYmxWSEpYUW9MRlRsaHBhbHZtaW5MaFM4aHdia0FOcXh1TFpqX3BhZlhzZHhJb2VqdTZnaldMNUdDR2RGX0dUdw?oc=5
5. Cape Verde will beat Argentina 1-0 in World Cup clash, predicts president - BBC | BBC | https://news.google.com/rss/articles/CBMiWkFVX3lxTE84T1pXT0FLNU1YN0xNenVlTXc3aVFFMjBJWk1JSERadWE2a3BFU3VUWkJoS3RGMkY5RXI5bTBNT1hvR3FNekVQMnRtQWpTWDlYYWtJYXhsd3VnQQ?oc=5

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
| fifwc-arg-cvi-2026-07-03-arg | 阿根廷 会在 2026-07-03 获胜吗？ | 是 | 84.5% | 87.0% | +2.5% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-draw | 阿根廷 vs 佛得角 会打平吗？ | 是 | 11.5% | 12.0% | +0.5% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-cvi | 佛得角 会在 2026-07-03 获胜吗？ | 是 | 4.2% | 1.8% | -2.5% | 中低 | 跳过 | edge 低于 4 个百分点 |

### 让分盘
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-arg-cvi-2026-07-03-spread-home-1pt5 | 让分：阿根廷 (-1.5) | 阿根廷 | 61.5% | 67.0% | +5.5% | 中低 | 小仓限价 | 结构化 edge，小仓限价 |
| fifwc-arg-cvi-2026-07-03-spread-away-1pt5 | 让分：佛得角 (-1.5) | 佛得角 | 0.7% | 0.7% | +0.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-arg-cvi-2026-07-03-spread-home-2pt5 | 让分：阿根廷 (-2.5) | 阿根廷 | 37.5% | 37.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-spread-away-2pt5 | 让分：佛得角 (-2.5) | 佛得角 | 0.1% | 2.2% | +2.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-arg-cvi-2026-07-03-spread-home-3pt5 | 让分：阿根廷 (-3.5) | 阿根廷 | 20.0% | 20.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-spread-away-3pt5 | 让分：佛得角 (-3.5) | 佛得角 | 0.1% | 2.1% | +2.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-arg-cvi-2026-07-03-spread-home-4pt5 | 让分：阿根廷 (-4.5) | 阿根廷 | 9.0% | 9.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-spread-away-4pt5 | 让分：佛得角 (-4.5) | 佛得角 | 0.1% | 2.1% | +2.0% | 低 | 跳过 | 价格过于极端 |
| fifwc-arg-cvi-2026-07-03-spread-home-5pt5 | 让分：阿根廷 (-5.5) | 阿根廷 | 3.8% | 3.8% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-spread-away-5pt5 | 让分：佛得角 (-5.5) | 佛得角 | 0.1% | 2.1% | +2.0% | 低 | 跳过 | 价格过于极端 |

### 总进球盘
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-arg-cvi-2026-07-03-total-0pt5 | 阿根廷 vs 佛得角：总进球大小 0.5 | 大 | 95.5% | 95.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-total-1pt5 | 阿根廷 vs 佛得角：总进球大小 1.5 | 大 | 80.5% | 80.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-total-2pt5 | 阿根廷 vs 佛得角：总进球大小 2.5 | 大 | 57.5% | 55.0% | -2.5% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-total-3pt5 | 阿根廷 vs 佛得角：总进球大小 3.5 | 大 | 35.5% | 35.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-total-4pt5 | 阿根廷 vs 佛得角：总进球大小 4.5 | 大 | 18.5% | 18.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-total-5pt5 | 阿根廷 vs 佛得角：总进球大小 5.5 | 大 | 8.5% | 4.0% | -4.5% | 偏低+ | 仅观察 | baseline edge 需要首发确认 |
| fifwc-arg-cvi-2026-07-03-total-6pt5 | 阿根廷 vs 佛得角：总进球大小 6.5 | 大 | 3.4% | 0.1% | -3.3% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-total-7pt5 | 阿根廷 vs 佛得角：总进球大小 7.5 | 大 | 1.1% | 0.1% | -1.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-arg-cvi-2026-07-03-total-8pt5 | 阿根廷 vs 佛得角：总进球大小 8.5 | 大 | 0.7% | 0.1% | -0.5% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-arg-cvi-2026-07-03-first-half-total-0pt5 | 阿根廷 vs 佛得角：上半场 大小 0.5 | 大 | 76.0% | 76.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-first-half-total-1pt5 | 阿根廷 vs 佛得角：上半场 大小 1.5 | 大 | 39.5% | 39.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-first-half-total-2pt5 | 阿根廷 vs 佛得角：上半场 大小 2.5 | 大 | 16.0% | 13.5% | -2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-second-half-total-0pt5 | 阿根廷 vs 佛得角：下半场 大小 0.5 | 大 | 80.5% | 80.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-second-half-total-1pt5 | 阿根廷 vs 佛得角：下半场 大小 1.5 | 大 | 50.0% | 50.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-second-half-total-2pt5 | 阿根廷 vs 佛得角：下半场 大小 2.5 | 大 | 24.5% | 22.0% | -2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 双方均进球
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-arg-cvi-2026-07-03-btts | 阿根廷 vs 佛得角: 双方均进球 | 是 | 32.5% | 32.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-btts-first-half | 阿根廷 vs 佛得角: 上半场双方均进球 | 是 | 13.5% | 13.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-btts-second-half | 阿根廷 vs 佛得角: 下半场双方均进球 | 是 | 18.5% | 18.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 首支进球队伍
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-arg-cvi-2026-07-03-first-to-score-home | 阿根廷 会先于 佛得角 进球吗？ | 是 | 84.5% | 84.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-first-to-score-away | 佛得角 会先于 阿根廷 进球吗？ | 是 | 11.5% | 9.0% | -2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-first-to-score-neither | 阿根廷 vs 佛得角: 无球队先进球? | 是 | 5.5% | 2.0% | -3.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 球队进球数
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-arg-cvi-2026-07-03-team-total-home-0pt5 | 阿根廷 vs 佛得角：阿根廷 大小 0.5 | 大 | 93.0% | 93.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-team-total-home-1pt5 | 阿根廷 vs 佛得角：阿根廷 大小 1.5 | 大 | 74.0% | 74.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-team-total-home-2pt5 | 阿根廷 vs 佛得角：阿根廷 大小 2.5 | 大 | 48.0% | 44.5% | -3.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-team-total-away-0pt5 | 阿根廷 vs 佛得角：佛得角 大小 0.5 | 大 | 35.5% | 35.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-team-total-away-1pt5 | 阿根廷 vs 佛得角：佛得角 大小 1.5 | 大 | 8.0% | 8.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-team-total-away-2pt5 | 阿根廷 vs 佛得角：佛得角 大小 2.5 | 大 | 1.4% | 0.1% | -1.3% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-arg-cvi-2026-07-03-first-half-team-total-home-0pt5 | 阿根廷 vs 佛得角：阿根廷 上半场 大小 0.5 | 大 | 69.5% | 72.0% | +2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-first-half-team-total-home-1pt5 | 阿根廷 vs 佛得角：阿根廷 上半场 大小 1.5 | 大 | 32.5% | 37.5% | +5.0% | 偏低+ | 小仓限价 | 结构化 edge，小仓限价 |
| fifwc-arg-cvi-2026-07-03-first-half-team-total-away-0pt5 | 阿根廷 vs 佛得角：佛得角 上半场 大小 0.5 | 大 | 18.0% | 18.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-first-half-team-total-away-1pt5 | 阿根廷 vs 佛得角：佛得角 上半场 大小 1.5 | 大 | 3.2% | 3.2% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-second-half-team-total-home-0pt5 | 阿根廷 vs 佛得角：阿根廷 下半场 大小 0.5 | 大 | 74.5% | 77.0% | +2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-second-half-team-total-home-1pt5 | 阿根廷 vs 佛得角：阿根廷 下半场 大小 1.5 | 大 | 38.5% | 43.5% | +5.0% | 偏低+ | 小仓限价 | 结构化 edge，小仓限价 |
| fifwc-arg-cvi-2026-07-03-second-half-team-total-away-0pt5 | 阿根廷 vs 佛得角：佛得角 下半场 大小 0.5 | 大 | 23.5% | 23.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-arg-cvi-2026-07-03-second-half-team-total-away-1pt5 | 阿根廷 vs 佛得角：佛得角 下半场 大小 1.5 | 大 | 2.6% | 2.6% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |

## 澳大利亚 vs 埃及 [fifwc-aus-egy-2026-07-03]

### 共享信息源
1. FIFA World Cup 2026: How to watch Australia vs Egypt in the round of 32 – head-to-head, full schedule - olympics.com | olympics.com | https://news.google.com/rss/articles/CBMiygFBVV95cUxQbkwtcEw0QWNvaGtzdVFMM0JsRlRrc083TDJ3cHZsMTY5dHYxVE84ejhjVUhYQUF5Zk15U0lfS1k5ZFVXeE1YMW0zclZlN2dRUTZTaDFxSjJaU2FqU1E5SVZwbjhIYlh2bENDS0tLSUMxdU1CcnRBOTUwTkRQU1kzREhGQTZSNFpIcVplTHRaem1sOEE4Q2VyZkRLTXdDUmxKODNaN1RwMDJCZmN1bTJxaUxJVng2REJvQXJKVFdFY2NxS0tUbXV0ZFZ3?oc=5
2. PREVIEW | Australia vs Egypt: team news, lineups, predictions (World Cup 03/07) - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMihwFBVV95cUxOZ0FLS1pxQkp0VkdfUlc2VkhuUG1MMVJveS03eDktWlNfemliYWRsbDJMYy1wSlZZd0tPMjJvcVJ2cXRETXFlWllPZTNhNTExby1mXzNEdHhNTWdCY0xmZzY5c3UyQnZtbGM5endERVdnX05nWmRLMGV6clk2MmFhdFZGWHBNN1k?oc=5
3. Why VAR ruled Iran’s ‘winner’ offside to put them at risk of World Cup exit as Egypt progress - The Athletic - The New York Times | The New York Times | https://news.google.com/rss/articles/CBMiiwFBVV95cUxOektvNTNPSlB1SHU3bTFlV2NNTl9fLTZfck9BS1JfSklUTGNvVG1pMTI2Y1lkTXZwczFGN3E2N0xoeGtjckZrS005clh0TTdwOTR5N19VSWg4RW9hdWpjWHZTc04zdUtSdXFMc3Biek40VkJ0eUxZYmdYZHA3YlpiUmFaU184TGs5Qjkw?oc=5
4. Socceroos to meet Mo Salah’s Egypt in World Cup last 32 with star player under injury cloud - The Guardian | The Guardian | https://news.google.com/rss/articles/CBMioAFBVV95cUxNMUhZVFBWUHpUVEMtNzNheW9NNU15amhuNHlKQ2pwbVE5aGlvLVlNeFltb3pubThKZjUzODd6THgwQTl0YWtib08zdVdQVkFqbWx4UFktVkFaWENlU2dkeVJ0a05DdGJqUkZsa0NrWkJELWV2TVYzY3ppQmwwa3hkS3V5VHRGRUItYVprUHlkemRyT3hVUEhBazRwYWc0UG4w?oc=5
5. Australia vs. Egypt: How to watch, stream World Cup Round of 32 match - MLSsoccer.com | MLSsoccer.com | https://news.google.com/rss/articles/CBMingFBVV95cUxOT09JbDZ6Y09zbUR6RjJpTFVTaWxReFVGV2lwTHdLZ2ZSRjNwX19NaXRDR2JTcTJJQmRaMmowVE9ia2RJQXFFZnZYaDlYdUh0cFZpRWZlYXNUaFJCMktkLXJrOTcxanhvZXhkMkRoSlRaVlRfVklWTmw2TmlTSHBXMUxyMkIwUGJYTWVmdXhQSmtxZUJWdjlsY1hhY0NSZw?oc=5

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
| fifwc-aus-egy-2026-07-03-aus | 澳大利亚 会在 2026-07-03 获胜吗？ | 是 | 28.5% | 28.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-draw | 澳大利亚 vs 埃及 会打平吗？ | 是 | 33.5% | 36.5% | +3.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-egy | 埃及 会在 2026-07-03 获胜吗？ | 是 | 38.5% | 38.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |

### 让分盘
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-aus-egy-2026-07-03-spread-home-1pt5 | 让分：澳大利亚 (-1.5) | 澳大利亚 | 9.5% | 12.5% | +3.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-spread-away-1pt5 | 让分：埃及 (-1.5) | 埃及 | 15.5% | 15.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-spread-home-2pt5 | 让分：澳大利亚 (-2.5) | 澳大利亚 | 2.6% | 4.7% | +2.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-spread-away-2pt5 | 让分：埃及 (-2.5) | 埃及 | 4.6% | 0.1% | -4.5% | 偏低+ | 仅观察 | baseline edge 需要首发确认 |
| fifwc-aus-egy-2026-07-03-spread-home-3pt5 | 让分：澳大利亚 (-3.5) | 澳大利亚 | 0.8% | 2.8% | +2.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-aus-egy-2026-07-03-spread-away-3pt5 | 让分：埃及 (-3.5) | 埃及 | 1.5% | 0.1% | -1.4% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-aus-egy-2026-07-03-spread-home-4pt5 | 让分：澳大利亚 (-4.5) | 澳大利亚 | 0.1% | 2.2% | +2.0% | 低 | 跳过 | 价格过于极端 |
| fifwc-aus-egy-2026-07-03-spread-away-4pt5 | 让分：埃及 (-4.5) | 埃及 | 0.8% | 0.1% | -0.7% | 低 | 跳过 | 价格过于极端 |
| fifwc-aus-egy-2026-07-03-spread-home-5pt5 | 让分：澳大利亚 (-5.5) | 澳大利亚 | 0.1% | 2.2% | +2.0% | 低 | 跳过 | 价格过于极端 |
| fifwc-aus-egy-2026-07-03-spread-away-5pt5 | 让分：埃及 (-5.5) | 埃及 | 0.2% | 0.1% | -0.1% | 低 | 跳过 | 价格过于极端 |

### 总进球盘
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-aus-egy-2026-07-03-total-0pt5 | 澳大利亚 vs 埃及：总进球大小 0.5 | 大 | 85.5% | 85.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-total-1pt5 | 澳大利亚 vs 埃及：总进球大小 1.5 | 大 | 59.5% | 59.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-total-2pt5 | 澳大利亚 vs 埃及：总进球大小 2.5 | 大 | 33.5% | 33.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-total-3pt5 | 澳大利亚 vs 埃及：总进球大小 3.5 | 大 | 15.5% | 15.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-total-4pt5 | 澳大利亚 vs 埃及：总进球大小 4.5 | 大 | 6.0% | 6.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-total-5pt5 | 澳大利亚 vs 埃及：总进球大小 5.5 | 大 | 1.8% | 0.1% | -1.7% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-aus-egy-2026-07-03-total-6pt5 | 澳大利亚 vs 埃及：总进球大小 6.5 | 大 | 0.5% | 0.1% | -0.4% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-aus-egy-2026-07-03-total-7pt5 | 澳大利亚 vs 埃及：总进球大小 7.5 | 大 | 0.2% | 0.1% | -0.1% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-aus-egy-2026-07-03-total-8pt5 | 澳大利亚 vs 埃及：总进球大小 8.5 | 大 | 0.1% | 0.1% | -0.1% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-aus-egy-2026-07-03-first-half-total-0pt5 | 澳大利亚 vs 埃及：上半场 大小 0.5 | 大 | 59.5% | 59.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-first-half-total-1pt5 | 澳大利亚 vs 埃及：上半场 大小 1.5 | 大 | 24.0% | 24.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-first-half-total-2pt5 | 澳大利亚 vs 埃及：上半场 大小 2.5 | 大 | 7.0% | 7.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-second-half-total-0pt5 | 澳大利亚 vs 埃及：下半场 大小 0.5 | 大 | 67.0% | 67.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-second-half-total-1pt5 | 澳大利亚 vs 埃及：下半场 大小 1.5 | 大 | 33.0% | 33.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-second-half-total-2pt5 | 澳大利亚 vs 埃及：下半场 大小 2.5 | 大 | 13.5% | 13.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 双方均进球
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-aus-egy-2026-07-03-btts | 澳大利亚 vs 埃及: 双方均进球 | 是 | 43.5% | 48.5% | +5.0% | 中低 | 小仓限价 | 结构化 edge，小仓限价 |
| fifwc-aus-egy-2026-07-03-btts-first-half | 澳大利亚 vs 埃及: 上半场双方均进球 | 是 | 14.0% | 14.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-btts-second-half | 澳大利亚 vs 埃及: 下半场双方均进球 | 是 | 21.5% | 21.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 首支进球队伍
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-aus-egy-2026-07-03-first-to-score-home | 澳大利亚 会先于 埃及 进球吗？ | 是 | 37.5% | 37.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-first-to-score-away | 埃及 会先于 澳大利亚 进球吗？ | 是 | 49.5% | 49.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-first-to-score-neither | 澳大利亚 vs 埃及: 无球队先进球? | 是 | 13.0% | 9.5% | -3.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 球队进球数
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-aus-egy-2026-07-03-team-total-home-0pt5 | 澳大利亚 vs 埃及：澳大利亚 大小 0.5 | 大 | 60.5% | 60.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-team-total-home-1pt5 | 澳大利亚 vs 埃及：澳大利亚 大小 1.5 | 大 | 24.0% | 24.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-team-total-home-2pt5 | 澳大利亚 vs 埃及：澳大利亚 大小 2.5 | 大 | 6.5% | 3.0% | -3.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-team-total-away-0pt5 | 澳大利亚 vs 埃及：埃及 大小 0.5 | 大 | 68.5% | 71.0% | +2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-team-total-away-1pt5 | 澳大利亚 vs 埃及：埃及 大小 1.5 | 大 | 31.0% | 31.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-team-total-away-2pt5 | 澳大利亚 vs 埃及：埃及 大小 2.5 | 大 | 10.5% | 7.0% | -3.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-first-half-team-total-home-0pt5 | 澳大利亚 vs 埃及：澳大利亚 上半场 大小 0.5 | 大 | 34.0% | 34.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-first-half-team-total-home-1pt5 | 澳大利亚 vs 埃及：澳大利亚 上半场 大小 1.5 | 大 | 7.5% | 7.5% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-first-half-team-total-away-0pt5 | 澳大利亚 vs 埃及：埃及 上半场 大小 0.5 | 大 | 39.0% | 41.5% | +2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-first-half-team-total-away-1pt5 | 澳大利亚 vs 埃及：埃及 上半场 大小 1.5 | 大 | 7.5% | 7.5% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-second-half-team-total-home-0pt5 | 澳大利亚 vs 埃及：澳大利亚 下半场 大小 0.5 | 大 | 42.5% | 42.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-second-half-team-total-home-1pt5 | 澳大利亚 vs 埃及：澳大利亚 下半场 大小 1.5 | 大 | 10.0% | 10.0% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-second-half-team-total-away-0pt5 | 澳大利亚 vs 埃及：埃及 下半场 大小 0.5 | 大 | 47.0% | 49.5% | +2.5% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-aus-egy-2026-07-03-second-half-team-total-away-1pt5 | 澳大利亚 vs 埃及：埃及 下半场 大小 1.5 | 大 | 15.5% | 15.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

## 哥伦比亚 vs 加纳 [fifwc-col-gha-2026-07-03]

### 共享信息源
1. Colombia vs. Ghana - Kick-off time, team news, how to watch World Cup round of 32 clash - ESPN | ESPN | https://news.google.com/rss/articles/CBMiswFBVV95cUxOMjljXzBaZmpSZUVOQ3VOZHFxc0UwbUZSLXcwMlVpVVdzaTU2T0VWOHE0aUM3X0IwdWtaQVF2SmxnSGxjbkNzbWNjWWNsX1ZfcG1XNUR5OTRZNTRYUnJUWGRXbm1DbGFEa2NhaF9xM2FXRV9BRVJIRjZiT1JiSjBBdVgyR3Z4NTNUdHNZSnd1NHNVOHBDOW5DUi1laGZQdjlvdlJndnBBVVI4a3RaMW0wNWlpdw?oc=5
2. Croatia grab second in World Cup Group L, Ghana through in third: Colombia or Portugal next? - The Athletic - The New York Times | The New York Times | https://news.google.com/rss/articles/CBMiowFBVV95cUxPcVI5UXFFbUpqRGViNndKUVd6TlNhYVFLVUF5LXU1UGgtVjFDSjJxa3E1cVdWTFhnc0I0cXJNeGluTnlpeC03aFNyU05GekxDOWFBRERWZ0RzZENkdmFISWx0cS1PZV82OG9uVC1iVlJUN0pnT0lIa3BIdW92NHlFcmNodldZb3dyQzRpYlRnaVJZc1hWdndDdWJVa1N6Y3o2d25B?oc=5
3. PREVIEW | Colombia vs Ghana: team news, lineups, predictions (World Cup 04/07) - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMihgFBVV95cUxPNUxsS3RVSHpTbkFiTXlIX3FmM3pfRFRqNHVOSktpSzZtM3cwUXNJRGpRY3EwaXlRcnNOZS1xZkpNYnhPUmdrMjlPRTIwNUhycTE5NEFzY0pzZmszS2Jpc25PQTZIdnRQVEFfMGlFbG5BdzZzc0hhLUVRbl9VX0hWMkdaeEVwdw?oc=5
4. Opening odds for Colombia vs. Ghana in the 2026 FIFA World Cup Round of 32 - DraftKings Network | DraftKings Network | https://news.google.com/rss/articles/CBMiugFBVV95cUxQWU1acWNOSjJnNENjNEEyT2VSVjhNTEMwbWZNQW02UEJXbnJ1YUJmcVZsMndiWW9IS01Kc01sSU9OU2dyenJldDVrcVJ5NHc4WDZEX0xrdVhFZGxkUHR3d1BraFVsTXVtdkFFSnA5M1VUbnBGS1BtLUdRbFU4TXZuckF2YkVzMjNuX2NycHFzeFZlVEpzNzNRWThOV2lBeFptSV9qTDdVVTlxWTBRQ01uU2ZaQW1naHNzdWc?oc=5
5. 2026 World Cup Bracket: Full Round Of 32 Matchups - FOX Sports | FOX Sports | https://news.google.com/rss/articles/CBMiiAFBVV95cUxOR1hSc0FVc1ZNZjZqU3puWlFLYWcxWVhnUjNHV25jNU9DNWh5TzBVcXpzdVdsMGxaRUpqUFlaY2RnV2RZaDNCMnF5QktVZWJYNkFtVHVfMEx4OGtZVUpockJ3elF6UHNKZGNYTjJUeHVsdnJCNHRETExPcy01d1A1VWtWTEtwZkFE0gGIAUFVX3lxTE8ySjlRQ0JsTmFKMlBVS2c4MWN6eS1SOVRISExSbENFMUluZ2pCa2lPOVVvOV9oTG5waXI0ZlpLVkFyekZQaVMwcnJPY3d4bEtIaGlKdXpSOTlxcDl6Nk1zalhfdHpUWnhGbk1INE9NOUhESlNjeklnYlZoeDhHYy1vSTZjNUhNc0I?oc=5

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
| fifwc-col-gha-2026-07-03-col | 哥伦比亚 会在 2026-07-03 获胜吗？ | 是 | 64.5% | 66.0% | +1.5% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-draw | 哥伦比亚 vs 加纳 会打平吗？ | 是 | 24.5% | 24.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-gha | 加纳 会在 2026-07-03 获胜吗？ | 是 | 11.5% | 11.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |

### 让分盘
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-col-gha-2026-07-03-spread-home-1pt5 | 让分：哥伦比亚 (-1.5) | 哥伦比亚 | 37.5% | 41.5% | +4.0% | 中低 | 仅观察 | baseline edge 需要首发确认 |
| fifwc-col-gha-2026-07-03-spread-away-1pt5 | 让分：加纳 (-1.5) | 加纳 | 2.7% | 2.7% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-spread-home-2pt5 | 让分：哥伦比亚 (-2.5) | 哥伦比亚 | 17.5% | 13.0% | -4.5% | 偏低+ | 仅观察 | baseline edge 需要首发确认 |
| fifwc-col-gha-2026-07-03-spread-away-2pt5 | 让分：加纳 (-2.5) | 加纳 | 0.5% | 2.6% | +2.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-col-gha-2026-07-03-spread-home-3pt5 | 让分：哥伦比亚 (-3.5) | 哥伦比亚 | 6.0% | 0.9% | -5.1% | 偏低+ | 小仓限价 | 结构化 edge，小仓限价 |
| fifwc-col-gha-2026-07-03-spread-away-3pt5 | 让分：加纳 (-3.5) | 加纳 | 0.5% | 2.6% | +2.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-col-gha-2026-07-03-spread-home-4pt5 | 让分：哥伦比亚 (-4.5) | 哥伦比亚 | 2.2% | 0.1% | -2.1% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-spread-away-4pt5 | 让分：加纳 (-4.5) | 加纳 | 0.2% | 2.2% | +2.0% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-col-gha-2026-07-03-spread-home-5pt5 | 让分：哥伦比亚 (-5.5) | 哥伦比亚 | 0.8% | 0.1% | -0.7% | 低 | 跳过 | 价格过于极端 |
| fifwc-col-gha-2026-07-03-spread-away-5pt5 | 让分：加纳 (-5.5) | 加纳 | 0.1% | 2.1% | +2.0% | 低 | 跳过 | 价格过于极端 |

### 总进球盘
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-col-gha-2026-07-03-total-0pt5 | 哥伦比亚 vs 加纳：总进球大小 0.5 | 大 | 90.5% | 90.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-total-1pt5 | 哥伦比亚 vs 加纳：总进球大小 1.5 | 大 | 68.5% | 68.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-total-2pt5 | 哥伦比亚 vs 加纳：总进球大小 2.5 | 大 | 41.5% | 41.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-total-3pt5 | 哥伦比亚 vs 加纳：总进球大小 3.5 | 大 | 21.5% | 21.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-total-4pt5 | 哥伦比亚 vs 加纳：总进球大小 4.5 | 大 | 9.0% | 9.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-total-5pt5 | 哥伦比亚 vs 加纳：总进球大小 5.5 | 大 | 3.8% | 0.1% | -3.7% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-total-6pt5 | 哥伦比亚 vs 加纳：总进球大小 6.5 | 大 | 1.2% | 0.1% | -1.1% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-col-gha-2026-07-03-total-8pt5 | 哥伦比亚 vs 加纳：总进球大小 8.5 | 大 | 0.1% | 0.1% | -0.1% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-col-gha-2026-07-03-first-half-total-0pt5 | 哥伦比亚 vs 加纳：上半场 大小 0.5 | 大 | 64.0% | 64.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-first-half-total-1pt5 | 哥伦比亚 vs 加纳：上半场 大小 1.5 | 大 | 29.0% | 29.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-first-half-total-2pt5 | 哥伦比亚 vs 加纳：上半场 大小 2.5 | 大 | 9.0% | 9.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-total-7pt5 | 哥伦比亚 vs 加纳：总进球大小 7.5 | 大 | 0.5% | 0.1% | -0.4% | 偏低+ | 跳过 | 价格过于极端 |
| fifwc-col-gha-2026-07-03-second-half-total-0pt5 | 哥伦比亚 vs 加纳：下半场 大小 0.5 | 大 | 71.5% | 71.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-second-half-total-1pt5 | 哥伦比亚 vs 加纳：下半场 大小 1.5 | 大 | 39.5% | 39.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-second-half-total-2pt5 | 哥伦比亚 vs 加纳：下半场 大小 2.5 | 大 | 17.5% | 17.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 双方均进球
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-col-gha-2026-07-03-btts | 哥伦比亚 vs 加纳: 双方均进球 | 是 | 39.5% | 39.5% | +0.0% | 中低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-btts-first-half | 哥伦比亚 vs 加纳: 上半场双方均进球 | 是 | 14.0% | 14.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-btts-second-half | 哥伦比亚 vs 加纳: 下半场双方均进球 | 是 | 20.0% | 20.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 首支进球队伍
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-col-gha-2026-07-03-first-to-score-home | 哥伦比亚 会先于 加纳 进球吗？ | 是 | 68.5% | 68.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-first-to-score-away | 加纳 会先于 哥伦比亚 进球吗？ | 是 | 23.0% | 20.5% | -2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-first-to-score-neither | 哥伦比亚 vs 加纳: 无球队先进球? | 是 | 10.0% | 6.5% | -3.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |

### 球队进球数
| 盘口 slug | 问题/盘口 | 方向 | 市场概率 | 模型概率 | edge | 置信度 | 状态 | 跳过原因 |
|---|---|---:|---:|---:|---:|---|---|---|
| fifwc-col-gha-2026-07-03-team-total-home-1pt5 | 哥伦比亚 vs 加纳：哥伦比亚 大小 1.5 | 大 | 52.5% | 52.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-team-total-home-0pt5 | 哥伦比亚 vs 加纳：哥伦比亚 大小 0.5 | 大 | 82.5% | 82.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-team-total-home-2pt5 | 哥伦比亚 vs 加纳：哥伦比亚 大小 2.5 | 大 | 25.5% | 22.0% | -3.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-team-total-away-0pt5 | 哥伦比亚 vs 加纳：加纳 大小 0.5 | 大 | 46.5% | 46.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-team-total-away-1pt5 | 哥伦比亚 vs 加纳：加纳 大小 1.5 | 大 | 13.0% | 13.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-team-total-away-2pt5 | 哥伦比亚 vs 加纳：加纳 大小 2.5 | 大 | 2.9% | 0.1% | -2.8% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-first-half-team-total-home-0pt5 | 哥伦比亚 vs 加纳：哥伦比亚 上半场 大小 0.5 | 大 | 54.0% | 56.5% | +2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-first-half-team-total-home-1pt5 | 哥伦比亚 vs 加纳：哥伦比亚 上半场 大小 1.5 | 大 | 17.5% | 17.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-first-half-team-total-away-0pt5 | 哥伦比亚 vs 加纳：加纳 上半场 大小 0.5 | 大 | 23.0% | 23.0% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-first-half-team-total-away-1pt5 | 哥伦比亚 vs 加纳：加纳 上半场 大小 1.5 | 大 | 2.2% | 2.2% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-second-half-team-total-home-0pt5 | 哥伦比亚 vs 加纳：哥伦比亚 下半场 大小 0.5 | 大 | 62.0% | 64.5% | +2.5% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-second-half-team-total-home-1pt5 | 哥伦比亚 vs 加纳：哥伦比亚 下半场 大小 1.5 | 大 | 28.5% | 28.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-second-half-team-total-away-0pt5 | 哥伦比亚 vs 加纳：加纳 下半场 大小 0.5 | 大 | 32.5% | 32.5% | +0.0% | 偏低+ | 跳过 | edge 低于 4 个百分点 |
| fifwc-col-gha-2026-07-03-second-half-team-total-away-1pt5 | 哥伦比亚 vs 加纳：加纳 下半场 大小 1.5 | 大 | 6.5% | 6.5% | +0.0% | 低 | 跳过 | edge 低于 4 个百分点 |

## 策略观察项详细证据
### 阿根廷 vs 佛得角 | fifwc-arg-cvi-2026-07-03-spread-home-1pt5
- 候选项：让分：阿根廷 (-1.5) / 阿根廷；动作=小仓限价买入；参考方向=阿根廷；市场概率=61.5%；模型概率=67.0%；当前 edge=+5.5%；状态=小仓限价。
- 证据链：
  1. Polymarket market_slug=fifwc-arg-cvi-2026-07-03-spread-home-1pt5；参考方向市场概率=61.5%；模型概率=67.0%；edge=+5.5%。
  2. 同场盘口结构用于校验：市场类型=spread_lines；比赛=阿根廷 vs 佛得角；候选方向=让分：阿根廷 (-1.5) / 阿根廷。
  3. Cape Verde: All to know before FIFA World Cup knockout against Argentina - Al Jazeera | Al Jazeera | https://news.google.com/rss/articles/CBMirwFBVV95cUxPeWJFLWMwSXBfNzJ2NzFzWVFQMmFSS3NKdlZqUUE4XzM0eEFEa0xjcFRDMlR0QmpCaFNQc2VmZ1paakY1eDNYaWJiTThiWjJpMWpmSTBINUNLNVNTbGQyN3Q5Tnd0anFSek56TW9oNHVVa3BIcnJRR0htNUFJNDNsR0IxRV93UFFGNEJqNTRqTUJNZ2R6ZFNqSjQ3c0RxaUxmSVJ2ZWU3Y1VtZzRoWHhV0gG0AUFVX3lxTE15eTQxamM4Mk9PTHdrMXlSTDFmeEYxQVpBbmYwdjBZV3F6bTRGN2ZweTN3TU4wdlVIZlF6T1JqU2x5X05fdlJvMHEzWnQycm5wUXlQMjljc01FX0ZBS0I2VzZ5Sks4cXFzekJKRzZubHA5ZFNhaFQ5ckVNdVZ3UHV0cHM5TmhIWFBwczRTMkt3bkJsMXFWQnFfZThEYXAwZ2ROVkNpNHNDdjZXcDlqT0ZRWUpCZA?oc=5
  4. Cape Verde are celebrating one of World Cup’s greatest feats. Can they shock Messi and Argentina next? - The Athletic - The New York Times | The New York Times | https://news.google.com/rss/articles/CBMioAFBVV95cUxPd240TjdZTXZxX2dvQTBYMmhkamFkQkRlVWtjNnlMN3UyVjlmaTlia1BuNmFLQ2JJaHA0QnZXaFJIMExMdUZhR3gwSkVuaVFRX2NodVZJTFV5RDc5U09kWWhqYnhXUUU1aUQyVEstQzNDRGVFbzVDQVo4ckh2aUZ0VEhhcmM0ek4tbkFnRDVIVF9BbnNTUUxWYXhxREdlbDc5?oc=5
  5. World Cup 2026 R32 Argentina vs. Cape Verde Prediction: Knockout Preview & Best Bets - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMigwFBVV95cUxNT0lXWWRWbG5PSE84b3FYZmtreExnSW16T29JNXNheTlONXlnWU9fVXpQZmpsRzNVOVQ1LWdnVkpPLTVGV3FkRVlwS0dibWtrTzdpY1FEbjR5eEV6TWpRaWNaMktjeXRicGxMTlE5Vjk4eHRzclBobzBKNlB5U05XODNGUQ?oc=5
- 推理链：
  1. fifwc-arg-cvi-2026-07-03-spread-home-1pt5 是 阿根廷 vs 佛得角 的让分盘口；模型把胜平负优势和净胜球分布拆开处理，因此 让分：阿根廷 (-1.5) / 阿根廷 的市场概率 61.5% 与模型概率 67.0% 出现偏差。
  2. 该信号 edge 为 +5.5%，核心判断是当前让分价格相对胜率分布偏离，而不是把胜率直接等同于穿盘率。
  3. 如果临场价格移动超过 4 个百分点或首发改变净胜球路径，fifwc-arg-cvi-2026-07-03-spread-home-1pt5 需要降级为观察。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 哥伦比亚 vs 加纳 | fifwc-col-gha-2026-07-03-spread-home-3pt5
- 候选项：让分：哥伦比亚 (-3.5) / 否；动作=小仓限价买入；参考方向=否；市场概率=94.0%；模型概率=99.1%；当前 edge=+5.1%；状态=小仓限价。
- 证据链：
  1. Polymarket market_slug=fifwc-col-gha-2026-07-03-spread-home-3pt5；参考方向市场概率=94.0%；模型概率=99.1%；edge=+5.1%。
  2. 同场盘口结构用于校验：市场类型=spread_lines；比赛=哥伦比亚 vs 加纳；候选方向=让分：哥伦比亚 (-3.5) / 否。
  3. Colombia vs. Ghana - Kick-off time, team news, how to watch World Cup round of 32 clash - ESPN | ESPN | https://news.google.com/rss/articles/CBMiswFBVV95cUxOMjljXzBaZmpSZUVOQ3VOZHFxc0UwbUZSLXcwMlVpVVdzaTU2T0VWOHE0aUM3X0IwdWtaQVF2SmxnSGxjbkNzbWNjWWNsX1ZfcG1XNUR5OTRZNTRYUnJUWGRXbm1DbGFEa2NhaF9xM2FXRV9BRVJIRjZiT1JiSjBBdVgyR3Z4NTNUdHNZSnd1NHNVOHBDOW5DUi1laGZQdjlvdlJndnBBVVI4a3RaMW0wNWlpdw?oc=5
  4. Croatia grab second in World Cup Group L, Ghana through in third: Colombia or Portugal next? - The Athletic - The New York Times | The New York Times | https://news.google.com/rss/articles/CBMiowFBVV95cUxPcVI5UXFFbUpqRGViNndKUVd6TlNhYVFLVUF5LXU1UGgtVjFDSjJxa3E1cVdWTFhnc0I0cXJNeGluTnlpeC03aFNyU05GekxDOWFBRERWZ0RzZENkdmFISWx0cS1PZV82OG9uVC1iVlJUN0pnT0lIa3BIdW92NHlFcmNodldZb3dyQzRpYlRnaVJZc1hWdndDdWJVa1N6Y3o2d25B?oc=5
  5. PREVIEW | Colombia vs Ghana: team news, lineups, predictions (World Cup 04/07) - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMihgFBVV95cUxPNUxsS3RVSHpTbkFiTXlIX3FmM3pfRFRqNHVOSktpSzZtM3cwUXNJRGpRY3EwaXlRcnNOZS1xZkpNYnhPUmdrMjlPRTIwNUhycTE5NEFzY0pzZmszS2Jpc25PQTZIdnRQVEFfMGlFbG5BdzZzc0hhLUVRbl9VX0hWMkdaeEVwdw?oc=5
- 推理链：
  1. fifwc-col-gha-2026-07-03-spread-home-3pt5 是 哥伦比亚 vs 加纳 的让分盘口；模型把胜平负优势和净胜球分布拆开处理，因此 让分：哥伦比亚 (-3.5) / 否 的市场概率 94.0% 与模型概率 99.1% 出现偏差。
  2. 该信号 edge 为 +5.1%，核心判断是当前让分价格相对胜率分布偏离，而不是把胜率直接等同于穿盘率。
  3. 如果临场价格移动超过 4 个百分点或首发改变净胜球路径，fifwc-col-gha-2026-07-03-spread-home-3pt5 需要降级为观察。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 澳大利亚 vs 埃及 | fifwc-aus-egy-2026-07-03-btts
- 候选项：澳大利亚 vs 埃及: 双方均进球 / 是；动作=小仓限价买入；参考方向=是；市场概率=43.5%；模型概率=48.5%；当前 edge=+5.0%；状态=小仓限价。
- 证据链：
  1. Polymarket market_slug=fifwc-aus-egy-2026-07-03-btts；参考方向市场概率=43.5%；模型概率=48.5%；edge=+5.0%。
  2. 同场盘口结构用于校验：市场类型=btts；比赛=澳大利亚 vs 埃及；候选方向=澳大利亚 vs 埃及: 双方均进球 / 是。
  3. FIFA World Cup 2026: How to watch Australia vs Egypt in the round of 32 – head-to-head, full schedule - olympics.com | olympics.com | https://news.google.com/rss/articles/CBMiygFBVV95cUxQbkwtcEw0QWNvaGtzdVFMM0JsRlRrc083TDJ3cHZsMTY5dHYxVE84ejhjVUhYQUF5Zk15U0lfS1k5ZFVXeE1YMW0zclZlN2dRUTZTaDFxSjJaU2FqU1E5SVZwbjhIYlh2bENDS0tLSUMxdU1CcnRBOTUwTkRQU1kzREhGQTZSNFpIcVplTHRaem1sOEE4Q2VyZkRLTXdDUmxKODNaN1RwMDJCZmN1bTJxaUxJVng2REJvQXJKVFdFY2NxS0tUbXV0ZFZ3?oc=5
  4. PREVIEW | Australia vs Egypt: team news, lineups, predictions (World Cup 03/07) - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMihwFBVV95cUxOZ0FLS1pxQkp0VkdfUlc2VkhuUG1MMVJveS03eDktWlNfemliYWRsbDJMYy1wSlZZd0tPMjJvcVJ2cXRETXFlWllPZTNhNTExby1mXzNEdHhNTWdCY0xmZzY5c3UyQnZtbGM5endERVdnX05nWmRLMGV6clk2MmFhdFZGWHBNN1k?oc=5
  5. Why VAR ruled Iran’s ‘winner’ offside to put them at risk of World Cup exit as Egypt progress - The Athletic - The New York Times | The New York Times | https://news.google.com/rss/articles/CBMiiwFBVV95cUxOektvNTNPSlB1SHU3bTFlV2NNTl9fLTZfck9BS1JfSklUTGNvVG1pMTI2Y1lkTXZwczFGN3E2N0xoeGtjckZrS005clh0TTdwOTR5N19VSWg4RW9hdWpjWHZTc04zdUtSdXFMc3Biek40VkJ0eUxZYmdYZHA3YlpiUmFaU184TGs5Qjkw?oc=5
- 推理链：
  1. fifwc-aus-egy-2026-07-03-btts 是 澳大利亚 vs 埃及 的双方均进球盘口；同场两队 0.5 球队进球线没有否定弱侧进球路径，因此 澳大利亚 vs 埃及: 双方均进球 / 是 从市场概率 43.5% 上修到模型概率 48.5%。
  2. 该信号的 edge 为 +5.0%，来源是 BTTS 与球队进球数之间的结构差，不是因为单纯看好胜平负热门方。
  3. 若临场首发削弱任一方进球路径，fifwc-aus-egy-2026-07-03-btts 必须重新定价并取消小仓限价。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 阿根廷 vs 佛得角 | fifwc-arg-cvi-2026-07-03-first-half-team-total-home-1pt5
- 候选项：阿根廷 vs 佛得角：阿根廷 上半场 大小 1.5 / 大；动作=小仓限价买入；参考方向=大；市场概率=32.5%；模型概率=37.5%；当前 edge=+5.0%；状态=小仓限价。
- 证据链：
  1. Polymarket market_slug=fifwc-arg-cvi-2026-07-03-first-half-team-total-home-1pt5；参考方向市场概率=32.5%；模型概率=37.5%；edge=+5.0%。
  2. 同场盘口结构用于校验：市场类型=team_total_lines；比赛=阿根廷 vs 佛得角；候选方向=阿根廷 vs 佛得角：阿根廷 上半场 大小 1.5 / 大。
  3. Cape Verde: All to know before FIFA World Cup knockout against Argentina - Al Jazeera | Al Jazeera | https://news.google.com/rss/articles/CBMirwFBVV95cUxPeWJFLWMwSXBfNzJ2NzFzWVFQMmFSS3NKdlZqUUE4XzM0eEFEa0xjcFRDMlR0QmpCaFNQc2VmZ1paakY1eDNYaWJiTThiWjJpMWpmSTBINUNLNVNTbGQyN3Q5Tnd0anFSek56TW9oNHVVa3BIcnJRR0htNUFJNDNsR0IxRV93UFFGNEJqNTRqTUJNZ2R6ZFNqSjQ3c0RxaUxmSVJ2ZWU3Y1VtZzRoWHhV0gG0AUFVX3lxTE15eTQxamM4Mk9PTHdrMXlSTDFmeEYxQVpBbmYwdjBZV3F6bTRGN2ZweTN3TU4wdlVIZlF6T1JqU2x5X05fdlJvMHEzWnQycm5wUXlQMjljc01FX0ZBS0I2VzZ5Sks4cXFzekJKRzZubHA5ZFNhaFQ5ckVNdVZ3UHV0cHM5TmhIWFBwczRTMkt3bkJsMXFWQnFfZThEYXAwZ2ROVkNpNHNDdjZXcDlqT0ZRWUpCZA?oc=5
  4. Cape Verde are celebrating one of World Cup’s greatest feats. Can they shock Messi and Argentina next? - The Athletic - The New York Times | The New York Times | https://news.google.com/rss/articles/CBMioAFBVV95cUxPd240TjdZTXZxX2dvQTBYMmhkamFkQkRlVWtjNnlMN3UyVjlmaTlia1BuNmFLQ2JJaHA0QnZXaFJIMExMdUZhR3gwSkVuaVFRX2NodVZJTFV5RDc5U09kWWhqYnhXUUU1aUQyVEstQzNDRGVFbzVDQVo4ckh2aUZ0VEhhcmM0ek4tbkFnRDVIVF9BbnNTUUxWYXhxREdlbDc5?oc=5
  5. World Cup 2026 R32 Argentina vs. Cape Verde Prediction: Knockout Preview & Best Bets - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMigwFBVV95cUxNT0lXWWRWbG5PSE84b3FYZmtreExnSW16T29JNXNheTlONXlnWU9fVXpQZmpsRzNVOVQ1LWdnVkpPLTVGV3FkRVlwS0dibWtrTzdpY1FEbjR5eEV6TWpRaWNaMktjeXRicGxMTlE5Vjk4eHRzclBobzBKNlB5U05XODNGUQ?oc=5
- 推理链：
  1. fifwc-arg-cvi-2026-07-03-first-half-team-total-home-1pt5 是 阿根廷 vs 佛得角 的球队进球数盘口；模型用胜平负、BTTS 和该队进球线交叉校验 阿根廷 vs 佛得角：阿根廷 上半场 大小 1.5 / 大，模型概率为 37.5%。
  2. 市场参考概率为 32.5%，edge 为 +5.0%；该信号来自球队进球线和比赛层面价格的结构差。
  3. 若该队 0.5/1.5 进球线或 BTTS 临场反向移动，fifwc-arg-cvi-2026-07-03-first-half-team-total-home-1pt5 需要取消。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 阿根廷 vs 佛得角 | fifwc-arg-cvi-2026-07-03-second-half-team-total-home-1pt5
- 候选项：阿根廷 vs 佛得角：阿根廷 下半场 大小 1.5 / 大；动作=小仓限价买入；参考方向=大；市场概率=38.5%；模型概率=43.5%；当前 edge=+5.0%；状态=小仓限价。
- 证据链：
  1. Polymarket market_slug=fifwc-arg-cvi-2026-07-03-second-half-team-total-home-1pt5；参考方向市场概率=38.5%；模型概率=43.5%；edge=+5.0%。
  2. 同场盘口结构用于校验：市场类型=team_total_lines；比赛=阿根廷 vs 佛得角；候选方向=阿根廷 vs 佛得角：阿根廷 下半场 大小 1.5 / 大。
  3. Cape Verde: All to know before FIFA World Cup knockout against Argentina - Al Jazeera | Al Jazeera | https://news.google.com/rss/articles/CBMirwFBVV95cUxPeWJFLWMwSXBfNzJ2NzFzWVFQMmFSS3NKdlZqUUE4XzM0eEFEa0xjcFRDMlR0QmpCaFNQc2VmZ1paakY1eDNYaWJiTThiWjJpMWpmSTBINUNLNVNTbGQyN3Q5Tnd0anFSek56TW9oNHVVa3BIcnJRR0htNUFJNDNsR0IxRV93UFFGNEJqNTRqTUJNZ2R6ZFNqSjQ3c0RxaUxmSVJ2ZWU3Y1VtZzRoWHhV0gG0AUFVX3lxTE15eTQxamM4Mk9PTHdrMXlSTDFmeEYxQVpBbmYwdjBZV3F6bTRGN2ZweTN3TU4wdlVIZlF6T1JqU2x5X05fdlJvMHEzWnQycm5wUXlQMjljc01FX0ZBS0I2VzZ5Sks4cXFzekJKRzZubHA5ZFNhaFQ5ckVNdVZ3UHV0cHM5TmhIWFBwczRTMkt3bkJsMXFWQnFfZThEYXAwZ2ROVkNpNHNDdjZXcDlqT0ZRWUpCZA?oc=5
  4. Cape Verde are celebrating one of World Cup’s greatest feats. Can they shock Messi and Argentina next? - The Athletic - The New York Times | The New York Times | https://news.google.com/rss/articles/CBMioAFBVV95cUxPd240TjdZTXZxX2dvQTBYMmhkamFkQkRlVWtjNnlMN3UyVjlmaTlia1BuNmFLQ2JJaHA0QnZXaFJIMExMdUZhR3gwSkVuaVFRX2NodVZJTFV5RDc5U09kWWhqYnhXUUU1aUQyVEstQzNDRGVFbzVDQVo4ckh2aUZ0VEhhcmM0ek4tbkFnRDVIVF9BbnNTUUxWYXhxREdlbDc5?oc=5
  5. World Cup 2026 R32 Argentina vs. Cape Verde Prediction: Knockout Preview & Best Bets - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMigwFBVV95cUxNT0lXWWRWbG5PSE84b3FYZmtreExnSW16T29JNXNheTlONXlnWU9fVXpQZmpsRzNVOVQ1LWdnVkpPLTVGV3FkRVlwS0dibWtrTzdpY1FEbjR5eEV6TWpRaWNaMktjeXRicGxMTlE5Vjk4eHRzclBobzBKNlB5U05XODNGUQ?oc=5
- 推理链：
  1. fifwc-arg-cvi-2026-07-03-second-half-team-total-home-1pt5 是 阿根廷 vs 佛得角 的球队进球数盘口；模型用胜平负、BTTS 和该队进球线交叉校验 阿根廷 vs 佛得角：阿根廷 下半场 大小 1.5 / 大，模型概率为 43.5%。
  2. 市场参考概率为 38.5%，edge 为 +5.0%；该信号来自球队进球线和比赛层面价格的结构差。
  3. 若该队 0.5/1.5 进球线或 BTTS 临场反向移动，fifwc-arg-cvi-2026-07-03-second-half-team-total-home-1pt5 需要取消。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 阿根廷 vs 佛得角 | fifwc-arg-cvi-2026-07-03-total-5pt5
- 候选项：阿根廷 vs 佛得角：总进球大小 5.5 / 否；动作=条件观察；参考方向=否；市场概率=91.5%；模型概率=96.0%；当前 edge=+4.5%；状态=仅观察。
- 证据链：
  1. Polymarket market_slug=fifwc-arg-cvi-2026-07-03-total-5pt5；参考方向市场概率=91.5%；模型概率=96.0%；edge=+4.5%。
  2. 同场盘口结构用于校验：市场类型=totals_lines；比赛=阿根廷 vs 佛得角；候选方向=阿根廷 vs 佛得角：总进球大小 5.5 / 否。
  3. Cape Verde: All to know before FIFA World Cup knockout against Argentina - Al Jazeera | Al Jazeera | https://news.google.com/rss/articles/CBMirwFBVV95cUxPeWJFLWMwSXBfNzJ2NzFzWVFQMmFSS3NKdlZqUUE4XzM0eEFEa0xjcFRDMlR0QmpCaFNQc2VmZ1paakY1eDNYaWJiTThiWjJpMWpmSTBINUNLNVNTbGQyN3Q5Tnd0anFSek56TW9oNHVVa3BIcnJRR0htNUFJNDNsR0IxRV93UFFGNEJqNTRqTUJNZ2R6ZFNqSjQ3c0RxaUxmSVJ2ZWU3Y1VtZzRoWHhV0gG0AUFVX3lxTE15eTQxamM4Mk9PTHdrMXlSTDFmeEYxQVpBbmYwdjBZV3F6bTRGN2ZweTN3TU4wdlVIZlF6T1JqU2x5X05fdlJvMHEzWnQycm5wUXlQMjljc01FX0ZBS0I2VzZ5Sks4cXFzekJKRzZubHA5ZFNhaFQ5ckVNdVZ3UHV0cHM5TmhIWFBwczRTMkt3bkJsMXFWQnFfZThEYXAwZ2ROVkNpNHNDdjZXcDlqT0ZRWUpCZA?oc=5
  4. Cape Verde are celebrating one of World Cup’s greatest feats. Can they shock Messi and Argentina next? - The Athletic - The New York Times | The New York Times | https://news.google.com/rss/articles/CBMioAFBVV95cUxPd240TjdZTXZxX2dvQTBYMmhkamFkQkRlVWtjNnlMN3UyVjlmaTlia1BuNmFLQ2JJaHA0QnZXaFJIMExMdUZhR3gwSkVuaVFRX2NodVZJTFV5RDc5U09kWWhqYnhXUUU1aUQyVEstQzNDRGVFbzVDQVo4ckh2aUZ0VEhhcmM0ek4tbkFnRDVIVF9BbnNTUUxWYXhxREdlbDc5?oc=5
  5. World Cup 2026 R32 Argentina vs. Cape Verde Prediction: Knockout Preview & Best Bets - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMigwFBVV95cUxNT0lXWWRWbG5PSE84b3FYZmtreExnSW16T29JNXNheTlONXlnWU9fVXpQZmpsRzNVOVQ1LWdnVkpPLTVGV3FkRVlwS0dibWtrTzdpY1FEbjR5eEV6TWpRaWNaMktjeXRicGxMTlE5Vjk4eHRzclBobzBKNlB5U05XODNGUQ?oc=5
- 推理链：
  1. fifwc-arg-cvi-2026-07-03-total-5pt5 是 阿根廷 vs 佛得角 的总进球盘口；模型用 BTTS、球队进球线和同场大小球阶梯检查总进球分布，得到 阿根廷 vs 佛得角：总进球大小 5.5 / 否 模型概率 96.0%。
  2. 市场参考概率为 91.5%，结构化 edge 为 +4.5%；该 edge 来自同场盘口阶梯一致性，而不是外部硬统计断言。
  3. 如果 BTTS 或球队进球线临场反向移动，fifwc-arg-cvi-2026-07-03-total-5pt5 的总进球信号失效。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 澳大利亚 vs 埃及 | fifwc-aus-egy-2026-07-03-spread-away-2pt5
- 候选项：让分：埃及 (-2.5) / 否；动作=条件观察；参考方向=否；市场概率=95.4%；模型概率=99.9%；当前 edge=+4.5%；状态=仅观察。
- 证据链：
  1. Polymarket market_slug=fifwc-aus-egy-2026-07-03-spread-away-2pt5；参考方向市场概率=95.4%；模型概率=99.9%；edge=+4.5%。
  2. 同场盘口结构用于校验：市场类型=spread_lines；比赛=澳大利亚 vs 埃及；候选方向=让分：埃及 (-2.5) / 否。
  3. FIFA World Cup 2026: How to watch Australia vs Egypt in the round of 32 – head-to-head, full schedule - olympics.com | olympics.com | https://news.google.com/rss/articles/CBMiygFBVV95cUxQbkwtcEw0QWNvaGtzdVFMM0JsRlRrc083TDJ3cHZsMTY5dHYxVE84ejhjVUhYQUF5Zk15U0lfS1k5ZFVXeE1YMW0zclZlN2dRUTZTaDFxSjJaU2FqU1E5SVZwbjhIYlh2bENDS0tLSUMxdU1CcnRBOTUwTkRQU1kzREhGQTZSNFpIcVplTHRaem1sOEE4Q2VyZkRLTXdDUmxKODNaN1RwMDJCZmN1bTJxaUxJVng2REJvQXJKVFdFY2NxS0tUbXV0ZFZ3?oc=5
  4. PREVIEW | Australia vs Egypt: team news, lineups, predictions (World Cup 03/07) - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMihwFBVV95cUxOZ0FLS1pxQkp0VkdfUlc2VkhuUG1MMVJveS03eDktWlNfemliYWRsbDJMYy1wSlZZd0tPMjJvcVJ2cXRETXFlWllPZTNhNTExby1mXzNEdHhNTWdCY0xmZzY5c3UyQnZtbGM5endERVdnX05nWmRLMGV6clk2MmFhdFZGWHBNN1k?oc=5
  5. Why VAR ruled Iran’s ‘winner’ offside to put them at risk of World Cup exit as Egypt progress - The Athletic - The New York Times | The New York Times | https://news.google.com/rss/articles/CBMiiwFBVV95cUxOektvNTNPSlB1SHU3bTFlV2NNTl9fLTZfck9BS1JfSklUTGNvVG1pMTI2Y1lkTXZwczFGN3E2N0xoeGtjckZrS005clh0TTdwOTR5N19VSWg4RW9hdWpjWHZTc04zdUtSdXFMc3Biek40VkJ0eUxZYmdYZHA3YlpiUmFaU184TGs5Qjkw?oc=5
- 推理链：
  1. fifwc-aus-egy-2026-07-03-spread-away-2pt5 是 澳大利亚 vs 埃及 的让分盘口；模型把胜平负优势和净胜球分布拆开处理，因此 让分：埃及 (-2.5) / 否 的市场概率 95.4% 与模型概率 99.9% 出现偏差。
  2. 该信号 edge 为 +4.5%，核心判断是当前让分价格相对胜率分布偏离，而不是把胜率直接等同于穿盘率。
  3. 如果临场价格移动超过 4 个百分点或首发改变净胜球路径，fifwc-aus-egy-2026-07-03-spread-away-2pt5 需要降级为观察。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 哥伦比亚 vs 加纳 | fifwc-col-gha-2026-07-03-spread-home-2pt5
- 候选项：让分：哥伦比亚 (-2.5) / 否；动作=条件观察；参考方向=否；市场概率=82.5%；模型概率=87.0%；当前 edge=+4.5%；状态=仅观察。
- 证据链：
  1. Polymarket market_slug=fifwc-col-gha-2026-07-03-spread-home-2pt5；参考方向市场概率=82.5%；模型概率=87.0%；edge=+4.5%。
  2. 同场盘口结构用于校验：市场类型=spread_lines；比赛=哥伦比亚 vs 加纳；候选方向=让分：哥伦比亚 (-2.5) / 否。
  3. Colombia vs. Ghana - Kick-off time, team news, how to watch World Cup round of 32 clash - ESPN | ESPN | https://news.google.com/rss/articles/CBMiswFBVV95cUxOMjljXzBaZmpSZUVOQ3VOZHFxc0UwbUZSLXcwMlVpVVdzaTU2T0VWOHE0aUM3X0IwdWtaQVF2SmxnSGxjbkNzbWNjWWNsX1ZfcG1XNUR5OTRZNTRYUnJUWGRXbm1DbGFEa2NhaF9xM2FXRV9BRVJIRjZiT1JiSjBBdVgyR3Z4NTNUdHNZSnd1NHNVOHBDOW5DUi1laGZQdjlvdlJndnBBVVI4a3RaMW0wNWlpdw?oc=5
  4. Croatia grab second in World Cup Group L, Ghana through in third: Colombia or Portugal next? - The Athletic - The New York Times | The New York Times | https://news.google.com/rss/articles/CBMiowFBVV95cUxPcVI5UXFFbUpqRGViNndKUVd6TlNhYVFLVUF5LXU1UGgtVjFDSjJxa3E1cVdWTFhnc0I0cXJNeGluTnlpeC03aFNyU05GekxDOWFBRERWZ0RzZENkdmFISWx0cS1PZV82OG9uVC1iVlJUN0pnT0lIa3BIdW92NHlFcmNodldZb3dyQzRpYlRnaVJZc1hWdndDdWJVa1N6Y3o2d25B?oc=5
  5. PREVIEW | Colombia vs Ghana: team news, lineups, predictions (World Cup 04/07) - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMihgFBVV95cUxPNUxsS3RVSHpTbkFiTXlIX3FmM3pfRFRqNHVOSktpSzZtM3cwUXNJRGpRY3EwaXlRcnNOZS1xZkpNYnhPUmdrMjlPRTIwNUhycTE5NEFzY0pzZmszS2Jpc25PQTZIdnRQVEFfMGlFbG5BdzZzc0hhLUVRbl9VX0hWMkdaeEVwdw?oc=5
- 推理链：
  1. fifwc-col-gha-2026-07-03-spread-home-2pt5 是 哥伦比亚 vs 加纳 的让分盘口；模型把胜平负优势和净胜球分布拆开处理，因此 让分：哥伦比亚 (-2.5) / 否 的市场概率 82.5% 与模型概率 87.0% 出现偏差。
  2. 该信号 edge 为 +4.5%，核心判断是当前让分价格相对胜率分布偏离，而不是把胜率直接等同于穿盘率。
  3. 如果临场价格移动超过 4 个百分点或首发改变净胜球路径，fifwc-col-gha-2026-07-03-spread-home-2pt5 需要降级为观察。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。

### 哥伦比亚 vs 加纳 | fifwc-col-gha-2026-07-03-spread-home-1pt5
- 候选项：让分：哥伦比亚 (-1.5) / 否；动作=条件观察；参考方向=否；市场概率=62.5%；模型概率=58.5%；当前 edge=-4.0%；状态=仅观察。
- 证据链：
  1. Polymarket market_slug=fifwc-col-gha-2026-07-03-spread-home-1pt5；参考方向市场概率=62.5%；模型概率=58.5%；edge=-4.0%。
  2. 同场盘口结构用于校验：市场类型=spread_lines；比赛=哥伦比亚 vs 加纳；候选方向=让分：哥伦比亚 (-1.5) / 否。
  3. Colombia vs. Ghana - Kick-off time, team news, how to watch World Cup round of 32 clash - ESPN | ESPN | https://news.google.com/rss/articles/CBMiswFBVV95cUxOMjljXzBaZmpSZUVOQ3VOZHFxc0UwbUZSLXcwMlVpVVdzaTU2T0VWOHE0aUM3X0IwdWtaQVF2SmxnSGxjbkNzbWNjWWNsX1ZfcG1XNUR5OTRZNTRYUnJUWGRXbm1DbGFEa2NhaF9xM2FXRV9BRVJIRjZiT1JiSjBBdVgyR3Z4NTNUdHNZSnd1NHNVOHBDOW5DUi1laGZQdjlvdlJndnBBVVI4a3RaMW0wNWlpdw?oc=5
  4. Croatia grab second in World Cup Group L, Ghana through in third: Colombia or Portugal next? - The Athletic - The New York Times | The New York Times | https://news.google.com/rss/articles/CBMiowFBVV95cUxPcVI5UXFFbUpqRGViNndKUVd6TlNhYVFLVUF5LXU1UGgtVjFDSjJxa3E1cVdWTFhnc0I0cXJNeGluTnlpeC03aFNyU05GekxDOWFBRERWZ0RzZENkdmFISWx0cS1PZV82OG9uVC1iVlJUN0pnT0lIa3BIdW92NHlFcmNodldZb3dyQzRpYlRnaVJZc1hWdndDdWJVa1N6Y3o2d25B?oc=5
  5. PREVIEW | Colombia vs Ghana: team news, lineups, predictions (World Cup 04/07) - Yahoo Sports | Yahoo Sports | https://news.google.com/rss/articles/CBMihgFBVV95cUxPNUxsS3RVSHpTbkFiTXlIX3FmM3pfRFRqNHVOSktpSzZtM3cwUXNJRGpRY3EwaXlRcnNOZS1xZkpNYnhPUmdrMjlPRTIwNUhycTE5NEFzY0pzZmszS2Jpc25PQTZIdnRQVEFfMGlFbG5BdzZzc0hhLUVRbl9VX0hWMkdaeEVwdw?oc=5
- 推理链：
  1. fifwc-col-gha-2026-07-03-spread-home-1pt5 是 哥伦比亚 vs 加纳 的让分盘口；模型把胜平负优势和净胜球分布拆开处理，因此 让分：哥伦比亚 (-1.5) / 否 的市场概率 62.5% 与模型概率 58.5% 出现偏差。
  2. 该信号 edge 为 -4.0%，核心判断是当前让分价格相对胜率分布偏离，而不是把胜率直接等同于穿盘率。
  3. 如果临场价格移动超过 4 个百分点或首发改变净胜球路径，fifwc-col-gha-2026-07-03-spread-home-1pt5 需要降级为观察。
- 反证：
  1. 本次流程没有接入已验证的 Opta/WhoScored 技术统计源，也没有确认首发，因此仓位必须小，临场必须重新定价。
- 失效观察：
  1. 只有当价格达到触发价，且首发/伤停消息没有否定相关进球路径时，才允许把观察项升级为限价单。
