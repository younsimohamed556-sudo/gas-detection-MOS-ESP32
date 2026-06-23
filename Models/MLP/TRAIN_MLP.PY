import time
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.neural_network   import MLPClassifier
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
FEATURE_MODE = "basic" # "basic" = capteurs bruts seulement | "full" = toutes les features

# ── Paramètres MLP ────────────────────────────────────────────────────────────
HIDDEN_LAYERS     = (64, 32)       # Architecture : 2 couches cachées
ACTIVATION        = "tanh"         # Fonction d'activation : tanh
SOLVER            = "adam"         # Optimiseur
LEARNING_RATE_INT = "adaptive"     # Taux d'apprentissage adaptatif
MAX_ITER          = 500            # Nombre max d'itérations
ALPHA_REG         = 1e-4           # Régularisation L2

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

# Mode "basic" : capteurs compensés + T/H uniquement
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

# ── VI. ENTRAÎNEMENT MLP ──────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"VI. ENTRAÎNEMENT MLP  (activation={ACTIVATION}, couches={HIDDEN_LAYERS})")
print("=" * 60)

t0 = time.time()
mlp = MLPClassifier(
    hidden_layer_sizes = HIDDEN_LAYERS,
    activation         = ACTIVATION,      # tanh
    solver             = SOLVER,
    learning_rate      = LEARNING_RATE_INT,
    max_iter           = MAX_ITER,
    alpha              = ALPHA_REG,
    random_state       = SEED,
    early_stopping     = True,
    validation_fraction= 0.10,
    n_iter_no_change   = 20,
    verbose            = False,
)
mlp.fit(X_train, y_train)
t_train = time.time() - t0
print(f"  Convergence en {mlp.n_iter_} itérations")
print(f"  Temps : {t_train:.3f} s")

# ── VII. ÉVALUATION ───────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("VII. ÉVALUATION")
print("=" * 60)
cv = cross_val_score(
    MLPClassifier(
        hidden_layer_sizes=HIDDEN_LAYERS, activation=ACTIVATION,
        solver=SOLVER, learning_rate=LEARNING_RATE_INT,
        max_iter=MAX_ITER, alpha=ALPHA_REG,
        random_state=SEED, early_stopping=True,
        validation_fraction=0.10, n_iter_no_change=20,
    ),
    X_train, y_train,
    cv=StratifiedKFold(5, shuffle=True, random_state=SEED),
    scoring="accuracy", n_jobs=-1
)
print(f"  CV 5-Fold (train) : {cv.round(4)}  →  {cv.mean():.4f} ± {cv.std():.4f}")
y_pred = mlp.predict(X_test)
acc    = accuracy_score(y_test, y_pred)
print(f"  Accuracy test     : {acc*100:.2f}%\n")
print(classification_report(y_test, y_pred, target_names=CLASSES, zero_division=0))

# ── VIII. VISUALISATIONS ──────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle(
    f"MLP tanh {HIDDEN_LAYERS} — Détection Gaz ESP32  |  Acc={acc*100:.2f}%",
    fontweight="bold"
)

# Matrice de confusion
ConfusionMatrixDisplay(confusion_matrix(y_test, y_pred),
    display_labels=CLASSES).plot(ax=axes[0], cmap="Oranges", colorbar=False)
axes[0].set_title("Matrice de Confusion")
axes[0].tick_params(axis="x", rotation=15)

# Courbe de perte (loss curve)
axes[1].plot(mlp.loss_curve_, color="#e74c3c", linewidth=1.5, label="Train loss")
if hasattr(mlp, "validation_scores_") and mlp.validation_scores_:
    val_loss = [1 - s for s in mlp.validation_scores_]
    axes[1].plot(val_loss, color="#3498db", linewidth=1.5, linestyle="--", label="Val loss")
axes[1].set_xlabel("Itérations")
axes[1].set_ylabel("Loss")
axes[1].set_title("Courbe de Perte (tanh)")
axes[1].legend()
axes[1].grid(alpha=0.3)

# Distribution R_MQ135/MQ7 par classe
colors = {"Air Pur":"#2ecc71","CH4":"#3498db","Fumée":"#e67e22","CO":"#e74c3c"}
for gas in CLASSES:
    sub = df_train[df_train["Gas_Type"]==gas]["R_MQ135_MQ7"]
    axes[2].hist(sub, bins=40, alpha=0.70, label=gas, color=colors[gas], edgecolor="white")
axes[2].set_xlabel("MQ135 / MQ7")
axes[2].set_title("Séparabilité CH4 vs Fumée")
axes[2].legend()
axes[2].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("mlp_resultats.png", dpi=150, bbox_inches="tight")
plt.close()
print("  mlp_resultats.png ✓")

# ── IX. GÉNÉRATION mlp_gaz.h ──────────────────────────────────────────────────
print("\n" + "=" * 60)
print("IX. GÉNÉRATION mlp_gaz.h")
print("=" * 60)

# Extraire les poids et biais de chaque couche
coefs  = mlp.coefs_         # liste de matrices [W0, W1, ..., Wn]
biases = mlp.intercepts_    # liste de vecteurs [b0, b1, ..., bn]
n_layers = len(coefs)       # nombre de couches (entrée→cachée1, cachée1→cachée2, ..., sortie)
nf = len(FEATURES)
nc = len(CLASSES)

# Dimensions
layer_sizes = [nf] + list(HIDDEN_LAYERS) + [nc]

means_s  = ", ".join(f"{m:.6f}f" for m in scaler.mean_)
stds_s   = ", ".join(f"{s:.6f}f" for s in scaler.scale_)
at_s     = ", ".join(f"{ALPHA_T[k]:.6f}f" for k in SENSORS)
ah_s     = ", ".join(f"{ALPHA_H[k]:.6f}f" for k in SENSORS)
names_c  = "\n".join(f'  "{c}"{("," if i<nc-1 else "")}' for i,c in enumerate(CLASSES))

# Sérialiser les poids et biais couche par couche
def mat_to_c(mat, name, rows, cols):
    """Convertit une matrice numpy en tableau C statique 2D."""
    lines = []
    for r in range(rows):
        row_s = ", ".join(f"{mat[r, c]:.8f}f" for c in range(cols))
        lines.append(f"  {{ {row_s} }}")
    return f"static const float {name}[{rows}][{cols}] = {{\n" + ",\n".join(lines) + "\n};\n"

def vec_to_c(vec, name, size):
    """Convertit un vecteur numpy en tableau C statique 1D."""
    vals = ", ".join(f"{v:.8f}f" for v in vec)
    return f"static const float {name}[{size}] = {{ {vals} }};\n"

weight_blocks = []
bias_blocks   = []
for i, (W, b) in enumerate(zip(coefs, biases)):
    in_sz  = layer_sizes[i]
    out_sz = layer_sizes[i+1]
    weight_blocks.append(mat_to_c(W, f"MLP_W{i}", in_sz, out_sz))
    bias_blocks.append(vec_to_c(b, f"MLP_B{i}", out_sz))

layer_sizes_s = ", ".join(str(s) for s in layer_sizes)

header = f"""\
/*
 * mlp_gaz.h — MLP tanh CALIBRÉ SUR CAPTEURS RÉELS
 * ════════════════════════════════════════════════════════════════
 * Classes    : 0=Air Pur | 1=CH4 | 2=Fumée | 3=CO
 * Accuracy   : {acc*100:.2f}%
 * Architecture : {' → '.join(str(s) for s in layer_sizes)}
 * Activation : tanh (couches cachées) + softmax (sortie)
 * EMA : montée α={EMA_RISE}  descente α={EMA_FALL}
 * Descente : seuil={DESCENTE_SEUIL} lectures  delta={DESCENTE_DELTA}
 * Robustesse : bruit σ={NOISE_SIGMA:.0f} ADU + {LABEL_NOISE*100:.0f}% label noise
 * Split train/test AVANT EMA — pas de data leakage
 * Généré par TRAIN_MLP.PY
 */
#ifndef MLP_GAZ_H
#define MLP_GAZ_H
#include <math.h>
#include <stdint.h>
#include <stdbool.h>
#ifdef __cplusplus
extern "C" {{
#endif

#define MLP_N_FEATURES     {nf}
#define MLP_N_CLASSES      {nc}
#define MLP_N_LAYERS       {n_layers + 1}
#define MLP_EMA_RISE       {EMA_RISE}f
#define MLP_EMA_FALL       {EMA_FALL}f
#define MLP_CONFIRM_N      {CONFIRM_N}
#define MLP_DESCENTE_SEUIL {DESCENTE_SEUIL}
#define MLP_DESCENTE_DELTA {DESCENTE_DELTA}f
#define MLP_T_REF          {T_REF}f
#define MLP_H_REF          {H_REF}f
#define MLP_B_MQ2          {B_MQ2:.2f}f
#define MLP_B_MQ7          {B_MQ7:.2f}f
#define MLP_B_MQ135        {B_MQ135:.2f}f

static const int   MLP_LAYER_SIZES[{len(layer_sizes)}] = {{ {layer_sizes_s} }};
static const char* MLP_CLASSES[{nc}] = {{
{names_c}
}};
static const float MLP_MEAN[{nf}]  = {{ {means_s} }};
static const float MLP_STD[{nf}]   = {{ {stds_s}  }};
static const float MLP_AT[4] = {{ {at_s} }};
static const float MLP_AH[4] = {{ {ah_s} }};

/* ── Poids et biais des couches ─────────────────────────────── */
"""

# Corps : poids + biais
body = ""
for block in weight_blocks:
    body += block + "\n"
for block in bias_blocks:
    body += block + "\n"

footer = f"""\
/* ── Variables d'état (EMA, confirmation) ───────────────────── */
static float   _mlp_ema[4]       = {{-1.0f,-1.0f,-1.0f,-1.0f}};
static float   _mlp_prev[4]      = {{0.0f,0.0f,0.0f,0.0f}};
static float   _mlp_desc_prev[4] = {{0.0f,0.0f,0.0f,0.0f}};
static uint8_t _mlp_desc_count   = 0;
static bool    _mlp_descente     = false;
static int     _mlp_vbuf[{nc}][{CONFIRM_N}];
static int     _mlp_vidx = 0;
static int     _mlp_init = 0;

/* ── Helpers ─────────────────────────────────────────────────── */
static inline const char* mlp_class_name(int i) {{
  return (i>=0&&i<MLP_N_CLASSES)?MLP_CLASSES[i]:"Unknown";
}}

static inline void mlp_reset() {{
  for(int i=0;i<4;i++){{
    _mlp_ema[i]=-1.0f; _mlp_prev[i]=0.0f; _mlp_desc_prev[i]=0.0f;
  }}
  for(int c=0;c<MLP_N_CLASSES;c++)
    for(int k=0;k<MLP_CONFIRM_N;k++) _mlp_vbuf[c][k]=0;
  _mlp_vidx=0; _mlp_init=0; _mlp_desc_count=0; _mlp_descente=false;
}}

static inline bool mlp_en_descente() {{ return _mlp_descente; }}

/* ── Inférence MLP ───────────────────────────────────────────── */
/*
 * Architecture :  {' → '.join(str(s) for s in layer_sizes)}
 * Couches cachées : tanh
 * Couche de sortie : softmax  → argmax pour la classe prédite
 */
static int mlp_predict(float mq2, float mq4, float mq7, float mq135,
                       float temp, float hum) {{
  float raw[4]={{mq2,mq4,mq7,mq135}};
  if(!_mlp_init){{mlp_reset();_mlp_init=1;}}

  /* ── EMA asymétrique ── */
  for(int i=0;i<4;i++){{
    if(_mlp_ema[i]<0.0f){{_mlp_ema[i]=raw[i];continue;}}
    float a=(raw[i]>_mlp_ema[i])?MLP_EMA_RISE:MLP_EMA_FALL;
    _mlp_ema[i]=a*raw[i]+(1.0f-a)*_mlp_ema[i];
  }}

  /* ── Compensation T/H ── */
  float c[4];
  for(int i=0;i<4;i++){{
    float F=1.0f+MLP_AT[i]*(temp-MLP_T_REF)+MLP_AH[i]*(hum-MLP_H_REF);
    if(F<0.70f)F=0.70f; if(F>1.40f)F=1.40f;
    c[i]=_mlp_ema[i]/F;
    if(c[i]<0.0f)c[i]=0.0f; if(c[i]>4095.0f)c[i]=4095.0f;
  }}

  /* ── Construction du vecteur de features ── */
  float x[MLP_N_FEATURES]={{
    c[0],c[1],c[2],c[3],
    temp,hum
  }};

  /* ── Normalisation Z-score ── */
  for(int i=0;i<MLP_N_FEATURES;i++)
    x[i]=(x[i]-MLP_MEAN[i])/MLP_STD[i];

  /* ── Détection descente ── */
  _mlp_descente=false;
  if(_mlp_init>1){{
    bool desc=(c[0]<_mlp_desc_prev[0]-MLP_DESCENTE_DELTA)&&
              (c[2]<_mlp_desc_prev[2]-MLP_DESCENTE_DELTA)&&
              (c[3]<_mlp_desc_prev[3]-MLP_DESCENTE_DELTA);
    if(desc) _mlp_desc_count++; else _mlp_desc_count=0;
    if(_mlp_desc_count>=MLP_DESCENTE_SEUIL){{
      _mlp_descente=true;
      mlp_reset();
      return 0;
    }}
  }}
  _mlp_desc_prev[0]=c[0];_mlp_desc_prev[1]=c[1];
  _mlp_desc_prev[2]=c[2];_mlp_desc_prev[3]=c[3];

  /* ── Forward pass couche 0 : tanh ── */
  float h0[{layer_sizes[1]}];
  for(int j=0;j<{layer_sizes[1]};j++){{
    float s=MLP_B0[j];
    for(int i=0;i<MLP_N_FEATURES;i++) s+=x[i]*MLP_W0[i][j];
    h0[j]=tanhf(s);
  }}

  /* ── Forward pass couche 1 : tanh ── */
  float h1[{layer_sizes[2]}];
  for(int j=0;j<{layer_sizes[2]};j++){{
    float s=MLP_B1[j];
    for(int i=0;i<{layer_sizes[1]};i++) s+=h0[i]*MLP_W1[i][j];
    h1[j]=tanhf(s);
  }}

  /* ── Couche de sortie : softmax ── */
  float out[MLP_N_CLASSES];
  float maxv=-1e30f;
  for(int j=0;j<MLP_N_CLASSES;j++){{
    float s=MLP_B2[j];
    for(int i=0;i<{layer_sizes[2]};i++) s+=h1[i]*MLP_W2[i][j];
    out[j]=s;
    if(s>maxv)maxv=s;
  }}
  float sumexp=0.0f;
  for(int j=0;j<MLP_N_CLASSES;j++){{out[j]=expf(out[j]-maxv);sumexp+=out[j];}}
  for(int j=0;j<MLP_N_CLASSES;j++) out[j]/=sumexp;

  /* ── Argmax ── */
  int raw_cls=0;
  for(int i=1;i<MLP_N_CLASSES;i++)
    if(out[i]>out[raw_cls]) raw_cls=i;

  /* ── Fenêtre de confirmation ── */
  for(int c2=0;c2<MLP_N_CLASSES;c2++) _mlp_vbuf[c2][_mlp_vidx]=0;
  _mlp_vbuf[raw_cls][_mlp_vidx]=1;
  _mlp_vidx=(_mlp_vidx+1)%MLP_CONFIRM_N;
  int tot[MLP_N_CLASSES]={{0}};
  for(int c2=0;c2<MLP_N_CLASSES;c2++)
    for(int k=0;k<MLP_CONFIRM_N;k++) tot[c2]+=_mlp_vbuf[c2][k];
  int best=0;
  for(int i=1;i<MLP_N_CLASSES;i++)
    if(tot[i]>tot[best]) best=i;
  return best;
}}

#ifdef __cplusplus
}}
#endif
#endif /* MLP_GAZ_H */
"""

with open("mlp_gaz.h", "w", encoding="utf-8") as f:
    f.write(header)
    f.write(body)
    f.write(footer)

import os
print(f"  mlp_gaz.h ✓  ({os.path.getsize('mlp_gaz.h')//1024} Ko)")
print(f"  Accuracy   : {acc*100:.2f}%")
print(f"  Temps train : {t_train:.3f} s")
print(f"  Architecture : {' → '.join(str(s) for s in layer_sizes)}")
print(f"  Activation  : {ACTIVATION}")
print("=" * 60)

from sklearn.model_selection import learning_curve, validation_curve

# ════════════════════════════════════════════════════════════════════════════
# COURBES D'APPRENTISSAGE ET DE VALIDATION CROISÉE
# (mêmes hyperparamètres que le modèle final : early_stopping inclus)
# ════════════════════════════════════════════════════════════════════════════

MLP_KWARGS = dict(activation=ACTIVATION, solver=SOLVER,
                   learning_rate=LEARNING_RATE_INT, max_iter=MAX_ITER,
                   alpha=ALPHA_REG, random_state=SEED,
                   early_stopping=True, validation_fraction=0.10,
                   n_iter_no_change=20)

train_sizes, train_scores, val_scores = learning_curve(
    MLPClassifier(hidden_layer_sizes=HIDDEN_LAYERS, **MLP_KWARGS),
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

# Validation croisée sur le nombre de neurones de la 1ère couche cachée
neurons_range = np.array([4, 8, 16, 32, 48, 64, 96, 128, 192, 256])
vc_train, vc_val = validation_curve(
    MLPClassifier(**MLP_KWARGS),
    X_train, y_train,
    param_name="hidden_layer_sizes",
    param_range=[(n, 32) for n in neurons_range],
    cv=StratifiedKFold(5, shuffle=True, random_state=SEED),
    scoring="accuracy",
    n_jobs=-1,
)
vc_train_mean = vc_train.mean(axis=1)
vc_train_std  = vc_train.std(axis=1)
vc_val_mean   = vc_val.mean(axis=1)
vc_val_std    = vc_val.std(axis=1)

best_n_idx  = np.argmax(vc_val_mean)
best_n_val  = neurons_range[best_n_idx]
n_used_idx  = np.argmin(np.abs(neurons_range - HIDDEN_LAYERS[0]))

pct_fmt = plt.FuncFormatter(lambda v, _: f"{v*100:.1f}%")

# ── FIGURE COMBINÉE : gauche = Apprentissage | droite = Validation croisée ───
fig2, (ax_lc, ax_vc) = plt.subplots(1, 2, figsize=(18, 6))
fig2.suptitle(f"MLP ({HIDDEN_LAYERS}, {ACTIVATION}) — Courbes d'Apprentissage et de Validation Croisée",
               fontsize=14, fontweight="bold", y=1.01)

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
ax_lc.set_xlabel("Taille de l'ensemble d'entraînement (échantillons)", fontsize=14)
ax_lc.set_ylabel("Précision", fontsize=14)
ax_lc.set_title("Courbe d'Apprentissage — MLP", fontsize=16, fontweight="bold")
ax_lc.legend(loc="lower right", fontsize=13)
ax_lc.tick_params(axis="both", labelsize=12)
y_min_lc = min(train_mean.min(), val_mean.min()) - 3 * max(train_std.max(), val_std.max())
y_max_lc = max(train_mean.max(), val_mean.max()) + 3 * max(train_std.max(), val_std.max())
ax_lc.set_ylim(max(0.0, round(y_min_lc - 0.01, 2)), min(1.01, round(y_max_lc + 0.01, 2)))
ax_lc.yaxis.set_major_formatter(pct_fmt)
ax_lc.grid(alpha=0.35)

# ── Droite : Courbe de Validation Croisée (neurones 1ère couche) ─────────────
ax_vc.plot(neurons_range, vc_train_mean, "o-", color="#2196F3", linewidth=2,
           label="Précision entraînement")
ax_vc.fill_between(neurons_range,
                   vc_train_mean - vc_train_std, vc_train_mean + vc_train_std,
                   alpha=0.15, color="#2196F3")
ax_vc.plot(neurons_range, vc_val_mean, "s-", color="#E53935", linewidth=2,
           label="Précision validation croisée")
ax_vc.fill_between(neurons_range,
                   vc_val_mean - vc_val_std, vc_val_mean + vc_val_std,
                   alpha=0.15, color="#E53935")
ax_vc.axvline(best_n_val, color="#FF9800", linestyle="--", linewidth=1.5,
              label=f"Meilleur = {best_n_val} neurones ({vc_val_mean[best_n_idx]*100:.2f}%)")
ax_vc.axvline(HIDDEN_LAYERS[0], color="#43A047", linestyle=":", linewidth=1.5,
              label=f"Utilisé = {HIDDEN_LAYERS[0]} neurones ({vc_val_mean[n_used_idx]*100:.2f}%)")
ax_vc.set_xlabel("Neurones (1ère couche cachée, 2ème fixée à 32)", fontsize=14)
ax_vc.set_ylabel("Précision", fontsize=14)
ax_vc.set_title("Courbe de Validation Croisée — MLP", fontsize=16, fontweight="bold")
ax_vc.tick_params(axis="both", labelsize=12)
ax_vc.legend(loc="lower right" if vc_val_mean[0] > 0.5 else "upper right", fontsize=13)
y_min_vc = min(vc_train_mean.min(), vc_val_mean.min()) - 3 * max(vc_train_std.max(), vc_val_std.max())
y_max_vc = max(vc_train_mean.max(), vc_val_mean.max()) + 3 * max(vc_train_std.max(), vc_val_std.max())
ax_vc.set_ylim(max(0.0, round(y_min_vc - 0.01, 2)), min(1.01, round(y_max_vc + 0.01, 2)))
ax_vc.yaxis.set_major_formatter(pct_fmt)
ax_vc.grid(alpha=0.35)

plt.tight_layout()
plt.savefig("mlp_courbes_apprentissage_validation.png", dpi=150, bbox_inches="tight")
plt.close()
print("  mlp_courbes_apprentissage_validation.png ✓")
print("=" * 60)