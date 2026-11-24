#!/usr/bin/env python3
"""out/analysis.json から月次レポート(HTML)を作る。数値はすべて analysis.json から差し込む。
使い方: python3 build_report.py  → reports/2026-11.html"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(HERE, "out", "analysis.json")))
if not all(c["ok"] for c in A["verify"]):
    sys.exit("検証に FAIL があるためレポートを作らない")
M = A["metrics"]


def f(x, n=1, sign=False):
    if x is None:
        return "—"
    s = f"{x:+.{n}f}" if sign else f"{x:.{n}f}"
    return s.replace("-", "−")


def k(x):  # 千人 → 万人
    return f"{x/10:+.1f}".replace("-", "−")


cpi, core, pce, cpce = M["CPIAUCSL"], M["CPILFESL"], M["PCEPI"], M["PCEPILFE"]
sc, sh, oer, en, fd, cg = M["CUSR0000SASLE"], M["CUSR0000SAH1"], M["CUSR0000SEHC"], M["CPIENGSL"], M["CPIUFDSL"], M["CUSR0000SACL1E"]
ppi, ppic, ir = M["PPIFIS"], M["PPIFES"], M["IR"]
pay, ahe = M["payrolls"], M["CES0500000003"]
g, mk, pol, z = M["gdp"], M["market"], M["policy"], M["z"]
cm = M["core_measures"]
be = M["base_effect"]
sp = dict(M["daily"]["SP500"])
d_nov5 = (sp["2026-11-05"] / sp["2026-11-04"] - 1) * 100
d_nov20 = (sp["2026-11-20"] / sp["2026-11-19"] - 1) * 100
cpi_day = [e for e in M["events"] if e["date"] == "2026-11-10"][0]

charts = {
    "infl": {"type": "line", "unit": "%", "series": [
        {"name": "CPI総合 前年比", "data": M["charts"]["cpi_yoy"]},
        {"name": "コアCPI 前年比", "data": M["charts"]["core_yoy"]},
        {"name": "コアPCE 前年比", "data": M["charts"]["pce_core_yoy"]}], "ref": 2.0, "refLabel": "物価目標 2%"},
    "oil": {"type": "line", "unit": "ドル", "series": [{"name": "WTI原油(ドル/バレル)", "data": M["daily"]["DCOILWTICO"]}], "start": "2026-01-01"},
    "pay": {"type": "bar", "unit": "千人", "series": [{"name": "非農業部門雇用者数 前月差(千人)", "data": M["payrolls_series"]}]},
    "yld": {"type": "line", "unit": "%", "series": [
        {"name": "2年国債", "data": M["daily"]["DGS2"]}, {"name": "10年国債", "data": M["daily"]["DGS10"]}],
        "start": "2026-10-01", "marks": [[e["date"], e["name"]] for e in M["events"]]},
    "spx": {"type": "line", "unit": "", "series": [{"name": "S&P500", "data": M["daily"]["SP500"]}], "start": "2026-10-01"},
    "vu": {"type": "line", "unit": "", "series": [{"name": "求人件数 ÷ 失業者数(V/U)", "data": M["vu"]["series"]}], "ref": 1.0, "refLabel": "V/U = 1"},
}
contrib = [("個人消費", g["contrib"]["DPCERY2Q224SBEA"]), ("固定投資", g["contrib"]["A006RY2Q224SBEA"] - g["contrib"]["A014RY2Q224SBEA"]),
           ("在庫", g["contrib"]["A014RY2Q224SBEA"]), ("政府", g["contrib"]["A822RY2Q224SBEA"]), ("純輸出", g["contrib"]["A019RY2Q224SBEA"])]
charts["gdp"] = {"type": "hbar", "unit": "%pt", "series": [{"name": "7-9月期 実質GDP成長率への寄与度(%pt)", "data": contrib}]}

releases = [  # (公表日 ET, 統計, 機関, 対象, 主な結果) — 公表日は FRED releases/calendar で確認
    ("10/27", "新築住宅販売・住宅着工(遅延分)", "Census", "9月", f"新築販売 年率{M['HSN1F']['level']:.0f}千戸"),
    ("10/27", "ケース・シラー住宅価格", "S&P", "8月", f"前年比 {f(M['CSUSHPISA']['yoy'])}%"),
    ("10/27", "M2(H.6)", "FRB", "9月", f"前年比 {f(M['M2SL']['yoy'])}%"),
    ("10/29", "GDP速報値", "BEA", "7-9月期", f"前期比年率 {f(g['growth'])}%"),
    ("10/29", "個人所得・支出", "BEA", "9月", f"コアPCE前年比 {f(cpce['yoy'],2)}%"),
    ("10/30", "雇用コスト指数", "BLS", "7-9月期", f"前年比 {f(M['eci']['yoy'])}%"),
    ("11/02", "建設支出", "Census", "9月", f"前月比 {f(M['TTLCONS']['mom'],1,True)}%"),
    ("11/03", "製造業受注(確報)", "Census", "9月", f"コア資本財受注 前月比 {f(M['NEWORDER']['mom'],2,True)}%"),
    ("11/03", "JOLTS求人", "BLS", "9月", f"求人 {M['JTSJOL']['level']/1000:.2f}百万件"),
    ("11/04", "貿易収支", "Census/BEA", "9月", f"{M['BOPGSTB']['level']/1000:.1f}十億ドル"),
    ("11/05", "労働生産性", "BLS", "7-9月期", f"年率 {f(M['prod']['ann'],1,True)}%"),
    ("11/06", "雇用統計", "BLS", "10月", f"雇用者 {pay['chg']:+.0f}千人・失業率 {M['UNRATE']['level']}%"),
    ("11/06", "消費者信用", "FRB", "9月", f"前月比 {f(M['TOTALSL']['mom'],2,True)}%"),
    ("11/10", "消費者物価(CPI)", "BLS", "10月", f"総合 {f(cpi['mom'],2,True)}%・コア {f(core['mom'],2,True)}%(前月比)"),
    ("11/12", "中古住宅販売", "NAR", "10月", f"年率 {M['EXHOSLUSM495S']['level']/1e6:.2f}百万戸"),
    ("11/13", "生産者物価(PPI)", "BLS", "10月", f"最終需要 前年比 {f(ppi['yoy'])}%"),
    ("11/17", "小売売上高", "Census", "10月", f"前月比 {f(M['RSAFS']['mom'],2,True)}%"),
    ("11/17", "輸入物価", "BLS", "10月", f"前月比 {f(ir['mom'],2,True)}%"),
    ("11/17", "鉱工業生産", "FRB", "10月", f"前月比 {f(M['INDPRO']['mom'],2,True)}%"),
    ("11/18", "住宅着工・建築許可", "Census", "10月", f"着工 年率{M['HOUST']['level']:.0f}千戸"),
    ("毎週木", "新規失業保険申請", "DOL", "〜11/14週", f"{mk['ICSA']['end'][1]/1000:.0f}千件"),
]
rel_rows = "\n".join(f"<tr><td class=num>{d}</td><td>{n}</td><td>{a}</td><td>{p}</td><td class=num>{r}</td></tr>" for d, n, a, p, r in releases)
ver_rows = "\n".join(f"<tr><td><span class='pill {'ok' if c['ok'] else 'ng'}'>{'PASS' if c['ok'] else 'FAIL'}</span></td><td>{c['name']}</td><td class=small>{c['detail']}</td><td class=small>{c['method']}</td></tr>" for c in A["verify"])


def row(label, x, cols, n=2):
    return "<tr><th>" + label + "</th>" + "".join(f"<td class=num>{f(x.get(c), n, c in ('mom','mom_prev'))}</td>" for c in cols) + "</tr>"


cols = ("mom", "mom_prev", "ann3", "ann6", "ann13", "yoy_prev")
price_rows = "\n".join([
    row("CPI 総合", cpi, cols), row("コアCPI(食品・エネルギー除く)", core, cols), row("　エネルギー除くサービス", sc, cols),
    row("　住居費", sh, cols), row("　帰属家賃(OER)", oer, cols), row("　コア財", cg, cols), row("エネルギー", en, cols), row("食料", fd, cols),
    row("PPI 最終需要", ppi, cols), row("PPI 食品・エネルギー除く", ppic, cols), row("輸入物価", ir, cols)])

TEMPLATE = open(os.path.join(HERE, "report_template.html")).read()
html = TEMPLATE
for key, val in {
    "CHARTS": json.dumps(charts, ensure_ascii=False, separators=(",", ":")),
    "REL_ROWS": rel_rows, "VER_ROWS": ver_rows, "PRICE_ROWS": price_rows, "GEN": A["generated_utc"],
    "NVER": str(len(A["verify"])),
}.items():
    html = html.replace("{{" + key + "}}", val)

# 本文中の数値プレースホルダー
V = {
 "cpi_mom": f(cpi["mom"], 2), "core_mom": f(core["mom"], 2), "core_ann3": f(core["ann3"]), "core_ann6": f(core["ann6"]),
 "core_ann13": f(core["ann13"], 2), "cpi_ann13": f(cpi["ann13"], 2), "cpi_yoy_sep": f(cpi["yoy_prev"], 2), "core_yoy_sep": f(core["yoy_prev"], 2),
 "core_z": f(z["CPILFESL"]["z"], 2), "core_pct": f(z["CPILFESL"]["pctile"], 0), "sc_mom": f(sc["mom"], 2), "sc_ann3": f(sc["ann3"]),
 "sh_mom": f(sh["mom"], 2), "cg_mom": f(cg["mom"], 2), "en_mom": f(en["mom"], 2), "en_mom_prev": f(en["mom_prev"], 1), "en_yoy_sep": f(en["yoy_prev"], 1),
 "fd_mom": f(fd["mom"], 2),
 "med": f(cm["MEDCPIM158SFRBCLE"][1]), "trim": f(cm["TRMMEANCPIM158SFRBCLE"][1]), "sticky": f(cm["CORESTICKM159SFRBATL"][1], 2),
 "dtrim": f(cm["PCETRIM12M159SFRBDAL"][1], 2),
 "ppi_mom": f(ppi["mom"], 2), "ppi_yoy": f(ppi["yoy"]), "ppic_yoy": f(ppic["yoy"]), "ppi_mom_prev": f(ppi["mom_prev"], 2),
 "ir_mom": f(ir["mom"], 2), "ir_ann3": f(ir["ann3"]), "ir_yoy_sep": f(ir["yoy_prev"]),
 "pce_yoy": f(pce["yoy"], 2), "cpce_yoy": f(cpce["yoy"], 2), "cpce_mom": f(cpce["mom"], 2), "cpce_z": f(z["PCEPILFE"]["z"], 2), "cpce_ann3": f(cpce["ann3"]),
 "be_core": f(be["CPILFESL"]["sep_nov25_2m"], 2), "be_core_avg": f(be["CPILFESL"]["avg_2m_2025"], 2),
 "be_sh": f(be["CUSR0000SAH1"]["sep_nov25_2m"], 2), "be_sh_avg": f(be["CUSR0000SAH1"]["avg_2m_2025"], 2),
 "be_gap": f(be["CPILFESL"]["avg_2m_2025"] - be["CPILFESL"]["sep_nov25_2m"], 2),
 "mich": f(M["MICH"]["level"]), "bei0": f(mk["T10YIE"]["start"][1], 2), "bei1": f(mk["T10YIE"]["end"][1], 2), "fwd": f(mk["T5YIFR"]["end"][1], 2),
 "pay": f"{pay['chg']:+.0f}", "pay_prev": f"{pay['chg_prev']:+.0f}", "pay_prev2": f"{pay['chg_prev2']:+.0f}", "pay3": f"{pay['avg3']:.0f}",
 "pay6": f"{pay['avg6']:.0f}", "pay12": f"{pay['avg12']:.0f}", "priv": f"{pay['priv']:+.0f}", "mfg": f"{pay['mfg']:+.0f}", "fed": f"{pay['fed']:+.0f}",
 "pay_pct": f(z["PAYEMS_chg"]["pctile"], 0), "hh": f"{pay['hh_emp']:+.0f}", "clf": f"{pay['clf']:+.0f}",
 "ur": f(M["UNRATE"]["level"]), "ur_prev": f(M["UNRATE"]["prev"]), "u6": f(M["U6RATE"]["level"]), "u6_prev": f(M["U6RATE"]["prev"]),
 "lfpr": f(M["CIVPART"]["level"]), "epop": f(M["LNS12300060"]["level"]), "lt": f(M["LNS13025703"]["level"]), "lt_prev": f(M["LNS13025703"]["prev"]),
 "ahe_mom": f(ahe["mom"], 2), "ahe_yoy": f(ahe["yoy"], 2), "ahe_yoy_sep": f(ahe["yoy_prev"], 2),
 "real_wage_sep": f(ahe["yoy_prev"] - cpi["yoy_prev"], 2, True),
 "eci_yoy": f(M["eci"]["yoy"], 2), "eci_wag": f(M["eci"]["wag_yoy"], 2), "prod": f(M["prod"]["ann"]), "prod_yoy": f(M["prod"]["yoy"]),
 "ulc": f(M["prod"]["ulc_ann"], 1, True), "ulc_yoy": f(M["prod"]["ulc_yoy"]),
 "jol": f(M["JTSJOL"]["level"] / 1000, 2), "vu": f(M["vu"]["level"], 2), "quit": f(M["JTSQUR"]["level"]), "quit_prev": f(M["JTSQUR"]["prev"]),
 "hire": f(M["JTSHIR"]["level"]), "lay": f(M["JTSLDR"]["level"]),
 "ic": f"{mk['ICSA']['end'][1]/1000:.0f}", "cc": f"{mk['CCSA']['end'][1]/1e6:.3f}", "cc0": f"{mk['CCSA']['start'][1]/1e6:.3f}",
 "sahm": f(M["sahm"]["calc"], 2),
 "gdp": f(g["growth"]), "gdp_yoy": f(g["yoy"], 2), "fs": f(g["final_sales"]), "defl": f(g["deflator"]),
 "c_pce": f(g["contrib"]["DPCERY2Q224SBEA"], 2), "c_inv": f(g["contrib"]["A006RY2Q224SBEA"], 2), "c_stk": f(g["contrib"]["A014RY2Q224SBEA"], 2),
 "c_nx": f(g["contrib"]["A019RY2Q224SBEA"], 2), "c_gov": f(g["contrib"]["A822RY2Q224SBEA"], 2), "c_fix": f(g["contrib"]["A006RY2Q224SBEA"] - g["contrib"]["A014RY2Q224SBEA"], 2),
 "pdfp": f(g["pdfp"], 2),
 "nres": f(g["detail"]["A008RL1Q225SBEA"]), "equip": f(g["detail"]["Y033RL1Q225SBEA"]), "ipp": f(g["detail"]["Y001RL1Q225SBEA"]), "resi": f(g["detail"]["A011RL1Q225SBEA"]),
 "exp": f(g["exp_ann"]), "imp": f(g["imp_ann"]), "gdpnow": f(g["gdpnow_q4"][1], 2),
 "rpce": f(M["PCEC96"]["mom"], 2), "rpce_prev": f(M["PCEC96"]["mom_prev"], 2), "rdpi": f(M["DSPIC96"]["mom"], 2), "rdpi_yoy": f(M["DSPIC96"]["yoy"], 2),
 "sav": f(M["PSAVERT"]["level"]), "sav_y1": f(M["PSAVERT"]["y1"]),
 "rs": f(M["RSAFS"]["mom"], 2), "rs_prev": f(M["RSAFS"]["mom_prev"], 2), "rrs": f(M["RRSFS"]["mom"], 2), "ctl": f(M["control"]["mom"], 2), "ctl_prev": f(M["control"]["mom_prev"], 2),
 "ip": f(M["INDPRO"]["mom"], 2), "ipm": f(M["IPMAN"]["mom"], 2), "tcu": f(M["TCU"]["level"]), "tcu_prev": f(M["TCU"]["prev"]),
 "core_cap": f(M["NEWORDER"]["mom"], 2), "core_cap_yoy": f(M["NEWORDER"]["yoy"]), "dg": f(M["DGORDER"]["mom"], 2),
 "hs": f"{M['HOUST']['level']:.0f}", "hs_prev": f"{M['HOUST']['prev']:.0f}", "pm": f"{M['PERMIT']['level']:.0f}", "pm_prev": f"{M['PERMIT']['prev']:.0f}",
 "ehs": f(M["EXHOSLUSM495S"]["level"] / 1e6, 2), "ehs_prev": f(M["EXHOSLUSM495S"]["prev"] / 1e6, 2), "mort": f(mk["MORTGAGE30US"]["end"][1], 2),
 "tb": f(M["BOPGSTB"]["level"] / 1000, 1), "tb_y1": f(M["BOPGSTB"]["y1"] / 1000, 1), "imp_yoy": f(M["BOPTIMP"]["yoy"]), "exp_yoy": f(M["BOPTEXP"]["yoy"]),
 "cons": f(M["TTLCONS"]["mom"], 2), "umc": f(M["UMCSENT"]["level"]), "umc_y1": f(M["UMCSENT"]["y1"]),
 "up": f(pol["upper"], 2), "lo": f(pol["lower"], 2), "dff": f(pol["dff"][1], 2), "rff": f(pol["real_ff"], 2), "nrou": f(pol["nrou"], 2), "ugap": f(pol["ugap"], 2),
 "t05": f(pol["rules"]["taylor93_r0.5"], 2), "t10": f(pol["rules"]["taylor93_r1.0"], 2), "b05": f(pol["rules"]["balanced_r0.5"], 2), "b10": f(pol["rules"]["balanced_r1.0"], 2),
 "gap_lo": f((pol["rules"]["taylor93_r0.5"] - pol["dff"][1]) * 100, 0), "gap_hi": f((pol["rules"]["balanced_r1.0"] - pol["dff"][1]) * 100, 0),
 "spr_oct": f(M["yc_probit"]["spread_oct_avg"], 2), "prob": f(M["yc_probit"]["prob12m"]), "cp": f(M["recprob"][1], 1),
 "s10y3m": f(mk["T10Y3M"]["end"][1], 2),
 "spx0": f"{mk['SP500']['start'][1]:,.0f}", "spx1": f"{mk['SP500']['end'][1]:,.0f}", "spx": f(mk["SP500"]["pct"], 1, True),
 "vix0": f(mk["VIXCLS"]["start"][1]), "vix1": f(mk["VIXCLS"]["end"][1]), "hy0": f(mk["BAMLH0A0HYM2"]["start"][1], 2), "hy1": f(mk["BAMLH0A0HYM2"]["end"][1], 2),
 "hy": f(mk["BAMLH0A0HYM2"]["chg"] * 100, 0, True), "ig": f(mk["BAMLC0A0CM"]["chg"] * 100, 0, True),
 "y2": f(mk["DGS2"]["chg"] * 100, 0, True), "y10": f(mk["DGS10"]["chg"] * 100, 0, True), "y10_1": f(mk["DGS10"]["end"][1], 2), "y2_1": f(mk["DGS2"]["end"][1], 2),
 "r10": f(mk["DFII10"]["chg"] * 100, 0, True), "bei": f(mk["T10YIE"]["chg"] * 100, 0, True), "r10_1": f(mk["DFII10"]["end"][1], 2),
 "wti0": f(mk["DCOILWTICO"]["start"][1], 2), "wti1": f(mk["DCOILWTICO"]["end"][1], 2), "wti": f(mk["DCOILWTICO"]["pct"], 1, True),
 "usd": f(mk["DTWEXBGS"]["pct"], 1, True), "nfci": f(mk["NFCI"]["end"][1], 3), "stl": f(mk["STLFSI4"]["end"][1], 2),
 "cpi_d2": f(cpi_day["DGS2"] * 100, 0, True), "cpi_d10": f(cpi_day["DGS10"] * 100, 0, True), "sd2": f(M["dgs2_daily_sd"] * 100, 1),
 "cpi_sig": f(cpi_day["DGS2"] / M["dgs2_daily_sd"], 1), "nov5": f(d_nov5, 2, True), "nov20": f(d_nov20, 2, True),
}
for key, val in V.items():
    html = html.replace("{{" + key + "}}", val)
import re
left = re.findall(r"\{\{(\w+)\}\}", html)
if left:
    sys.exit(f"未置換のプレースホルダー: {left}")
os.makedirs(os.path.join(HERE, "reports"), exist_ok=True)
open(os.path.join(HERE, "reports", "2026-11.html"), "w").write(html)
print("ok", len(html))
