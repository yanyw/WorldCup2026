# 20260715 两轮分析审核记录

## 第一轮：审核 REJECT，分析端部分接受

审核代理复算确认：

- 固定 1.5pp 在不确定性、VWAP 和 taker fee 之后应用，顺序正确。
- 1X2 三项 Yes/No 和 O/U 2.5 两方向共 8 个 outcome 均已覆盖。
- P1/P2 的加时比分清洗与 P3 的 120 分钟 xG 排除正确。
- 当前最接近的 Draw `No` taker edge 为 -0.216pp，Argentina `Yes` 为 -0.501pp，当前价空仓成立。
- 角球没有可执行市场，不应虚构候选。

审核代理提出把 BetMGM Draw 从 `+185` 改成 `+188`。分析端拒绝此项：

- `+188` 来自 VegasInsider 记录的美东周一 21:00 盘口。
- `+185` 来自 BetMGM 7 月 14 日更晚发布的公开投注更新，与当前 evidence 文件引用一致。
- 两者不是同一时点；使用更晚的 `+185` 更合理。
- 即便换成 `+188`，影响不足 0.1pp，也不会改变空仓，但证据链必须按时间而不是按审核偏好选择。

分析端接受审核关于冻结同一版本输入与输出的意见：外部 totals 更新后已重新运行 `evaluate_candidates_0715.py`，不能只改 evidence 不重算。

## 第二轮：终审

第二轮重点复算：

```text
Draw No:
p_trade = 0.676437
taker effective cost = 0.678597
robust edge = -0.002160

Argentina Yes:
p_trade = 0.323322
taker effective cost = 0.328335
robust edge = -0.005013
```

两项均低于固定 `+0.015` 门槛。当前 best bid 也分别高于模型允许的最高 maker 价格 66.00c 和 30.75c，不能通过 maker 规避门槛。

终审裁决：`ACCEPT CURRENT-PRICE NO BET`。

最终空仓不是因为漏掉 No token、忽略角球或金额过小，而是所有符合证据门槛的直接 outcome 在当前价格和费用后均无正的稳健 edge。
