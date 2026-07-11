# 20260711 工作流说明：0709 连续升级版

## 继承而非重建

本轮以 0709 的生产轻量 P1/P2/P3 为基础，没有另起一套不可比较的模型。

保留部分：

- P1：时间衰减、ridge 收缩的国家队攻防 Poisson。
- P2：顺序 Elo + multinomial 1X2 校准，只审核相对强弱。
- P3：FIFA 当前赛事 xG，小样本权重上限 25%。
- 外部信息血缘：sportsbook 为市场知情簇主基准，Opta 同簇敏感性，Polymarket 只作交易价格。
- 费用、CLOB 深度、maker/taker、fractional Kelly、同场相关性和两轮审核。
- 用户固定的费用及全部风险扣减后 1.5pp 门槛。

本轮升级：

1. 历史结果改成90分钟口径；有加时风险但无第二来源确认的比赛直接剔除。
2. FIFA 报告若只提供120分钟汇总 xG，整场从 P3 剔除，不再线性缩放。
3. 缺失盘口只允许由同市场家族的直接盘口联合投影；投影器尚未完成 leave-one-line-out 验证时不进入正式候选。
4. 情景 P10 明确标记为未校准，不能充当统计下界。
5. 概率允许双向修正。1X2先将博彩共识与Opta按75%/25%融合为外部概率，再给内部模型25%权重，名义中心权重为博彩56.25%、Opta18.75%、内部25%；O/U 2.5没有Opta直接概率时按博彩75%、内部25%。
6. 不再使用逐outcome的 `min()` 和固定2pp双重缓冲。改为 `u=max(0.5pp, 0.5*博彩来源分歧 + 0.1*内外模型分歧 + 0.25pp数据质量惩罚)`，方向性保守概率为 `p_trade=p_center-u`。固定1.5pp仍是费用和不确定性之后的独立下注门槛。
7. Kelly必须使用包含taker fee的有效成交成本，不能用裸成交价高估仓位。

## 本轮数据冻结

- 时间窗口：2026-07-11 21:09 北京时间起未来24小时。
- 比赛：Norway vs England、Argentina vs Switzerland。
- Polymarket：两个主事件和 More Markets 的完整目标订单簿，共40个市场。
- 角球：两个 Polymarket 事件均未发现可执行角球市场，因此没有角球正式候选。
- 外部直接盘口：BetMGM 90分钟 1X2 与 O/U 2.5；Oddschecker 交叉核对；Opta 仅作同簇敏感性。

## 90分钟证据规则

`data/extra_time_verification_0711.json` 保存四场与 P3 有关的加时证据。

- Belgium 2-2 Senegal（90分钟），Belgium 3-2 AET。
- Argentina 1-1 Cape Verde（90分钟），Argentina 3-2 AET。
- Netherlands 1-1 Morocco（90分钟及AET），Morocco点球晋级。
- Switzerland 0-0 Colombia（90分钟及AET），Switzerland点球晋级。

P1/P2 使用经第二来源确认的 `score_90`；其他841条加时/点球或范围不确定记录剔除。P3剔除上述四份120分钟汇总报告。

## 当前未完成但不伪装成完成的项目

- P1 嵌套 walk-forward 仍是 shadow；当前指标仍来自单一时间 holdout。
- totals/1X2 的经验覆盖区间和 beta calibration 尚未完成。
- 相邻盘口投影器尚未完成历史 leave-one-line-out 验证。
- maker 成交概率和 CLV 需要真实订单样本。

这些限制通过证据门槛和保守 `p_trade` 处理，不通过临时提高1.5pp门槛处理。
