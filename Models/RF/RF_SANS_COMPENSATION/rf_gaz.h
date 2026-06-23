/*
 * rf_gaz.h — CALIBRÉ SUR CAPTEURS RÉELS
 * ════════════════════════════════════════════════════════════════
 * Classes  : 0=Air Pur | 1=CH4 | 2=Fumée | 3=CO
 * Accuracy : 99.88%   Arbres:10   Features:20
 * EMA : montée α=0.6  descente α=0.4
 * Descente : seuil=4 lectures  delta=2.0
 */
#ifndef RF_GAZ_H
#define RF_GAZ_H
#include <math.h>
#ifdef __cplusplus
extern "C" {
#endif

#define RF_N_TREES        10
#define RF_N_FEATURES     20
#define RF_N_CLASSES      4
#define RF_EMA_RISE       0.6f
#define RF_EMA_FALL       0.4f
#define RF_CONFIRM_N      5
#define RF_DESCENTE_SEUIL 4
#define RF_DESCENTE_DELTA 2.0f
#define RF_B_MQ2          400.00f
#define RF_B_MQ7          369.00f
#define RF_B_MQ135        312.00f

static const char* RF_CLASSES[4] = {
  "Air Pur",
  "CH4",
  "Fumée",
  "CO"
};
static const float RF_MEAN[20] = { 876.048649f, 0.000000f, 981.770948f, 734.491771f, 476.048649f, 612.770948f, 422.491771f, 0.000000f, 0.030862f, 0.000000f, 0.288593f, 0.020489f, 0.834928f, 1.381525f, 1.763691f, 1.066286f, 2592.311368f, 527.029477f, 1230.663002f, 684.802430f };
static const float RF_STD[20]  = { 435.558027f, 1.000000f, 491.421871f, 499.452930f, 435.558027f, 491.421871f, 499.452930f, 1.000000f, 63.222964f, 1.000000f, 76.731309f, 51.566860f, 0.388787f, 0.992015f, 1.297771f, 0.526570f, 1083.532658f, 219.592462f, 521.575038f, 293.281457f  };

static float   _ema[4]       = {-1.0f,-1.0f,-1.0f,-1.0f};
static float   _prev[4]      = {0.0f,0.0f,0.0f,0.0f};
static float   _desc_prev[4] = {0.0f,0.0f,0.0f,0.0f};
static uint8_t _desc_count   = 0;
static bool    _descente     = false;
static int     _vbuf[4][5];
static int     _vidx = 0;
static int     _init = 0;

static inline const char* rf_class_name(int i) {
  return (i>=0&&i<RF_N_CLASSES)?RF_CLASSES[i]:"Unknown";
}

static inline void rf_reset() {
  for(int i=0;i<4;i++){
    _ema[i]=-1.0f; _prev[i]=0.0f; _desc_prev[i]=0.0f;
  }
  for(int c=0;c<RF_N_CLASSES;c++)
    for(int k=0;k<RF_CONFIRM_N;k++) _vbuf[c][k]=0;
  _vidx=0; _init=0; _desc_count=0; _descente=false;
}

static inline bool rf_en_descente() { return _descente; }

static int tree_0(const float* x);
static int tree_1(const float* x);
static int tree_2(const float* x);
static int tree_3(const float* x);
static int tree_4(const float* x);
static int tree_5(const float* x);
static int tree_6(const float* x);
static int tree_7(const float* x);
static int tree_8(const float* x);
static int tree_9(const float* x);

static int tree_0(const float* x) {
  if (x[2] <= -0.891659f) {
    return 0;
  } else {
    if (x[19] <= 0.747184f) {
      if (x[12] <= -0.621064f) {
        return 3;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_1(const float* x) {
  if (x[17] <= -0.977392f) {
    return 0;
  } else {
    if (x[10] <= -0.680082f) {
      if (x[4] <= 0.070017f) {
        return 3;
      } else {
        if (x[13] <= -0.523525f) {
          return 2;
        } else {
          if (x[0] <= 0.992087f) {
            return 1;
          } else {
            return 1;
          }
        }
      }
    } else {
      if (x[0] <= -0.088010f) {
        return 3;
      } else {
        if (x[5] <= -0.023200f) {
          if (x[10] <= -0.476384f) {
            return 2;
          } else {
            return 2;
          }
        } else {
          return 1;
        }
      }
    }
  }
}

static int tree_2(const float* x) {
  if (x[19] <= -0.870848f) {
    return 0;
  } else {
    if (x[4] <= 0.007361f) {
      return 3;
    } else {
      if (x[19] <= 0.845000f) {
        if (x[4] <= 0.398320f) {
          return 2;
        } else {
          return 2;
        }
      } else {
        return 1;
      }
    }
  }
}

static int tree_3(const float* x) {
  if (x[6] <= 1.059686f) {
    if (x[12] <= -0.653655f) {
      return 3;
    } else {
      if (x[18] <= -0.963923f) {
        return 0;
      } else {
        return 2;
      }
    }
  } else {
    return 1;
  }
}

static int tree_4(const float* x) {
  if (x[4] <= 0.007361f) {
    if (x[0] <= -0.987018f) {
      return 0;
    } else {
      return 3;
    }
  } else {
    if (x[3] <= 1.059686f) {
      if (x[19] <= -0.209112f) {
        return 2;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_5(const float* x) {
  if (x[15] <= 0.210219f) {
    if (x[15] <= -0.648768f) {
      return 3;
    } else {
      if (x[3] <= 0.191466f) {
        return 0;
      } else {
        return 1;
      }
    }
  } else {
    if (x[6] <= -0.265985f) {
      return 2;
    } else {
      return 2;
    }
  }
}

static int tree_6(const float* x) {
  if (x[12] <= -0.650220f) {
    return 3;
  } else {
    if (x[16] <= 0.918744f) {
      if (x[13] <= -0.598387f) {
        return 2;
      } else {
        return 0;
      }
    } else {
      return 1;
    }
  }
}

static int tree_7(const float* x) {
  if (x[19] <= -0.872529f) {
    return 0;
  } else {
    if (x[15] <= -0.519906f) {
      return 3;
    } else {
      if (x[13] <= -0.534256f) {
        if (x[8] <= -4.004413f) {
          return 2;
        } else {
          return 2;
        }
      } else {
        return 1;
      }
    }
  }
}

static int tree_8(const float* x) {
  if (x[12] <= 0.936669f) {
    if (x[2] <= 0.367930f) {
      if (x[18] <= -0.963923f) {
        return 0;
      } else {
        return 2;
      }
    } else {
      if (x[8] <= -2.192571f) {
        return 3;
      } else {
        return 3;
      }
    }
  } else {
    return 1;
  }
}

static int tree_9(const float* x) {
  if (x[16] <= 0.817178f) {
    if (x[5] <= 0.367930f) {
      if (x[6] <= -0.548153f) {
        if (x[18] <= -1.614654f) {
          return 0;
        } else {
          return 0;
        }
      } else {
        return 2;
      }
    } else {
      if (x[19] <= -0.405758f) {
        return 3;
      } else {
        return 3;
      }
    }
  } else {
    return 1;
  }
}

typedef int (*tfn)(const float*);
static const tfn _trees[RF_N_TREES] = {
  tree_0,
  tree_1,
  tree_2,
  tree_3,
  tree_4,
  tree_5,
  tree_6,
  tree_7,
  tree_8,
  tree_9
};

static int rf_predict(float mq2, float mq4, float mq7, float mq135,
                      float temp, float hum) {
  float raw[4]={mq2,mq4,mq7,mq135};
  if(!_init){rf_reset();_init=1;}

  /* EMA asymétrique */
  for(int i=0;i<4;i++){
    if(_ema[i]<0.0f){_ema[i]=raw[i];continue;}
    float a=(raw[i]>_ema[i])?RF_EMA_RISE:RF_EMA_FALL;
    _ema[i]=a*raw[i]+(1.0f-a)*_ema[i];
  }

  /* Pas de compensation T/H (modèle sans T/H) */
  float c[4];
  for(int i=0;i<4;i++){
    c[i]=_ema[i];
    if(c[i]<0.0f)c[i]=0.0f; if(c[i]>4095.0f)c[i]=4095.0f;
  }

  /* Dérivées temporelles */
  float d[4];
  for(int i=0;i<4;i++){d[i]=c[i]-_prev[i];_prev[i]=c[i];}

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
  float x[RF_N_FEATURES]={
    c[0],c[1],c[2],c[3],
    mq2_d,mq7_d,mq135_d,mq4_f,
    d[0],d[1],d[2],d[3],
    R_MQ135_MQ7,R_MQ7_MQ2,R_MQ7_MQ135,R_MQ2_MQ7,
    sum_c,std_c,max_c,gi
  };

  /* Normalisation Z-Score */
  for(int i=0;i<RF_N_FEATURES;i++)
    x[i]=(x[i]-RF_MEAN[i])/RF_STD[i];

  /* ── Détection descente → retour Air Pur forcé ── */
  _descente=false;
  if(_init>1){
    bool desc=(c[0]<_desc_prev[0]-RF_DESCENTE_DELTA)&&
              (c[2]<_desc_prev[2]-RF_DESCENTE_DELTA)&&
              (c[3]<_desc_prev[3]-RF_DESCENTE_DELTA);
    if(desc) _desc_count++; else _desc_count=0;
    if(_desc_count>=RF_DESCENTE_SEUIL){
      _descente=true;
      rf_reset();
      return 0;
    }
  }
  _desc_prev[0]=c[0];_desc_prev[1]=c[1];
  _desc_prev[2]=c[2];_desc_prev[3]=c[3];

  /* Vote Random Forest */
  int votes[RF_N_CLASSES]={0};
  for(int t=0;t<RF_N_TREES;t++){
    int cls=_trees[t](x);
    if(cls>=0&&cls<RF_N_CLASSES) votes[cls]++;
  }
  int raw_cls=0;
  for(int i=1;i<RF_N_CLASSES;i++)
    if(votes[i]>votes[raw_cls]) raw_cls=i;

  /* Filtre majoritaire */
  for(int c2=0;c2<RF_N_CLASSES;c2++) _vbuf[c2][_vidx]=0;
  _vbuf[raw_cls][_vidx]=1;
  _vidx=(_vidx+1)%RF_CONFIRM_N;
  int tot[RF_N_CLASSES]={0};
  for(int c2=0;c2<RF_N_CLASSES;c2++)
    for(int k=0;k<RF_CONFIRM_N;k++) tot[c2]+=_vbuf[c2][k];
  int best=0;
  for(int i=1;i<RF_N_CLASSES;i++)
    if(tot[i]>tot[best]) best=i;
  return best;
}

#ifdef __cplusplus
}
#endif
#endif /* RF_GAZ_H */
