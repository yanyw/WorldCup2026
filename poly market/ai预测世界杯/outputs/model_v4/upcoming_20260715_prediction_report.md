# 世界杯后续比赛 Polymarket 预测与交易报告（v4）

生成时间（UTC）：2026-07-15T15:21:01.895372+00:00；盘口快照：`data\raw\polymarket\semifinals_normalized_20260715_151240Z.csv`。

## 核心预测

| 比赛（北京时间） | 主胜 | 平 | 客胜 | 大2.5 | BTTS | 预期进球 |
|---|---:|---:|---:|---:|---:|---:|
| England–Argentina（2026-07-16T03:00:00+08:00） | 35.5% | 32.0% | 32.5% | 41.5% | 49.5% | 1.20–1.14 |

## 游戏属性与临场因素审计

| 比赛 | FC26首发均值 | 综合属性差（主-客） | 阵型 | 主/客λ乘数 |
|---|---:|---:|---|---:|
| England–Argentina | 83.6–82.8 | +0.42 | 4-2-3-1 vs 4-1-3-2 | 1.018/1.001 |

FC 26 属性只以12%可靠度修正尖锐赔率/Elo/Poisson基线；裁判不做方向性偏置，只提高总进球尾部与情景不确定性。

## 可执行建议

当前没有合约同时通过 5pp 稳健边际、订单簿深度、成交量和价差过滤；建议不追价。

## 条件限价观察单（不按当前卖价追单）

| 比赛 | 合约与方向 | 当前卖价 | 5pp最高入场价 | 中心净边际 | 流动性 |
|---|---|---:|---:|---:|---:|
| England–Argentina | Both teams to score first half NO | 82.00% | 75.64% | +3.8% | A |
| England–Argentina | Second half over 1.5 YES | 39.00% | 23.31% | +1.6% | A |
| England–Argentina | Argentina (-1.5) YES | 12.00% | 2.40% | +1.4% | A |
| England–Argentina | England first half over 0.5 NO | 60.00% | 45.37% | +1.4% | C |
| England–Argentina | Both teams to score NO | 48.00% | 35.44% | +1.2% | A |
| England–Argentina | Total over 1.5 YES | 67.50% | 52.13% | +1.2% | A |
| England–Argentina | Second half over 0.5 YES | 74.00% | 59.23% | +1.0% | D |
| England–Argentina | First half over 0.5 NO | 38.00% | 24.43% | +1.0% | A |
| England–Argentina | First half over 1.5 NO | 75.00% | 60.87% | +0.8% | A |
| England–Argentina | Total over 2.5 YES | 39.50% | 23.40% | +0.8% | A |
| England–Argentina | Second half over 2.5 YES | 16.00% | 2.60% | +0.6% | C |
| England–Argentina | England 0-1 Argentina NO | 90.00% | 80.89% | +0.5% | A |
| England–Argentina | England 3-1 Argentina NO | 96.20% | 88.38% | +0.4% | A |
| England–Argentina | Total over 5.5 NO | 96.20% | 86.94% | +0.4% | A |
| England–Argentina | England 3-3 Argentina NO | 99.00% | 91.98% | +0.3% | A |

## 风险纪律

早盘允许观察 3c 价差，但不会降低 5pp 稳健边际；成交量不足 $1,000 的盘口不执行。高度相关盘口每场只保留一个下注，单场上限为本金 0.5%，并以 2.5% Kelly 和一档深度 0.5% 进一步压缩。赛前首发、伤病和尖锐赔率变化后必须重跑。

该报告是量化研究输出，不保证盈利，也不自动下单。