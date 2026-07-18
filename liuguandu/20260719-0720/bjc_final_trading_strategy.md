# 🏆 世界杯决赛周 — 最终交易策略 (可直接下单)

**模型**: Dixon-Coles v2 | **数据源**: Polymarket 实时盘口 | **资金池**: $10,000
**生成时间**: 2026-07-18 | **策略版本**: v3.0 (去冗余优化)

---

## 📊 组合总览

| 指标 | 数值 |
|------|------|
| 总交易笔数 | **19 笔** |
| 总风险敞口 | **$1,590** (15.9%) |
| FRA-ENG 敞口 | $860 (8.6%) |
| ESP-ARG 敞口 | $730 (7.3%) |
| 组合EV | **+$178** (+1.78%) |
| 95% VaR | **-$299** |
| 盈利概率 (Top49场景) | **28.5%** |
| BUY 仓位 | 12 笔 |
| SELL 仓位 | 7 笔 |

---

## France vs England

**2026-07-19 05:00 (北京时间)** | **Hard Rock Stadium, Miami**

> 核心逻辑: 市场高估法国、高估进球数。做多英格兰价值、做空进球预期。

| # | 盘口 | 方向 | 价格 | 金额 | Edge | 如何下单 |
|---|------|------|------|------|------|----------|
| 1 | England 90分钟胜 | 🟢 BUY | 24¢ | **$130** | +13.3pp | 在 Polymarket Moneyline 市场买入 England @ 24¢ |
| 2 | 90分钟平局 | 🟢 BUY | 23¢ | **$90** | +3.9pp | 在 Polymarket Moneyline 市场买入 Draw @ 23¢ |
| 3 | 总进球 ≤3.5 | 🔴 SELL | 44¢ | **$100** | +15.6pp | 在 Polymarket Total O/U 市场卖出 Over 3.5 @ 44¢ (等价于买入 Under 3.5 @ 56¢) |
| 4 | 双方不都进球 (BTTS NO) | 🔴 SELL | 68¢ | **$100** | +12.8pp | 在 Polymarket BTTS 市场卖出 Yes @ 68¢ (等价于买入 No @ 32¢) |
| 5 | 法国进球 ≤2.5 | 🔴 SELL | 32¢ | **$100** | +17.0pp | 在 Polymarket France Total 市场卖出 Over 2.5 @ 32¢ (等价于买入 Under 2.5 @ 68¢) |
| 6 | 英格兰受让 +1.5 | 🔴 SELL | 29¢ | **$100** | +12.7pp | 在 Polymarket Spread 市场卖出 France -1.5 @ 29¢ (等价于买入 England +1.5 @ 71¢) |
| 7 | 英格兰先进球 | 🟢 BUY | 36¢ | **$120** | +10.9pp | 在 Polymarket Team to Score First 市场买入 England @ 36¢ |
| 8 | 英格兰晋级 | 🔴 SELL | 66¢ | **$100** | +16.7pp | 在 Polymarket To Advance 市场卖出 France @ 66¢ (等价于买入 England @ 34¢) |
| 9 | 点球大战发生 | 🟢 BUY | 11¢ | **$20** | +1.1pp | 在 Polymarket Penalty Shootout 市场买入 Yes @ 11¢ (小仓对冲) |
| | | | | **合计 $860** | | |

---

## Spain vs Argentina

**2026-07-20 03:00 (北京时间)** | **MetLife Stadium, New Jersey**

> 核心逻辑: 西班牙攻防占优，λ=1.56 vs 1.12。做多西班牙、做多进球、做空点球。

| # | 盘口 | 方向 | 价格 | 金额 | Edge | 如何下单 |
|---|------|------|------|------|------|----------|
| 10 | 西班牙 90分钟胜 | 🟢 BUY | 42¢ | **$130** | +4.7pp | 在 Polymarket Moneyline 市场买入 Spain @ 42¢ |
| 11 | 阿根廷 90分钟胜 | 🟢 BUY | 26¢ | **$30** | +1.1pp | 在 Polymarket Moneyline 市场买入 Argentina @ 26¢ |
| 12 | 总进球 >2.5 | 🟢 BUY | 41¢ | **$110** | +9.0pp | 在 Polymarket Total O/U 市场买入 Over 2.5 @ 41¢ |
| 13 | 双方都进球 (BTTS YES) | 🟢 BUY | 51¢ | **$80** | +2.6pp | 在 Polymarket BTTS 市场买入 Yes @ 51¢ |
| 14 | 西班牙进球 ≥1.5 | 🟢 BUY | 39¢ | **$100** | +7.1pp | 在 Polymarket Spain Total 市场买入 Over 1.5 @ 39¢ |
| 15 | 西班牙让球 -1.5 | 🟢 BUY | 19¢ | **$90** | +5.2pp | 在 Polymarket Spread 市场买入 Spain -1.5 @ 19¢ |
| 16 | 阿根廷进球 ≥1.5 | 🟢 BUY | 27¢ | **$70** | +3.8pp | 在 Polymarket Argentina Total 市场买入 Over 1.5 @ 27¢ |
| 17 | 阿根廷先进球 | 🟢 BUY | 37¢ | **$50** | +1.8pp | 在 Polymarket Team to Score First 市场买入 Argentina @ 37¢ |
| 18 | 无点球大战 | 🔴 SELL | 19¢ | **$40** | +7.2pp | 在 Polymarket Penalty Shootout 市场卖出 Yes @ 19¢ (等价于买入 No @ 81¢) ⚠️注意: SELL风险不对称 |
| 19 | 西班牙晋级 | 🟢 BUY | 59¢ | **$30** | +0.8pp | 在 Polymarket To Advance 市场买入 Spain @ 59¢ |
| | | | | **合计 $730** | | |

---

## ⚠️ SELL 仓位重要提醒

SELL 仓位 (卖出YES合约) 的收益/损失**不对称**：

| # | 盘口 | 金额 | 赢→赚 | 输→赔 | 风险比 |
|---|------|------|------|------|------|
| 3 | 总进球 ≤3.5 🟢 | $100 | +$100 | -$151 | 1.5x |
| 4 | BTTS NO 🟢 | $100 | +$100 | -$56 | 0.6x |
| 5 | 法国进球 ≤2.5 🟡 | $100 | +$100 | -$253 | 2.5x |
| 6 | 英格兰 +1.5 🟡 | $100 | +$100 | -$291 | 2.9x |
| 8 | 英格兰晋级 🟢 | $100 | +$100 | -$61 | 0.6x |
| 18 | 无点球大战 🔴 | $40 | +$40 | -$171 | 4.3x |

**🔴 #18 (无点球大战) 风险比 4.3x — 已从原$123减至$40。若判断错误损失$171。**

---

## 📋 下单操作指南

### Polymarket 下单步骤

**BUY 仓位 (12笔)**:
1. 打开对应市场页面（如 Moneyline / BTTS / Total O/U 等）
2. 选择要买的 OUTCOME (如 England / Draw / Over 2.5 / Yes 等)
3. 输入购买金额 (Amount列)
4. 限价单填入目标价格 (¢列)，或市价单直接成交

**SELL 仓位 (7笔)**:
1. 打开对应市场页面
2. 选择要卖的 OUTCOME (如 France / Over 3.5 / BTTS Yes 等)  
3. 点击 SELL (不是 BUY!)
4. 输入卖出份额金额 (Amount列)
5. 限价单填入目标价格 (¢列)

> 💡 **等价理解**: SELL France @ 66¢ = BUY England @ 34¢  
> 两种下单方式结果相同，选择流动性更好的一侧即可

---

## ✅ 一键下单清单 (按顺序执行)

### 🇫🇷🏴󠁧󠁢󠁥󠁮󠁧󠁿 France vs England

```
☐ 1.  [BUY]  英格兰 90分钟胜      → Polymarket Moneyline → England    → $130 @ 24¢
☐ 2.  [BUY]  90分钟平局           → Polymarket Moneyline → Draw       →  $90 @ 23¢
☐ 3.  [SELL] 总进球 ≤3.5          → Polymarket Total O/U → Over 3.5   → $100 @ 44¢ (卖!)
☐ 4.  [SELL] BTTS NO             → Polymarket BTTS      → Yes        → $100 @ 68¢ (卖!)
☐ 5.  [SELL] 法国进球 ≤2.5        → Polymarket FRA Total → Over 2.5   → $100 @ 32¢ (卖!)
☐ 6.  [SELL] 英格兰 +1.5          → Polymarket Spread    → FRA -1.5   → $100 @ 29¢ (卖!)
☐ 7.  [BUY]  英格兰先进球          → Polymarket First    → England    → $120 @ 36¢
☐ 8.  [SELL] 英格兰晋级            → Polymarket Advance  → France     → $100 @ 66¢ (卖!)
☐ 9.  [BUY]  点球大战             → Polymarket Penalty  → Yes        →  $20 @ 11¢
        小计: $860
```

### 🇪🇸🇦🇷 Spain vs Argentina

```
☐ 10. [BUY]  西班牙 90分钟胜       → Polymarket Moneyline → Spain      → $130 @ 42¢
☐ 11. [BUY]  阿根廷 90分钟胜       → Polymarket Moneyline → Argentina  →  $30 @ 26¢
☐ 12. [BUY]  总进球 >2.5          → Polymarket Total O/U → Over 2.5   → $110 @ 41¢
☐ 13. [BUY]  BTTS YES            → Polymarket BTTS      → Yes        →  $80 @ 51¢
☐ 14. [BUY]  西班牙进球 ≥2        → Polymarket ESP Total → Over 1.5   → $100 @ 39¢
☐ 15. [BUY]  西班牙 -1.5          → Polymarket Spread    → Spain -1.5 →  $90 @ 19¢
☐ 16. [BUY]  阿根廷进球 ≥2        → Polymarket ARG Total → Over 1.5   →  $70 @ 27¢
☐ 17. [BUY]  阿根廷先进球          → Polymarket First    → Argentina  →  $50 @ 37¢
☐ 18. [SELL] 无点球大战 ⚠️         → Polymarket Penalty  → Yes        →  $40 @ 19¢ (卖!)
☐ 19. [BUY]  西班牙晋级            → Polymarket Advance  → Spain      →  $30 @ 59¢
        小计: $730
```

---

### 💰 总计: $1,590 / $10,000 (15.9%)

### ⚡ 风险提示

- **#18 (无点球大战 SELL)** 风险比最高 (4.3x)，已减仓至$40。若西班牙-阿根廷进入点球，该仓位亏损$171
- **#5 (法国≤2.5 SELL)** +#6 (英格兰+1.5 SELL) 若法国大比分获胜 (>2球)，两仓合计可亏损$544
- 所有价格以 Polymarket 实时盘口为准，下单前确认当前价格偏离不超过 ±3¢
- 建议按顺序逐笔下单，每笔成交后再下下一笔，避免滑点

---
*Dixon-Coles v2 模型 | 回测 101 场 | Brier Score ≈ 0.25 | 仅供研究参考*