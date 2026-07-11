# 20260711 双向修正规则：两轮独立审核

审核代理：独立子代理 `019f51ba-525f-7e82-bf1f-37cb5265a5bb`

原则：分析代理可以拒绝审核意见，但必须给出数字或代码依据；不能为了形式迎合审核。

## 第一轮：REJECT初始候选

初始分析使用Oddschecker页面正文中的旧静态盘口：Norway-England O/U 2.5为Over -130、Under +114。该输入使Under 2.5成为42.50c taker候选。

审核发现页面顶部实时市场区已经更新为：

```text
Norway / Draw / England = +290 / +280 / -105
Over / Under 2.5        = -138 / +122
```

页面下方静态说明仍显示旧数字，采集误读由此产生。分析代理独立打开页面后确认审核正确，接受该意见并更新两场Oddschecker实时header数字。

实时总进球赔率重算：

```text
Oddschecker Under去水概率   43.7211%
BetMGM Under去水概率        45.3230%
博彩共识                    44.5221%
内部模型                    48.3523%
p_center                    45.4796%
动态不确定性 u               1.4340pp
p_trade                     44.0456%
42.50c taker有效成本         43.7219%
taker robust Edge            0.3237pp
```

裁决：接受审核意见，撤销42.50c taker。`0.3237pp < 1.5pp`。

第一轮还发现maker判断遗漏：旧代码要求 `maker_max < ask`，会在taker因手续费不合格、但低于ask的maker挂单仍合法时误判。分析代理接受并修复为：

```python
maker_price = min(maker_max, floor_to_tick(ask - tick))
```

Kelly自审同时发现旧实现用裸taker价格而非费用后成本计算仓位。该问题已修复；taker Kelly使用有效成本，maker Kelly使用零费用挂单价。

## 第二轮：ACCEPT返修结果

返修后的唯一正式方向：

```text
Norway-England Under 2.5
POST-ONLY BUY @ 42.25c
不得改为42.50c taker
```

独立审核复算：

```text
p_trade                 44.045609%
maker价格               42.250000%
maker robust Edge        1.795609pp
固定门槛                1.500000pp
超过门槛                0.295609pp
```

Maker Kelly：

```text
full Kelly
= (0.4404560938 - 0.4225) / (1 - 0.4225)
= 3.109280%

缩放仓位
= 1000 * 3.109280% * 5% * 0.75
= 1.16598 USDC
```

价格约束：`maker_max=42.50c`，best bid/ask为42.25c/42.50c，tick为0.25c，因此 `ask-tick=42.25c`，最终post-only挂单价为42.25c。满足 `maker_price < best_ask` 且 `p_trade-maker_price >= 1.5pp`。

第二轮其余检查均通过：

- 1X2融合后每场三项和为100%，Yes/No中心概率严格互补。
- O/U 2.5按博彩75%、内部25%执行，没有把Opta 1X2伪映射到大小球。
- 费用、VWAP、方向映射和maker/taker区分正确。
- 其余15个直接估值outcome均未达到maker或taker条件。
- 按用户要求，不因金额小或最小订单问题改变裁决。

## 最终审核裁决

`ACCEPT POST-ONLY BUY Norway-England Under 2.5 @ 42.25c`。

挂单未成交不算持仓；不得为成交而改成42.50c taker。临场盘口、首发或费用变化后必须重新运行，不能直接沿用冻结快照。
