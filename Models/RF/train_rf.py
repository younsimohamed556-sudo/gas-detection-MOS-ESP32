import time
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.ensemble        import RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing   import StandardScaler, LabelEncoder
from sklearn.metrics         import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
warnings.filterwarnings("ignore")

# ── Paramètres ────────────────────────────────────────────────────────────────
DATASET   = "feeds.csv"
EMA_ALPHA = 0.30
TEST_SIZE = 0.20
SEED      = 42
SENSORS   = ["MQ2", "MQ4", "MQ7", "MQ135"]
CLASSES   = ["Air Pur", "CH4", "Fumée", "CO"]
T_REF     = 28.0
H_REF     = 60.0
ALPHA_T   = {"MQ2": -0.010, "MQ4": -0.012, "MQ7": -0.015, "MQ135": -0.009}
ALPHA_H   = {"MQ2": +0.006, "MQ4": +0.005, "MQ7": +0.007, "MQ135": +0.008}
EPS       = 1e-6

# ── 0. CHARGEMENT ET PRÉPARATION feeds.csv ────────────────────────────────────
print("=" * 60)
print("0. CHARGEMENT ET PRÉPARATION feeds.csv")
print("=" * 60)

raw = pd.read_csv(DATASET)
print(f"  Lignes brutes : {len(raw)}")

raw = raw.rename(columns={
    "TEMPERATURE (°C)"          : "Temperature",
    "HUMIDITE (%)"              : "Humidity",
    "Fumee (raw)"               : "MQ2",
    "Methane_Gaz_naturel (raw)" : "MQ4",
    "Monoxyde_de_carbone (raw)" : "MQ7",
    "Qualite_air (raw)"         : "MQ135",
})
raw = raw[["Temperature", "Humidity", "MQ2", "MQ4", "MQ7", "MQ135"]]
raw.dropna(inplace=True)
raw.reset_index(drop=True, inplace=True)
print(f"  Lignes après suppression NaN : {len(raw)}")

# ── Labellisation par seuils physiques ────────────────────────────────────────
P75_fumee = raw["MQ2"].quantile(0.75)
P60_ch4   = raw["MQ4"].quantile(0.60)
P75_co    = raw["MQ7"].quantile(0.75)
print(f"  Seuils  →  MQ2(Fumée)>{P75_fumee:.0f}  MQ4(CH4)>{P60_ch4:.0f}  MQ7(CO)>{P75_co:.0f}")

def label_row(row):
    scores = {
        "Fumée" : row["MQ2"] / (P75_fumee + 1),
        "CH4"   : row["MQ4"] / (P60_ch4   + 1),
        "CO"    : row["MQ7"] / (P75_co    + 1),
    }
    dominant  = max(scores, key=scores.get)
    max_score = scores[dominant]
    return dominant if max_score >= 0.8 else "Air Pur"

raw["Gas_Type"] = raw.apply(label_row, axis=1)
print(f"  Distribution :\n{raw['Gas_Type'].value_counts().to_string()}")

df = raw.copy()

# ── I. Structure ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("I. STRUCTURE DU DATASET")
print("=" * 60)
print(f"  Lignes : {len(df)}")
print(f"  Colonnes : {df.columns.tolist()}")

# ── II. Filtrage — outliers IQR×3 ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("II. FILTRAGE ET NETTOYAGE")
print("=" * 60)
mask = pd.Series(False, index=df.index)
for col in SENSORS:
    Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
    IQR    = Q3 - Q1
    mask  |= (df[col] < Q1 - 3*IQR) | (df[col] > Q3 + 3*IQR)
n_out = mask.sum()
df    = df[~mask].reset_index(drop=True)
print(f"  Outliers supprimés (IQR×3) : {n_out}")
print(f"  Dataset final              : {len(df)} lignes")

# ── II.3 Lissage EMA par classe ────────────────────────────────────────────────
print(f"\n  Lissage EMA (α={EMA_ALPHA}) — par classe :")
for gas in CLASSES:
    idx = df[df["Gas_Type"] == gas].index
    for col in SENSORS:
        v = df.loc[idx, col].values.astype(float)
        if len(v) == 0:
            continue
        s    = np.empty(len(v))
        s[0] = v[0]
        for t in range(1, len(v)):
            s[t] = EMA_ALPHA * v[t] + (1 - EMA_ALPHA) * s[t - 1]
        df.loc[idx, col + "_s"] = np.round(s, 2)
    print(f"    {gas:<10} : {len(idx)} points lissés")

# ── Compensation environnementale T/H ─────────────────────────────────────────
T = df["Temperature"].values
H = df["Humidity"].values
for col in SENSORS:
    F              = np.clip(1 + ALPHA_T[col]*(T-T_REF) + ALPHA_H[col]*(H-H_REF), 0.70, 1.40)
    df[col + "_c"] = np.clip(df[col + "_s"] / F, 0, 4095).round(2)

# ── III. Extraction de caractéristiques ───────────────────────────────────────
print("\n" + "=" * 60)
print("III. EXTRACTION DE CARACTÉRISTIQUES")
print("=" * 60)

for gas in CLASSES:
    idx = df[df["Gas_Type"] == gas].index
    for col in SENSORS:
        df.loc[idx, "d" + col] = df.loc[idx, col + "_c"].diff().fillna(0.0)

df["R_MQ2_MQ4"]   = df["MQ2_c"] / (df["MQ4_c"]   + EPS)
df["R_MQ7_MQ135"] = df["MQ7_c"] / (df["MQ135_c"] + EPS)
df["sum_c"]  = df[[c + "_c" for c in SENSORS]].sum(axis=1)
df["std_c"]  = df[[c + "_c" for c in SENSORS]].std(axis=1)
df["max_c"]  = df[[c + "_c" for c in SENSORS]].max(axis=1)
df["GI_c"]   = df["MQ2_c"]*0.25 + df["MQ4_c"]*0.20 + df["MQ7_c"]*0.25 + df["MQ135_c"]*0.30

FEATURES = (
    [c + "_c" for c in SENSORS]
    + ["Temperature", "Humidity"]
    + ["GI_c"]
    + ["d" + c for c in SENSORS]
    + ["R_MQ2_MQ4", "R_MQ7_MQ135"]
    + ["sum_c", "std_c", "max_c"]
)

print(f"  {len(FEATURES)} features :")
for i, f in enumerate(FEATURES, 1):
    print(f"    {i:2d}. {f}")

print("\n  Pouvoir discriminant des rapports :")
print(f"  {'Classe':<10}  {'R_MQ2/MQ4':>10}  {'R_MQ7/MQ135':>12}")
print(f"  {'-'*10}  {'-'*10}  {'-'*12}")
for gas in CLASSES:
    r1 = df[df["Gas_Type"]==gas]["R_MQ2_MQ4"].mean()
    r2 = df[df["Gas_Type"]==gas]["R_MQ7_MQ135"].mean()
    print(f"  {gas:<10}  {r1:>10.3f}  {r2:>12.3f}")

# ── IV. Normalisation Z-Score ─────────────────────────────────────────────────
print("\n" + "=" * 60)
print("IV. NORMALISATION Z-SCORE")
print("=" * 60)
df_m     = df.dropna(subset=FEATURES).copy()
X        = df_m[FEATURES].values
y        = df_m["Gas_Type"].values
scaler   = StandardScaler()
X_scaled = scaler.fit_transform(X)
print(f"  μ[:4] = {scaler.mean_[:4].round(1)}")
print(f"  σ[:4] = {scaler.scale_[:4].round(1)}")

le          = LabelEncoder()
le.classes_ = np.array(CLASSES)
y_enc       = le.transform(y)

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y_enc, test_size=TEST_SIZE, random_state=SEED, stratify=y_enc)
print(f"\n  Train : {len(X_train)}  |  Test : {len(X_test)}")

# ── V. Entraînement Random Forest ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("V. ENTRAÎNEMENT RANDOM FOREST")
print("=" * 60)
t0 = time.time()
rf = RandomForestClassifier(
    n_estimators=200, max_depth=15,
    min_samples_split=3, min_samples_leaf=1,
    max_features="sqrt", class_weight="balanced",
    random_state=SEED, n_jobs=-1)
rf.fit(X_train, y_train)
t_train = time.time() - t0
print(f"  Temps d'entraînement : {t_train:.3f} s")

# ── VI. Évaluation ────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("VI. ÉVALUATION")
print("=" * 60)
cv = cross_val_score(rf, X_scaled, y_enc,
    cv=StratifiedKFold(5, shuffle=True, random_state=SEED),
    scoring="accuracy", n_jobs=-1)
print(f"  CV 5-Fold : {cv.round(4)}  →  {cv.mean():.4f} ± {cv.std():.4f}")
y_pred = rf.predict(X_test)
acc    = accuracy_score(y_test, y_pred)
print(f"  Accuracy  : {acc:.4f} ({acc*100:.2f}%)  |  Temps : {t_train:.3f} s\n")
print(classification_report(y_test, y_pred, target_names=CLASSES, zero_division=0))

# ── VII. Visualisations ───────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Random Forest — Détection Gaz ESP32", fontweight="bold")

ConfusionMatrixDisplay(confusion_matrix(y_test, y_pred),
    display_labels=CLASSES).plot(ax=axes[0], cmap="Blues", colorbar=False)
axes[0].set_title("Matrice de Confusion")
axes[0].tick_params(axis="x", rotation=15)

idx = np.argsort(rf.feature_importances_)[::-1][:len(FEATURES)]
axes[1].barh(range(len(FEATURES)), rf.feature_importances_[idx][::-1],
             color=plt.cm.viridis(np.linspace(0.2, 0.85, len(FEATURES))))
axes[1].set_yticks(range(len(FEATURES)))
axes[1].set_yticklabels([FEATURES[i] for i in idx][::-1], fontsize=8)
axes[1].set_title("Importance des Features")
axes[1].grid(axis="x", alpha=0.3)

colors = {"Air Pur":"#2ecc71","CH4":"#3498db","Fumée":"#e67e22","CO":"#e74c3c"}
for gas in CLASSES:
    sub = df_m[df_m["Gas_Type"]==gas]["R_MQ2_MQ4"]
    axes[2].hist(sub, bins=40, alpha=0.70, label=gas, color=colors[gas], edgecolor="white")
axes[2].axvline(0.6, color="gray", linestyle="--", linewidth=1)
axes[2].axvline(0.8, color="gray", linestyle="--", linewidth=1)
axes[2].set_xlabel("Rs_MQ2 / Rs_MQ4")
axes[2].set_title("Séparabilité Rs_MQ2/Rs_MQ4 (CH4 vs Fumée)")
axes[2].legend()
axes[2].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("rf_resultats.png", dpi=150, bbox_inches="tight")
plt.close()
print("  rf_resultats.png ✓")

# ── VIII. Génération rf_gaz.h ─────────────────────────────────────────────────
print("\n" + "=" * 60)
print("VIII. GÉNÉRATION rf_gaz.h")
print("=" * 60)

def tree_to_c(tree, idx):
    t = tree.tree_
    lines = [f"static int tree_{idx}(const float* x) {{"]
    def rec(node, d):
        p = "  " * (d + 1)
        if t.feature[node] == -2:
            lines.append(f"{p}return {int(np.argmax(t.value[node][0]))};")
        else:
            lines.append(f"{p}if (x[{t.feature[node]}] <= {t.threshold[node]:.6f}f) {{")
            rec(t.children_left[node],  d + 1)
            lines.append(f"{p}}} else {{")
            rec(t.children_right[node], d + 1)
            lines.append(f"{p}}}")
    rec(0, 0)
    lines.append("}")
    return "\n".join(lines)

nf = len(FEATURES)
nt = len(rf.estimators_)
nc = len(CLASSES)

means_s = ", ".join(f"{m:.6f}f" for m in scaler.mean_)
stds_s  = ", ".join(f"{s:.6f}f" for s in scaler.scale_)
at_s    = ", ".join(f"{ALPHA_T[k]:.6f}f" for k in SENSORS)
ah_s    = ", ".join(f"{ALPHA_H[k]:.6f}f" for k in SENSORS)
names_c = "\n".join(f'  "{c}"{("," if i<nc-1 else "")}' for i,c in enumerate(CLASSES))
trees_c = "\n\n".join(tree_to_c(e, i) for i, e in enumerate(rf.estimators_))
protos  = "\n".join(f"static int tree_{i}(const float* x);" for i in range(nt))
fn_arr  = "  " + ",\n  ".join(f"tree_{i}" for i in range(nt))

header = f"""\
/*
 * rf_gaz.h
 * Classes  : 0=Air Pur | 1=CH4 | 2=Fumée | 3=CO
 * Accuracy : {acc*100:.2f}%  Arbres:{nt}  Features:{nf}
 * Rapports : Rs_MQ2/Rs_MQ4 (CH4 vs Fumée) | Rs_MQ7/Rs_MQ135 (CO)
 * Dataset  : feeds.csv  ({len(df_m)} lignes)
 */
#ifndef RF_GAZ_H
#define RF_GAZ_H
#include <math.h>
#ifdef __cplusplus
extern "C" {{
#endif

#define RF_N_TREES    {nt}
#define RF_N_FEATURES {nf}
#define RF_N_CLASSES  {nc}
#define RF_EMA_ALPHA  {EMA_ALPHA}f
#define RF_T_REF      {T_REF}f
#define RF_H_REF      {H_REF}f

static const char* RF_CLASSES[{nc}] = {{
{names_c}
}};
static const float RF_MEAN[{nf}] = {{ {means_s} }};
static const float RF_STD[{nf}]  = {{ {stds_s}  }};
static const float RF_AT[4] = {{ {at_s} }};
static const float RF_AH[4] = {{ {ah_s} }};

static float _ema[4]  = {{-1,-1,-1,-1}};
static float _prev[4] = {{0,0,0,0}};

static inline const char* rf_class_name(int i) {{
  return (i>=0&&i<RF_N_CLASSES)?RF_CLASSES[i]:"Unknown";
}}

{protos}

{trees_c}

typedef int (*tfn)(const float*);
static const tfn _trees[RF_N_TREES] = {{
{fn_arr}
}};

static int rf_predict(float mq2, float mq4, float mq7, float mq135,
                      float temp, float hum) {{
  float raw[4]={{mq2,mq4,mq7,mq135}};

  /* EMA : Rs_lissé(t) = α·Rs_brut(t) + (1-α)·Rs_lissé(t-1) */
  for(int i=0;i<4;i++){{
    if(_ema[i]<0) _ema[i]=raw[i];
    else _ema[i]=RF_EMA_ALPHA*raw[i]+(1.0f-RF_EMA_ALPHA)*_ema[i];
  }}

  /* Compensation T/H */
  float c[4];
  for(int i=0;i<4;i++){{
    float F=1.0f+RF_AT[i]*(temp-RF_T_REF)+RF_AH[i]*(hum-RF_H_REF);
    if(F<0.70f)F=0.70f; if(F>1.40f)F=1.40f;
    c[i]=_ema[i]/F;
    if(c[i]<0)c[i]=0; if(c[i]>4095)c[i]=4095;
  }}

  /* Dérivées temporelles */
  float d[4];
  for(int i=0;i<4;i++){{d[i]=c[i]-_prev[i];_prev[i]=c[i];}}

  /* Rapports inter-capteurs */
  float R_MQ2_MQ4   = c[0]/(c[1]+1e-6f);
  float R_MQ7_MQ135 = c[2]/(c[3]+1e-6f);

  /* Stats globales */
  float sum_c = c[0]+c[1]+c[2]+c[3];
  float mean4 = sum_c/4.0f;
  float var=0; for(int i=0;i<4;i++) var+=(c[i]-mean4)*(c[i]-mean4);
  float std_c = sqrtf(var/4.0f);
  float max_c = c[0];
  for(int i=1;i<4;i++) if(c[i]>max_c) max_c=c[i];

  /* Gas_Index pondéré */
  float gi = c[0]*0.25f+c[1]*0.20f+c[2]*0.25f+c[3]*0.30f;

  /* Vecteur features [{nf}] */
  float x[RF_N_FEATURES]={{
    c[0],c[1],c[2],c[3],
    temp,hum,gi,
    d[0],d[1],d[2],d[3],
    R_MQ2_MQ4,R_MQ7_MQ135,
    sum_c,std_c,max_c
  }};

  /* Normalisation Z-Score */
  for(int i=0;i<RF_N_FEATURES;i++)
    x[i]=(x[i]-RF_MEAN[i])/RF_STD[i];

  /* Vote majoritaire */
  int votes[RF_N_CLASSES]={{0}};
  for(int t=0;t<RF_N_TREES;t++){{
    int cls=_trees[t](x);
    if(cls>=0&&cls<RF_N_CLASSES) votes[cls]++;
  }}
  int best=0;
  for(int i=1;i<RF_N_CLASSES;i++)
    if(votes[i]>votes[best]) best=i;
  return best;
}}

#ifdef __cplusplus
}}
#endif
#endif /* RF_GAZ_H */
"""

with open("rf_gaz.h","w",encoding="utf-8") as f:
    f.write(header)

import os
print(f"  rf_gaz.h ✓  ({os.path.getsize('rf_gaz.h')//1024} Ko)")
print(f"  Accuracy : {acc*100:.2f}%  |  Temps : {t_train:.3f} s")
print("=" * 60)

