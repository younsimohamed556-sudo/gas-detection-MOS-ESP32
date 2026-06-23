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
EMA_RISE  = 0.60        # α montée  : détection rapide
EMA_FALL  = 0.40        # α descente : retour rapide Air Pur
TEST_SIZE = 0.20
SEED      = 42
SENSORS   = ["MQ2", "MQ4", "MQ7", "MQ135"]
CLASSES   = ["Air Pur", "CH4", "Fumée", "CO"]
EPS       = 1e-6
CONFIRM_N = 5
DESCENTE_SEUIL = 4      # lectures consécutives en descente → Air Pur forcé
DESCENTE_DELTA = 2.0    # chute minimum par lecture

# Baselines réelles
B_MQ2   = 400.0
B_MQ7   = 369.0
B_MQ135 = 312.0

# Compensation T/H

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
    print(f"    {gas:<10}  MQ2={s.MQ2.mean():.0f}  MQ4={s.MQ4.mean():.0f}  MQ7={s.MQ7.mean():.0f}  MQ135={s.MQ135.mean():.0f}")

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
print(f"  Dataset final              : {len(df)} lignes")

# ── III. LISSAGE EMA ASYMÉTRIQUE ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("III. LISSAGE EMA ASYMÉTRIQUE")
print("=" * 60)
print(f"  α montée={EMA_RISE}  α descente={EMA_FALL}")
for col in SENSORS:
    v = df[col].values.astype(float)
    s    = np.empty(len(v))
    s[0] = v[0]
    for t in range(1, len(v)):
        alpha = EMA_RISE if v[t] > s[t-1] else EMA_FALL
        s[t]  = alpha * v[t] + (1 - alpha) * s[t-1]
    df[col + "_s"] = np.round(s, 2)
print(f"  Lissage appliqué sur {len(df)} lignes (ordre chronologique)")

# ── COMPENSATION T/H ──────────────────────────────────────────────────────────
for col in SENSORS:
    df[col + "_c"] = np.clip(df[col + "_s"] / F, 0, 4095).round(2)

# ── IV. EXTRACTION DE FEATURES ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("IV. EXTRACTION DE FEATURES")
print("=" * 60)

for col in SENSORS:
    df["d" + col] = df[col + "_c"].diff().fillna(0.0)

df["MQ2_delta"]   = df["MQ2_c"]   - B_MQ2
df["MQ7_delta"]   = df["MQ7_c"]   - B_MQ7
df["MQ135_delta"] = df["MQ135_c"] - B_MQ135
df["MQ4_flag"]    = (df["MQ4_c"] > 10).astype(float)

df["R_MQ135_MQ7"] = df["MQ135_c"] / (df["MQ7_c"]   + EPS)
df["R_MQ7_MQ2"]   = df["MQ7_c"]   / (df["MQ2_c"]   + EPS)
df["R_MQ7_MQ135"] = df["MQ7_c"]   / (df["MQ135_c"] + EPS)
df["R_MQ2_MQ7"]   = df["MQ2_c"]   / (df["MQ7_c"]   + EPS)

df["sum_c"] = df[[c + "_c" for c in SENSORS]].sum(axis=1)
df["std_c"] = df[[c + "_c" for c in SENSORS]].std(axis=1)
df["max_c"] = df[[c + "_c" for c in SENSORS]].max(axis=1)
df["GI_c"]  = df["MQ2_c"]*0.25 + df["MQ4_c"]*0.20 + df["MQ7_c"]*0.25 + df["MQ135_c"]*0.30

FEATURES = (
    [c + "_c"  for c in SENSORS]
  + ["MQ2_delta", "MQ7_delta", "MQ135_delta", "MQ4_flag"]
  + ["d" + c   for c in SENSORS]
  + ["R_MQ135_MQ7", "R_MQ7_MQ2", "R_MQ7_MQ135", "R_MQ2_MQ7"]
  + ["sum_c", "std_c", "max_c", "GI_c"]
)

print(f"  {len(FEATURES)} features")
print("\n  Pouvoir discriminant R_MQ135/MQ7 :")
for gas in CLASSES:
    r = df[df["Gas_Type"]==gas]["R_MQ135_MQ7"].mean()
    print(f"    {gas:<10} : {r:.3f}")

# ── V. NORMALISATION Z-SCORE ──────────────────────────────────────────────────
print("\n" + "=" * 60)
print("V. NORMALISATION Z-SCORE")
print("=" * 60)
df_m     = df.dropna(subset=FEATURES).copy()
X        = df_m[FEATURES].values
y        = df_m["Gas_Type"].values
scaler   = StandardScaler()
X_scaled = scaler.fit_transform(X)

le          = LabelEncoder()
le.classes_ = np.array(CLASSES)
y_enc       = le.transform(y)

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y_enc, test_size=TEST_SIZE, random_state=SEED, stratify=y_enc)
print(f"  Train : {len(X_train)}  |  Test : {len(X_test)}")

# ── VI. ENTRAÎNEMENT ──────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("VI. ENTRAÎNEMENT RANDOM FOREST")
print("=" * 60)
t0 = time.time()
rf = RandomForestClassifier(
    n_estimators=10, max_depth=15,
    min_samples_split=3, min_samples_leaf=1,
    max_features="sqrt", class_weight="balanced",
    random_state=SEED, n_jobs=-1)
rf.fit(X_train, y_train)
t_train = time.time() - t0
print(f"  Temps : {t_train:.3f} s")

# ── VII. ÉVALUATION ───────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("VII. ÉVALUATION")
print("=" * 60)
cv = cross_val_score(rf, X_scaled, y_enc,
    cv=StratifiedKFold(5, shuffle=True, random_state=SEED),
    scoring="accuracy", n_jobs=-1)
print(f"  CV 5-Fold : {cv.round(4)}  →  {cv.mean():.4f} ± {cv.std():.4f}")
y_pred = rf.predict(X_test)
acc    = accuracy_score(y_test, y_pred)
print(f"  Accuracy  : {acc*100:.2f}%\n")
print(classification_report(y_test, y_pred, target_names=CLASSES, zero_division=0))

# ── VIII. VISUALISATIONS ──────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Random Forest — Détection Gaz ESP32", fontweight="bold")

ConfusionMatrixDisplay(confusion_matrix(y_test, y_pred),
    display_labels=CLASSES).plot(ax=axes[0], cmap="Blues", colorbar=False)
axes[0].set_title("Matrice de Confusion")
axes[0].tick_params(axis="x", rotation=15)

idx_sort = np.argsort(rf.feature_importances_)[::-1]
axes[1].barh(range(len(FEATURES)), rf.feature_importances_[idx_sort][::-1],
             color=plt.cm.viridis(np.linspace(0.2, 0.85, len(FEATURES))))
axes[1].set_yticks(range(len(FEATURES)))
axes[1].set_yticklabels([FEATURES[i] for i in idx_sort][::-1], fontsize=8)
axes[1].set_title("Importance des Features")
axes[1].grid(axis="x", alpha=0.3)

colors = {"Air Pur":"#2ecc71","CH4":"#3498db","Fumée":"#e67e22","CO":"#e74c3c"}
for gas in CLASSES:
    sub = df_m[df_m["Gas_Type"]==gas]["R_MQ135_MQ7"]
    axes[2].hist(sub, bins=40, alpha=0.70, label=gas, color=colors[gas], edgecolor="white")
axes[2].set_xlabel("MQ135 / MQ7")
axes[2].set_title("Séparabilité CH4 vs Fumée")
axes[2].legend()
axes[2].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("rf_resultats.png", dpi=150, bbox_inches="tight")
plt.close()
print("  rf_resultats.png ✓")

# ── IX. GÉNÉRATION rf_gaz.h ───────────────────────────────────────────────────
print("\n" + "=" * 60)
print("IX. GÉNÉRATION rf_gaz.h")
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

nf      = len(FEATURES)
nt      = len(rf.estimators_)
nc      = len(CLASSES)
means_s = ", ".join(f"{m:.6f}f" for m in scaler.mean_)
stds_s  = ", ".join(f"{s:.6f}f" for s in scaler.scale_)
names_c = "\n".join(f'  "{c}"{("," if i<nc-1 else "")}' for i,c in enumerate(CLASSES))
trees_c = "\n\n".join(tree_to_c(e, i) for i, e in enumerate(rf.estimators_))
protos  = "\n".join(f"static int tree_{i}(const float* x);" for i in range(nt))
fn_arr  = "  " + ",\n  ".join(f"tree_{i}" for i in range(nt))

header = f"""\
/*
 * rf_gaz.h — CALIBRÉ SUR CAPTEURS RÉELS
 * ════════════════════════════════════════════════════════════════
 * Classes  : 0=Air Pur | 1=CH4 | 2=Fumée | 3=CO
 * Accuracy : {acc*100:.2f}%   Arbres:{nt}   Features:{nf}
 * EMA : montée α={EMA_RISE}  descente α={EMA_FALL}
 * Descente : seuil={DESCENTE_SEUIL} lectures  delta={DESCENTE_DELTA}
 */
#ifndef RF_GAZ_H
#define RF_GAZ_H
#include <math.h>
#ifdef __cplusplus
extern "C" {{
#endif

#define RF_N_TREES        {nt}
#define RF_N_FEATURES     {nf}
#define RF_N_CLASSES      {nc}
#define RF_EMA_RISE       {EMA_RISE}f
#define RF_EMA_FALL       {EMA_FALL}f
#define RF_CONFIRM_N      {CONFIRM_N}
#define RF_DESCENTE_SEUIL {DESCENTE_SEUIL}
#define RF_DESCENTE_DELTA {DESCENTE_DELTA}f
#define RF_B_MQ2          {B_MQ2:.2f}f
#define RF_B_MQ7          {B_MQ7:.2f}f
#define RF_B_MQ135        {B_MQ135:.2f}f

static const char* RF_CLASSES[{nc}] = {{
{names_c}
}};
static const float RF_MEAN[{nf}] = {{ {means_s} }};
static const float RF_STD[{nf}]  = {{ {stds_s}  }};

static float   _ema[4]       = {{-1.0f,-1.0f,-1.0f,-1.0f}};
static float   _prev[4]      = {{0.0f,0.0f,0.0f,0.0f}};
static float   _desc_prev[4] = {{0.0f,0.0f,0.0f,0.0f}};
static uint8_t _desc_count   = 0;
static bool    _descente     = false;
static int     _vbuf[{nc}][{CONFIRM_N}];
static int     _vidx = 0;
static int     _init = 0;

static inline const char* rf_class_name(int i) {{
  return (i>=0&&i<RF_N_CLASSES)?RF_CLASSES[i]:"Unknown";
}}

static inline void rf_reset() {{
  for(int i=0;i<4;i++){{
    _ema[i]=-1.0f; _prev[i]=0.0f; _desc_prev[i]=0.0f;
  }}
  for(int c=0;c<RF_N_CLASSES;c++)
    for(int k=0;k<RF_CONFIRM_N;k++) _vbuf[c][k]=0;
  _vidx=0; _init=0; _desc_count=0; _descente=false;
}}

static inline bool rf_en_descente() {{ return _descente; }}

{protos}

{trees_c}

typedef int (*tfn)(const float*);
static const tfn _trees[RF_N_TREES] = {{
{fn_arr}
}};

static int rf_predict(float mq2, float mq4, float mq7, float mq135,
                      float temp, float hum) {{
  float raw[4]={{mq2,mq4,mq7,mq135}};
  if(!_init){{rf_reset();_init=1;}}

  /* EMA asymétrique */
  for(int i=0;i<4;i++){{
    if(_ema[i]<0.0f){{_ema[i]=raw[i];continue;}}
    float a=(raw[i]>_ema[i])?RF_EMA_RISE:RF_EMA_FALL;
    _ema[i]=a*raw[i]+(1.0f-a)*_ema[i];
  }}

  /* Pas de compensation T/H (modèle sans T/H) */
  float c[4];
  for(int i=0;i<4;i++){{
    c[i]=_ema[i];
    if(c[i]<0.0f)c[i]=0.0f; if(c[i]>4095.0f)c[i]=4095.0f;
  }}

  /* Dérivées temporelles */
  float d[4];
  for(int i=0;i<4;i++){{d[i]=c[i]-_prev[i];_prev[i]=c[i];}}

  /* Deltas baselines */
  float mq2_d  =c[0]-RF_B_MQ2;
  float mq7_d  =c[2]-RF_B_MQ7;
  float mq135_d=c[3]-RF_B_MQ135;
  float mq4_f  =(c[1]>10.0f)?1.0f:0.0f;

  /* Rapports inter-capteurs */
  float R_MQ135_MQ7=c[3]/(c[2]+1e-6f);
  float R_MQ7_MQ2  =c[2]/(c[0]+1e-6f);
  float R_MQ7_MQ135=c[2]/(c[3]+1e-6f);
  float R_MQ2_MQ7  =c[0]/(c[2]+1e-6f);

  /* Stats globales */
  float sum_c=c[0]+c[1]+c[2]+c[3];
  float mean4=sum_c/4.0f;
  float var=0.0f;
  for(int i=0;i<4;i++) var+=(c[i]-mean4)*(c[i]-mean4);
  float std_c=sqrtf(var/4.0f);
  float max_c=c[0];
  for(int i=1;i<4;i++) if(c[i]>max_c) max_c=c[i];
  float gi=c[0]*0.25f+c[1]*0.20f+c[2]*0.25f+c[3]*0.30f;

  /* Vecteur features */
  float x[RF_N_FEATURES]={{
    c[0],c[1],c[2],c[3],
    mq2_d,mq7_d,mq135_d,mq4_f,
    d[0],d[1],d[2],d[3],
    R_MQ135_MQ7,R_MQ7_MQ2,R_MQ7_MQ135,R_MQ2_MQ7,
    sum_c,std_c,max_c,gi
  }};

  /* Normalisation Z-Score */
  for(int i=0;i<RF_N_FEATURES;i++)
    x[i]=(x[i]-RF_MEAN[i])/RF_STD[i];

  /* ── Détection descente → retour Air Pur forcé ── */
  _descente=false;
  if(_init>1){{
    bool desc=(c[0]<_desc_prev[0]-RF_DESCENTE_DELTA)&&
              (c[2]<_desc_prev[2]-RF_DESCENTE_DELTA)&&
              (c[3]<_desc_prev[3]-RF_DESCENTE_DELTA);
    if(desc) _desc_count++; else _desc_count=0;
    if(_desc_count>=RF_DESCENTE_SEUIL){{
      _descente=true;
      rf_reset();
      return 0;
    }}
  }}
  _desc_prev[0]=c[0];_desc_prev[1]=c[1];
  _desc_prev[2]=c[2];_desc_prev[3]=c[3];

  /* Vote Random Forest */
  int votes[RF_N_CLASSES]={{0}};
  for(int t=0;t<RF_N_TREES;t++){{
    int cls=_trees[t](x);
    if(cls>=0&&cls<RF_N_CLASSES) votes[cls]++;
  }}
  int raw_cls=0;
  for(int i=1;i<RF_N_CLASSES;i++)
    if(votes[i]>votes[raw_cls]) raw_cls=i;

  /* Filtre majoritaire */
  for(int c2=0;c2<RF_N_CLASSES;c2++) _vbuf[c2][_vidx]=0;
  _vbuf[raw_cls][_vidx]=1;
  _vidx=(_vidx+1)%RF_CONFIRM_N;
  int tot[RF_N_CLASSES]={{0}};
  for(int c2=0;c2<RF_N_CLASSES;c2++)
    for(int k=0;k<RF_CONFIRM_N;k++) tot[c2]+=_vbuf[c2][k];
  int best=0;
  for(int i=1;i<RF_N_CLASSES;i++)
    if(tot[i]>tot[best]) best=i;
  return best;
}}

#ifdef __cplusplus
}}
#endif
#endif /* RF_GAZ_H */
"""

with open("rf_gaz.h", "w", encoding="utf-8") as f:
    f.write(header)

import os
print(f"  rf_gaz.h ✓  ({os.path.getsize('rf_gaz.h')//1024} Ko)")
print(f"  Accuracy : {acc*100:.2f}%  |  Temps : {t_train:.3f} s")
print("=" * 60)

# ── X. COURBES D'APPRENTISSAGE ET DE VALIDATION CROISÉE ──────────────────────
from sklearn.model_selection import learning_curve, validation_curve

print("\n" + "=" * 60)
print("X. COURBES D'APPRENTISSAGE ET DE VALIDATION CROISÉE")
print("=" * 60)

train_sizes, train_scores, val_scores = learning_curve(
    RandomForestClassifier(n_estimators=10, max_depth=15,
                            min_samples_split=3, min_samples_leaf=1,
                            max_features="sqrt", class_weight="balanced",
                            random_state=SEED, n_jobs=-1),
    X_train, y_train,
    train_sizes=np.linspace(0.10, 1.0, 10),
    cv=StratifiedKFold(5, shuffle=True, random_state=SEED),
    scoring="accuracy",
    n_jobs=-1,
    shuffle=True,
    random_state=SEED,
)

train_mean = train_scores.mean(axis=1)
train_std  = train_scores.std(axis=1)
val_mean   = val_scores.mean(axis=1)
val_std    = val_scores.std(axis=1)

print(f"  Train final  : {train_mean[-1]*100:.2f}% ± {train_std[-1]*100:.2f}%")
print(f"  Val finale   : {val_mean[-1]*100:.2f}% ± {val_std[-1]*100:.2f}%")

n_range = np.array([10, 25, 50, 75, 100, 150, 200, 300, 400, 500])
vc_train, vc_val = validation_curve(
    RandomForestClassifier(max_depth=15, min_samples_split=3, min_samples_leaf=1,
                            max_features="sqrt", class_weight="balanced",
                            random_state=SEED, n_jobs=-1),
    X_train, y_train,
    param_name="n_estimators",
    param_range=n_range,
    cv=StratifiedKFold(5, shuffle=True, random_state=SEED),
    scoring="accuracy",
    n_jobs=-1,
)

vc_train_mean = vc_train.mean(axis=1)
vc_train_std  = vc_train.std(axis=1)
vc_val_mean   = vc_val.mean(axis=1)
vc_val_std    = vc_val.std(axis=1)

best_n_idx = np.argmax(vc_val_mean)
best_n_val = n_range[best_n_idx]
n_used_idx = np.argmin(np.abs(n_range - 10))

print(f"  Meilleur n_estimators (CV) : {best_n_val}  →  {vc_val_mean[best_n_idx]*100:.2f}%")
print(f"  n_estimators utilisé = 10 →  {vc_val_mean[n_used_idx]*100:.2f}%")

# ── FIGURE COMBINÉE : gauche = Apprentissage | droite = Validation croisée ───
fig2, (ax_lc, ax_vc) = plt.subplots(1, 2, figsize=(18, 6))
fig2.suptitle("Random Forest (n_estimators=10) — Courbes d'Apprentissage et de Validation Croisée",
               fontsize=14, fontweight="bold", y=1.01)

pct_fmt = plt.FuncFormatter(lambda v, _: f"{v*100:.1f}%")

# ── Gauche : Courbe d'Apprentissage ──────────────────────────────────────────
ax_lc.plot(train_sizes, train_mean, "o-", color="#2196F3", linewidth=2,
           label="Précision entraînement")
ax_lc.fill_between(train_sizes,
                   train_mean - train_std, train_mean + train_std,
                   alpha=0.15, color="#2196F3")
ax_lc.plot(train_sizes, val_mean, "s-", color="#E53935", linewidth=2,
           label="Précision validation croisée")
ax_lc.fill_between(train_sizes,
                   val_mean - val_std, val_mean + val_std,
                   alpha=0.15, color="#E53935")
ax_lc.axhline(acc, color="#43A047", linestyle="--", linewidth=1.5,
              label=f"Précision test ({acc*100:.2f}%)")
ax_lc.set_xlabel("Taille de l'ensemble d'entraînement (échantillons)", fontsize=11)
ax_lc.set_ylabel("Précision", fontsize=11)
ax_lc.set_title("Courbe d'Apprentissage — Random Forest", fontsize=12, fontweight="bold")
ax_lc.legend(loc="lower right", fontsize=10)
y_min_lc = min(train_mean.min(), val_mean.min()) - 3 * max(train_std.max(), val_std.max())
y_max_lc = max(train_mean.max(), val_mean.max()) + 3 * max(train_std.max(), val_std.max())
ax_lc.set_ylim(max(0.0, round(y_min_lc - 0.01, 2)), min(1.01, round(y_max_lc + 0.01, 2)))
ax_lc.yaxis.set_major_formatter(pct_fmt)
ax_lc.grid(alpha=0.35)

# ── Droite : Courbe de Validation Croisée (n_estimators) ─────────────────────
ax_vc.plot(n_range, vc_train_mean, "o-", color="#2196F3", linewidth=2,
           label="Précision entraînement")
ax_vc.fill_between(n_range,
                   vc_train_mean - vc_train_std, vc_train_mean + vc_train_std,
                   alpha=0.15, color="#2196F3")
ax_vc.plot(n_range, vc_val_mean, "s-", color="#E53935", linewidth=2,
           label="Précision validation croisée")
ax_vc.fill_between(n_range,
                   vc_val_mean - vc_val_std, vc_val_mean + vc_val_std,
                   alpha=0.15, color="#E53935")
ax_vc.axvline(best_n_val, color="#FF9800", linestyle="--", linewidth=1.5,
              label=f"Meilleur n_estimators={best_n_val} ({vc_val_mean[best_n_idx]*100:.2f}%)")
ax_vc.axvline(10, color="#43A047", linestyle=":", linewidth=1.5,
              label=f"n_estimators utilisé = 10 ({vc_val_mean[n_used_idx]*100:.2f}%)")
ax_vc.set_xlabel("Nombre d'arbres (n_estimators)", fontsize=11)
ax_vc.set_ylabel("Précision", fontsize=11)
ax_vc.set_title("Courbe de Validation Croisée — Random Forest", fontsize=12, fontweight="bold")
ax_vc.legend(loc="lower right" if vc_val_mean[0] > 0.5 else "upper right", fontsize=10)
y_min_vc = min(vc_train_mean.min(), vc_val_mean.min()) - 3 * max(vc_train_std.max(), vc_val_std.max())
y_max_vc = max(vc_train_mean.max(), vc_val_mean.max()) + 3 * max(vc_train_std.max(), vc_val_std.max())
ax_vc.set_ylim(max(0.0, round(y_min_vc - 0.01, 2)), min(1.01, round(y_max_vc + 0.01, 2)))
ax_vc.yaxis.set_major_formatter(pct_fmt)
ax_vc.grid(alpha=0.35)

plt.tight_layout()
plt.savefig("rf_courbes_apprentissage_validation.png", dpi=150, bbox_inches="tight")
plt.close()
print("  rf_courbes_apprentissage_validation.png ✓")
print("=" * 60)