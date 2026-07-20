# 模型与预测历史索引

本页按研究演化顺序索引从项目开始到当前版本的主要代码、报告和预测。历史输出不覆盖、不回填，以便复盘当时可获得的数据和判断。

| 阶段 | 日期 | 核心变化 | 主要入口 | 主要输出 |
|---|---|---|---|---|
| 早期原型 | 2026-07-11/12 | 泊松、俱乐部映射和快速 Walk-Forward 原型 | `walkforward_backtest_fast.py`, `src/predict_markets.py` | 根目录早期报告、`predictions_walkforward.csv`, `outputs/all_market_predictions.csv` |
| v2 | 2026-07-12 | 历史国家队模型、Dixon–Coles、Elo 审核、赔率去水、保守 Kelly | `src/run_prediction_v2.py`, `src/validate_historical.py` | `outputs/model_v2/` |
| v3 | 2026-07-12 至 07-15 | 真实 Elo 预热、Walk-Forward、比分修正、尖锐赔率共识、相关盘口去重 | `src/validate_walkforward_v3.py`, `src/analyze_semifinals_v3.py` | `outputs/model_v3/`, `docs/模型升级_v3_审计报告.md` |
| v4 | 2026-07-15 | 订单簿补集、胜平负/正确比分/首球分区、嵌套大小球、跨事件等价合约 | `src/scan_orderbook_arbitrage.py`, `src/analyze_cross_event_arbitrage.py`, `src/predict_conditional_matches.py` | `outputs/model_v4/`, `docs/模型升级_v4_赛前审计.md` |
| 纯游戏引擎 | 2026-07-15 | FC 26 属性、阵型对位、体能、换人、裁判、VAR、逐分钟事件 | `src/scrape_fc26_ratings.py`, `src/simulate_match_game_engine.py` | `outputs/pure_game_engine/`, `docs/纯游戏引擎_v1_逐分钟建模.md` |
| v5 套利复审 | 2026-07-15/16 | Dutch-book 线性规划、条件 maker 组合、流动性与触发条件 | `src/scan_dutch_book_lp.py`, `src/scan_triggered_maker_arbitrage.py`, `src/analyze_upcoming_v5.py` | `outputs/model_v5/`, `docs/模型升级_v5_套利再审查.md` |
| 真实数据引擎 | 2026-07-16 | FIFA 逐场表现、StatsBomb 历史事件、球员/裁判/阶段/补时微观模型 | `src/collect_fifa_performance_reports.py`, `src/build_fifa_2026_features.py`, `src/build_statsbomb_dynamics.py`, `src/simulate_match_real_data_engine.py` | `outputs/real_data_engine/` |
| v6 赛后复盘 | 2026-07-16 至 07-18 | 英格兰—阿根廷预测复盘、剩余两场独立模拟、盘口全覆盖 | `src/analyze_remaining_v6.py`, `src/simulate_remaining_matches_v6.py` | `outputs/model_v6/`, `outputs/remaining_matches_v6/`, `docs/模型升级_v6_赛后复盘与剩余两场预测.md` |
| v7 最终更新 | 2026-07-18/19 | 45 万路径/场、最新阵容/伤病/裁判/天气、球员出场混合分布、754 盘口逐项分类 | `src/collect_remaining_markets.py`, `src/simulate_remaining_matches_v6.py --config config/remaining_matches_v7.json` | `outputs/remaining_matches_v7/` |
| v8.1 决赛更新 | 2026-07-19 | 季军赛赛后校准、射正/角球状态解耦、早期比分反馈、终结效率尾部、裁判本届赛事加权、点球先验重收缩、角球盘口族熔断、决赛专用快照 | `src/simulate_remaining_matches_v6.py --config config/world_cup_final_v8.json` | `outputs/world_cup_final_v8/`, `docs/模型升级_v8_季军赛复盘与决赛预测.md` |

## 关键报告入口

- 研究设计：[`研究方案_v2.md`](研究方案_v2.md)
- v3 审计：[`模型升级_v3_审计报告.md`](模型升级_v3_审计报告.md)
- v4 赛前审计：[`模型升级_v4_赛前审计.md`](模型升级_v4_赛前审计.md)
- v5 套利复审：[`模型升级_v5_套利再审查.md`](模型升级_v5_套利再审查.md)
- v6 复盘：[`模型升级_v6_赛后复盘与剩余两场预测.md`](模型升级_v6_赛后复盘与剩余两场预测.md)
- v7 详细更新：[`../outputs/remaining_matches_v7/detailed_update_20260718.md`](../outputs/remaining_matches_v7/detailed_update_20260718.md)
- v8.1 季军赛复盘与决赛预测：[`模型升级_v8_季军赛复盘与决赛预测.md`](模型升级_v8_季军赛复盘与决赛预测.md)

## 历史输出维护规则

1. 已发布预测目录视为只读，不使用同名目录覆盖重跑。
2. 新运行目录使用 `outputs/runs/YYYYMMDDTHHMMSSZ_<model>_<fixture>/`。
3. 每次预测至少保存配置、输入快照路径、随机种子、生成时间、主报告和机器可读结果。
4. 赛后复盘新增文件，不修改赛前报告中的原始概率。
5. `LATEST*.txt` 只是采集入口指针；历史报告必须记录实际快照文件名，不能只依赖 `LATEST`。
