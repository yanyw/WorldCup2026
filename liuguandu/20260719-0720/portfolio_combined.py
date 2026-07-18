#!/usr/bin/env python3
"""
仓位组合分析: 将 France-England + Spain-Argentina 两场比赛的22笔交易
整合为统一投资组合，分析联合风险收益特征。
"""
import json, math, itertools
from collections import defaultdict

# ============================================================
# 0. 配置
# ============================================================
BANKROLL = 10000
MAX_G = 10

# ============================================================
# 1. DC 矩阵重建
# ============================================================
def pois(k, lam):
    if k < 0 or lam < 0: return 0.0
    return math.exp(-lam) * (lam**k) / math.factorial(k)

def dc_matrix(lh, la, rho, max_g=MAX_G):
    raw = [[0.0]*(max_g+1) for _ in range(max_g+1)]
    for i in range(max_g+1):
        for j in range(max_g+1):
            if   i==0 and j==0: tau = 1.0 - lh*la*rho
            elif i==1 and j==0: tau = 1.0 + lh*rho
            elif i==0 and j==1: tau = 1.0 + la*rho
            elif i==1 and j==1: tau = 1.0 - rho
            else:               tau = 1.0
            raw[i][j] = pois(i, lh) * pois(j, la) * max(tau, 1e-10)
    total = sum(sum(r) for r in raw)
    return [[v/total for v in r] for r in raw] if total > 0 else raw

# 比赛参数
MATCHES = {
    "FRA_ENG": {
        "lam_h": 1.3297, "lam_a": 1.3606, "rho": -0.04,
        "label": "France vs England (季军赛)"
    },
    "ESP_ARG": {
        "lam_h": 1.5553, "lam_a": 1.1198, "rho": -0.04,
        "label": "Spain vs Argentina (决赛)"
    },
}

# 生成两个DC矩阵
mx_fe = dc_matrix(1.3297, 1.3606, -0.04)
mx_ea = dc_matrix(1.5553, 1.1198, -0.04)
matrices = {"FRA_ENG": mx_fe, "ESP_ARG": mx_ea}

# ============================================================
# 2. 仓位数据
# ============================================================
with open("/workspace/wc2026_v2/finals_detailed_predictions.json") as f:
    data = json.load(f)

all_positions = []
for match_key in ["0719_Fran_Engl", "0720_Spai_Arge"]:
    for pos in data[match_key]["positions"]:
        pos["match_key"] = match_key
        all_positions.append(pos)

# ============================================================
# 3. 单场比赛单仓位 P&L 计算
# ============================================================
def position_pnl(pos, h_goals, a_goals, result_extra_time=False, result_penalty=False):
    """
    计算单个仓位在给定比分下的 P&L。
    pos: 仓位字典
    h_goals, a_goals: 常规时间比分
    result_extra_time: 是否进入加时 (常规时间平局)
    result_penalty: 是否进入点球 (常规时间平局 + 加时无胜负)
    """
    name = pos["name"]
    direction = pos["direction"]  # "buy" or "sell"
    p_mkt = pos["p_market"]
    amount = pos["amount"]
    total_goals = h_goals + a_goals
    btts = (h_goals > 0 and a_goals > 0)
    draw = (h_goals == a_goals)

    # 判断该仓位是否"赢"
    win = False

    if name == "1X2 AWAY":
        win = (a_goals > h_goals)
    elif name == "1X2 HOME":
        win = (h_goals > a_goals)
    elif name == "1X2 DRAW":
        win = draw

    elif name == "BTTS YES":
        win = btts
    elif name == "BTTS NO":
        win = not btts

    elif name.startswith("O") and not name.startswith("O/"):  # O2.5, O3.5 etc
        line = float(name[1:])
        win = total_goals > line
    elif name.startswith("U") and not name.startswith("U/"):  # U3.5 etc
        line = float(name[1:])
        win = total_goals <= line

    elif name.startswith("H -"):  # Home spread
        line = float(name[3:])
        win = (h_goals - a_goals) > line
    elif name.startswith("A +"):  # Away spread
        line = float(name[3:])
        win = (a_goals - h_goals) > -line  # same as h_goals - a_goals <= line

    elif name.startswith("H O"):  # Home team total Over
        line = float(name[3:])
        win = h_goals > line
    elif name.startswith("H U"):  # Home team total Under
        line = float(name[3:])
        win = h_goals <= line
    elif name.startswith("A O"):  # Away team total Over
        line = float(name[3:])
        win = a_goals > line
    elif name.startswith("A U"):  # Away team total Under
        line = float(name[3:])
        win = a_goals <= line

    elif name == "ToAdvance AWAY":
        # Away晋级: 常规时间赢 OR (平局 + 赢加时/点球)
        # 这里简化: 常规时间平局时，晋级概率约50%
        win = (a_goals > h_goals)  # sell means shorting AWAY advance
    elif name == "ToAdvance HOME":
        win = (h_goals > a_goals)

    elif name == "FirstScorer AWAY":
        # 简化: away先进球 ≈ away得分>0 且 (away先进球概率)
        if h_goals == 0 and a_goals == 0:
            win = False
        else:
            win = (a_goals > 0)  # 简化近似
    elif name == "FirstScorer HOME":
        if h_goals == 0 and a_goals == 0:
            win = False
        else:
            win = (h_goals > 0)

    elif name == "ExtraTime YES":
        win = draw
    elif name == "ExtraTime NO":
        win = not draw

    elif name == "Penalty YES":
        win = draw  # 加时后进入点球的前提是常规时间平局
    elif name == "Penalty NO":
        win = not draw

    # 仓位名称本身就代表期望结果，不需要翻转
    # "BTTS NO" sell → 期望 BTTS 不发生 → win=not btts ✓ (名称已包含)
    # "U3.5" sell → 期望总分≤3 → win=total≤3.5 ✓ (名称已包含)
    # "1X2 AWAY" buy → 期望客胜 → win=a>h ✓ (名称已包含)

    # 计算 P&L (Polymarket 预测市场逻辑)
    # p_mkt = 该仓位名称对应的底层合约市场价
    # BUY:  赢→ +amount*(1/p_mkt - 1)   输→ -amount
    # SELL: 赢→ +amount                  输→ -amount*(1/p_mkt - 1)
    if win:
        if direction == "buy":
            return amount * (1.0 / p_mkt - 1.0)
        else:
            return amount  # 卖出赢 → 对手方亏，我们赚全额本金
    else:
        if direction == "buy":
            return -amount
        else:
            return -amount * (1.0 / p_mkt - 1.0)  # 卖出输 → 赔对手方

# ============================================================
# 4. 组合场景分析
# ============================================================
def analyze_portfolio():
    # 获取每场比赛的 top 比分 (覆盖~75%概率质量)
    def top_scores(mx, n=7):
        scores = []
        for i in range(8):
            for j in range(8):
                scores.append((i, j, mx[i][j]))
        scores.sort(key=lambda x: x[2], reverse=True)
        return scores[:n]

    scores_fe = top_scores(mx_fe, 7)
    scores_ea = top_scores(mx_ea, 7)

    # 分离两场比赛的仓位
    pos_fe = [p for p in all_positions if p["match_key"] == "0719_Fran_Engl"]
    pos_ea = [p for p in all_positions if p["match_key"] == "0720_Spai_Arge"]

    print("=" * 100)
    print("  投资组合综合分析: 世界杯决赛周 22笔交易")
    print("=" * 100)
    print(f"  总资金: ${BANKROLL:,}")
    print(f"  France-England: {len(pos_fe)} 笔, ${sum(p['amount'] for p in pos_fe):,.0f}")
    print(f"  Spain-Argentina: {len(pos_ea)} 笔, ${sum(p['amount'] for p in pos_ea):,.0f}")
    total_exposure = sum(p['amount'] for p in all_positions)
    print(f"  组合总风险敞口: ${total_exposure:,.0f} ({total_exposure/BANKROLL*100:.1f}%)")
    print()

    # --- 仓位分类汇总 ---
    print("=" * 100)
    print("  仓位分类汇总")
    print("=" * 100)
    
    categories = defaultdict(lambda: {"buy_amount": 0, "sell_amount": 0, "buy_count": 0, "sell_count": 0})
    for p in all_positions:
        name = p["name"]
        # 分类
        if name.startswith("1X2"): cat = "1X2 胜负平"
        elif name.startswith("BTTS"): cat = "BTTS 双方进球"
        elif name.startswith("O") or name.startswith("U"): cat = "总分 O/U"
        elif " -" in name or " +" in name: cat = "让分盘"
        elif name.startswith("H ") or name.startswith("A "): cat = "球队总分"
        elif name.startswith("ToAdvance"): cat = "晋级"
        elif name.startswith("FirstScorer"): cat = "先进球"
        elif name.startswith("ExtraTime"): cat = "加时赛"
        elif name.startswith("Penalty"): cat = "点球大战"
        else: cat = "其他"
        
        if p["direction"] == "buy":
            categories[cat]["buy_amount"] += p["amount"]
            categories[cat]["buy_count"] += 1
        else:
            categories[cat]["sell_amount"] += p["amount"]
            categories[cat]["sell_count"] += 1

    print(f"  {'类别':<18s} {'买入笔数':>6s} {'买入金额':>10s} {'卖出笔数':>6s} {'卖出金额':>10s} {'合计':>10s}")
    print(f"  {'─'*18} {'─'*6} {'─'*10} {'─'*6} {'─'*10} {'─'*10}")
    for cat, v in sorted(categories.items()):
        total = v["buy_amount"] + v["sell_amount"]
        print(f"  {cat:<18s} {v['buy_count']:>6d} ${v['buy_amount']:>9,.0f} {v['sell_count']:>6d} ${v['sell_amount']:>9,.0f} ${total:>9,.0f}")
    print()

    # --- 联合场景 P&L 网格 ---
    print("=" * 100)
    print("  联合场景 P&L 矩阵 (France-England 得分 × Spain-Argentina 得分)")
    print("=" * 100)
    print(f"  选取每场 Top 7 比分，共 49 个联合场景")
    print()

    # 表头
    header_scores = [f"{h}-{a}" for h, a, _ in scores_ea]
    header_title = "FRA-ENG ↓ \\ ESP-ARG →"
    print(f"  {header_title:<20s}", end="")
    for s in header_scores:
        print(f" {s:>12s}", end="")
    print(f" {'边际EV':>10s}")
    print(f"  {'─'*20}", end="")
    for _ in header_scores:
        print(f" {'─'*12}", end="")
    print(f" {'─'*10}")

    all_scenarios = []
    for h_fe, a_fe, p_fe in scores_fe:
        fe_score = f"{h_fe}-{a_fe}"
        row_pnls = []
        row_ev = 0
        for h_ea, a_ea, p_ea in scores_ea:
            joint_p = p_fe * p_ea
            # FRA-ENG 仓位的 P&L
            pnl_fe = sum(position_pnl(p, h_fe, a_fe) for p in pos_fe)
            # ESP-ARG 仓位的 P&L
            pnl_ea = sum(position_pnl(p, h_ea, a_ea) for p in pos_ea)
            total_pnl = pnl_fe + pnl_ea
            row_pnls.append(total_pnl)
            row_ev += total_pnl * joint_p
            all_scenarios.append({
                "score_fe": fe_score, "score_ea": f"{h_ea}-{a_ea}",
                "p_fe": p_fe, "p_ea": p_ea, "joint_p": joint_p,
                "pnl_fe": pnl_fe, "pnl_ea": pnl_ea, "pnl_total": total_pnl
            })

        print(f"  {fe_score:<20s}", end="")
        for pnl in row_pnls:
            color = "\033[92m" if pnl > 0 else "\033[91m" if pnl < 0 else ""
            print(f" {color}${pnl:>11,.0f}\033[0m", end="")
        print(f" ${row_ev:>9,.0f}")

    # 底部: 边际 EV
    print(f"  {'─'*20}", end="")
    for _ in header_scores:
        print(f" {'─'*12}", end="")
    print(f" {'─'*10}")

    print(f"  {'ESP-ARG 边际 EV':<20s}", end="")
    for j, (h_ea, a_ea, p_ea) in enumerate(scores_ea):
        col_ev = 0
        for i, (h_fe, a_fe, p_fe) in enumerate(scores_fe):
            joint_p = p_fe * p_ea
            pnl_fe = sum(position_pnl(p, h_fe, a_fe) for p in pos_fe)
            pnl_ea = sum(position_pnl(p, h_ea, a_ea) for p in pos_ea)
            col_ev += (pnl_fe + pnl_ea) * joint_p
        color = "\033[92m" if col_ev > 0 else "\033[91m"
        print(f" {color}${col_ev:>11,.0f}\033[0m", end="")
    print()

    # --- 组合统计 ---
    print()
    print("=" * 100)
    print("  组合风险指标")
    print("=" * 100)

    # 总 EV
    total_ev = sum(s["pnl_total"] * s["joint_p"] for s in all_scenarios)
    # 剩余概率质量（不在top 7中的）
    remaining_p = 1.0 - sum(s["joint_p"] for s in all_scenarios)

    print(f"  总期望收益 (EV): ${total_ev:+,.0f}  ({total_ev/BANKROLL*100:+.2f}%)")

    # 按 P&L 排序
    sorted_scenarios = sorted(all_scenarios, key=lambda x: x["pnl_total"])

    # VaR
    cum_p = 0
    var_95 = 0
    for s in sorted_scenarios:
        cum_p += s["joint_p"]
        if cum_p >= 0.05:
            var_95 = s["pnl_total"]
            break
    print(f"  95% VaR (最差5%场景): ${var_95:+,.0f}")

    cum_p = 0
    var_99 = 0
    for s in sorted_scenarios:
        cum_p += s["joint_p"]
        if cum_p >= 0.01:
            var_99 = s["pnl_total"]
            break
    print(f"  99% VaR (最差1%场景): ${var_99:+,.0f}")

    # 最佳/最差
    best = sorted_scenarios[-1]
    worst = sorted_scenarios[0]
    print(f"  最佳场景: {best['score_fe']} + {best['score_ea']} → ${best['pnl_total']:+,.0f} (p={best['joint_p']*100:.2f}%)")
    print(f"  最差场景: {worst['score_fe']} + {worst['score_ea']} → ${worst['pnl_total']:+,.0f} (p={worst['joint_p']*100:.2f}%)")

    # 盈利概率
    win_p = sum(s["joint_p"] for s in all_scenarios if s["pnl_total"] > 0)
    loss_p = sum(s["joint_p"] for s in all_scenarios if s["pnl_total"] < 0)
    print(f"  盈利概率: {win_p*100:.1f}%  |  亏损概率: {loss_p*100:.1f}%  |  盈亏比: {win_p/max(loss_p,0.001):.2f}")

    # 收益分布
    print()
    print("=" * 100)
    print("  P&L 分布区间")
    print("=" * 100)
    bins = [(-99999, -2000), (-2000, -1000), (-1000, -500), (-500, 0),
            (0, 500), (500, 1000), (1000, 2000), (2000, 5000), (5000, 99999)]
    labels = ["<-$2,000", "-$2,000~-$1,000", "-$1,000~-$500", "-$500~$0",
              "$0~$500", "$500~$1,000", "$1,000~$2,000", "$2,000~$5,000", ">$5,000"]
    
    print(f"  {'区间':<20s} {'概率':>8s} {'累计':>8s}  {'分布'}")
    print(f"  {'─'*20} {'─'*8} {'─'*8}  {'─'*40}")
    cum = 0
    for (lo, hi), label in zip(bins, labels):
        prob = sum(s["joint_p"] for s in all_scenarios if lo <= s["pnl_total"] < hi)
        cum += prob
        bar = "█" * int(prob * 200)
        print(f"  {label:<20s} {prob*100:>7.1f}% {cum*100:>7.1f}%  {bar}")

    # --- 两场比赛相关性 ---
    print()
    print("=" * 100)
    print("  两场比赛 P&L 相关性分析")
    print("=" * 100)

    # 分别计算每场比赛的P&L分布
    fe_pnls = []
    ea_pnls = []
    fe_ev = 0
    ea_ev = 0
    for s in all_scenarios:
        fe_pnls.append((s["pnl_fe"], s["joint_p"]))
        ea_pnls.append((s["pnl_ea"], s["joint_p"]))
        fe_ev += s["pnl_fe"] * s["joint_p"]
        ea_ev += s["pnl_ea"] * s["joint_p"]

    print(f"  France-England 独立 EV: ${fe_ev:+,.0f}  |  Spain-Argentina 独立 EV: ${ea_ev:+,.0f}")
    print(f"  组合总 EV: ${total_ev:+,.0f}  (= {fe_ev:+,.0f} + {ea_ev:+,.0f})")
    print()

    # 协方差 (简化: 只看FE盈亏 vs EA盈亏的符号)
    both_win = sum(s["joint_p"] for s in all_scenarios if s["pnl_fe"] > 0 and s["pnl_ea"] > 0)
    both_lose = sum(s["joint_p"] for s in all_scenarios if s["pnl_fe"] < 0 and s["pnl_ea"] < 0)
    fe_win_ea_lose = sum(s["joint_p"] for s in all_scenarios if s["pnl_fe"] > 0 and s["pnl_ea"] < 0)
    fe_lose_ea_win = sum(s["joint_p"] for s in all_scenarios if s["pnl_fe"] < 0 and s["pnl_ea"] > 0)

    print(f"  联合盈亏分布:")
    print(f"    两场都盈: {both_win*100:.1f}%  → 组合最强区间")
    print(f"    FE盈+EA亏: {fe_win_ea_lose*100:.1f}%  → 部分对冲")
    print(f"    FE亏+EA盈: {fe_lose_ea_win*100:.1f}%  → 部分对冲")
    print(f"    两场都亏: {both_lose*100:.1f}%  → 组合最弱区间")
    print(f"    自然对冲概率: {(fe_win_ea_lose + fe_lose_ea_win)*100:.1f}%")
    print(f"    至少一场盈利: {(1-both_lose)*100:.1f}%")

    # --- 仓位贡献分析 ---
    print()
    print("=" * 100)
    print("  仓位 EV 贡献排名 (按单笔 EV 绝对贡献)")
    print("=" * 100)

    # 计算每笔仓位的 EV 贡献
    pos_contributions = []
    for p in all_positions:
        ev = 0
        for s in all_scenarios:
            if p["match_key"] == "0719_Fran_Engl":
                h, a = map(int, s["score_fe"].split("-"))
            else:
                h, a = map(int, s["score_ea"].split("-"))
            pnl = position_pnl(p, h, a)
            ev += pnl * s["joint_p"]
        pos_contributions.append({
            "name": p["name"],
            "direction": p["direction"],
            "amount": p["amount"],
            "match": "FE" if p["match_key"] == "0719_Fran_Engl" else "EA",
            "ev": ev,
            "edge": p["edge"],
        })

    pos_contributions.sort(key=lambda x: abs(x["ev"]), reverse=True)

    print(f"  {'#':>3s} {'比赛':>4s} {'方向':>5s} {'盘口':<22s} {'仓位':>7s} {'EV贡献':>8s} {'ROI':>6s}")
    print(f"  {'─'*3} {'─'*4} {'─'*5} {'─'*22} {'─'*7} {'─'*8} {'─'*6}")
    for i, pc in enumerate(pos_contributions, 1):
        roi = pc["ev"] / pc["amount"] * 100 if pc["amount"] > 0 else 0
        dir_sym = "▲BUY" if pc["direction"] == "buy" else "▼SELL"
        ev_sign = "+" if pc["ev"] > 0 else ""
        print(f"  {i:>3d} {pc['match']:>4s} {dir_sym:>5s} {pc['name']:<22s} ${pc['amount']:>6,.0f} {ev_sign}${pc['ev']:>7,.0f} {roi:>5.1f}%")

    # --- 风险分解: 最差场景溯源 ---
    print()
    print("=" * 100)
    print("  风险溯源: Top 5 最差联合场景")
    print("=" * 100)
    print(f"  {'场景':<25s} {'联合概率':>8s} {'FE P&L':>10s} {'EA P&L':>10s} {'组合 P&L':>10s} {'主要亏损来源'}")
    print(f"  {'─'*25} {'─'*8} {'─'*10} {'─'*10} {'─'*10} {'─'*20}")

    for s in sorted_scenarios[:5]:
        # 找出最赔钱的仓位
        fe_pos_losses = []
        ea_pos_losses = []
        h_fe, a_fe = map(int, s["score_fe"].split("-"))
        h_ea, a_ea = map(int, s["score_ea"].split("-"))
        for p in pos_fe:
            pnl = position_pnl(p, h_fe, a_fe)
            if pnl < -50:
                fe_pos_losses.append((p["name"], pnl))
        for p in pos_ea:
            pnl = position_pnl(p, h_ea, a_ea)
            if pnl < -50:
                ea_pos_losses.append((p["name"], pnl))

        all_losses = fe_pos_losses + ea_pos_losses
        all_losses.sort(key=lambda x: x[1])
        loss_sources = ", ".join([f"{n}(${l:.0f})" for n, l in all_losses[:2]])

        print(f"  {s['score_fe']:<6s} + {s['score_ea']:<6s}      {s['joint_p']*100:>5.1f}%   "
              f"${s['pnl_fe']:>9,.0f}  ${s['pnl_ea']:>9,.0f}  "
              f"\033[91m${s['pnl_total']:>9,.0f}\033[0m   {loss_sources}")

    # --- 投资组合优化建议 ---
    print()
    print("=" * 100)
    print("  组合优化建议")
    print("=" * 100)

    # 检查是否有对冲不足的场景
    # 找出所有"两场都亏"场景中的共性
    both_lose_scenarios = [s for s in all_scenarios if s["pnl_fe"] < 0 and s["pnl_ea"] < 0]
    both_lose_total = sum(s["joint_p"] for s in both_lose_scenarios)

    print(f"  1. 两场都亏概率: {both_lose_total*100:.1f}%")
    if both_lose_scenarios:
        print(f"     - 最大双亏: ${min(s['pnl_total'] for s in both_lose_scenarios):,.0f}")
    else:
        print(f"     - 在 Top 49 场景中无双亏场景 (但尾部风险仍存在)")
    print(f"     - 建议: 该组合已通过跨比赛分散降低集中风险")

    print()
    print(f"  2. 自然对冲覆盖率: {(fe_win_ea_lose + fe_lose_ea_win)*100:.1f}%")
    if (fe_win_ea_lose + fe_lose_ea_win) > 0.4:
        print(f"     ✅ 组合具有较好的自然对冲属性")
    else:
        print(f"     ⚠️ 组合对冲不足，建议增加反向仓位")

    print()
    print(f"  3. 总风险敞口: {total_exposure/BANKROLL*100:.1f}% (两场合计)")
    print(f"     - FE单场: {sum(p['amount'] for p in pos_fe)/BANKROLL*100:.1f}%")
    print(f"     - EA单场: {sum(p['amount'] for p in pos_ea)/BANKROLL*100:.1f}%")
    print(f"     - 两场比赛独立，风险可加。当前20%总敞口在可接受范围内。")

    # EV/风险比
    total_ev_simple = sum(
        (p["p_model"] if p["direction"] == "buy" else p["p_market"]) * p["amount"] * (
            (1/p["p_market"]-1) if p["direction"] == "buy" else (1/(1-p["p_market"])-1)
        ) - 
        ((1-p["p_model"]) if p["direction"] == "buy" else (1-p["p_market"])) * p["amount"]
        for p in all_positions
    )
    # 使用联合场景的更准确的EV
    exact_total_ev = total_ev

    print()
    print(f"  4. 组合夏普比率 (粗略): {exact_total_ev/total_exposure:.3f}")
    print()

    # --- 非对称风险特别分析 ---
    print("=" * 100)
    print("  ⚠️ 非对称风险警示: SELL 仓位尾部风险分析")
    print("=" * 100)

    sell_positions = [p for p in all_positions if p["direction"] == "sell"]
    print(f"  {'盘口':<22s} {'仓位':>7s} {'市场价格':>8s} {'赢→收益':>10s} {'输→损失':>10s} {'风险比':>8s}")
    print(f"  {'─'*22} {'─'*7} {'─'*8} {'─'*10} {'─'*10} {'─'*8}")
    for p in sell_positions:
        if p["direction"] == "sell":
            win_gain = p["amount"]
            lose_loss = -p["amount"] * (1.0 / p["p_market"] - 1.0)
            risk_ratio = abs(lose_loss / win_gain)
            risk_flag = " 🔴" if risk_ratio > 3 else " 🟡" if risk_ratio > 1.5 else " 🟢"
            print(f"  {p['name']:<22s} ${p['amount']:>6,.0f} {p['p_market']*100:>7.1f}% "
                  f"+${win_gain:>9,.0f} -${abs(lose_loss):>9,.0f} "
                  f"{risk_ratio:>5.1f}x{risk_flag}")

    print()
    print(f"  🔴 风险比>3x: 一旦判断错误，损失远超收益")
    print(f"  🟡 风险比1.5-3x: 中等非对称风险")
    print(f"  🟢 风险比<1.5x: 风险收益相对均衡")
    print()
    print(f"  建议: 对🔴标记的仓位，考虑减仓50%或设置止损")

    return all_scenarios

if __name__ == "__main__":
    scenarios = analyze_portfolio()

    # 保存分析结果
    output = {
        "portfolio_summary": {
            "total_positions": len(all_positions),
            "total_exposure": sum(p["amount"] for p in all_positions),
            "total_exposure_pct": round(sum(p["amount"] for p in all_positions) / BANKROLL * 100, 1),
        },
        "scenarios": [{
            "score_fe": s["score_fe"],
            "score_ea": s["score_ea"],
            "joint_probability": round(s["joint_p"], 6),
            "pnl_fe": round(s["pnl_fe"], 0),
            "pnl_ea": round(s["pnl_ea"], 0),
            "pnl_total": round(s["pnl_total"], 0),
        } for s in scenarios],
    }
    with open("/workspace/wc2026_v2/portfolio_analysis.json", "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 组合分析结果已保存")
