# yanyawei 工作区

本目录维护世界杯 Polymarket 盘口研究。每期报告包含数据快照、统一概率模型、独立校验、费用后 Edge、仓位和最终执行日程。

## 当前报告

- [`world_cup_betting_workflow_0629.md`](world_cup_betting_workflow_0629.md)：北京时间 6/29-6/30 四场淘汰赛的完整工作流与最终决策
- [`data/market_model_snapshot_0629.json`](data/market_model_snapshot_0629.json)：本期盘口、模型概率和交易结果的结构化快照
- [`scripts/validate_snapshot.py`](scripts/validate_snapshot.py)：重新计算 Poisson 概率并检查快照一致性

## 阅读顺序

直接阅读主报告即可。JSON 用于后续自动化、回测和结果复盘，不单独承载分析结论。

校验命令：`python yanyawei/20260628/scripts/validate_snapshot.py`
