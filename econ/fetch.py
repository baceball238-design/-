#!/usr/bin/env python3
"""FREDの公式CSV(fredgraph.csv)から系列を取得し、raw/<run>/<id>.csv に保存する。
使い方: python3 fetch.py <run名>   (検証のため2回以上、時間をおいて取得する)"""
import sys, os, time, urllib.request
from series import SERIES
run = sys.argv[1]; out = os.path.join(os.path.dirname(__file__), "raw", run); os.makedirs(out, exist_ok=True)
for sid, *_ in SERIES:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd=2015-01-01"
    for k in range(4):
        try:
            b = urllib.request.urlopen(url, timeout=40).read(); break
        except Exception as e:
            print("retry", sid, e, file=sys.stderr); time.sleep(2 * (k + 1))
    else:
        print("FAIL", sid); continue
    open(os.path.join(out, sid + ".csv"), "wb").write(b)
    time.sleep(0.3)
print("done", run)
