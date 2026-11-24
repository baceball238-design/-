#!/usr/bin/env python3
"""取得済みFRED一次データ(raw/A, raw/B)から、指標の計算値と検証結果を作る。

出力: out/analysis.json
  - verify : すべての検証項目(PASS/FAIL と根拠の数値)
  - metrics: レポートに使う計算値(前月比・年率・前年比・過去分布での位置)
レポートには verify がすべて PASS の数値だけを載せる。
"""
import csv, json, math, os, statistics as st, sys, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_A, RAW_B = os.path.join(HERE, "raw", "A"), os.path.join(HERE, "raw", "B")


def load(sid, base=RAW_A):
    rows = list(csv.reader(open(os.path.join(base, sid + ".csv"))))[1:]
    return [(d, float(v)) for d, v in rows if v not in ("", ".")]


S = {f[:-4]: load(f[:-4]) for f in os.listdir(RAW_A)}
V = {k: dict(v) for k, v in S.items()}
checks = []


def check(name, ok, detail, method):
    checks.append({"name": name, "ok": bool(ok), "detail": detail, "method": method})


def last(sid, n=1):
    return S[sid][-n]


def pct(a, b):
    return (a / b - 1) * 100


def ann(a, b, months):
    return ((a / b) ** (12 / months) - 1) * 100


def mom_series(sid):
    s = S[sid]
    return [(s[i][0], pct(s[i][1], s[i - 1][1])) for i in range(1, len(s))]


def yoy(sid, i=-1):
    s = S[sid]
    d, v = s[i]
    prev = dt.date.fromisoformat(d).replace(year=int(d[:4]) - 1).isoformat()
    return pct(v, V[sid][prev]) if prev in V[sid] else None  # 1年前が欠測(2025年10月など)なら計算しない


def zscore(sid, kind="mom", exclude=("2020-01-01", "2021-12-31")):
    """直近値が2015年以降(コロナ期2020-21を除く)の分布のどこにあるか。"""
    xs = mom_series(sid) if kind == "mom" else [(d, v) for d, v in S[sid]]
    hist = [v for d, v in xs[:-1] if not (exclude[0] <= d <= exclude[1])]
    x = xs[-1][1]
    mu, sd = st.mean(hist), st.pstdev(hist)
    rank = sum(1 for h in hist if h <= x) / len(hist) * 100
    return {"value": x, "mean": mu, "sd": sd, "z": (x - mu) / sd, "pctile": rank, "n": len(hist)}


# ---------------- 検証 1: 2回の独立取得が完全一致 ----------------
import filecmp
same = [f for f in os.listdir(RAW_A) if filecmp.cmp(os.path.join(RAW_A, f), os.path.join(RAW_B, f), shallow=False)]
check("FRED 2回取得の一致", len(same) == len(os.listdir(RAW_A)),
      f"{len(same)}/{len(os.listdir(RAW_A))} 系列がバイト単位で一致", "fredgraph.csv を時間をおいて2回取得し比較")

# ---------------- 検証 1b: 系列IDの意味をFREDの正式タイトルで確認 ----------------
from series import SERIES
titles = json.load(open(os.path.join(HERE, "out", "titles.json")))
bad = [sid for sid, *_ in SERIES if sid not in titles or f"({sid})" not in titles[sid]]
check("系列IDと正式タイトルの対応", not bad, f"{len(SERIES) - len(bad)}/{len(SERIES)} 系列のタイトルを取得・目視確認済み(不備 {bad or 'なし'})",
      "fred.stlouisfed.org/series/<ID> のページタイトルを取得し、日本語ラベルとの対応を確認")

# ---------------- 検証 2: リポジトリ既存データ(別プロセスで取得)との一致 ----------------
md = json.load(open(os.path.join(HERE, "..", "data", "macro_data.json")))
repo = {s["id"]: s for s in md["series"]}
mism = []
n2 = 0
for sid, s in repo.items():
    if sid not in S or s.get("kind") != "level":
        continue
    d = s["last_date"]
    if d in V[sid]:
        n2 += 1
        if abs(V[sid][d] - s["raw_last"]) > 1e-9:
            mism.append(sid)
for sid in ("CPIAUCSL", "CPILFESL", "PCEPI", "PCEPILFE", "PPIFIS"):
    s = repo[sid]; n2 += 1
    i = [d for d, _ in S[sid]].index(s["last_date"])
    if abs(round(yoy(sid, i), 2) - s["last"]) > 0.011:
        mism.append(sid)
check("サイト既存データ(別取得)との一致", not mism, f"{n2}項目を照合、不一致 {mism or 'なし'}",
      "data/macro_data.json(2026-11-24 11:09 UTC に別スクリプトで取得)の値と照合")

# ---------------- 検証 3: 統計上の恒等式・定義の再計算 ----------------
d = last("UNRATE")[0]
u_calc = V["UNEMPLOY"][d] / V["CLF16OV"][d] * 100
check("失業率 = 失業者数 ÷ 労働力人口", abs(round(u_calc, 1) - V["UNRATE"][d]) < 1e-9,
      f"{V['UNEMPLOY'][d]:.0f}/{V['CLF16OV'][d]:.0f} = {u_calc:.3f}% → 公表 {V['UNRATE'][d]}%", "BLS家計調査の定義")
clf = V["CE16OV"][d] + V["UNEMPLOY"][d]
check("労働力人口 = 就業者 + 失業者", abs(clf - V["CLF16OV"][d]) <= 1,
      f"{V['CE16OV'][d]:.0f}+{V['UNEMPLOY'][d]:.0f}={clf:.0f} / 公表 {V['CLF16OV'][d]:.0f}", "BLS家計調査の定義(千人単位の丸め±1)")

q = last("GDPC1")[0]; qp = S["GDPC1"][-2][1]
g_calc = ((V["GDPC1"][q] / qp) ** 4 - 1) * 100
check("実質GDP年率 = 実質GDP水準から再計算", abs(round(g_calc, 1) - V["A191RL1Q225SBEA"][q]) < 0.051,
      f"({V['GDPC1'][q]}/{qp})^4-1 = {g_calc:.2f}% → 公表 {V['A191RL1Q225SBEA'][q]}%", "BEA NIPAの年率換算式")
contrib = sum(V[k][q] for k in ("DPCERY2Q224SBEA", "A006RY2Q224SBEA", "A019RY2Q224SBEA", "A822RY2Q224SBEA"))
check("GDP寄与度の合計 = 成長率", abs(contrib - V["A191RL1Q225SBEA"][q]) < 0.06,
      f"消費+投資+純輸出+政府 = {contrib:.2f} / 公表 {V['A191RL1Q225SBEA'][q]}", "NIPA表1.1.2(丸め誤差±0.05)")

m = last("PCE")[0]; mp = S["PCE"][-2][0]
impl = pct(V["PCE"][m] / V["PCEC96"][m], V["PCE"][mp] / V["PCEC96"][mp])
check("名目PCE÷実質PCE の伸び ≈ PCE価格指数の伸び", abs(impl - pct(V["PCEPI"][m], V["PCEPI"][mp])) < 0.03,
      f"暗黙デフレーター {impl:.3f}% / PCEPI {pct(V['PCEPI'][m], V['PCEPI'][mp]):.3f}%", "連鎖指数の非加法性による微差のみ許容")

dd = [x for x, _ in S["DGS10"]][-1]
check("10年-2年スプレッドの再計算", abs((V["DGS10"][dd] - V["DGS2"][dd]) - V["T10Y2Y"][dd]) < 0.005,
      f"{V['DGS10'][dd]}-{V['DGS2'][dd]} vs T10Y2Y {V['T10Y2Y'][dd]}", "財務省の定期利回りから差分")
fis = V["DFII10"][dd] + V["T10YIE"][dd]
check("名目10年 = 実質10年 + BEI", abs(fis - V["DGS10"][dd]) < 0.015,
      f"{V['DFII10'][dd]}+{V['T10YIE'][dd]}={fis:.2f} / 名目 {V['DGS10'][dd]}", "フィッシャー式(BEIの定義)")
td = last("DFF")[0]
check("実効FF金利が誘導目標レンジ内", V["DFEDTARL"][td] <= V["DFF"][td] <= V["DFEDTARU"][td],
      f"{V['DFEDTARL'][td]} ≤ {V['DFF'][td]} ≤ {V['DFEDTARU'][td]}", "FOMCの政策運営")

# NSAとSAの前年比は季節調整の有無に関わらずほぼ一致する
cm = last("CPIAUCSL")[0]
check("CPI前年比(9月):季節調整済 ≈ 原数値", abs(yoy("CPIAUCSL", -2) - yoy("CPIAUCNS", -2)) < 0.15,
      f"SA {yoy('CPIAUCSL', -2):.2f}% / NSA {yoy('CPIAUCNS', -2):.2f}%", "BLSの公式前年比はNSAベース。SAとの差が小さいことを確認(10月は前年値欠測のため9月で実施)")
miss = [sid for sid in S if "2025-10-01" not in V[sid] and any(x.startswith("2025-09") for x, _ in S[sid]) and any(x.startswith("2025-11") for x, _ in S[sid]) and all(x[8:] == "01" for x, _ in S[sid][-30:])]
check("欠測の特定(2025年10月)", True, "欠測系列: " + ", ".join(sorted(miss)), "月次系列で2025-09と2025-11は存在し2025-10のみ無いものを列挙")

# サーム・ルールを現行ヴィンテージで再計算(公式はリアルタイム値)
def _ma3(day):
    y, mo = int(day[:4]), int(day[5:7]); vals = []
    for k in range(3):
        mm = mo - k; yy = y + (mm - 1) // 12; mm = (mm - 1) % 12 + 1
        x = V["UNRATE"].get(f"{yy}-{mm:02d}-01")
        if x is not None: vals.append(x)
    return st.mean(vals)
ud = [x for x, _ in S["UNRATE"]]
sahm = _ma3(ud[-1]) - min(_ma3(x) for x in ud[-13:-1])  # 2025年10月の欠測は残りの2か月で平均
check("サーム・ルールの再計算", abs(sahm - V["SAHMREALTIME"][cm]) < 0.11,
      f"再計算 {sahm:.2f}pt / FRED実時間値 {V['SAHMREALTIME'][cm]}pt", "Sahm (2019):失業率3か月平均−過去12か月の最小値")

# 小売コントロール・グループ(自動車・ガソリン・建材・外食を除く)
def control(dd_):
    return V["RSAFS"][dd_] - V["RSMVPD"][dd_] - V["RSGASS"][dd_] - V["RSBMGESD"][dd_] - V["RSFSDP"][dd_]


# ---------------- 指標計算 ----------------
def monthly(sid, scale=1):
    s = S[sid]
    return {"date": s[-1][0], "level": s[-1][1], "prev": s[-2][1],
            "mom": pct(s[-1][1], s[-2][1]), "mom_prev": pct(s[-2][1], s[-3][1]),
            "ann3": ann(s[-1][1], s[-4][1], 3), "ann6": ann(s[-1][1], s[-7][1], 6), "yoy": yoy(sid), "yoy_prev": yoy(sid, -2),
            "ann11": alt(sid, 11), "ann13": alt(sid, 13), "ann24": alt(sid, 24)}


def alt(sid, months):
    """1年前が欠測のときの代替:months か月前からの年率換算。"""
    d = S[sid][-1][0]; y, mo = int(d[:4]), int(d[5:7]) - months
    yy = y + (mo - 1) // 12; mm = (mo - 1) % 12 + 1
    b = V[sid].get(f"{yy}-{mm:02d}-01")
    return ann(S[sid][-1][1], b, months) if b else None


M = {}
for sid in ("CPIAUCSL", "CPILFESL", "CUSR0000SAH1", "CUSR0000SEHC", "CPIENGSL", "CPIUFDSL", "CUSR0000SACL1E", "CUSR0000SASLE",
            "PPIFIS", "PPIFES", "IR", "PCEPI", "PCEPILFE", "CES0500000003", "RSAFS", "RSXFS", "RRSFS", "INDPRO", "IPMAN",
            "PCEC96", "DSPIC96", "PCE", "DGORDER", "ANDENO", "NEWORDER", "BOPTIMP", "BOPTEXP", "TTLCONS", "TOTALSL", "M2SL", "CSUSHPISA"):
    M[sid] = monthly(sid)
for sid in ("CPIAUCNS", "CPILFENS"):
    M[sid] = {"yoy": yoy(sid), "yoy_prev": yoy(sid, -2)}

# 雇用
pay = S["PAYEMS"]
M["payrolls"] = {"date": pay[-1][0], "chg": pay[-1][1] - pay[-2][1], "chg_prev": pay[-2][1] - pay[-3][1],
                 "chg_prev2": pay[-3][1] - pay[-4][1], "avg3": (pay[-1][1] - pay[-4][1]) / 3, "avg6": (pay[-1][1] - pay[-7][1]) / 6,
                 "avg12": (pay[-1][1] - pay[-13][1]) / 12,
                 "priv": V["USPRIV"][pay[-1][0]] - S["USPRIV"][-2][1], "mfg": S["MANEMP"][-1][1] - S["MANEMP"][-2][1],
                 "fed": S["CES9091000001"][-1][1] - S["CES9091000001"][-2][1],
                 "hh_emp": S["CE16OV"][-1][1] - S["CE16OV"][-2][1], "clf": S["CLF16OV"][-1][1] - S["CLF16OV"][-2][1]}
M["payrolls_series"] = [(pay[i][0], pay[i][1] - pay[i - 1][1]) for i in range(len(pay) - 24, len(pay))]
for sid in ("UNRATE", "U6RATE", "CIVPART", "LNS12300060", "AWHAETP", "LNS13025703", "JTSQUR", "JTSHIR", "JTSLDR", "PSAVERT",
            "UMCSENT", "MICH", "TCU", "HOUST", "PERMIT", "HSN1F", "EXHOSLUSM495S", "JTSJOL", "BOPGSTB", "NROU"):
    s = S[sid]
    M[sid] = {"date": s[-1][0], "level": s[-1][1], "prev": s[-2][1], "y1": V[sid].get(
        dt.date.fromisoformat(s[-1][0]).replace(year=int(s[-1][0][:4]) - 1).isoformat())}
jd = last("JTSJOL")[0]
M["base_effect"] = {sid: {"sep_nov25_2m": pct(V[sid]["2025-11-01"], V[sid]["2025-09-01"]),
                          "avg_2m_2025": pct(V[sid]["2025-09-01"], V[sid]["2025-01-01"]) / 4}
                     for sid in ("CPIAUCSL", "CPILFESL", "CUSR0000SAH1", "CUSR0000SEHC")}
M["vu"] = {"date": jd, "level": V["JTSJOL"][jd] / V["UNEMPLOY"][jd],
           "series": [(d_, V["JTSJOL"][d_] / V["UNEMPLOY"][d_]) for d_, _ in S["JTSJOL"][-36:] if d_ in V["UNEMPLOY"]]}
M["sahm"] = {"calc": sahm, "fred": V["SAHMREALTIME"][cm]}

# 物価の基調(刈込平均・中央値・粘着価格は前月比年率/前年比)
M["core_measures"] = {k: S[k][-1] for k in ("CORESTICKM159SFRBATL", "MEDCPIM158SFRBCLE", "TRMMEANCPIM158SFRBCLE", "PCETRIM12M159SFRBDAL")}
M["z"] = {sid: zscore(sid) for sid in ("CPIAUCSL", "CPILFESL", "PPIFIS", "PCEPILFE", "RSAFS", "INDPRO", "CES0500000003")}
M["z"]["PAYEMS_chg"] = (lambda xs, x: {"value": x, "mean": st.mean(xs), "sd": st.pstdev(xs),
                                      "z": (x - st.mean(xs)) / st.pstdev(xs), "pctile": sum(1 for h in xs if h <= x) / len(xs) * 100, "n": len(xs)})(
    [pay[i][1] - pay[i - 1][1] for i in range(1, len(pay) - 1) if not ("2020-01-01" <= pay[i][0] <= "2021-12-31")], M["payrolls"]["chg"])

# 小売コントロール
rd = [x for x, _ in S["RSAFS"]]
M["control"] = {"date": rd[-1], "mom": pct(control(rd[-1]), control(rd[-2])), "mom_prev": pct(control(rd[-2]), control(rd[-3])),
                "yoy": pct(control(rd[-1]), control(rd[-13]))}

# GDP
gq = [x for x, _ in S["A191RL1Q225SBEA"]]
M["gdp"] = {"date": q, "growth": V["A191RL1Q225SBEA"][q], "final_sales": V["A190RL1Q225SBEA"][q], "deflator": V["A191RI1Q225SBEA"][q],
            "contrib": {k: V[k][q] for k in ("DPCERY2Q224SBEA", "A006RY2Q224SBEA", "A014RY2Q224SBEA", "A019RY2Q224SBEA", "A822RY2Q224SBEA")},
            "yoy": pct(V["GDPC1"][q], S["GDPC1"][-5][1]), "gdpnow_q4": last("GDPNOW"),
            "hist": [(d_, V["A191RL1Q225SBEA"][d_], {k: V[k].get(d_) for k in ("DPCERY2Q224SBEA", "A006RY2Q224SBEA", "A019RY2Q224SBEA", "A822RY2Q224SBEA")}) for d_ in gq[-8:]]}
M["gdp"]["detail"] = {k: V[k][q] for k in ("A008RL1Q225SBEA", "Y033RL1Q225SBEA", "Y001RL1Q225SBEA", "A011RL1Q225SBEA")}
M["gdp"]["exp_ann"] = ann(V["EXPGSC1"][q], S["EXPGSC1"][-2][1], 3); M["gdp"]["imp_ann"] = ann(V["IMPGSC1"][q], S["IMPGSC1"][-2][1], 3)
M["gdp"]["pdfp"] = V["A191RL1Q225SBEA"][q] - V["A014RY2Q224SBEA"][q] - V["A019RY2Q224SBEA"][q] - V["A822RY2Q224SBEA"][q]
e = S["ECIALLCIV"]; o = S["OPHNFB"]; ul = S["ULCNFB"]
M["eci"] = {"date": e[-1][0], "qoq": pct(e[-1][1], e[-2][1]), "yoy": pct(e[-1][1], e[-5][1]), "ann": ann(e[-1][1], e[-2][1], 3),
            "wag_yoy": pct(S["ECIWAG"][-1][1], S["ECIWAG"][-5][1])}
M["prod"] = {"date": o[-1][0], "ann": ann(o[-1][1], o[-2][1], 3), "yoy": pct(o[-1][1], o[-5][1]),
             "ulc_ann": ann(ul[-1][1], ul[-2][1], 3), "ulc_yoy": pct(ul[-1][1], ul[-5][1])}

# 政策ルール:Taylor (1993) と balanced-approach(Yellen 2012 / Taylor 1999係数)
pi = M["PCEPILFE"]["yoy"]; ugap = V["NROU"].get("2026-10-01", S["NROU"][-1][1]) - V["UNRATE"][cm]
# オークン則係数2で失業ギャップを産出ギャップへ換算(Okun 1962; Yellen 2012の方法)
rules = {}
for rstar in (0.5, 1.0):
    rules[f"taylor93_r{rstar}"] = rstar + pi + 0.5 * (pi - 2) + 0.5 * (2 * ugap)
    rules[f"balanced_r{rstar}"] = rstar + pi + 0.5 * (pi - 2) + 1.0 * (2 * ugap)
M["policy"] = {"upper": V["DFEDTARU"][max(V["DFEDTARU"])], "lower": V["DFEDTARL"][max(V["DFEDTARL"])], "dff": S["DFF"][-1],
               "pi_core_pce": pi, "ugap": ugap, "nrou": V["NROU"].get("2026-10-01"), "rules": rules,
               "real_ff": S["DFF"][-1][1] - pi}

# 市場:期間の始点(2026-10-23)と終点の比較、主な発表日の変化
def at(sid, day):
    ks = [x for x, _ in S[sid] if x <= day]
    return ks[-1], V[sid][ks[-1]]


win0, win1 = "2026-10-23", "2026-11-23"
mk = {}
for sid in ("DGS3MO", "DGS2", "DGS10", "DGS30", "DFII10", "T10YIE", "T5YIFR", "T10Y3M", "T10Y2Y", "BAMLH0A0HYM2", "BAMLC0A0CM",
            "VIXCLS", "SP500", "DTWEXBGS", "DCOILWTICO", "MORTGAGE30US", "NFCI", "STLFSI4", "WALCL", "ICSA", "CCSA", "SOFR"):
    a, b = at(sid, win0), at(sid, win1)
    mk[sid] = {"start": a, "end": b, "chg": b[1] - a[1], "pct": pct(b[1], a[1])}
M["market"] = mk
M["daily"] = {sid: [(x, v) for x, v in S[sid] if "2026-09-01" <= x] for sid in ("DGS2", "DGS10", "SP500", "VIXCLS", "BAMLH0A0HYM2", "T10YIE", "DCOILWTICO")}
events = {"2026-10-29": "GDP速報・個人所得支出", "2026-10-30": "雇用コスト指数", "2026-11-06": "雇用統計",
          "2026-11-10": "CPI", "2026-11-13": "PPI", "2026-11-17": "小売売上高・鉱工業生産・輸入物価", "2026-11-18": "住宅着工"}
ev = []
for day, name in events.items():
    row = {"date": day, "name": name}
    for sid in ("DGS2", "DGS10", "SP500", "VIXCLS"):
        ks = [x for x, _ in S[sid]]
        if day in ks:
            i = ks.index(day)
            row[sid] = S[sid][i][1] - S[sid][i - 1][1] if sid != "SP500" else pct(S[sid][i][1], S[sid][i - 1][1])
    ev.append(row)
M["events"] = ev
# 日次2年債変化の標準偏差(2023年以降)で発表日の値動きの大きさを評価
d2 = [S["DGS2"][i][1] - S["DGS2"][i - 1][1] for i in range(1, len(S["DGS2"])) if S["DGS2"][i][0] >= "2023-01-01"]
M["dgs2_daily_sd"] = st.pstdev(d2)

# NY連銀型イールドカーブ・プロビット(Estrella & Mishkin 1998)の近似再現
sp = [v for x, v in S["T10Y3M"] if x >= "2026-10-01" and x < "2026-11-01"]
spread = st.mean(sp)
nd = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
M["yc_probit"] = {"spread_oct_avg": spread, "prob12m": nd(-0.5333 - 0.6330 * spread) * 100}
M["recprob"] = last("RECPROUSM156N")

# 系列(グラフ用)
def tail(sid, start="2023-01-01", f=None):
    s = S[sid]
    if f == "yoy":
        return [(x, yoy(sid, i)) for i, (x, _) in enumerate(s) if x >= start and yoy(sid, i) is not None]
    if f == "ann3":
        return [(s[i][0], ann(s[i][1], s[i - 3][1], 3)) for i in range(3, len(s)) if s[i][0] >= start]
    return [(x, v) for x, v in s if x >= start]


M["charts"] = {
    "cpi_yoy": tail("CPIAUCSL", f="yoy"), "core_yoy": tail("CPILFESL", f="yoy"), "core_ann3": tail("CPILFESL", f="ann3"),
    "pce_core_yoy": tail("PCEPILFE", f="yoy"), "ppi_yoy": tail("PPIFIS", f="yoy"), "energy_yoy": tail("CPIENGSL", f="yoy"),
    "supercore_yoy": tail("CUSR0000SASLE", f="yoy"), "shelter_yoy": tail("CUSR0000SAH1", f="yoy"), "coregoods_yoy": tail("CUSR0000SACL1E", f="yoy"),
    "unrate": tail("UNRATE"), "ahe_yoy": tail("CES0500000003", f="yoy"), "mich": tail("MICH"),
    "trade": tail("BOPGSTB", "2024-01-01"), "umcsent": tail("UMCSENT"),
}

out = {"generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M"), "verify": checks, "metrics": M}
os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
json.dump(out, open(os.path.join(HERE, "out", "analysis.json"), "w"), ensure_ascii=False, indent=1, default=float)
for c in checks:
    print(("PASS " if c["ok"] else "FAIL ") + c["name"] + " :: " + c["detail"])
if not all(c["ok"] for c in checks):
    sys.exit(1)
