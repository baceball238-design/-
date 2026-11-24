"""分析対象のFRED系列。(id, 日本語名, 公表機関, FREDリリースID)"""
SERIES = [
 # 雇用統計 (BLS, rid 50)
 ("PAYEMS","非農業部門雇用者数","BLS",50),("USPRIV","民間雇用者数","BLS",50),("MANEMP","製造業雇用者数","BLS",50),
 ("CES9091000001","連邦政府雇用者数","BLS",50),("UNRATE","失業率","BLS",50),("U6RATE","U-6失業率","BLS",50),
 ("CIVPART","労働参加率","BLS",50),("LNS12300060","25-54歳就業率","BLS",50),("CES0500000003","平均時給(民間)","BLS",50),
 ("AWHAETP","週平均労働時間","BLS",50),("UNEMPLOY","失業者数","BLS",50),("CLF16OV","労働力人口","BLS",50),
 ("CE16OV","家計調査就業者数","BLS",50),("LNS13025703","長期失業者比率(27週以上)", "BLS",50),
 # JOLTS (rid 192)
 ("JTSJOL","求人件数","BLS",192),("JTSQUR","自発的離職率","BLS",192),("JTSHIR","採用率","BLS",192),("JTSLDR","解雇率","BLS",192),
 # 新規失業保険 (DOL, rid 180)
 ("ICSA","新規失業保険申請","DOL",180),("CCSA","継続受給者数","DOL",180),
 # CPI (BLS, rid 10)
 ("CPIAUCSL","CPI総合(SA)","BLS",10),("CPIAUCNS","CPI総合(NSA)","BLS",10),("CPILFESL","コアCPI(SA)","BLS",10),("CPILFENS","コアCPI(NSA)","BLS",10),
 ("CUSR0000SAH1","CPI住居費","BLS",10),("CUSR0000SEHC","CPI帰属家賃(OER)","BLS",10),("CPIENGSL","CPIエネルギー","BLS",10),
 ("CPIUFDSL","CPI食料","BLS",10),("CUSR0000SACL1E","CPIコア財","BLS",10),("CUSR0000SASLE","CPIエネルギー除くサービス","BLS",10),
 ("CORESTICKM159SFRBATL","粘着価格コアCPI(アトランタ連銀)","FRB Atlanta",10),
 ("MEDCPIM158SFRBCLE","中央値CPI(クリーブランド連銀)","FRB Cleveland",10),("TRMMEANCPIM158SFRBCLE","16%刈込平均CPI(クリーブランド連銀)","FRB Cleveland",10),
 # PPI (rid 46)
 ("PPIFIS","PPI最終需要","BLS",46),("PPIFES","PPI最終需要(食品・エネルギー除く)","BLS",46),
 # 輸入物価 (rid 188)
 ("IR","輸入物価指数","BLS",188),
 # 個人所得・支出 (BEA, rid 54)
 ("PCEPI","PCE価格指数","BEA",54),("PCEPILFE","コアPCE価格指数","BEA",54),("PCE","個人消費支出(名目)","BEA",54),
 ("PCEC96","実質個人消費支出","BEA",54),("DSPIC96","実質可処分所得","BEA",54),("PSAVERT","貯蓄率","BEA",54),
 ("PCETRIM12M159SFRBDAL","刈込平均PCE前年比(ダラス連銀)","FRB Dallas",54),
 # GDP (BEA, rid 53)
 ("A191RL1Q225SBEA","実質GDP成長率(前期比年率)","BEA",53),("GDPC1","実質GDP","BEA",53),
 ("DPCERY2Q224SBEA","寄与度:個人消費","BEA",53),("A006RY2Q224SBEA","寄与度:民間投資","BEA",53),
 ("A014RY2Q224SBEA","寄与度:在庫","BEA",53),("A019RY2Q224SBEA","寄与度:純輸出","BEA",53),("A822RY2Q224SBEA","寄与度:政府","BEA",53),
 ("A191RI1Q225SBEA","GDPデフレーター(年率)","BEA",53),("A190RL1Q225SBEA","実質最終販売(年率)","BEA",53),
 # ECI・生産性 (rid 11, 47)
 ("ECIALLCIV","雇用コスト指数(民間+州地方)","BLS",11),("ECIWAG","ECI 民間賃金","BLS",11),
 ("OPHNFB","労働生産性(非農業)","BLS",47),("ULCNFB","単位労働コスト(非農業)","BLS",47),
 # 小売 (Census, rid 9)
 ("RSAFS","小売売上高","Census",9),("RSXFS","小売(自動車除く)","Census",9),("RSMVPD","自動車・部品","Census",9),
 ("RSGASS","ガソリンスタンド","Census",9),("RSBMGESD","建材","Census",9),("RSFSDP","外食","Census",9),("RRSFS","実質小売売上高","Census/FRB",9),
 # 鉱工業 (FRB, rid 13)
 ("INDPRO","鉱工業生産","FRB",13),("IPMAN","製造業生産","FRB",13),("TCU","設備稼働率","FRB",13),
 # 住宅 (rid 27, 97, 291, 199)
 ("HOUST","住宅着工","Census",27),("PERMIT","建築許可","Census",27),("HSN1F","新築住宅販売","Census",97),
 ("EXHOSLUSM495S","中古住宅販売","NAR",291),("CSUSHPISA","ケース・シラー全米住宅価格","S&P",199),
 # 製造業受注・建設・貿易・信用
 ("DGORDER","耐久財受注","Census",95),("ANDENO","非国防資本財受注","Census",95),("NEWORDER","コア資本財受注(非国防・航空機除く)","Census",95),
 ("TTLCONS","建設支出","Census",229),("BOPGSTB","貿易収支(財・サービス)","Census/BEA",51),("TOTALSL","消費者信用残高","FRB",14),
 # 信頼感 (rid 91)
 ("UMCSENT","ミシガン大学消費者信頼感","Univ. of Michigan",91),("MICH","1年先期待インフレ(ミシガン大)","Univ. of Michigan",91),
 # 金融・市場
 ("DFEDTARU","FF誘導目標上限","FRB",101),("DFEDTARL","FF誘導目標下限","FRB",101),("DFF","実効FF金利","FRB NY",None),("SOFR","SOFR","FRB NY",None),
 ("DGS3MO","3か月国債","Treasury",18),("DGS2","2年国債","Treasury",18),("DGS10","10年国債","Treasury",18),("DGS30","30年国債","Treasury",18),
 ("DFII10","10年実質金利","Treasury",18),("T10YIE","10年BEI","FRB St.Louis",None),("T5YIFR","5年先5年BEI","FRB St.Louis",None),
 ("T10Y2Y","10年-2年","FRB St.Louis",None),("T10Y3M","10年-3か月","FRB St.Louis",None),
 ("BAMLH0A0HYM2","HYスプレッド","ICE BofA",None),("BAMLC0A0CM","IGスプレッド","ICE BofA",None),("VIXCLS","VIX","CBOE",None),
 ("SP500","S&P500","S&P",None),("DTWEXBGS","広義ドル指数","FRB",None),("DCOILWTICO","WTI原油","EIA",None),
 ("NFCI","シカゴ連銀金融環境指数","FRB Chicago",None),("STLFSI4","セントルイス連銀金融ストレス","FRB St.Louis",None),
 ("WALCL","FRB総資産","FRB",20),("M2SL","M2","FRB",21),("MORTGAGE30US","30年住宅ローン金利","Freddie Mac",None),
 ("SAHMREALTIME","サーム・ルール(実時間)","FRB St.Louis",None),("RECPROUSM156N","景気後退確率(Chauvet-Piger)","FRB St.Louis",None),
 ("A008RL1Q225SBEA","実質設備投資(非住宅)","BEA",53),("Y033RL1Q225SBEA","実質機械設備投資","BEA",53),
 ("Y001RL1Q225SBEA","実質知的財産投資","BEA",53),("A011RL1Q225SBEA","実質住宅投資","BEA",53),
 ("EXPGSC1","実質輸出","BEA",53),("IMPGSC1","実質輸入","BEA",53),("BOPTIMP","輸入(国際収支ベース)","Census/BEA",51),("BOPTEXP","輸出(国際収支ベース)","Census/BEA",51),
 ("CUSR0000SETB01","CPIガソリン","BLS",10),("GASREGW","レギュラーガソリン小売価格","EIA",None),
 ("NROU","自然失業率(CBO)","CBO",None),("GDPNOW","GDPNow","FRB Atlanta",386),("ECBDFR","ECB預金金利","ECB",None),
]
