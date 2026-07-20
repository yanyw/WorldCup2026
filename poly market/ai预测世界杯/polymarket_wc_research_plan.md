# Polymarket世界杯预测市场量化策略 — 超详细研究计划

**最后更新**：2026-07-11 | **作者**：binpom & Claude

---

## 目录

1. [研究动机与核心假设](#1-研究动机与核心假设)
2. [总体架构](#2-总体架构)
3. [数据层：数据源与数据管道](#3-数据层数据源与数据管道)
4. [模型层：四种预测模型的完整设计](#4-模型层四种预测模型的完整设计)
5. [偏差检测与信号生成层](#5-偏差检测与信号生成层)
6. [交易执行与风险管理层](#6-交易执行与风险管理层)
7. [回测框架设计](#7-回测框架设计)
8. [评价指标体系](#8-评价指标体系)
9. [技术栈与工程架构](#9-技术栈与工程架构)
10. [里程碑与时间线](#10-里程碑与时间线)
11. [风险与不确定性](#11-风险与不确定性)
12. [附录：关键文献与参考](#12-附录关键文献与参考)

---

## 1. 研究动机与核心假设

### 1.1 终极目标

利用个人构建的预测模型，生成比Polymarket更"理性"的比赛概率估计，在Polymarket上识别并交易定价偏差，获得正期望收益。

### 1.2 核心假设（需要回测验证）

| 编号 | 假设 | 可证伪条件 |
|------|------|-----------|
| H1 | Polymarket存在系统性定价偏差（不是完全有效的） | 模型-市场偏差无法预测实际结果 |
| H2 | 统计模型（Elo+Poisson）能产生比市场更准确的概率估计 | 回测Brier Score高于市场隐含概率 |
| H3 | 偏差信号超过阈值时下注，能产生正期望收益 | 回测Sharpe ≤ 0 |
| H4 | 定价偏差在特定类型比赛（弱队比赛、小组赛vs淘汰赛）中更大 | 不同比赛类型偏差无显著差异 |

### 1.3 不做的事情

- 跨市场套利（Polymarket vs Pinnacle/Bet365）：聚焦单一执行场所
- 高频/做市：不做订单簿层面的流动性套利
- 时序交易（路径二）：本阶段聚焦截面偏差

---

## 2. 总体架构

```
                          ┌─────────────────────────────────┐
                          │         Polymarket API           │
                          │    (世界杯盘口实时数据+历史)      │
                          └──────────────┬──────────────────┘
                                         │
┌────────────────────┐                   ▼
│   数据层            │    ┌─────────────────────────────────┐
│                    │    │    偏差信号生成引擎               │
│ • football-data    │    │                                  │
│   (联赛历史比赛)    │    │  模型概率 − 市场隐含概率          │
│ • eloratings.net   │    │  = 定价偏差向量                   │
│ • FBref/StatsBomb  │    │  (按盘口类型独立计算)             │
│ • 自建Polymarket   │    │                                  │
│   历史数据库       │    │  ┌──────────┐  ┌──────────────┐  │
│                    │    │  │偏差方向   │  │偏差幅度>阈值? │  │
└────────┬───────────┘    │  └──────────┘  └──────────────┘  │
         │                │          │              │         │
         ▼                │          ▼              ▼         │
┌────────────────────┐    │  ┌──────────────────────────┐    │
│   模型层            │    │  │      交易信号            │    │
│                    │    │  │  Buy YES / Buy NO / Pass │    │
│ ① Elo → 胜负概率   │    │  └──────────────────────────┘    │
│ ② Poisson/DC →     │    └─────────────────────────────────┘
│    比分概率分布     │                     │
│ ③ 贝叶斯赔率融合   │                     ▼
│ ④ XGBoost集成      │    ┌─────────────────────────────────┐
│                    │    │   仓位管理与风险控制              │
└────────────────────┘    │   Kelly Criterion / Fixed-frac   │
                          │   单盘口上限 / 总敞口上限          │
                          └─────────────────────────────────┘
                                         │
                                         ▼
                          ┌─────────────────────────────────┐
                          │   回测+评价 → 策略迭代            │
                          └─────────────────────────────────┘
```

### 2.2 信息流

1. **离线阶段（回测）**：历史比赛数据 → 训练/估计模型参数 → 模拟下注序列 → 计算绩效指标
2. **在线阶段（实战）**：当前盘口快照 → 模型预测 → 偏差检测 → 信号 → 手动/半自动执行
3. **迭代阶段**：每轮比赛后更新Elo评分和DC参数 → 评估预测精度 → 调整阈值

---

## 3. 数据层：数据源与数据管道

### 3.1 数据矩阵

| 数据类型 | 来源 | 时间范围 | 粒度 | 获取方式 |
|---------|------|---------|------|---------|
| **俱乐部比赛结果+赔率** | football-data.co.uk | 2010–2026，英超/西甲/德甲/意甲/法甲等22个联赛 | 单场 | CSV下载 |
| **国家队Elo评分历史** | eloratings.net | 1872–至今 | 按日 | Web爬取 |
| **国家队比赛结果** | FBref / 11v11.com | 全部历史 | 单场 | Web爬取 |
| **球队进阶指标(xG/xGA)** | FBref / Understat | 2014–至今（五大联赛） | 单场 | Web爬取 |
| **Polymarket世界杯盘口** | Polymarket CLOB API | 当前+近期历史 | 实时 | API |
| **Polymarket历史交易数据** | Polymarket / PolyMarket archival | 2022世界杯/国际赛事 | 逐笔 | 待定（可能需自建） |

### 3.2 Football-Data.co.uk 详细字段

每场比赛包含的关键字段：
- `Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR`（基础赛果）
- `HTHG, HTAG, HTR`（半场数据）
- `HS, AS, HST, AST, HF, AF, HC, AC, HY, AY, HR, AR`（射门/犯规/角球/黄红牌）
- `B365H, B365D, B365A`（Bet365赔率）
- `BWH, BWD, BWA`（Bet&Win赔率）
- `IWH, IWD, IWA`（Interwetten赔率）
- `PSH, PSD, PSA`（Pinnacle赔率）⭐核心对比基准
- `PSCH, PSCD, PSCA`（Pinnacle收盘赔率）
- `BbAvH, BbAvD, BbAvA`（市场平均赔率）
- `BbMxH, BbAv>2.5, BbAv<2.5`（大小球盘口）

### 3.3 数据管道设计

```
Stage 1: Raw Ingestion
  ├── football_data_downloader.py    — 批量下载CSV → raw/
  ├── elo_scraper.py                 — 爬取eloratings.net → raw/
  ├── fbref_scraper.py               — 爬取FBref进阶数据 → raw/
  └── polymarket_collector.py        — API拉取盘口快照 → raw/

Stage 2: Cleaning & Standardization
  ├── match_cleaner.py               — 统一队名、日期格式、处理缺失值
  ├── elo_processor.py               — 解析Elo评分时间序列
  └── odds_parser.py                 — 去除博彩margin、计算隐含概率

Stage 3: Feature Engineering
  ├── team_form_features.py          — 近期战绩滚动特征
  ├── head_to_head_features.py       — 历史交锋特征
  ├── rest_days_features.py          — 休息天数
  └── tournament_context.py          — 小组赛/淘汰赛/友谊赛标记

Stage 4: Model-Ready Dataset
  └── build_training_dataset.py      — 合并所有特征 → 统一格式 → train/val/test split
```

### 3.4 Polymarket API 关键端点

```
# 获取特定市场的订单簿
GET https://clob.polymarket.com/book?token_id={token_id}

# 获取市场价格
GET https://clob.polymarket.com/price?token_id={token_id}&side={buy|sell}

# 搜索市场
GET https://clob.polymarket.com/markets?tag=world-cup-2026

# Gamma Markets API（更易用的封装）
GET https://gamma-api.polymarket.com/markets?tag=world-cup

# 关键字段解析
# token_id: 每个二元期权的唯一标识
# outcome: "Yes" / "No"
# price: 当前价格 = 市场隐含概率 (0-1)
# best_bid / best_ask: 最优买卖价
```

### 3.5 盘口类型与对应模型输出

| Polymarket盘口 | 预测模型需求 | 模型输出格式 |
|---------------|-------------|-------------|
| 比赛胜者 (Match Winner) | 胜/平/负概率 | P(H), P(D), P(A) |
| 让球盘 (Handicap) | 比分分布 | P(比分差) |
| 总进球 Over/Under 2.5 | 总进球分布 | P(总进球≥3), P(总进球≤2) |
| 正确比分 (Correct Score) | 比分分布 | P(每个比分) |
| Both Teams to Score | 比分分布 | P(H≥1 & A≥1) |
| 夺冠 (Winner) | 模拟比赛树 | P(夺冠) |
| 晋级 (To Advance) | 单场+后续模拟 | P(晋级) |
| 最佳射手 (Top Scorer) | 球员进球模型 | P(球员总进球) |

---

## 4. 模型层：四种预测模型的完整设计

### 4.1 模型①：Elo评分模型

#### 4.1.1 基础Elo公式

**预期胜率**：
```
P(A beats B) = 1 / (1 + 10^((Elo_B - Elo_A) / 400))
```

**赛后更新**：
```
Elo_A_new = Elo_A_old + K × G × (W - P(A beats B))
```
其中：
- K = 权重因子（世界杯淘汰赛 K=60，小组赛 K=40，友谊赛 K=20）
- G = 净胜球因子（G = 1 若净胜1球，G = 1.5 若净胜2球，G = (11+N)/8 若净胜≥3球）
- W = 实际结果（W=1 胜，W=0.5 平，W=0 负）

#### 4.1.2 扩展到平局概率

基础Elo只输出胜率，需要补充平局概率。方法：

**方法A — 经验分布法**：基于Elo差的历史平局率查表
```
draw_prob = f(Elo_diff)  # 从历史数据中拟合
```
拟合曲线：draw_prob = a × exp(-b × |Elo_diff|²)（钟形函数，Elo差越大平局越少）

**方法B — 三结果扩展**：引入draw_boundary_high和draw_boundary_low
```
P(胜) = P(X > b_high)
P(平) = P(b_low < X < b_high)
P(负) = P(X < b_low)
```
在实证上，b_high ≈ 0.4, b_low ≈ -0.4 是合理的初始值（需用数据校准）。

#### 4.1.3 特殊因子

- **主场优势**：加约100 Elo分（本届世界杯：美洲球队享近似主场优势）
- **中立场地**：不加成
- **旅行疲劳**：跨洲旅行减15-30分

### 4.2 模型②：泊松分布 / 狄克逊-科尔斯模型

#### 4.2.1 标准泊松回归

假设主队进球数 H ~ Poisson(λ_H)，客队进球数 A ~ Poisson(λ_A)，且 H ⟂ A。

```
log(λ_H) = baseline + attack_i + defense_j + home_advantage
log(λ_A) = baseline + attack_j + defense_i
```

其中 attack_i 是球队i的攻击力，defense_j 是球队j的防守力（防守越强值越小/越负）。

**参数估计**：最大似然估计（MLE）
```
logL = Σ [H_k × log(λ_H_k) + A_k × log(λ_A_k) - λ_H_k - λ_A_k - log(H_k! × A_k!)]
```
用 `scipy.optimize.minimize` 或 `statsmodels` 求解。

**加上约束**：所有 attack 参数之和 = 0（识别约束），防止共线性。

#### 4.2.2 狄克逊-科尔斯修正

核心修正1 — 低比分相关性：

定义 τ_{λ,μ}(h,a) 来修正低比分区域的独立泊松假设：
```
τ_{λ,μ}(h,a) = 1 - λ×μ×ρ         若 h=0, a=0
             = 1 + λ×ρ             若 h=0, a=1
             = 1 + μ×ρ             若 h=1, a=0
             = 1 - ρ               若 h=1, a=1
             = 1                   other
```
ρ 是低比分相关性参数（通常 ρ ≈ -0.05 ~ -0.13）。

修正后的联合概率：
```
P(H=h, A=a) = τ_{λ,μ}(h,a) × Poisson(h|λ) × Poisson(a|μ)
```

核心修正2 — 时间衰减加权：

参数不是在整个数据集上一次性估计的，而是用一个指数衰减窗口。
```
w_k = exp(-ξ × t_k)
```
其中 t_k 是距离当前的天数，ξ 控制衰减速度（ξ=0.001~0.005）。

相比标准泊松，DC模型的似然函数变成了：
```
logL = Σ w_k × log[τ_{λ_k,μ_k}(h_k, a_k) × Poisson(h_k|λ_k) × Poisson(a_k|μ_k)]
```

#### 4.2.3 比分分布生成

估计完参数后，对于每场比赛计算所有可能比分的概率（截断到0-9球足够）：

```python
def score_probability(lambda_h, lambda_a, rho, max_goals=9):
    probs = {}
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            poisson_p = poisson.pmf(h, lambda_h) * poisson.pmf(a, lambda_a)
            tau = dc_adjustment(h, a, lambda_h, lambda_a, rho)
            probs[(h, a)] = poisson_p * tau
    # 归一化
    total = sum(probs.values())
    return {k: v/total for k, v in probs.items()}
```

#### 4.2.4 从比分分布到Polymarket盘口定价

```python
# 胜/平/负
P_H = sum(p for (h,a), p in probs.items() if h > a)
P_D = sum(p for (h,a), p in probs.items() if h == a)
P_A = sum(p for (h,a), p in probs.items() if h < a)

# Over 2.5 goals
P_Over25 = sum(p for (h,a), p in probs.items() if h + a > 2.5)

# Both Teams to Score
P_BTTS = sum(p for (h,a), p in probs.items() if h >= 1 and a >= 1)

# Correct Score
P_CS = {f"{h}-{a}": p for (h,a), p in probs.items()}
```

### 4.3 模型③：贝叶斯赔率信息融合

#### 4.3.1 核心框架

将Pinnacle赔率视为"市场先验"，模型提供"似然函数"，输出贝叶斯后验。

**第1步：从Pinnacle赔率提取隐含概率（去Margin）**

Pinnacle赔率通常有2-3%的overround（margin），需要normalize去除。
```
raw_P(H) = 1/O_H, raw_P(D) = 1/O_D, raw_P(A) = 1/O_A
overround = raw_P(H) + raw_P(D) + raw_P(A) - 1
P(H) = raw_P(H) / (1 + overround)   # 等比例去margin
```

**第2步：构建似然函数**

假设有一个模型评分 S（可以是Elo差或DC模型的胜率），似然函数建立 S 和实际比赛结果之间的关系。使用逻辑回归校准：

```
P(Win | S) = 1 / (1 + exp(-(α + β × S)))

```

α 和 β 用历史数据拟合。这个校准步骤至关重要——模型的原始输出可能没有良好校准（比如预测70%胜率的情况实际只赢了60%）。

**第3步：贝叶斯融合（二结果简化版）**

对于Polymarket的二元YES/NO盘口（本质就是二结果），用Beta-Bernoulli共轭先验：

- 先验：Beta(a_0, b_0)，其中 a_0/(a_0+b_0) = Pinnacle去margin后的概率，a_0+b_0 = 先验强度（设为训练窗口内Pinnacle Brier Score的倒数）
- 似然：模型给出的"等效观测" → a_lik = w × P_model, b_lik = w × (1 - P_model)，w是模型权重
- 后验：Beta(a_0 + a_lik, b_0 + b_lik)

后验均值 = (a_0 + a_lik) / (a_0 + b_0 + a_lik + b_lik) = **融合后的理性概率**

关键超参数 w（模型置信度权重）通过回测校准：在验证集上最大化对数似然。

**第4步：三结果扩展**

对于比赛胜者（三结果），用Dirichlet先验 + Multinomial似然，后验也是Dirichlet。

### 4.4 模型④：XGBoost集成

#### 4.4.1 特征工程（完整特征列表）

**球队强度特征**（静态）：
- `elo_diff`：Elo评分差
- `fifa_rank_diff`：FIFA排名差
- `market_value_ratio`：球队市值比（Transfermarkt数据）

**近期状态特征**（时间序列）：
- `form_avg_goals_scored_5`：近5场场均进球
- `form_avg_goals_conceded_5`：近5场场均失球
- `form_avg_xG_5`：近5场场均预期进球
- `form_avg_xGA_5`：近5场场均预期失球
- `form_points_per_game_5`：近5场场均积分
- `form_win_streak`：当前连胜场次
- `form_clean_sheet_rate_10`：近10场零封率

**赛程与场地特征**：
- `days_since_last_match`：距上一场天数
- `days_since_last_match_opp`：对手距上一场天数
- `rest_advantage`：休息天数差
- `travel_distance`：旅行距离（千米）
- `is_home`：是否主场
- `is_neutral`：是否中立场地
- `altitude`：海拔（美洲高海拔球场）
- `temperature`：预计比赛温度

**历史交锋特征**：
- `h2h_win_rate_10`：近10次交锋胜率
- `h2h_avg_goals_diff`：近10次交锋场均净胜球
- `h2h_years_since_last`：距上次交锋年数

**比赛场景特征**：
- `is_knockout`：是否淘汰赛
- `is_group_stage`：是否小组赛
- `importance_score`：比赛重要性评分（小组出线关键战vs无关比赛）
- `goal_diff_needed`：需要多少净胜球来晋级
- `days_in_tournament`：球队在赛会中的天数

**赔率/市场特征**（用于特征但不用于融合模型③）：
- `pinnacle_implied_prob_H/D/A`：Pinnacle隐含概率
- `market_consensus_std`：不同博彩公司赔率的标准差（不确定性指标）
- `odds_movement_24h`：24小时内赔率变动幅度

**目标变量**：
- `result_H`（二分类：主队胜=1，其余=0）
- `result_D`（二分类：平局=1，其余=0）
- `total_goals`（回归：总进球数）

#### 4.4.2 XGBoost配置

```python
params = {
    'objective': 'binary:logistic',    # 胜/负；平局单独建模
    'eval_metric': 'logloss',
    'max_depth': 4,                    # 限制深度防过拟合
    'learning_rate': 0.02,
    'n_estimators': 2000,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'min_child_weight': 5,
    'reg_alpha': 0.1,                 # L1正则化
    'reg_lambda': 1.0,                # L2正则化
    'early_stopping_rounds': 50
}
```

#### 4.4.3 交叉验证策略（关键：时序数据不能随机分）

使用**时间序列交叉验证**（TimeSeriesSplit）：

```
Fold 1: Train[2010–2015] → Test[2015–2016]
Fold 2: Train[2010–2016] → Test[2016–2017]
Fold 3: Train[2010–2017] → Test[2017–2018]
...
Fold N: Train[2010–2022] → Test[2022–2023]
```

最后留出**2023–2026数据作为最终测试集**（不参与任何超参数调优），用于真实外推评估。世界杯数据单独作为一个out-of-distribution测试。

#### 4.4.4 概率校准

即使XGBoost输出概率，也需要校准。用 Platt Scaling 或 Isotonic Regression 在验证集上做概率校准：

```python
from sklearn.calibration import CalibratedClassifierCV
calibrated_model = CalibratedClassifierCV(xgb_model, method='isotonic', cv='prefit')
```

### 4.5 模型集成策略

四种模型的概率通过加权平均整合为"理性预测"：

```
P_final = w1 × P_Elo + w2 × P_DC + w3 × P_Bayes + w4 × P_XGBoost
```

其中 w_i 通过验证集上的 Brier Score 或对数似然动态确定。可选：使用模型置信度的反Brier加权（Brier越低的模型权重越大）。

---

## 5. 偏差检测与信号生成层

### 5.1 偏差度量

对于每个Polymarket盘口：

```
Bias = P_model(market) − P_polymarket(market)
```

P_model 是我们集成模型的预测概率，P_polymarket 是 Polymarket 的 YES 价格（隐含概率）。

**关键细节**：对于Polymarket的二元期权市场，YES + NO ≠ 1（因为有买卖价差和订单簿不均衡），我们需要判断使用best_bid、best_ask还是mid_price。建议使用**mid_price**，并在稳健性检验中用best_bid和best_ask做边界测试。

### 5.2 信号生成规则（梯度方案）

**方案A — 固定阈值（最简单）**

```
信号 = BUY_YES    if Bias > θ_high        (θ_high默认0.05)
       BUY_NO     if Bias < −θ_low         (θ_low默认0.05)
       NO_ACTION   otherwise
```

**方案B — 偏差+置信度加权（推荐）**

```
信号强度 = Bias × Confidence_factor
Confidence_factor = min(1, N_samples / N_min)
```
N_samples 是该盘口的历史交易笔数或订单簿深度。流动性越差，我们对信号越不自信。

**方案C — 凯利分数标准化**

```
信号 = f* = (P_model × odds_decimal - 1) / (odds_decimal - 1)
       = (P_model / P_market - 1) / (1/P_market - 1)
```
f* > 0且 > threshold → BUY_YES；f* < 0且 |f*| > threshold → BUY_NO。

这在数学上是凯利 Criterion 的直接应用，把偏差幅度自然地映射为仓位建议。

### 5.3 多重盘口一致性检验（防假信号）

对于同一场比赛的多个盘口，检查偏差方向是否一致：

- 如果模型认为主队胜率被低估，那"主队胜+1.5"的盘口也应该被低估
- 如果不一致（比如胜率被低估但over 2.5被高估），标记为"矛盾信号"，降低置信度

### 5.4 阈值校准（回测环节核心任务）

在回测中扫描不同的 θ 取值（0.01 → 0.15），找到在验证集上最大化以下指标的最优阈值：
- 夏普比率（主要）
- 盈亏比（Profit Factor）
- 最大回撤（Max Drawdown，约束条件）

---

## 6. 交易执行与风险管理层

### 6.1 仓位管理

**核心方法：分数凯利（Fractional Kelly）**

```
投注金额 = f × bankroll × f*
```
其中：
- f = 凯利分数（0.25~0.50，保守策略用0.25）
- bankroll = 当前总资金
- f* = 凯利公式建议的仓位比例（见上文）

**约束**：
- 单盘口最大投入：总资金的 5%
- 单场比赛总投入（所有盘口合计）：总资金的 10%
- 所有活跃头寸总投入：总资金的 30%

### 6.2 Polymarket执行注意事项

- **滑点**：市价单 vs 限价单。限价单可能不成交。建议用限价单在 mid_price ± 1 tick 范围内挂单
- **Gas费**：Polymarket在Polygon上，gas费可忽略不计（< $0.01）
- **流动性**：非核心盘口（如特定正确比分）流动性可能很差，需要检查订单簿深度
- **价差**：bid-ask spread 在流动性好的盘口约1-2%，差的可能>5%。spread > 5%的盘口自动跳过

### 6.3 退出策略

- **持有至到期**（HODL to settlement）：二元期权到期自动结算，这是最简单的
- **或提前平仓**：如果Bias方向反转超过一定阈值，卖出平仓

### 6.4 操作SOP

```
赛前48h：    获取ElO评分 → 跑Poisson/DC模型 → 获取Polymarket盘口快照
赛前24h：    偏差检测 → 信号生成 → 手动审核信号 → 执行下注
比赛结束：   记录结算结果 → 更新模型参数 → 记录到绩效追踪表
每周复盘：   PnL统计 → 模型校准 → 阈值微调
```

---

## 7. 回测框架设计

### 7.1 回测架构

```
回测引擎 (BacktestEngine)
├── DataLoader — 按时间顺序喂入比赛数据
├── ModelManager — 管理4个模型的状态（参数随时间更新）
│   └── 每场比赛后更新Elo评分和DC参数（仅使用比赛时可获得的信息）
├── OddsProvider — 提供每场比赛的市场隐含概率
├── SignalGenerator — 偏差 → 信号
├── PositionSizer — 信号 → 仓位大小
├── Portfolio — 追踪PnL、权益曲线
└── MetricsReporter — 输出绩效报告
```

### 7.2 关键：杜绝前视偏差（Look-Ahead Bias）

这是整个研究中最容易犯的错误，每条都要严格遵守：

| 规则 | 具体做法 |
|------|---------|
| 训练/测试严格按时间分离 | 每场比赛只用比赛日之前的数据训练的模型做预测 |
| Elo按时间顺序更新 | 不能先用整个赛季的Elo数据算完再回测 |
| DC参数滚动窗口 | 参数估计窗口只能在比赛日之前 |
| 赔率数据只用赛前可得的 | 不能使用收盘赔率替代接近开盘时刻的赔率 |
| 特征计算不得跨越时间 | 近5场场均进球 = 在比赛日之前的最近5场，不含本场 |

### 7.3 回测数据切分

```
Time Period           用途
─────────────────────────────────────────
2010–2016            初始训练 + 交叉验证
2016–2022            验证集（超参数调优）
2022–2026            测试集（最终评估，完全不改任何参数）
2026世界杯            出域测试（Out-of-distribution）
```

---

## 8. 评价指标体系

### 8.1 概率预测精度指标

| 指标 | 公式 | 含义 |
|------|------|------|
| Brier Score | (1/N) × Σ(P_pred_i − O_i)² | 整体概率精度，越小越好。baseline = 0.25（随机猜） |
| Log Loss | −(1/N) × Σ[O_i×log(P_i) + (1−O_i)×log(1−P_i)] | 对概率极值错误惩罚更重 |
| Reliability Curve | 预测概率分桶 → 实际胜率 | 校准诊断图。完美校准 = 45°线 |
| AUC-ROC | 排序能力 | >0.7 可用，>0.8 良好 |

### 8.2 交易绩效指标

| 指标 | 公式 | 含义 |
|------|------|------|
| 总PnL | Σ(结算 - 下注成本) | 绝对收益 |
| ROI | 总PnL / 总下注金额 | 资本回报率 |
| 夏普比率 | (R̄ − r_f) / σ_R | 风险调整收益，>1 = 良好 |
| 盈亏比 (PF) | 总盈利 / 总亏损 | >1.5 可用 |
| 胜率 | 盈利盘口 / 总盘口 | 结合平均赔率看 |
| 最大回撤 (MaxDD) | 最大跌幅 / 峰值 | <30% |
| 卡玛比率 | 年化收益 / MaxDD | 综合指标 |
| 期望值 (EV) | 平均(PnL / 下注) | >0 才有正期望 |

### 8.3 统计显著性

使用Bootstrap检验：随机打乱模型预测与Polymarket偏差的对应关系10000次，看实际Sharpe在零假设分布中的位置。p < 0.05 拒绝"策略是随机噪音"。

---

## 9. 技术栈与工程架构

### 9.1 技术栈

| 层 | 技术 |
|-----|------|
| 语言 | Python 3.11+ |
| 数值计算 | NumPy, SciPy |
| 数据处理 | Pandas, Polars |
| 统计建模 | Statsmodels, Pyro (贝叶斯) |
| 机器学习 | Scikit-learn, XGBoost, LightGBM |
| 概率校准 | Scikit-learn CalibratedClassifierCV |
| 可视化 | Matplotlib, Seaborn, Plotly |
| Web数据获取 | Requests, BeautifulSoup4, Selenium |
| API交互 | requests, websocket-client |
| 回测引擎 | 自建 (Backtrader太重，自定义轻量引擎) |
| 实验管理 | MLflow 或 Weights & Biases |
| 项目组织 | Jupyter Notebook (探索) + Python Script (生产) |

### 9.2 项目目录结构

```
polymarket-wc-research/
├── data/
│   ├── raw/                    # 原始下载数据
│   │   ├── football_data/      # football-data.co.uk CSVs
│   │   ├── elo/               # Elo评分爬取
│   │   ├── fbref/             # FBref进阶数据
│   │   └── polymarket/        # Polymarket API快照
│   ├── processed/              # 清洗后的标准化数据
│   │   ├── match_results.parquet
│   │   ├── elo_ratings.parquet
│   │   ├── team_features.parquet
│   │   └── market_odds.parquet
│   └── features/               # 模型就绪的特征矩阵
│       ├── train.parquet
│       ├── val.parquet
│       └── test.parquet
├── models/
│   ├── elo_model.py            # Elo评分模型
│   ├── dc_model.py             # Dixon-Coles泊松模型
│   ├── bayes_fusion.py         # 贝叶斯赔率融合
│   ├── xgb_model.py            # XGBoost集成
│   ├── calibration.py          # 概率校准工具
│   └── ensemble.py             # 模型集成
├── backtest/
│   ├── engine.py               # 回测引擎
│   ├── signal_generator.py     # 信号生成
│   ├── position_sizer.py       # 仓位管理
│   └── metrics.py              # 绩效指标
├── pipeline/
│   ├── download_football_data.py
│   ├── scrape_elo.py
│   ├── scrape_fbref.py
│   ├── collect_polymarket.py
│   ├── build_features.py
│   └── run_pipeline.sh         # 一键运行
├── notebooks/
│   ├── 01_eda.ipynb            # 探索性数据分析
│   ├── 02_elo_baseline.ipynb   # Elo基线模型
│   ├── 03_poisson_dc.ipynb     # 泊松/DC模型
│   ├── 04_bayes_fusion.ipynb   # 贝叶斯融合
│   ├── 05_xgboost.ipynb        # XGBoost
│   ├── 06_ensemble.ipynb       # 集成与对比
│   ├── 07_backtest.ipynb       # 回测与评价
│   └── 08_polymarket_live.ipynb # 实时分析
├── config/
│   ├── params.yaml             # 全局参数配置
│   └── leagues.yaml            # 联赛列表与配置
├── outputs/                    # 输出报告和图表
├── tests/                      # 单元测试
├── requirements.txt
├── README.md
└── mlflow/                     # MLflow实验记录
```

---

## 10. 里程碑与时间线

### Phase 1：环境搭建与数据准备（2-3天，现在开始）

```
□ Git仓库初始化 + 目录结构搭建
□ Python环境配置 + requirements.txt
□ football-data.co.uk 数据下载脚本（22联赛 × 15年）
□ ELOratings.net 爬虫（历史Elo评分）
□ FBref爬虫（国家队数据 + xG等进阶指标）
□ 数据清洗与标准化（统一队名映射表）
□ 初步EDA：联赛比赛总数、Elo分布、赔率分布
```

**交付物**：`data/processed/` 中的完整干净数据集，`notebooks/01_eda.ipynb`

### Phase 2：模型①+②构建与验证（3-4天）

```
□ Elo模型实现（Python class）
  ├── Elo历史重演（从历史第一场比赛开始逐场更新）
  ├── 平局概率校准
  └── K值、主场优势等超参数网格搜索
□ Poisson/DC模型实现
  ├── 标准Poisson回归（MLE估计attack/defense参数）
  ├── DC低比分修正因子
  ├── 时间衰减窗口估计
  └── 比分分布→盘口概率转换
□ 两模型在验证集(2016-2022)上的Brier Score对比
□ 基准回测：只用Elo偏差做信号
```

**交付物**：`models/elo_model.py`, `models/dc_model.py`, `notebooks/02_elo_baseline.ipynb`, `notebooks/03_poisson_dc.ipynb`

### Phase 3：模型③+④与集成（3-4天）

```
□ 贝叶斯融合模型
  ├── Pinnacle去margin函数
  ├── Beta-Bernoulli贝叶斯更新
  └── Dirichlet三结果版本
□ XGBoost模型
  ├── 完整特征工程pipeline
  ├── 时间序列交叉验证
  ├── 超参数调优 (Optuna)
  └── 概率校准 (Isotonic Regression)
□ 四模型集成 (加权平均 + 动态权重视觉化)
□ 在测试集(2022-2026)上的最终评估
```

**交付物**：`models/bayes_fusion.py`, `models/xgb_model.py`, `models/ensemble.py`, 相关notebooks

### Phase 4：回测引擎与策略验证（2-3天）

```
□ 回测引擎构建
  ├── 避免前视偏差的DataLoader
  ├── 按时间顺序的事件驱动回测
  └── 绩效追踪与PnL计算
□ 信号生成器 vs 阈值扫描
  ├── 固定阈值方案
  ├── 凯利分数方案
  └── 最优阈值选择（验证集上最大化Sharpe）
□ 完整回测报告
  ├── 权益曲线
  ├── 按盘口类型/联赛/比赛类型的分解分析
  └── Bootstrap显著性检验
```

**交付物**：`backtest/engine.py`, `backtest/signal_generator.py`, 回测报告

### Phase 5：Polymarket实战验证（1-2天，世界杯决赛前）

```
□ Polymarket API数据收集脚本
□ 当前世界杯剩余比赛预测
  ├── 更新Elo评分至2026-07-11
  ├── 跑DC模型预测
  ├── 获取Polymarket当前盘口
  └── 偏差分析 → 信号生成
□ 小规模模拟下注追踪（或实盘小资金）
□ Out-of-sample验证记录
```

**交付物**：`notebooks/08_polymarket_live.ipynb`

### Phase 6：总结与优化（1天）

```
□ 研究总结报告
□ 四种模型对比分析
□ 策略优缺点复盘
□ 下一步优化方向
```

---

## 11. 风险与不确定性

### 11.1 方法论风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 过拟合历史数据 | 策略在样本外失效 | 严格时序CV + 保留最终测试集不动 |
| 前视偏差 | 回测虚高，实战亏损 | 代码中逐场检查；每条特征都验证时间戳 |
| 幸存者偏差 | 模型对"还在踢的强队"过量学习 | 使用退市球队的数据，不删减 |
| 模型错误指定 | DC假设不成立（进球非独立） | 用残差诊断检验 + 多个模型交叉验证 |
| Polymarket流动性不足 | 无法按预期价格执行 | 回测中加入流动性/滑点模拟 |

### 11.2 外部风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 世界杯仅剩约8场比赛 | 实战样本极小，无法统计验证 | 重点放在历史联赛回测；世界杯仅做定性验证 |
| Polymarket 2026世界杯盘口可能不同于联赛 | 迁移学习gap | 用2022世界杯数据做bridging验证（如果有） |
| 规则/监管变化 | Polymarket某些盘口下架 | 盘中监控 + 冗余盘口覆盖 |

### 11.3 诚实自检

回测做完之后，必须回答这几个问题（不做的话自欺欺人）：

1. 如果在Polymarket上实际执行这些信号，考虑滑点+Gas费+bid-ask spread后，PnL还正吗？
2. 策略的最大回撤发生在什么时候？当时我的心理承受力够吗？
3. 剔除2026世界杯数据（因为没做完），策略在2010-2022纯历史上的表现如何？
4. 如果我随机打乱模型预测，策略的表现怎样？（bootstrap零假设检验）
5. 策略是否依赖于少数几场"大赢"？（怪兽依赖度检测——去掉最赚钱的5笔交易后还正吗？）

---

## 12. 附录：关键文献与参考

### 12.1 学术经典

- Dixon, M.J. & Coles, S.G. (1997). "Modelling Association Football Scores and Inefficiencies in the Football Betting Market." *JRSS Series C*. — DC模型的原始论文，必读。
- Maher, M.J. (1982). "Modelling association football scores." *Statistica Neerlandica*. — 泊松模型的起源。
- Elo, A.E. (1978). *The Rating of Chessplayers, Past and Present*. — Elo系统的原始描述。
- FiveThirtyEight's Soccer Predictions methodology — Elo+SPI混合模型的实际工程应用。

### 12.2 预测市场研究

- Wolfers, J. & Zitzewitz, E. (2004). "Prediction Markets." *JEP*. — 预测市场的经典综述。
- Snowberg, E., Wolfers, J. & Zitzewitz, E. (2013). "Prediction Markets for Economic Forecasting." — 预测市场偏差的系统性研究。
- Polymarket whitepaper & CLOB documentation — 技术实现细节。

### 12.3 足球博彩

- Pinnacle's "How to Remove the Vig" — 去margin方法。
- Joseph Buchdahl's *Squares & Sharps, Suckers & Sharks* — 足球博彩市场的数学与心理学。
- Football-Data.co.uk notes — 数据字段说明。

### 12.4 量化技术

- Lopez de Prado, M. (2018). *Advances in Financial Machine Learning*. — 过拟合防御、时序交叉验证。
- Kelly, J.L. (1956). "A New Interpretation of Information Rate." — 凯利标准原始论文。

---

## 下一步行动

选择从 Phase 1 的第一步开始：

**1. 搭建项目目录 + Python环境**
**2. 下载 football-data.co.uk 数据（21个联赛 × 10+年）**
**3. 可视化探索：联赛比赛总数分布、Elo评分分布、博彩赔率分布**

你准备好了我就开始写代码。建议从 `01_eda.ipynb` 开始——先看到数据的样子，再做模型决策会更踏实。
