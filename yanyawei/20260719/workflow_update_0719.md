# 2026-07-19 工作流增量

本文件是既有正式流程的增量，不重写历史版本。规则从 `2026-07-19` 起生效，旧目录保留其当时真实使用的方法和结果。

## 本轮核心改动

从交易决策中彻底删除“内部模型与外部概率分歧惩罚”：

```text
旧：u = max(0.5pp, 0.5 * 机构来源离散度
                    + 0.1 * |p_internal - p_external|
                    + 数据质量项)

新：u = max(0.5pp, 0.5 * 机构来源离散度
                    + 数据质量项)
```

`|p_internal - p_external|` 继续输出，作用是帮助人类定位模型适用域、数据口径或阵容信息问题，但其数值不再直接降低 `p_trade`，也不触发自动否决。模型适用域问题只能由有事实依据、事前定义的证据门处理，不能把“大分歧”本身当成错误。

内部 P1/P2/P3 的情景区间仍属于模型风险诊断，且 `scenario_p10` 未经校准，不进入本轮 `p_trade`。0719 包装层同时把旧情景生成器的组件分歧输入固定为零：保留固定模型风险和决赛环境放宽，但不再按 P1/P3 分歧扩大区间。因此不存在隐藏的分歧惩罚。

## 固定计算链

1. **先复盘**：结算上轮真实成交；概率评分使用和为 1 的 `p_center`，不能用带折扣的 `p_trade`。
2. **限定时间与结算口径**：只使用开赛前可得数据；足球赛果、让球和总进球一律按 90 分钟加伤停补时，不含加时和点球，除非合约规则另有说明。
3. **内部模型**：
   - P1：时间衰减、ridge 收缩的攻防 Poisson。
   - P2：顺序 Elo 与多分类校准，只调整双方强弱比例，不设定总进球。
   - P3：FIFA 同届比赛 xG 的对手调整模型，权重上限 25%。
4. **模型适用域**：新闻用于验证阵容、动机、赛制和环境是否使模型失效。失效时走证据门，不按分歧大小扣分。
5. **外部概率**：每家完整双向或三向报价先单独去水，再跨机构平均。Polymarket 只作执行价格，不进入公允概率。
6. **Opta**：同为 90 分钟口径时进入 1X2 外部层；总进球没有直接 Opta 概率时不做推测映射。
7. **双向修正**：

```text
1X2: p_external = 0.75 * sportsbook_consensus + 0.25 * Opta
O/U 2.5: p_external = sportsbook_consensus
p_center = 0.75 * p_external + 0.25 * p_internal
```

内部模型可以把外部中心向上或向下修正，但固定只占 25%。

8. **交易概率**：

```text
u = max(0.5pp, 0.5 * sportsbook_source_range + data_quality)
p_trade = p_center - u
```

先构造一致的基础概率与互补概率，再分别对每个买入方向计算保守下界。因此 Yes 和 No 的两个 `p_trade` 不要求相加为 100%。

9. **执行成本**：

```text
taker fee per share = feeRate * price * (1 - price)
taker effective cost = planned VWAP + fee per share
maker effective cost = post-only limit price
```

10. **固定门槛**：费用、VWAP 与 `u` 之后，`robust edge >= 1.5pp` 才可下注。
11. **证据资格**：只有同盘口直接机构基准或事前回测合格的投影器才能进入 edge 筛选。相邻 totals、让球、BTTS、球队进球和角球不能临时从 Poisson 外推后下注。
12. **组合去重**：同一比赛的互补、包含及高度相关合约按事件簇合并，不能伪装成分散下注。
13. **两轮审核**：审核代理找漏洞，分析代理逐条接受或拒绝并说明理由；返修后由同一审核角色再次核算。

## 最终报告要求

每个正式下注必须披露 P1/P2/P3、最终 lambda、内部概率、机构去水概率、Opta、`p_external`、`p_center`、机构离散度、数据质量项、`p_trade`、订单簿、费用、edge、执行模式和仓位。没有下注时，对最接近门槛的候选提供同样链条及条件观察价。

## 可复现入口

```powershell
python yanyawei/20260719/scripts/build_models_0719.py
python yanyawei/20260719/scripts/refresh_markets_0719.py
python yanyawei/20260719/scripts/evaluate_candidates_0719.py
```
