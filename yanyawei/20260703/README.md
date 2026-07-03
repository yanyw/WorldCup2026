# yanyawei 工作区

本目录维护世界杯 Polymarket 盘口研究。每期报告包含数据快照、统一概率模型、独立校验、费用后 Edge、仓位和最终执行日程。

## 当前报告

- [`world_cup_betting_decision_0702.md`](world_cup_betting_decision_0702.md)：北京时间 7/3-7/6 十场比赛的最新组合与执行限价
- [`workflow_methodology_v2.md`](workflow_methodology_v2.md)：升级后的完整方法论
- [`review_log_0702.md`](review_log_0702.md)：双代理两轮审核意见与分析代理裁决
- [`data/portfolio_decisions_0702.json`](data/portfolio_decisions_0702.json)：结构化下注组合
- [`data/polymarket_live_0702.json`](data/polymarket_live_0702.json)：Gamma API 实时盘口与最佳 bid/ask
- [`scripts/refresh_polymarket_0702.py`](scripts/refresh_polymarket_0702.py)：刷新 Polymarket 主盘口和更多盘口
- [`scripts/build_model_0702.py`](scripts/build_model_0702.py)：统一概率模型
- [`scripts/validate_portfolio_0702.py`](scripts/validate_portfolio_0702.py)：概率、费用和组合风控校验
- [`winner_basket_analysis_0702.md`](winner_basket_analysis_0702.md)：法国、阿根廷、西班牙、英格兰冠军组合的预期盈亏分析
- [`data/winner_basket_model_0702.json`](data/winner_basket_model_0702.json)：冠军组合的逐队概率、价格、费用和期望值中间结果
- [`scripts/winner_basket_model_0702.py`](scripts/winner_basket_model_0702.py)：冠军组合可复算模型

历史报告保留在 [`../20260628/world_cup_betting_workflow_0629.md`](../20260628/world_cup_betting_workflow_0629.md)。

## 阅读顺序

直接阅读主报告即可。JSON 用于后续自动化、回测和结果复盘，不单独承载分析结论。

模型与校验：

```powershell
python yanyawei/20260703/scripts/refresh_polymarket_0702.py
python yanyawei/20260703/scripts/build_model_0702.py
python yanyawei/20260703/scripts/validate_portfolio_0702.py
```
