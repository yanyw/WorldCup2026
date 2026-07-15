# 2026-07-15 最新下注决策

本目录延续 `20260709` 和 `20260711` 工作流，固定使用费用、滑点和模型不确定性之后 `robust_edge >= 1.5pp` 的门槛。

- 最终报告：`world_cup_betting_decision_0715.md`
- 两轮审核：`audit_rounds_0715.md`
- 内部模型：`data/model_results_0715.json`
- 外部证据：`data/external_evidence_0715.json`
- Polymarket CLOB：`data/polymarket_snapshot_0715.json`
- 全候选计算：`data/candidate_evaluation_0715.json`

当前结论是空仓。空仓表示当前可成交价格不满足门槛，不表示比赛没有观点，也不表示低价条件单永远无效。临场首发、外部赔率或 CLOB 变化后必须重新运行，不能沿用本目录中的冻结价格直接下单。
