import pandas as pd

url = "../data/admisiones_historico.csv"

df = pd.read_csv(url, delimiter=",", encoding="utf-8")

for col in df.select_dtypes(include="object").columns:
    print(f"\n{col}: {df[col].nunique()} valores únicos")
    print(df[col].value_counts(dropna=False).head(10))
df.columns = (df.columns.str.strip()
                        .str.lower()
                        .str.replace(" ", "_"))

print(df.head())