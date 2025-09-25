# LUCKY MIRROR — ポジティブ占いシステム（簡易プロトタイプ）

## セットアップ
```
pip install flask openai pandas matplotlib
export OPENAI_API_KEY=sk-...  # 任意（なくても動作、ルールベースに自動フォールバック）
python app.py
# ブラウザで http://localhost:8000 を開く
```

## データ保存
- アンケートは `outputs/survey.csv` に追記保存（匿名）

## 解析
```
python analysis/analyze.py
# outputs/ にグラフPNGとサマリーCSVが出力されます
```
