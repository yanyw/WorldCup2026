# 真实数据逐分钟引擎：数据字典

所有概率都在 `[0,1]` 内；`expected_*` 是该分钟的期望事件次数。高频事件同一分钟可能出现多次，因此同时给出 `p_any_* = 1-exp(-expected_*)`。第 91–95 行分别对应 90+1 至 90+5。

## minute_by_minute_1_95.csv

- `minute`：比赛分钟；常规时间共 95 个模型时间格。
- `p_england/argentina_shot`、`sot`、`goal`：该分钟至少一次射门、射正、进球的模拟频率。
- `p_england/argentina_foul`、`yellow`、`red`：该分钟犯规、黄牌、红牌危险率；裁判总量先做经验贝叶斯收缩，再按球队犯规倾向分配。
- `p_england/argentina_penalty`、`corner`：该分钟获得点球、角球的危险率。
- `p_var_review`：由进球、点球、红牌触发的 VAR 复核概率；不能当成官方 VAR 盘口的精确口径。
- `p_any_injury_stoppage`、`p_any_substitution`：任一队出现 StatsBomb 口径伤停或换人的概率。
- `expected_england_possession`：在当前比分与红牌状态下，英格兰下一分钟的期望控球份额。
- `p_england_leading_after`、`p_draw_after`、`p_argentina_leading_after`：该分钟结束后的赛果状态分布。
- `expected_*_goals_after`、`modal_score_after`：累计期望比分及众数比分。
- `expected_*_passes/line_breaks/final_third_receptions/crosses/throw_ins`：进攻与推进高频事件的该分钟期望次数。
- `expected_*_pressures/direct_pressures/forced_turnovers/regains/interceptions/tackles`：防守与压迫高频事件的该分钟期望次数。
- 对每个高频 `expected_*` 字段，都有对应的 `p_any_*`，表示该分钟至少发生一次的概率。

## extra_time_minute_by_minute_conditional.csv

只在 90 分钟战平的条件下读取。`minute` 为 96–125 的 30 个模型时间格，包含双方射门、进球以及该分钟后的领先/平局状态概率。加时速率来自 2018/2022 世界杯中 10 场加时赛并做小样本收缩。

## player_event_probabilities.csv

- 身份字段：`team`、`player`、`role`、`squad_status`。
- 使用字段：`p_appearance`、`expected_minutes`、`p_substituted`、`tournament_minutes`。
- 真实状态字段：`tournament_attempts`、`tournament_goals`。
- 预测字段：`expected_shots`、`expected_goals`、`p_anytime_goal_90m`、`p_first_goal`、`p_assist_90m`、`p_yellow_90m`。
- 球员总射门和总进球期望严格守恒到球队总量；首发未正式公布，所以人员级结果比球队级结果更不稳定。

## sensitivity_scenarios.csv

每行独立运行 40,000 次：基准、仅历史实力、移除比分状态、低/高节奏、Rice 缺阵、阿根廷额外疲劳。`england_win + draw + argentina_win = 1`。

## tactical_phase_profile.csv

FIFA 报告中的进攻、压迫、防守区块、转换、恢复、反抢等阶段占比的近期加权值。它们用于解释球队风格，具体胜负影响通过传球、穿线、三区接球、传中、压迫和失误等可计数事件进入，不另设无法验证的“战术评分”。

## real_data_engine_summary.json

完整机器可读结果：训练样本、球队画像、赛前事件率、裁判后验、90 分钟赛果、比分分布、晋级/加时/点球、事件均值、首球、时间外验证、敏感性、禁用输入确认和模型限制。

## factor_register.csv

逐项列出每一类因素的真实来源、观测值、进入模型的方式及不确定性处理。某因素若缺乏同口径历史因果系数（例如跨城旅行），会保留测量值并进入压力测试，而不会被随意赋予主观加成。
