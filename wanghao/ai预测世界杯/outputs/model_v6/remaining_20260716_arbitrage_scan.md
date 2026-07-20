# Polymarket 订单簿套利扫描

快照：`data\raw\polymarket\semifinals_normalized_20260716_080158Z.csv`；扫描组合 168 个。

没有发现扣除显示费率后、按当前卖一可锁定正收益的套利组合。

## 最接近套利的组合

| 类型 | 全成本 | 距离保本 |
|---|---:|---:|
| binary_complement | 1.0020 | -0.0020 |
| binary_complement | 1.0020 | -0.0020 |
| binary_complement | 1.0022 | -0.0022 |
| binary_complement | 1.0023 | -0.0023 |
| binary_complement | 1.0025 | -0.0025 |
| binary_complement | 1.0029 | -0.0029 |
| binary_complement | 1.0030 | -0.0030 |
| binary_complement | 1.0030 | -0.0030 |
| binary_complement | 1.0030 | -0.0030 |
| binary_complement | 1.0031 | -0.0031 |

说明：这是静态快照扫描，不保证多腿同时成交。容量按一档卖盘粗估；成交延迟、撤单、部分成交和规则差异会消灭表面套利。