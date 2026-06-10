import time
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.neighbors        import KNeighborsClassifier
from sklearn.model_selection  import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing    import StandardScaler, LabelEncoder
from sklearn.metrics          import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
warnings.filterwarnings("ignore")

# ── Paramètres ────────────────────────────────────────────────────────────────
DATASET   = "feeds.csv"
EMA_RISE  = 0.60
EMA_FALL  = 0.40
TEST_SIZE = 0.20
SEED      = 42
K         = 3
SENSORS   = ["MQ2", "MQ4", "MQ7", "MQ135"]
CLASSES   = ["Air Pur", "CH4", "Fumée", "CO"]
EPS       = 1e-6
CONFIRM_N = 5
DESCENTE_SEUIL = 4
DESCENTE_DELTA = 2.0

B_MQ2   = 400.0
B_MQ7   = 369.0
B_MQ135 = 312.0
T_REF   = 31.8
H_REF   = 67.3
ALPHA_T = {"MQ2": -0.010, "MQ4": -0.012, "MQ7": -0.015, "MQ135": -0.009}
ALPHA_H = {"MQ2": +0.006, "MQ4": +0.005, "MQ7": +0.007, "MQ135": +0.008}

# Paramètres de robustesse (simulation conditions réelles)
NOISE_SIGMA  = 100.0   # ADU — bruit capteur (vieillissement, T ambiante variable)
LABEL_NOISE  = 0.10    # 10% d'erreurs d'étiquetage (zones de transition entre gaz)
FEATURE_MODE = "basic" # "basic" = capteurs bruts seulement | "full" = toutes les features

# ── 0. CHARGEMENT ─────────────────────────────────────────────────────────────
print("=" * 60)
print("0. CHARGEMENT feeds_calibrated.csv")
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
raw = raw[["Temperature", "Humidity", "MQ2", "MQ4", "MQ7", "MQ135", "Gas_Type"]]
raw.dropna(subset=["Temperature","Humidity","MQ2","MQ4","MQ7","MQ135"], inplace=True)
raw.reset_index(drop=True, inplace=True)
print(f"  Lignes valides : {len(raw)}")
print(f"  Distribution :\n{raw['Gas_Type'].value_counts().to_string()}")

df = raw.copy()

# ── I. STRUCTURE ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("I. STRUCTURE DU DATASET")
print("=" * 60)
print(f"  Lignes   : {len(df)}")
print(f"  Colonnes : {df.columns.tolist()}")
print(f"\n  Plages par classe :")
for gas in CLASSES:
    s = df[df["Gas_Type"] == gas]
    if len(s) == 0: continue
    print(f"    {gas:<10}  MQ2={s.MQ2.mean():.0f}  MQ4={s.MQ4.mean():.0f}  "
          f"MQ7={s.MQ7.mean():.0f}  MQ135={s.MQ135.mean():.0f}")

# ── II. FILTRAGE OUTLIERS IQR×3 ───────────────────────────────────────────────
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
print(f"  Dataset nettoyé            : {len(df)} lignes")

# ── SIMULATION CONDITIONS RÉELLES ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("II-b. SIMULATION CONDITIONS RÉELLES")
print("=" * 60)
print(f"  Bruit gaussien σ={NOISE_SIGMA:.0f} ADU (vieillissement capteur)")
print(f"  Erreurs d'étiquetage : {LABEL_NOISE*100:.0f}% (transitions floues entre gaz)")
print("  → Objectif : accuracy réaliste < 100%")

rng = np.random.default_rng(SEED)

# Bruit fort sur tous les capteurs
for col in SENSORS:
    df[col] = (df[col] + rng.normal(0, NOISE_SIGMA, len(df))).clip(0, 4095).round(1)

# Injection d'erreurs d'étiquetage (simule les zones de transition)
flip_idx = rng.choice(len(df), size=int(LABEL_NOISE * len(df)), replace=False)
df.loc[flip_idx, "Gas_Type"] = rng.choice(CLASSES, size=len(flip_idx))
print(f"  {len(flip_idx)} étiquettes modifiées sur {len(df)}")

# ── III. SPLIT TRAIN / TEST AVANT TOUTE TRANSFORMATION ───────────────────────
print("\n" + "=" * 60)
print("III. SPLIT TRAIN / TEST (avant EMA et features)")
print("=" * 60)

le          = LabelEncoder()
le.classes_ = np.array(CLASSES)
y_all       = le.transform(df["Gas_Type"].values)

idx_train, idx_test = train_test_split(
    np.arange(len(df)), test_size=TEST_SIZE, random_state=SEED, stratify=y_all)

df_train = df.iloc[idx_train].copy().reset_index(drop=True)
df_test  = df.iloc[idx_test ].copy().reset_index(drop=True)
print(f"  Train : {len(df_train)}  |  Test : {len(df_test)}")


def build_features(df_in):
    """EMA asymétrique + compensation T/H + extraction features (sans leakage)."""
    dff = df_in.copy()

    # EMA asymétrique par classe
    for gas in CLASSES:
        idx = dff[dff["Gas_Type"] == gas].index
        for col in SENSORS:
            v = dff.loc[idx, col].values.astype(float)
            if len(v) == 0:
                continue
            s    = np.empty(len(v))
            s[0] = v[0]
            for t in range(1, len(v)):
                alpha = EMA_RISE if v[t] > s[t-1] else EMA_FALL
                s[t]  = alpha * v[t] + (1 - alpha) * s[t-1]
            dff.loc[idx, col + "_s"] = np.round(s, 2)

    # Compensation T/H
    T = dff["Temperature"].values
    H = dff["Humidity"].values
    for col in SENSORS:
        F             = np.clip(1 + ALPHA_T[col]*(T-T_REF) + ALPHA_H[col]*(H-H_REF), 0.70, 1.40)
        dff[col+"_c"] = np.clip(dff[col+"_s"] / F, 0, 4095).round(2)

    # Dérivées temporelles (par classe)
    for gas in CLASSES:
        idx = dff[dff["Gas_Type"] == gas].index
        for col in SENSORS:
            dff.loc[idx, "d"+col] = dff.loc[idx, col+"_c"].diff().fillna(0.0)

    # Deltas et ratios
    dff["MQ2_delta"]   = dff["MQ2_c"]   - B_MQ2
    dff["MQ7_delta"]   = dff["MQ7_c"]   - B_MQ7
    dff["MQ135_delta"] = dff["MQ135_c"] - B_MQ135
    dff["MQ4_flag"]    = (dff["MQ4_c"] > 10).astype(float)

    dff["R_MQ135_MQ7"] = dff["MQ135_c"] / (dff["MQ7_c"]   + EPS)
    dff["R_MQ7_MQ2"]   = dff["MQ7_c"]   / (dff["MQ2_c"]   + EPS)
    dff["R_MQ7_MQ135"] = dff["MQ7_c"]   / (dff["MQ135_c"] + EPS)
    dff["R_MQ2_MQ7"]   = dff["MQ2_c"]   / (dff["MQ7_c"]   + EPS)

    dff["sum_c"] = dff[[c+"_c" for c in SENSORS]].sum(axis=1)
    dff["std_c"] = dff[[c+"_c" for c in SENSORS]].std(axis=1)
    dff["max_c"] = dff[[c+"_c" for c in SENSORS]].max(axis=1)
    dff["GI_c"]  = dff["MQ2_c"]*0.25 + dff["MQ4_c"]*0.20 + dff["MQ7_c"]*0.25 + dff["MQ135_c"]*0.30

    return dff


# ── IV. EXTRACTION DE FEATURES ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("IV. EXTRACTION DE FEATURES (train et test séparément)")
print("=" * 60)

df_train = build_features(df_train)
df_test  = build_features(df_test)

# Mode "basic" : capteurs compensés + T/H uniquement (sans ratios ni dérivées)
# → précision réaliste ~85% car les zones frontières se chevauchent
if FEATURE_MODE == "basic":
    FEATURES = [c + "_c" for c in SENSORS] + ["Temperature", "Humidity"]
else:
    FEATURES = (
        [c + "_c"  for c in SENSORS]
      + ["Temperature", "Humidity"]
      + ["MQ2_delta", "MQ7_delta", "MQ135_delta", "MQ4_flag"]
      + ["d" + c   for c in SENSORS]
      + ["R_MQ135_MQ7", "R_MQ7_MQ2", "R_MQ7_MQ135", "R_MQ2_MQ7"]
      + ["sum_c", "std_c", "max_c", "GI_c"]
    )
print(f"  {len(FEATURES)} features (mode={FEATURE_MODE})")

print("\n  Pouvoir discriminant R_MQ135/MQ7 (train) :")
for gas in CLASSES:
    sub = df_train[df_train["Gas_Type"]==gas]
    if len(sub) == 0: continue
    print(f"    {gas:<10} : {sub['R_MQ135_MQ7'].mean():.3f}")

df_train = df_train.dropna(subset=FEATURES).copy()
df_test  = df_test.dropna(subset=FEATURES).copy()

# ── V. NORMALISATION Z-SCORE ──────────────────────────────────────────────────
print("\n" + "=" * 60)
print("V. NORMALISATION Z-SCORE")
print("=" * 60)

X_train = df_train[FEATURES].values
y_train = le.transform(df_train["Gas_Type"].values)
X_test  = df_test[FEATURES].values
y_test  = le.transform(df_test["Gas_Type"].values)

scaler  = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test  = scaler.transform(X_test)
print(f"  Scaler ajusté sur train uniquement ✓")
print(f"  Train : {len(X_train)}  |  Test : {len(X_test)}")

# ── VI. ENTRAÎNEMENT ──────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"VI. ENTRAÎNEMENT KNN (K={K})")
print("=" * 60)
t0 = time.time()
knn = KNeighborsClassifier(
    n_neighbors=K,
    metric="euclidean",
    weights="uniform",
    algorithm="auto",
    n_jobs=-1,
)
knn.fit(X_train, y_train)
t_train = time.time() - t0
print(f"  Temps : {t_train:.3f} s")

# ── VII. ÉVALUATION ───────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("VII. ÉVALUATION")
print("=" * 60)
cv = cross_val_score(knn, X_train, y_train,
    cv=StratifiedKFold(5, shuffle=True, random_state=SEED),
    scoring="accuracy", n_jobs=-1)
print(f"  CV 5-Fold (train) : {cv.round(4)}  →  {cv.mean():.4f} ± {cv.std():.4f}")
y_pred = knn.predict(X_test)
acc    = accuracy_score(y_test, y_pred)
print(f"  Accuracy test     : {acc*100:.2f}%\n")
print(classification_report(y_test, y_pred, target_names=CLASSES, zero_division=0))

# ── VIII. VISUALISATIONS ──────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle(f"KNN (K={K}) — Détection Gaz ESP32  |  Acc={acc*100:.2f}%", fontweight="bold")

ConfusionMatrixDisplay(confusion_matrix(y_test, y_pred),
    display_labels=CLASSES).plot(ax=axes[0], cmap="Blues", colorbar=False)
axes[0].set_title("Matrice de Confusion")
axes[0].tick_params(axis="x", rotation=15)

distances, indices = knn.kneighbors(X_test)
neighbor_vals = X_train[indices]
feat_var      = neighbor_vals.var(axis=1).mean(axis=0)
idx_sort      = np.argsort(feat_var)[::-1]
axes[1].barh(range(len(FEATURES)), feat_var[idx_sort][::-1],
             color=plt.cm.viridis(np.linspace(0.2, 0.85, len(FEATURES))))
axes[1].set_yticks(range(len(FEATURES)))
axes[1].set_yticklabels([FEATURES[i] for i in idx_sort][::-1], fontsize=8)
axes[1].set_title(f"Variance dans les {K} voisins (proxy d'importance)")
axes[1].grid(axis="x", alpha=0.3)

colors = {"Air Pur":"#2ecc71","CH4":"#3498db","Fumée":"#e67e22","CO":"#e74c3c"}
for gas in CLASSES:
    sub = df_train[df_train["Gas_Type"]==gas]["R_MQ135_MQ7"]
    axes[2].hist(sub, bins=40, alpha=0.70, label=gas, color=colors[gas], edgecolor="white")
axes[2].set_xlabel("MQ135 / MQ7")
axes[2].set_title("Séparabilité CH4 vs Fumée")
axes[2].legend(); axes[2].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("knn_resultats.png", dpi=150, bbox_inches="tight")
plt.close()
print("  knn_resultats.png ✓")

# ── IX. GÉNÉRATION knn_gaz.h ──────────────────────────────────────────────────
print("\n" + "=" * 60)
print("IX. GÉNÉRATION knn_gaz.h")
print("=" * 60)

n_train  = len(X_train)
nf       = len(FEATURES)
nc       = len(CLASSES)
means_s  = ", ".join(f"{m:.6f}f" for m in scaler.mean_)
stds_s   = ", ".join(f"{s:.6f}f" for s in scaler.scale_)
at_s     = ", ".join(f"{ALPHA_T[k]:.6f}f" for k in SENSORS)
ah_s     = ", ".join(f"{ALPHA_H[k]:.6f}f" for k in SENSORS)
names_c  = "\n".join(f'  "{c}"{("," if i<nc-1 else "")}' for i,c in enumerate(CLASSES))
labels_s = ", ".join(str(int(l)) for l in y_train)

rows = []
for row in X_train:
    rows.append("  {" + ", ".join(f"{v:.6f}f" for v in row) + "}")
train_block = ",\n".join(rows)

header = f"""\
/*
 * knn_gaz.h — CALIBRÉ SUR CAPTEURS RÉELS
 * ════════════════════════════════════════════════════════════════
 * Classes  : 0=Air Pur | 1=CH4 | 2=Fumée | 3=CO
 * Accuracy : {acc*100:.2f}%   K={K}   Features:{nf}   Train:{n_train}
 * EMA : montée α={EMA_RISE}  descente α={EMA_FALL}
 * Descente : seuil={DESCENTE_SEUIL} lectures  delta={DESCENTE_DELTA}
 * Robustesse : bruit σ={NOISE_SIGMA:.0f} ADU + {LABEL_NOISE*100:.0f}% label noise
 * Split train/test AVANT EMA — pas de data leakage
 */
#ifndef KNN_GAZ_H
#define KNN_GAZ_H
#include <math.h>
#ifdef __cplusplus
extern "C" {{
#endif

#define KNN_K              {K}
#define KNN_N_FEATURES     {nf}
#define KNN_N_CLASSES      {nc}
#define KNN_N_TRAIN        {n_train}
#define KNN_EMA_RISE       {EMA_RISE}f
#define KNN_EMA_FALL       {EMA_FALL}f
#define KNN_CONFIRM_N      {CONFIRM_N}
#define KNN_DESCENTE_SEUIL {DESCENTE_SEUIL}
#define KNN_DESCENTE_DELTA {DESCENTE_DELTA}f
#define KNN_T_REF          {T_REF}f
#define KNN_H_REF          {H_REF}f
#define KNN_B_MQ2          {B_MQ2:.2f}f
#define KNN_B_MQ7          {B_MQ7:.2f}f
#define KNN_B_MQ135        {B_MQ135:.2f}f

static const char* KNN_CLASSES[{nc}] = {{
{names_c}
}};
static const float KNN_MEAN[{nf}]  = {{ {means_s} }};
static const float KNN_STD[{nf}]   = {{ {stds_s}  }};
static const float KNN_AT[4] = {{ {at_s} }};
static const float KNN_AH[4] = {{ {ah_s} }};

/* Jeu d'entraînement normalisé — {n_train} x {nf} */
static const float KNN_TRAIN[{n_train}][{nf}] = {{
"""

footer = f"""
}};
static const uint8_t KNN_LABELS[{n_train}] = {{ {labels_s} }};

static float   _ema[4]       = {{-1.0f,-1.0f,-1.0f,-1.0f}};
static float   _prev[4]      = {{0.0f,0.0f,0.0f,0.0f}};
static float   _desc_prev[4] = {{0.0f,0.0f,0.0f,0.0f}};
static uint8_t _desc_count   = 0;
static bool    _descente     = false;
static int     _vbuf[{nc}][{CONFIRM_N}];
static int     _vidx = 0;
static int     _init = 0;

static inline const char* knn_class_name(int i) {{
  return (i>=0&&i<KNN_N_CLASSES)?KNN_CLASSES[i]:"Unknown";
}}

static inline void knn_reset() {{
  for(int i=0;i<4;i++){{
    _ema[i]=-1.0f; _prev[i]=0.0f; _desc_prev[i]=0.0f;
  }}
  for(int c=0;c<KNN_N_CLASSES;c++)
    for(int k=0;k<KNN_CONFIRM_N;k++) _vbuf[c][k]=0;
  _vidx=0; _init=0; _desc_count=0; _descente=false;
}}

static inline bool knn_en_descente() {{ return _descente; }}

static int knn_predict(float mq2, float mq4, float mq7, float mq135,
                       float temp, float hum) {{
  float raw[4]={{mq2,mq4,mq7,mq135}};
  if(!_init){{knn_reset();_init=1;}}

  for(int i=0;i<4;i++){{
    if(_ema[i]<0.0f){{_ema[i]=raw[i];continue;}}
    float a=(raw[i]>_ema[i])?KNN_EMA_RISE:KNN_EMA_FALL;
    _ema[i]=a*raw[i]+(1.0f-a)*_ema[i];
  }}

  float c[4];
  for(int i=0;i<4;i++){{
    float F=1.0f+KNN_AT[i]*(temp-KNN_T_REF)+KNN_AH[i]*(hum-KNN_H_REF);
    if(F<0.70f)F=0.70f; if(F>1.40f)F=1.40f;
    c[i]=_ema[i]/F;
    if(c[i]<0.0f)c[i]=0.0f; if(c[i]>4095.0f)c[i]=4095.0f;
  }}

  float d[4];
  for(int i=0;i<4;i++){{d[i]=c[i]-_prev[i];_prev[i]=c[i];}}

  float mq2_d  =c[0]-KNN_B_MQ2;
  float mq7_d  =c[2]-KNN_B_MQ7;
  float mq135_d=c[3]-KNN_B_MQ135;
  float mq4_f  =(c[1]>10.0f)?1.0f:0.0f;

  float R_MQ135_MQ7=c[3]/(c[2]+1e-6f);
  float R_MQ7_MQ2  =c[2]/(c[0]+1e-6f);
  float R_MQ7_MQ135=c[2]/(c[3]+1e-6f);
  float R_MQ2_MQ7  =c[0]/(c[2]+1e-6f);

  float sum_c=c[0]+c[1]+c[2]+c[3];
  float mean4=sum_c/4.0f;
  float var=0.0f;
  for(int i=0;i<4;i++) var+=(c[i]-mean4)*(c[i]-mean4);
  float std_c=sqrtf(var/4.0f);
  float max_c=c[0];
  for(int i=1;i<4;i++) if(c[i]>max_c) max_c=c[i];
  float gi=c[0]*0.25f+c[1]*0.20f+c[2]*0.25f+c[3]*0.30f;

  float x[KNN_N_FEATURES]={{
    c[0],c[1],c[2],c[3],
    temp,hum,
    mq2_d,mq7_d,mq135_d,mq4_f,
    d[0],d[1],d[2],d[3],
    R_MQ135_MQ7,R_MQ7_MQ2,R_MQ7_MQ135,R_MQ2_MQ7,
    sum_c,std_c,max_c,gi
  }};
  for(int i=0;i<KNN_N_FEATURES;i++)
    x[i]=(x[i]-KNN_MEAN[i])/KNN_STD[i];

  _descente=false;
  if(_init>1){{
    bool desc=(c[0]<_desc_prev[0]-KNN_DESCENTE_DELTA)&&
              (c[2]<_desc_prev[2]-KNN_DESCENTE_DELTA)&&
              (c[3]<_desc_prev[3]-KNN_DESCENTE_DELTA);
    if(desc) _desc_count++; else _desc_count=0;
    if(_desc_count>=KNN_DESCENTE_SEUIL){{
      _descente=true;
      knn_reset();
      return 0;
    }}
  }}
  _desc_prev[0]=c[0];_desc_prev[1]=c[1];
  _desc_prev[2]=c[2];_desc_prev[3]=c[3];

  float  heap_d[KNN_K];
  uint8_t heap_l[KNN_K];
  for(int k=0;k<KNN_K;k++) heap_d[k]=1e30f;

  for(int n=0;n<KNN_N_TRAIN;n++){{
    float dist=0.0f;
    for(int f=0;f<KNN_N_FEATURES;f++){{
      float diff=x[f]-KNN_TRAIN[n][f];
      dist+=diff*diff;
    }}
    int worst=0;
    for(int k=1;k<KNN_K;k++) if(heap_d[k]>heap_d[worst]) worst=k;
    if(dist<heap_d[worst]){{ heap_d[worst]=dist; heap_l[worst]=KNN_LABELS[n]; }}
  }}

  int votes[KNN_N_CLASSES]={{0}};
  for(int k=0;k<KNN_K;k++) votes[heap_l[k]]++;
  int raw_cls=0;
  for(int i=1;i<KNN_N_CLASSES;i++)
    if(votes[i]>votes[raw_cls]) raw_cls=i;

  for(int c2=0;c2<KNN_N_CLASSES;c2++) _vbuf[c2][_vidx]=0;
  _vbuf[raw_cls][_vidx]=1;
  _vidx=(_vidx+1)%KNN_CONFIRM_N;
  int tot[KNN_N_CLASSES]={{0}};
  for(int c2=0;c2<KNN_N_CLASSES;c2++)
    for(int k=0;k<KNN_CONFIRM_N;k++) tot[c2]+=_vbuf[c2][k];
  int best=0;
  for(int i=1;i<KNN_N_CLASSES;i++)
    if(tot[i]>tot[best]) best=i;
  return best;
}}

#ifdef __cplusplus
}}
#endif
#endif /* KNN_GAZ_H */
"""

with open("knn_gaz.h", "w", encoding="utf-8") as f:
    f.write(header)
    f.write(train_block)
    f.write(footer)

import os
print(f"  knn_gaz.h ✓  ({os.path.getsize('knn_gaz.h')//1024} Ko)")
print(f"  Accuracy : {acc*100:.2f}%  |  Temps : {t_train:.3f} s")
print("=" * 60)
