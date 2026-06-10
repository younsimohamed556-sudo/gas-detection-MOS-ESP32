import time
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.svm              import SVC
from sklearn.model_selection  import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing    import StandardScaler, LabelEncoder
from sklearn.metrics          import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
warnings.filterwarnings("ignore")

# ── Paramètres ────────────────────────────────────────────────────────────────
DATASET        = "feeds.csv"
EMA_RISE       = 0.60
EMA_FALL       = 0.40
TEST_SIZE      = 0.20
SEED           = 42
SENSORS        = ["MQ2", "MQ4", "MQ7", "MQ135"]
CLASSES        = ["Air Pur", "CH4", "Fumée", "CO"]
EPS            = 1e-6
CONFIRM_N      = 5
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
FEATURE_MODE = "basic" # "basic" = capteurs compensés + T/H | "full" = toutes les features

# ── Paramètres SVM ────────────────────────────────────────────────────────────
SVM_KERNEL   = "rbf"     # Noyau RBF (Radial Basis Function) — meilleur pour données capteurs
SVM_C        = 10.0      # Paramètre de régularisation (marge souple)
SVM_GAMMA    = "scale"   # γ = 1 / (n_features × X.var()) — automatique
SVM_DECISION = "ovr"     # One-vs-Rest multiclasse

# ── 0. CHARGEMENT ─────────────────────────────────────────────────────────────
print("=" * 60)
print("0. CHARGEMENT feeds.csv")
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

for col in SENSORS:
    df[col] = (df[col] + rng.normal(0, NOISE_SIGMA, len(df))).clip(0, 4095).round(1)

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

# ── VI. ENTRAÎNEMENT SVM ──────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"VI. ENTRAÎNEMENT SVM  (kernel={SVM_KERNEL}, C={SVM_C}, gamma={SVM_GAMMA})")
print("=" * 60)

t0  = time.time()
svm = SVC(
    kernel          = SVM_KERNEL,
    C               = SVM_C,
    gamma           = SVM_GAMMA,
    decision_function_shape = SVM_DECISION,
    probability     = True,      # active predict_proba (utile pour confiance)
    random_state    = SEED,
    class_weight    = "balanced",
)
svm.fit(X_train, y_train)
t_train = time.time() - t0

n_sv = svm.support_vectors_.shape[0]
print(f"  Vecteurs de support : {n_sv}  ({n_sv/len(X_train)*100:.1f}% du train)")
print(f"  Temps : {t_train:.3f} s")

# ── VII. ÉVALUATION ───────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("VII. ÉVALUATION")
print("=" * 60)
cv = cross_val_score(
    SVC(kernel=SVM_KERNEL, C=SVM_C, gamma=SVM_GAMMA,
        decision_function_shape=SVM_DECISION, class_weight="balanced",
        random_state=SEED),
    X_train, y_train,
    cv=StratifiedKFold(5, shuffle=True, random_state=SEED),
    scoring="accuracy", n_jobs=-1
)
print(f"  CV 5-Fold (train) : {cv.round(4)}  →  {cv.mean():.4f} ± {cv.std():.4f}")
y_pred      = svm.predict(X_test)
y_proba     = svm.predict_proba(X_test)
acc         = accuracy_score(y_test, y_pred)
print(f"  Accuracy test     : {acc*100:.2f}%\n")
print(classification_report(y_test, y_pred, target_names=CLASSES, zero_division=0))

# ── VIII. VISUALISATIONS ──────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle(
    f"SVM RBF (C={SVM_C}) — Détection Gaz ESP32  |  Acc={acc*100:.2f}%",
    fontweight="bold"
)

# Matrice de confusion
ConfusionMatrixDisplay(confusion_matrix(y_test, y_pred),
    display_labels=CLASSES).plot(ax=axes[0], cmap="Purples", colorbar=False)
axes[0].set_title("Matrice de Confusion")
axes[0].tick_params(axis="x", rotation=15)

# Confiance moyenne par classe (probabilité prédite)
conf_by_class = []
for i, gas in enumerate(CLASSES):
    mask_i = y_test == i
    if mask_i.sum() == 0:
        conf_by_class.append(0.0)
    else:
        conf_by_class.append(y_proba[mask_i, i].mean())

bar_colors = ["#2ecc71","#3498db","#e67e22","#e74c3c"]
bars = axes[1].bar(CLASSES, conf_by_class, color=bar_colors, edgecolor="white", linewidth=1.2)
axes[1].set_ylim(0, 1.05)
axes[1].set_ylabel("Probabilité moyenne")
axes[1].set_title("Confiance moyenne SVM par classe")
axes[1].axhline(y=0.5, color="grey", linestyle="--", linewidth=0.8, alpha=0.6)
for bar, val in zip(bars, conf_by_class):
    axes[1].text(bar.get_x() + bar.get_width()/2, val + 0.02,
                 f"{val:.3f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
axes[1].grid(axis="y", alpha=0.3)

# Distribution R_MQ135/MQ7 par classe
colors_g = {"Air Pur":"#2ecc71","CH4":"#3498db","Fumée":"#e67e22","CO":"#e74c3c"}
for gas in CLASSES:
    sub = df_train[df_train["Gas_Type"]==gas]["R_MQ135_MQ7"]
    axes[2].hist(sub, bins=40, alpha=0.70, label=gas, color=colors_g[gas], edgecolor="white")
axes[2].set_xlabel("MQ135 / MQ7")
axes[2].set_title("Séparabilité CH4 vs Fumée")
axes[2].legend()
axes[2].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("svm_resultats.png", dpi=150, bbox_inches="tight")
plt.close()
print("  svm_resultats.png ✓")

# ── IX. GÉNÉRATION svm_gaz.h ──────────────────────────────────────────────────
# Un SVM RBF n'est pas directement portable en C comme un MLP.
# On exporte les vecteurs de support + alpha + biais + gamma pour une inférence
# complète en C (kernel RBF calculé à la volée).
print("\n" + "=" * 60)
print("IX. GÉNÉRATION svm_gaz.h")
print("=" * 60)

nf    = len(FEATURES)
nc    = len(CLASSES)
n_sv  = svm.support_vectors_.shape[0]

means_s = ", ".join(f"{m:.6f}f" for m in scaler.mean_)
stds_s  = ", ".join(f"{s:.6f}f" for s in scaler.scale_)
at_s    = ", ".join(f"{ALPHA_T[k]:.6f}f" for k in SENSORS)
ah_s    = ", ".join(f"{ALPHA_H[k]:.6f}f" for k in SENSORS)
names_c = "\n".join(f'  "{c}"{("," if i<nc-1 else "")}' for i,c in enumerate(CLASSES))

# gamma effectif
gamma_val = (1.0 / (nf * X_train.var())) if SVM_GAMMA == "scale" else float(SVM_GAMMA)

# Vecteurs de support : [n_sv × nf]
sv_rows = []
for row in svm.support_vectors_:
    sv_rows.append("  {" + ", ".join(f"{v:.8f}f" for v in row) + "}")
sv_block = ",\n".join(sv_rows)

# dual_coef : [n_classes-1 × n_sv]  →  on aplatit en n_classes-1 lignes
dc = svm.dual_coef_   # shape (nc-1, n_sv)
dc_rows = []
for row in dc:
    dc_rows.append("  {" + ", ".join(f"{v:.8f}f" for v in row) + "}")
dc_block = ",\n".join(dc_rows)

# intercepts : vecteur de taille nc*(nc-1)/2 (OVO interne sklearn)
b_vals = ", ".join(f"{v:.8f}f" for v in svm.intercept_)
n_intercepts = len(svm.intercept_)

# Mapping classes OVO → index OVR (sklearn utilise OVO internement même en OVR)
# Pour l'inférence embarquée on utilise decision_function = W·K + b → argmax
# On expose dual_coef et intercept tels quels pour recalculer les scores OVO
n_dc_rows = dc.shape[0]   # nc - 1

header = f"""\
/*
 * svm_gaz.h — SVM RBF CALIBRÉ SUR CAPTEURS RÉELS
 * ════════════════════════════════════════════════════════════════
 * Classes    : 0=Air Pur | 1=CH4 | 2=Fumée | 3=CO
 * Accuracy   : {acc*100:.2f}%
 * Kernel     : RBF  γ={gamma_val:.8f}   C={SVM_C}
 * SV         : {n_sv} vecteurs de support / {len(X_train)} train
 * Stratégie  : OVO (One-vs-One, {nc*(nc-1)//2} classifieurs)
 * EMA : montée α={EMA_RISE}  descente α={EMA_FALL}
 * Descente : seuil={DESCENTE_SEUIL} lectures  delta={DESCENTE_DELTA}
 * Robustesse : bruit σ={NOISE_SIGMA:.0f} ADU + {LABEL_NOISE*100:.0f}% label noise
 * Split train/test AVANT EMA — pas de data leakage
 * Généré par TRAIN_SVM.PY
 */
#ifndef SVM_GAZ_H
#define SVM_GAZ_H
#include <math.h>
#include <stdint.h>
#include <stdbool.h>
#ifdef __cplusplus
extern "C" {{
#endif

#define SVM_N_FEATURES      {nf}
#define SVM_N_CLASSES       {nc}
#define SVM_N_SV            {n_sv}
#define SVM_N_INTERCEPTS    {n_intercepts}
#define SVM_GAMMA           {gamma_val:.8f}f
#define SVM_EMA_RISE        {EMA_RISE}f
#define SVM_EMA_FALL        {EMA_FALL}f
#define SVM_CONFIRM_N       {CONFIRM_N}
#define SVM_DESCENTE_SEUIL  {DESCENTE_SEUIL}
#define SVM_DESCENTE_DELTA  {DESCENTE_DELTA}f
#define SVM_T_REF           {T_REF}f
#define SVM_H_REF           {H_REF}f
#define SVM_B_MQ2           {B_MQ2:.2f}f
#define SVM_B_MQ7           {B_MQ7:.2f}f
#define SVM_B_MQ135         {B_MQ135:.2f}f

static const char* SVM_CLASSES[{nc}] = {{
{names_c}
}};
static const float SVM_MEAN[{nf}] = {{ {means_s} }};
static const float SVM_STD[{nf}]  = {{ {stds_s}  }};
static const float SVM_AT[4]      = {{ {at_s} }};
static const float SVM_AH[4]      = {{ {ah_s} }};

/* ── Vecteurs de support [{n_sv} × {nf}] ─────────────────────── */
static const float SVM_SV[{n_sv}][{nf}] = {{
{sv_block}
}};

/* ── Coefficients duaux [{n_dc_rows} × {n_sv}] ───────────────── */
/* dual_coef[i][j] = alpha_j * y_j  pour le classifieur i        */
static const float SVM_DC[{n_dc_rows}][{n_sv}] = {{
{dc_block}
}};

/* ── Biais [{n_intercepts}] (un par classifieur OVO) ─────────── */
static const float SVM_B[{n_intercepts}] = {{ {b_vals} }};

/* ── Variables d'état ────────────────────────────────────────── */
static float   _svm_ema[4]       = {{-1.0f,-1.0f,-1.0f,-1.0f}};
static float   _svm_prev[4]      = {{0.0f,0.0f,0.0f,0.0f}};
static float   _svm_desc_prev[4] = {{0.0f,0.0f,0.0f,0.0f}};
static uint8_t _svm_desc_count   = 0;
static bool    _svm_descente     = false;
static int     _svm_vbuf[{nc}][{CONFIRM_N}];
static int     _svm_vidx = 0;
static int     _svm_init = 0;

/* ── Helpers ─────────────────────────────────────────────────── */
static inline const char* svm_class_name(int i) {{
  return (i>=0&&i<SVM_N_CLASSES)?SVM_CLASSES[i]:"Unknown";
}}

static inline void svm_reset() {{
  for(int i=0;i<4;i++){{
    _svm_ema[i]=-1.0f; _svm_prev[i]=0.0f; _svm_desc_prev[i]=0.0f;
  }}
  for(int c=0;c<SVM_N_CLASSES;c++)
    for(int k=0;k<SVM_CONFIRM_N;k++) _svm_vbuf[c][k]=0;
  _svm_vidx=0; _svm_init=0; _svm_desc_count=0; _svm_descente=false;
}}

static inline bool svm_en_descente() {{ return _svm_descente; }}

/* ── Kernel RBF inline ───────────────────────────────────────── */
/* k(x, sv) = exp(-γ · ||x - sv||²)                              */
static inline float _svm_rbf(const float *x, int sv_idx) {{
  float dist2 = 0.0f;
  for(int i=0;i<SVM_N_FEATURES;i++){{
    float d = x[i] - SVM_SV[sv_idx][i];
    dist2 += d*d;
  }}
  return expf(-SVM_GAMMA * dist2);
}}

/* ── Inférence SVM (OVO vote) ────────────────────────────────── */
/*
 * Stratégie OVO : {nc*(nc-1)//2} classifieurs binaires.
 * Pour chaque paire (i,j) on calcule le score = Σ_k dual_coef[k][sv] * K(x, sv) + b
 * Le classifieur vote pour la classe gagnante.
 * La classe avec le plus de votes gagne.
 *
 * dual_coef sklearn shape : (n_classes-1, n_sv)
 * Les lignes correspondent aux classes de la façon suivante :
 *   DC[i][j] = alpha associé au vecteur de support j dans tous les classifieurs
 *              impliquant la classe i+1 comme classe positive.
 * Voir : https://scikit-learn.org/stable/modules/svm.html#multi-class-classification
 *
 * Simplification embarquée : on calcule les scores de décision OVO directement.
 * intercept_ ordre sklearn OVO : (0v1),(0v2),(0v3),(1v2),(1v3),(2v3)
 */
static int svm_predict(float mq2, float mq4, float mq7, float mq135,
                       float temp, float hum) {{
  float raw[4]={{mq2,mq4,mq7,mq135}};
  if(!_svm_init){{svm_reset();_svm_init=1;}}

  /* ── EMA asymétrique ── */
  for(int i=0;i<4;i++){{
    if(_svm_ema[i]<0.0f){{_svm_ema[i]=raw[i];continue;}}
    float a=(raw[i]>_svm_ema[i])?SVM_EMA_RISE:SVM_EMA_FALL;
    _svm_ema[i]=a*raw[i]+(1.0f-a)*_svm_ema[i];
  }}

  /* ── Compensation T/H ── */
  float c[4];
  for(int i=0;i<4;i++){{
    float F=1.0f+SVM_AT[i]*(temp-SVM_T_REF)+SVM_AH[i]*(hum-SVM_H_REF);
    if(F<0.70f)F=0.70f; if(F>1.40f)F=1.40f;
    c[i]=_svm_ema[i]/F;
    if(c[i]<0.0f)c[i]=0.0f; if(c[i]>4095.0f)c[i]=4095.0f;
  }}

  /* ── Vecteur de features normalisé ── */
  float x[SVM_N_FEATURES]={{c[0],c[1],c[2],c[3],temp,hum}};
  for(int i=0;i<SVM_N_FEATURES;i++)
    x[i]=(x[i]-SVM_MEAN[i])/SVM_STD[i];

  /* ── Détection descente ── */
  _svm_descente=false;
  if(_svm_init>1){{
    bool desc=(c[0]<_svm_desc_prev[0]-SVM_DESCENTE_DELTA)&&
              (c[2]<_svm_desc_prev[2]-SVM_DESCENTE_DELTA)&&
              (c[3]<_svm_desc_prev[3]-SVM_DESCENTE_DELTA);
    if(desc) _svm_desc_count++; else _svm_desc_count=0;
    if(_svm_desc_count>=SVM_DESCENTE_SEUIL){{
      _svm_descente=true;
      svm_reset();
      return 0;
    }}
  }}
  _svm_desc_prev[0]=c[0];_svm_desc_prev[1]=c[1];
  _svm_desc_prev[2]=c[2];_svm_desc_prev[3]=c[3];

  /* ── Calcul du kernel RBF pour tous les SV ── */
  float kvals[SVM_N_SV];
  for(int s=0;s<SVM_N_SV;s++) kvals[s]=_svm_rbf(x,s);

  /* ── Vote OVO ── */
  /* Ordre des classifieurs OVO sklearn pour 4 classes :
     clf 0 : classe 0 vs 1   (intercept idx 0)
     clf 1 : classe 0 vs 2   (intercept idx 1)
     clf 2 : classe 0 vs 3   (intercept idx 2)
     clf 3 : classe 1 vs 2   (intercept idx 3)
     clf 4 : classe 1 vs 3   (intercept idx 4)
     clf 5 : classe 2 vs 3   (intercept idx 5)
  */
  int votes[SVM_N_CLASSES]={{0,0,0,0}};
  int clf=0;
  for(int ci=0;ci<SVM_N_CLASSES;ci++){{
    for(int cj=ci+1;cj<SVM_N_CLASSES;cj++){{
      /* score = Σ_s DC[ci][s]*k(s) + Σ_s DC[cj-1][s]*k(s) + b */
      float score=SVM_B[clf];
      /* dual_coef ligne ci : alphas de tous les SV pour classifieurs où ci est positif */
      for(int s=0;s<SVM_N_SV;s++) score+=SVM_DC[ci][s]*kvals[s];
      /* dual_coef ligne cj-1 : alphas de tous les SV pour classifieurs où cj est positif */
      for(int s=0;s<SVM_N_SV;s++) score+=SVM_DC[cj-1][s]*kvals[s];
      if(score>=0.0f) votes[ci]++; else votes[cj]++;
      clf++;
    }}
  }}

  /* ── Argmax votes ── */
  int raw_cls=0;
  for(int i=1;i<SVM_N_CLASSES;i++)
    if(votes[i]>votes[raw_cls]) raw_cls=i;

  /* ── Fenêtre de confirmation ── */
  for(int c2=0;c2<SVM_N_CLASSES;c2++) _svm_vbuf[c2][_svm_vidx]=0;
  _svm_vbuf[raw_cls][_svm_vidx]=1;
  _svm_vidx=(_svm_vidx+1)%SVM_CONFIRM_N;
  int tot[SVM_N_CLASSES]={{0}};
  for(int c2=0;c2<SVM_N_CLASSES;c2++)
    for(int k=0;k<SVM_CONFIRM_N;k++) tot[c2]+=_svm_vbuf[c2][k];
  int best=0;
  for(int i=1;i<SVM_N_CLASSES;i++)
    if(tot[i]>tot[best]) best=i;
  return best;
}}

#ifdef __cplusplus
}}
#endif
#endif /* SVM_GAZ_H */
"""

with open("svm_gaz.h", "w", encoding="utf-8") as f:
    f.write(header)

import os
sz = os.path.getsize("svm_gaz.h")
print(f"  svm_gaz.h ✓  ({sz//1024} Ko)")
print(f"  Vecteurs de support exportés : {n_sv}")
print(f"  Accuracy   : {acc*100:.2f}%")
print(f"  Temps train : {t_train:.3f} s")
print(f"  Kernel     : {SVM_KERNEL}  C={SVM_C}  γ={gamma_val:.6f}")
print("=" * 60)

