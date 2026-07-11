# 2026-07-09 工作流更新：未来 1 天 + 角球混入主流程

## 核心流程

1. 限定预测窗口：本版只处理未来约 24 小时内已经有 Polymarket 可执行市场的比赛。
2. 获取 Polymarket 快照：保留 bid/ask、order book、fee schedule、盘口类型和 kickoff time。
3. 建立内部模型：P1 历史进球 Poisson、P2 Elo 1X2 强弱校准、P3 FIFA xG 当前赛事信号。
4. 获取外部基准：优先找同盘口 sportsbook 赔率；Opta 只作为同簇敏感性参考；Polymarket 不进入 fair probability。
5. 候选评估：使用 `p_center = p_external + reliability*(p_independent-p_external)`，`p_trade = p_external + reliability*(p10_independent-p_external)-buffer`。
6. 执行过滤：0709 版按用户指定把稳健边际阈值设为 3pp；taker 必须扣 fee 后仍满足阈值，maker 限价可低于 ask，但需要满足阈值并接受不成交。
7. 相关性约束：同一场优先只保留一个最终仓位，除非盘口逻辑显著独立且都有直接外部盘口支撑。
8. 审核：检查盘口定义、方向、外部赔率覆盖、费用、相关性和是否误用未来数据。

## 角球如何混入主流程

角球可以进入主流程，但不能直接套用进球 Poisson 模型。

处理规则：

- 先搜索 Polymarket 是否有可执行角球盘口。
- 若没有可交易盘口，只记录“已检查，无下注”。
- 若有角球盘口，优先寻找同盘口 sportsbook corner odds。
- 若没有同盘口外部赔率，必须建立独立 corner model：球队近期角球 for/against、对手强度、比赛节奏、领先/落后状态敏感性。
- 在没有可靠 corner model 或同盘口外部赔率前，角球只允许观察，不进入正式下注组合。

## 本版重要修正

此前候选评估容易从 1X2 拟合派生 totals/BTTS 概率。0709 版修正为：

- 如果存在 sportsbook 同盘口 totals 或 BTTS，直接用该盘口 devig 概率覆盖 1X2 拟合派生值。
- 这会显著降低 BTTS No、全场 Under 2.5 这类候选的表观边际。
- team total 若没有同盘口外部赔率，只能低 reliability、加 buffer，并优先作为 maker 条件单。
- 0709 版用户将稳健边际阈值从 5pp 改为 3pp；这会允许少数更贴近市场价的 post-only 条件单，但不放松同盘口外部校验规则。

审核后新增硬规则：

- team total 若没有同盘口 sportsbook team-total 赔率，不能进入最终下注组合。
- 1X2 拟合出的 team-total 外部概率只能作为观察信号，不能支撑真实下注。
- JSON 输出中此类候选标记为 `SKIP_NO_DIRECT_TEAM_TOTAL_BENCHMARK`。
- post-only 候选必须在报告中写成“拟挂单/观察项”，不能写成已持仓或已成交。
