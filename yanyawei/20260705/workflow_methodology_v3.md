# World Cup Polymarket 决策工作流 v3

## 1. 目标函数

目标不是提高单场命中率，也不是增加下注数量，而是在真实成交约束下提高长期费用后对数财富增长：

`maximize E[log(bankroll_after)]`

每笔交易必须同时满足：

1. 概率来自赛前可获得的信息，无未来信息泄漏。
2. 预测来源按信息血缘去重，不能把同一市场信号重复计权。
3. 以实际可成交订单簿价格计算费用、滑点和仓位。
4. 在模型误差、信息延迟和多盘口筛选偏差后仍有足够 Edge。
5. 组合最坏场景与相关敞口处于预设上限内。

## 2. 对 0705 研究综述的甄别

### 2.1 可以采用

| 主张 | 裁决 | 用法 |
|---|---|---|
| 时间顺序 walk-forward 回测 | 采用 | 所有权重、衰减、校准方法必须由历史赛前折验证 |
| 层级收缩 | 采用 | 国家队样本少，球队攻防参数必须向 Elo/总体均值收缩 |
| Dixon-Coles 低比分修正 | 有条件采用 | `rho` 必须估计并回测，禁止固定照抄 `-0.12` |
| Elo 及近期轨迹 | 采用为候选特征 | 先作为独立模型输入，只有改善样本外 log-loss/RPS 才进入生产 |
| 统一比分分布 | 采用 | 同一分布推导 1X2、让球、大小球和 BTTS，保证数学一致 |
| 亚洲让球市场是强基准 | 采用 | 低水位 sharp consensus 用作外部基准，不自动视为绝对真值 |
| 环境与旅行信息 | 采用为风险变量 | 未经本项目回测前，只扩大不确定性或触发人工复核，不直接硬加固定 xG |

### 2.2 需要修正或拒绝

| 综述主张 | 问题 | v3 处理 |
|---|---|---|
| 体育 taker 参数已从 `0.03` 升至 `0.06` | 与 Polymarket 官方文档及具体世界杯市场 API 不符 | 每个市场实时读取 fee schedule；体育默认不得硬编码为 `0.06` |
| maker 固定获得 `-0.0125` 返利 | 官方 maker fee 是 0；返利来自共享池，金额事前不确定 | 基础 EV 中 maker rebate 记 0，实际到账后才入账 |
| Yes Bias 可直接推出世界杯 Under/No 有 Edge | SSRN 论文只称偏差存在于部分市场，摘要特别举 Mention Markets；没有体育子样本证明 | 不给 Under/No 方向先验奖励，先做本项目体育盘回测 |
| Opta 是独立于市场的模型 | Opta 官方说明比赛预测使用博彩赔率与 Power Rankings | Opta 与 sharp odds 归入同一“市场知情簇”，不得和赔率重复满权重 |
| 固定 `rho=-0.12`、四年半衰期、固定比赛权重 | 都是特定模型参数，不具备跨数据集普适性 | 用 walk-forward 选择；样本不足时采用宽先验而不是假精确值 |
| SDR 的 RPS 0.127 可直接作为生产模型 | 论文真实存在，但目前是新 arXiv 预印本，只在 2018/2022 两届小测试集评估 | 作为 challenger，复现后再决定；本期不因其高指标直接加权 |
| 开源项目自报表现等于独立验证 | 代码有参考价值，但回测口径、数据清洗和选择偏差仍需复核 | 只作为 challenger 或实现参考，不当作已验证外部概率 |
| 海拔每 1000m 固定增加 0.5 球 | 原研究描述的是有长期适应优势的南美主场历史，不等于中立世界杯场地的通用系数 | 仅在球队适应差异、场地和到达时间均明确时作为风险标记 |
| 10K-50K 蒙特卡洛本身提高预测力 | 模拟次数只减少数值误差，不修复错误模型 | 先改善模型和校准，再把 MC 提高到数值误差足够小 |

## 3. 信息血缘与去重

每个概率来源必须登记 `source_id`、抓取时间、原始输入和信息类别：

### A. 独立统计簇

- 历史国家队赛果、对手强度、比赛类型和时间衰减。
- FIFA 2026 官方 xG、射门和红牌信息。
- Elo 当前值及近期轨迹。
- 阵容可用性、休息时间、旅行和场地信息。

### B. 市场知情簇

- 低水位亚洲让球与大小球 consensus。
- 传统博彩公司共识赔率。
- Opta 单场模拟，因为其官方模型使用博彩赔率。

### C. 交易目标簇

- Polymarket Gamma、CLOB、成交历史和深度。

**核心规则**：C 簇只用于发现价格和执行，不进入独立 fair probability。B 簇内部先聚合成一个基准，Opta 与博彩公司不能被当成多个独立投票。除非经过历史赛前回测证明，不能把 Polymarket 本身既作为概率输入又作为被比较的交易价格。

## 4. 数据冻结与合同审计

每次决策建立不可变 `as_of` 时间：

1. 保存比赛、场地、开赛时间和 90 分钟/晋级结算规则。
2. 保存 Gamma event、market、condition ID、token ID 和 outcome 顺序。
3. 保存 CLOB 双边深度，不只保存最佳价。
4. 保存每个外部来源的发布时间和抓取时间。
5. 赛后不得覆盖赛前文件，只能新增结果与复盘文件。

合同审计必须验证：

- `France -1.5 NO` 是否严格等价于对手 `+1.5`。
- 平局、加时、点球是否计入。
- 盘口线是否发生变化。
- 买入的是 YES token 还是 NO token，不能用 `1 - 页面价格` 假设可成交。

## 5. 独立概率模型

### 5.1 生产模型 P1：层级时间衰减进球模型

以至少最近 8-10 年国际比赛为主体，而不是只用本届 3-4 场：

`log(lambda_i,j) = mu + attack_i - defense_j + venue + match_type + rest + lineup`

- 攻防参数使用层级先验，向 Elo 和总体均值收缩。
- 时间衰减、比赛类型权重和主场参数由 walk-forward 回测选择。
- 红牌比赛按红牌发生时间建模；无法建模时剔除红牌后的比赛片段或降低权重。
- 2026 FIFA xG 作为近期状态观测，通过收缩更新长期实力；不再以 85% 权重直接支配 lambda。
- 使用 Dixon-Coles 或其他低比分相关结构，但 `rho` 按训练折估计。

### 5.2 生产模型 P2：Elo 结果模型

独立输出 1X2 概率，用于检查 P1 的比分分布是否异常：

- 当前 Elo 差是基线。
- 近期 Elo 轨迹是候选增量特征。
- 不从 P2 伪造大小球或 BTTS；没有进球分布支持的盘口标记为不可评估。

### 5.3 近期赛事模型 P3

只使用本届 FIFA xG、xGA、射门质量和对手强度，输出近期状态修正：

- 小样本必须向 P1 收缩。
- 默认有效样本少于 8 场时，P3 权重不得高于独立模型簇的 25%。
- 极端终结效率不能直接持续外推；实际进球只作为有限修正。

### 5.4 Challenger 模型

SDR、开源 Bayesian Dixon-Coles、XGBoost、角球/卡牌专项模型均放在 challenger 层。进入生产必须满足：

1. 可复现训练数据与赛前信息边界。
2. 至少两个历史大赛或足够国际比赛的 walk-forward 结果。
3. 相比当前生产模型改善 log-loss/RPS，而不只是准确率。
4. 概率校准没有明显恶化。
5. 加入集成后仍有增量，而非重复 Elo 或赔率信号。

## 6. 校准与集成

### 6.1 回测协议

- 严格按比赛时间滚动训练，预测时只能看此前数据。
- 2018、2022 和 2026 分赛事报告，也报告总体结果。
- 指标：log-loss、Brier、RPS、ECE、校准斜率和 CLV。
- 按 1X2、让球、大小球、BTTS 分开评估；不能用 1X2 的好成绩证明角球模型有效。
- 保存每一折的模型版本、超参数和原始预测。

### 6.2 概率校准

- 样本足够时比较 beta calibration、isotonic 和不校准基线。
- 校准器只能在训练窗口拟合，不能用当前世界杯未来结果。
- 样本不足时不做高自由度校准，改用更宽概率区间。

### 6.3 来源聚合

正式权重最终由样本外 log-loss stacking 学习。完成回测前，下一轮决策使用保守临时规则：

1. `p_independent`：P1/P2/P3 中可评估该盘口的模型中位数。
2. `p_sharp`：亚洲盘/低水位赔率去水后的共识；Opta只作为同簇核对，不重复加权。
3. `reliability`：独立簇相对 sharp 基准的可信系数。
4. `p_center = p_sharp + reliability * (p_independent - p_sharp)`。

临时 `reliability`：

- 0.10-0.20：只有本届小样本模型支持。
- 0.25-0.35：两个独立模型同向，数据完整。
- 0.40：模型已有样本外校准且阵容信息完整。
- 不得高于 0.40，直到本项目完成可审计回测。

这比固定“内部35% + Opta40% + 市场25%”更保守，也避免 Opta 与赔率重复计权。

对外部基准也遵守“直接证据优先”：1X2、O/U 2.5、BTTS 有直接低水位赔率时使用各自去水概率；只对缺少直接赔率的相邻让球或球队进球线使用外部 lambda 分布投影，并额外保留投影误差缓冲。不得用一个拟合比分分布覆盖更直接的盘口证据。

### 6.4 不确定性

输出后验或场景分布，不只输出点估计：

- `p_center`：中心概率。
- `p_low/p_high`：至少 80% 区间。
- `p_trade`：买入 YES 时使用保守下界，卖出或买 NO 时按对应结果下界计算。
- 来源分歧越大、数据越少、首发越不确定，区间越宽。

本轮采用以下可复现变换，而不是主观选择“保守一点”的概率：

`p_center = p_sharp + reliability * (p_independent - p_sharp)`

`p_trade = p_sharp + reliability * (p10_independent - p_sharp) - external_uncertainty_buffer`

其中 `p10_independent` 是独立模型情景分布对目标合约结果的第 10 百分位；外部不确定性缓冲为 1.0-2.0pp，按信息缺失和模型冲突预先设定。对互补结果必须先转换完整概率分布，再重新取该结果的分位数，不能简单使用 `1-p10`。

不能因为几个高度相关的来源同向就缩窄区间。

## 7. 市场扫描与候选门槛

### 7.1 可评估市场

- P1 比分矩阵：1X2、亚洲让球、O/U、BTTS。
- P2：只参与 1X2 审核。
- 角球、卡牌、首个进球者等盘口，没有专项回测模型时一律跳过。
- 生产扫描只保留主流线与具有足够深度的相邻线。极端让球和极端大小球即使数学上可计算，也会放大尾部模型误差与多重筛选偏差，默认不进入候选池。

### 7.2 多重筛选与赢家诅咒

扫描大量盘口后最高 Edge 往往被高估。每期必须记录扫描总数，并执行：

- 只因单一模型产生的最高 Edge，额外扣减至少 2pp。
- 多模型和 sharp 市场均强烈冲突时直接跳过，不用“大 Edge”抵消。
- 同一比赛的相关盘口视为一个假设族，最多选一个。
- 不为满足“下注更分散”降低门槛。

### 7.3 动态 Edge 门槛

对买入价格 `q`：

`fee_per_share = fee_rate * q * (1-q)`

`effective_cost = q + fee_per_share + slippage`

`robust_edge = p_trade - effective_cost`

入选需同时满足：

1. `robust_edge >= 3pp`；证据弱或来源冲突时要求 5pp。
2. `p_low > effective_cost`。
3. 订单簿深度足以在限价内成交全部计划仓位。
4. 最迟首发复核后仍满足门槛。

## 8. 费用、返利与执行

### 8.1 费用事实来源

- 每个市场从 CLOB market info/fee schedule 读取真实参数。
- 当前官方体育类别参考参数是 taker `0.03`、maker fee `0`，但仍以单市场 API 为准。
- maker rebate 来自共享池且事前不确定，基础 EV 和 Kelly 中按 0 处理。
- taker tier rebate 同样不预先计入，到账后作为执行收益单独记录。

### 8.2 可成交价格

- Taker 使用逐档订单簿计算 volume-weighted fill price，不用 best ask 乘全部仓位。
- Maker 单记录排队位置、挂单时间、是否成交和成交后盘口变化。
- `post-only` 未成交不算持仓。
- 价格快照超过 10 分钟、首发阶段超过 2 分钟即失效。

### 8.3 Maker 的逆向选择

maker 不是无条件优于 taker。临近首发时，旧报价被信息型交易者成交可能意味着坏消息：

- 重大阵容或天气消息窗口暂停挂单。
- 成交后 1、5、15 分钟记录 mid-price，评估 adverse selection。
- 只有历史 fill quality 为正时，才把 maker 作为主要执行方式。

## 9. 鲁棒 Kelly 与组合风险

使用费用和滑点后的成本 `c`：

`full_kelly = max(0, (p_trade - c) / (1-c))`

执行仓位：

`stake_fraction = full_kelly * kelly_fraction * confidence_multiplier`

临时生产参数：

- 已完成样本外校准：`kelly_fraction <= 0.10`。
- 未完成回测或依赖人工信息：`kelly_fraction <= 0.05`。
- 单笔实际成交上限：bankroll 的 0.75%。
- 单场所有相关盘口上限：1.0%。
- 同一球队、同一比赛日或同一因子簇上限：1.5%。
- 全部开放订单若成交后的总风险：3.0%。

用场景模拟计算组合损益，相关性来自共同比赛结果和共同球队路径；不能把每笔 Kelly 独立相加。冠军盘与该队单场晋级盘属于高度相关敞口。

## 10. 两代理两轮审计 v3

### 第一轮

分析代理生成全部概率、中间结果、候选和初始组合。审核代理必须逐项检查：

1. 合约方向、结算和 token 是否正确。
2. 是否存在未来信息泄漏或赛后覆盖。
3. Opta、赔率、Polymarket 是否被重复计权。
4. 概率是否来自适用盘口模型。
5. 费用是否来自该市场 API。
6. 深度、滑点和 maker 成交状态是否真实。
7. `p_trade` 是否真的是不确定性下界，而非主观挑选。
8. Kelly 是否只计算一次，组合相关风险是否超限。

分析代理对每条意见作 `接受 / 部分接受 / 拒绝`，必须给计算或来源，不能迎合。

### 第二轮

审核代理重点寻找返修引入的新问题，并做三项压力测试：

- 独立模型概率向 sharp 市场回归 50% 后，交易是否仍合格。
- 买价恶化 1-2c 后，交易是否仍合格。
- 一个关键球员缺阵或首发假设相反时，交易是否仍合格。

分析代理再次独立裁决并冻结最终版本。

## 11. 下一轮决策的实际运行顺序

1. **冻结时间**：列出未来目标比赛和市场，保存 `as_of`。
2. **合同审计**：核对结算、token、盘口线和开赛时间。
3. **采集 CLOB**：Gamma + order book 全深度 + 单市场 fee schedule。
4. **采集独立数据**：历史赛果/Elo、FIFA 2026 xG、伤停、预计首发、场地、休息和旅行。
5. **采集市场知情簇**：至少一个 sharp 亚洲盘来源；Opta作为同簇补充。
6. **运行 P1/P2/P3**：保存每层 lambda、概率、区间和模型版本。
7. **按血缘聚合**：生成 `p_independent`、`p_sharp`、`reliability`、`p_center` 和 `p_trade`。
8. **全盘口扫描**：记录所有被扫描市场，应用多重筛选扣减。
9. **费用与深度重算**：输出 maker/taker 各自的限价、滑点和 robust Edge。
10. **组合优化**：鲁棒 Kelly、相关性场景、单场和总风险约束。
11. **两轮审核**：保留所有接受、拒绝及理由。
12. **临场刷新**：T-60、T-15 各刷新一次；首发后重新计算，不追价。
13. **冻结与执行**：明确 `TAKER / POST_ONLY / SKIP`，未成交 maker 不计入仓位。
14. **赛后记录**：PnL、CLV、Brier/log-loss、成交后价格变化和误差归因。

## 12. 最终决策文件强制字段

每笔下注必须披露：

- 合约精确定义和 token。
- `as_of` 与来源时间。
- P1/P2/P3 的中间结果及适用范围。
- sharp 共识和 Opta 的信息血缘。
- `p_independent/p_sharp/reliability/p_center/p_low/p_trade`。
- 当前订单簿深度、计划成交均价、fee schedule 和滑点。
- robust Edge、压力测试结果和拒绝交易的阈值。
- Full Kelly、fraction、置信乘数、相关簇和最终 USDC。
- 首发、价格、盘口线和信息变化的撤单条件。

## 13. 主要来源

- [Polymarket official fees](https://docs.polymarket.com/trading/fees)
- [Polymarket maker rebates](https://docs.polymarket.com/market-makers/maker-rebates)
- [Opta prediction methodology](https://theanalyst.com/articles/opta-football-predictions)
- [Hegarty and Whelan: A Tale of Two Markets](https://www.karlwhelan.com/Papers/IJF.pdf)
- [Rezaei and Samadi: SDR of Elo Rating Histories](https://arxiv.org/abs/2606.24171)
- [Deleep et al.: How Wise is the Crowd?](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6322678)
- [0xNadr/wc2026](https://github.com/0xNadr/wc2026)
- [Hicruben World Cup prediction model](https://github.com/Hicruben/world-cup-2026-prediction-model)
- [Sports Medicine: 2026 World Cup environmental challenges](https://link.springer.com/article/10.1007/s40279-026-02398-4)

> 本工作流只定义研究与执行纪律，不保证盈利。任何未经样本外验证的高 Edge 都应先解释为模型风险，而不是机会。
