# 個人経済研究所 — 運用規程

米国を中心とする経済指標を、一次統計と査読済みの学術研究の枠組みだけで分析するための仕組み。
レポートは `reports/`、データ取得と検証は `fetch.py` / `analyze.py`、レポート生成は `build_report.py`。`raw/A/` は本号で使った取得データの控え(監査用)。

## 1. 情報源の序列

| 順位 | 種類 | 例 | 使い方 |
|---|---|---|---|
| 1 | 公表機関の一次統計 | BLS(雇用・物価)、BEA(GDP・PCE)、Census(小売・住宅・貿易)、FRB(鉱工業・金融)、財務省(国債利回り)、DOL(失業保険) | 数値の唯一の根拠 |
| 2 | 一次統計の公式再配布 | FRED(セントルイス連銀)。各機関の公表値を改変せずに収録 | 取得経路。系列IDと正式タイトルを必ず照合 |
| 3 | 中央銀行・公的研究機関の派生指標 | アトランタ連銀(粘着価格CPI・GDPNow)、クリーブランド連銀(中央値・刈込平均CPI)、ダラス連銀(刈込平均PCE)、シカゴ連銀(NFCI)、CBO(自然失業率) | 基調・環境の補助指標 |
| 4 | 査読済み学術論文・中銀の研究論文 | 下記「分析の枠組み」 | 解釈の枠組みのみ。数値の根拠にはしない |
| 対象外 | 報道、民間予想(コンセンサス)、SNS、検証できない二次情報 | — | 使わない。市場予想との比較(サプライズ)は一次ソースで検証できないため扱わない |

## 2. 検証手順(すべて `analyze.py` で自動化。1つでも FAIL ならレポートを作らない)

1. **二重取得**:同じ系列を時間をおいて2回取得し、バイト単位で一致を確認。
2. **ID照合**:FREDの各系列ページの正式タイトルを取得し、日本語ラベルとの対応を確認(例:`ANDENO` は「非国防資本財(航空機を含む)」で、コア資本財は `NEWORDER`)。
3. **別経路データとの照合**:サイトの既存データ(`data/macro_data.json`、別スクリプト・別時刻の取得)と値を突き合わせる。
4. **定義・恒等式の再計算**:失業率=失業者÷労働力、労働力=就業者+失業者、実質GDP年率の再計算、GDP寄与度の合計、名目÷実質PCE=PCE価格指数、名目10年=実質10年+BEI、10年−2年スプレッド、実効FF金利が誘導目標内、SAとNSAの前年比、サーム・ルールの再計算。
5. **欠測の特定**:欠測(例:2025年10月の政府閉鎖で家計調査とCPIが未公表)を機械的に列挙し、その月をまたぐ前年比は計算しない。代替として11か月・13か月・24か月の年率を併記する。
6. **発表日の確認**:FREDの発表カレンダー(`releases/calendar?rid=`)で、各統計の実際の公表日を確認する。

### 現在の制約
- この実行環境から到達できる公的サイトは `fred.stlouisfed.org` のみ(BLS・BEA・Census・ALFRED はネットワーク上到達不可)。そのため **速報値(初回公表値)と改定の検証はできない**。FREDの数値は現行ヴィンテージ(最新改定後)である。
- ミシガン大学の消費者信頼感は FRED への収録が1か月遅れるため、11月分は扱わない。

## 3. 分析の枠組み(査読済み・中央銀行の研究)

| 論点 | 枠組み | 文献 |
|---|---|---|
| 景気後退の判定 | 失業率3か月平均の上昇幅 | Sahm, C. (2019), "Direct Stimulus Payments to Individuals," in *Recession Ready*, Brookings/Hamilton Project |
| 景気後退の予測 | 10年−3か月金利差のプロビット | Estrella, A. & Mishkin, F. (1998), *Review of Economics and Statistics* 80(1); Estrella & Hardouvelis (1991), *Journal of Finance* 46(2) |
| 政策金利の目安 | テイラー・ルール | Taylor, J. (1993), *Carnegie-Rochester Conference Series on Public Policy* 39; Yellen, J. (2012) 講演 "Perspectives on Monetary Policy"(balanced approach) |
| 失業と産出 | オークンの法則 | Okun, A. (1962), "Potential GNP: Its Measurement and Significance" |
| 物価の基調 | 中央値CPI・刈込平均 | Bryan, M. & Cecchetti, S. (1994), in *Monetary Policy* (NBER); Dolmas, J. (2005), Dallas Fed WP 0506 |
| 物価の粘着性 | 粘着価格CPI | Bryan, M. & Meyer, B. (2010), Atlanta Fed *Economic Commentary* |
| 労働需給と物価 | 欠員/失業比率(V/U) | Benigno, P. & Eggertsson, G. (2023), NBER WP 31197; Ball, Leigh & Mishra (2022), *Brookings Papers on Economic Activity* |
| エネルギー価格の波及 | 原油ショックと景気・物価 | Hamilton, J. (2003), *Journal of Econometrics* 113(2); Bernanke, B. & Blanchard, O. (2023), "What Caused the U.S. Pandemic-Era Inflation?" Hutchins Center WP 86 |
| 家計の期待インフレ | 家計期待の形成 | Coibion, O. & Gorodnichenko, Y. (2015), *AEJ: Macroeconomics* 7(1) |
| 信用スプレッド | 社債スプレッドの景気予測力 | Gilchrist, S. & Zakrajšek, E. (2012), *American Economic Review* 102(4) |
| 発表と市場 | 指標発表日の金利反応 | Gürkaynak, R., Sack, B. & Swanson, E. (2005), *American Economic Review* 95(1) |

## 4. 使い方

```sh
cd econ
python3 fetch.py A   # 1回目の取得
python3 fetch.py B   # 時間をおいて2回目
python3 analyze.py   # 検証(すべてPASSが前提)と計算 → out/analysis.json
python3 build_report.py  # レポート → reports/2026-11.html(未置換の数値が残ると停止)
```
系列の追加は `series.py`。追加したら `out/titles.json` に正式タイトルを取り、目視で確認する。
