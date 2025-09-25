import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "outputs" / "survey.csv"
OUT = Path(__file__).resolve().parents[1] / "outputs"
OUT.mkdir(exist_ok=True, parents=True)

df = pd.read_csv(DATA)
if df.empty:
    print("No data yet. Run the app and submit some surveys.")
    raise SystemExit()

summary = df.agg({
    "positive_index":["mean","median"],
    "sukkiri":["mean"],
    "satisfaction":["mean"]
})
print(summary)
by_cond = df.groupby("condition")[["positive_index","sukkiri","satisfaction"]].mean()
print("\\nMeans by condition:\\n", by_cond)

summary.to_csv(OUT/"summary.csv")

plt.figure()
df["sukkiri"].value_counts().sort_index().plot(kind="bar")
plt.title("スッキリ度（度数分布）")
plt.xlabel("スッキリ度（1-5）")
plt.ylabel("人数")
plt.tight_layout()
plt.savefig(OUT/"hist_sukkiri.png")

plt.figure()
by_cond["positive_index"].plot(kind="bar")
plt.title("条件別のポジティブ指数（平均）")
plt.ylabel("指数")
plt.tight_layout()
plt.savefig(OUT/"positive_by_condition.png")

print("Saved charts to", OUT)