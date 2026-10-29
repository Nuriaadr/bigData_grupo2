import pandas as pd

url = "\data\admisiones_historico.csv"

df = pd.read_csv(url, delimiter=",", encoding="utf-8")

#Todos los datos pasan a tener letras minusculas y
# se reemplazan los espacios por guion
for col in df.select_dtypes(include="object").columns:
    print(f"\n{col}: {df[col].nunique()} valores únicos")
    print(df[col].value_counts(dropna=False).head(10))
df.columns = (df.columns.str.strip()
                        .str.lower()
                        .str.replace(" ", "_"))

#convierte en nulos reales todos los valores que significan “no hay dato”
# y quita los espacios sobrantes de los textos.
NULOS = {"", "null", "none", "nan", "n/d", "n/a", "na", "s/d",
         "error", "pendiente", "normal"}
for col in df.select_dtypes(include="object").columns:
    df[col] = df[col].str.strip()
    df[col] = df[col].where(~df[col].str.lower().isin(NULOS), float("nan"))

#Eliminacion de duplicados exactos
n = len(df)
df = df.drop_duplicates().reset_index(drop=True)
log.append(("Duplicados exactos eliminados", n - len(df)))
assert df["id_episodio"].is_unique, "Hay id_episodio repetidos con contenido distinto"


#convierte las dos columnas de fechas, que llegan como texto en 7 formatos distintos,
# a un único formato de fecha real
FORMATOS = ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S",
            "%d-%m-%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %I:%M %p")

def parse_fecha(s):
    if pd.isna(s):
        return pd.NaT
    for fmt in FORMATOS:
        try:
            return pd.to_datetime(s, format=fmt)
        except ValueError:
            pass
    return pd.NaT

for col in ("timestamp_llegada", "timestamp_alta"):
    antes = df[col].notna().sum()
    df[col] = df[col].map(parse_fecha)
    log.append((f"{col}: no parseables", int(antes - df[col].notna().sum())))

# Duración de la estancia: si el alta es anterior a la llegada, se anula
df["duracion_horas"] = (df["timestamp_alta"] - df["timestamp_llegada"]).dt.total_seconds() / 3600
neg = df["duracion_horas"] < 0
log.append(("Alta anterior a llegada (duración anulada)", int(neg.sum())))
df.loc[neg, "duracion_horas"] = float("nan")

#Deja la frecuencia caardiaca como una columna numérica y
# convierte en nulos los valores imposibles
ta = df["tension_arterial"].str.extract(r"^(\d{2,3})\s*[/_\- ]\s*(\d{2,3})$").astype(float)
df["pa_sistolica"], df["pa_diastolica"] = ta[0], ta[1]
df["pa_revisar"] = df["pa_sistolica"] <= df["pa_diastolica"]
log.append(("TA con sistólica <= diastólica (marcadas)", int(df["pa_revisar"].sum())))
df = df.drop(columns="tension_arterial")

#separa la tensión arterial, que viene como un único texto (150/88),
#en dos columnas numéricas:sistólica (la alta) y diastólica (la baja).
#Además marca los valores sospechosos.
ta = df["tension_arterial"].str.extract(r"^(\d{2,3})\s*[/_\- ]\s*(\d{2,3})$").astype(float)
df["pa_sistolica"], df["pa_diastolica"] = ta[0], ta[1]
df["pa_revisar"] = df["pa_sistolica"] <= df["pa_diastolica"]
log.append(("TA con sistólica <= diastólica (marcadas)", int(df["pa_revisar"].sum())))
df = df.drop(columns="tension_arterial")

#unifica las distintas formas de escribir el destino del paciente al alta,
#de modo que cada destino quede representado por un único valor.
df["destino_alta"] = (df["destino_alta"].str.lower()
                                        .str.replace(r"^alta_", "", regex=True)
                                        .replace({"alta": float("nan")}))
                                
#limpia la columna motivo_consulta: quita el texto “Urgencia por “ que se repite en todas las filas y
#deja solo la especialidad y realiza una prueba para ver si la limpieza ha sido correcta.
df["motivo_consulta"] = (df["motivo_consulta"]
                         .str.replace(r"^Urgencia por\s+", "", regex=True)
                         .str.lower())

#Se ordenan las columnas, guarda el resultado en el archivo de csv
cols = ["id_episodio", "sip_paciente", "timestamp_llegada", "timestamp_alta",
        "duracion_horas", "motivo_consulta", "frecuencia_cardiaca",
        "pa_sistolica", "pa_diastolica", "pa_revisar", "destino_alta"]
df = df[cols]
df.to_csv(url, index=False, date_format="%Y-%m-%d %H:%M:%S")
log.append(("Filas finales", len(df)))

print("\n=== RESUMEN DE LA LIMPIEZA ===")
print(*[f"{k}: {v}" for k, v in log], sep="\n")
print("\nNulos por columna:\n", df.isna().sum().to_string())