/*
 * rf_gaz.h — CALIBRÉ SUR CAPTEURS RÉELS
 * ════════════════════════════════════════════════════════════════
 * Classes  : 0=Air Pur | 1=CH4 | 2=Fumée | 3=CO
 * Accuracy : 100.00%   Arbres:200   Features:22
 *
 * Baselines capteurs réels :
 *   Air pur → MQ2=400  MQ7=369  MQ135=312  MQ4=0
 *
 * Différenciateurs clés :
 *   CH4   → MQ7↑ ET MQ135↑↑  (R_MQ135/MQ7 > 1.1)
 *   Fumée → MQ2↑↑ MQ7 bas    (R_MQ135/MQ7 < 0.95)
 *   CO    → MQ7↑↑ seul
 *   MQ4   → actif uniquement si CH4 (confirmateur)
 *
 * EMA : montée α=0.35  descente α=0.08
 * Filtre majoritaire : 5 lectures
 */
#ifndef RF_GAZ_H
#define RF_GAZ_H
#include <math.h>
#ifdef __cplusplus
extern "C" {
#endif

#define RF_N_TREES    200
#define RF_N_FEATURES 22
#define RF_N_CLASSES  4
#define RF_EMA_RISE   0.50f   // détection plus rapide
#define RF_EMA_FALL   0.20f   // retour à l'état normal 2.5x plus vite
#define RF_DESCENTE_SEUIL  4
#define RF_DESCENTE_DELTA  2.0f
#define RF_CONFIRM_N  5
#define RF_T_REF      31.8f
#define RF_H_REF      67.3f
#define RF_B_MQ2      400.00f
#define RF_B_MQ7      369.00f
#define RF_B_MQ135    312.00f

static const char* RF_CLASSES[4] = {
  "Air Pur",
  "CH4",
  "Fumée",
  "CO"
};
static const float RF_MEAN[22] = { 989.811653f, 0.000000f, 1127.893491f, 854.713693f, 30.843498f, 55.421307f, 589.811653f, 758.893491f, 542.713693f, 0.000000f, 0.004726f, 0.000000f, -0.083498f, 0.028843f, 0.863909f, 1.413959f, 1.753732f, 1.077284f, 2972.418836f, 610.899670f, 1429.584877f, 785.840394f };
static const float RF_STD[22]  = { 521.203857f, 1.000000f, 630.399271f, 602.016448f, 3.810155f, 16.992161f, 521.203857f, 630.399271f, 602.016448f, 1.000000f, 237.638673f, 1.000000f, 337.450387f, 260.661532f, 0.409281f, 1.051038f, 1.339275f, 0.556564f, 1339.032563f, 281.200480f, 670.902699f, 361.459030f  };
static const float RF_AT[4] = { -0.010000f, -0.012000f, -0.015000f, -0.009000f };
static const float RF_AH[4] = { 0.006000f, 0.005000f, 0.007000f, 0.008000f };

static float _ema[4]  = {-1.0f,-1.0f,-1.0f,-1.0f};
static float _prev[4] = {0.0f,0.0f,0.0f,0.0f};
static int   _vbuf[4][5];
static int   _vidx = 0;
static int   _init = 0;

static inline const char* rf_class_name(int i) {
  return (i>=0&&i<RF_N_CLASSES)?RF_CLASSES[i]:"Unknown";
}

static inline void rf_reset() {
  for(int i=0;i<4;i++){_ema[i]=-1.0f;_prev[i]=0.0f;}
  for(int c=0;c<RF_N_CLASSES;c++)
    for(int k=0;k<RF_CONFIRM_N;k++) _vbuf[c][k]=0;
  _vidx=0; _init=0;
}

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
static int tree_10(const float* x);
static int tree_11(const float* x);
static int tree_12(const float* x);
static int tree_13(const float* x);
static int tree_14(const float* x);
static int tree_15(const float* x);
static int tree_16(const float* x);
static int tree_17(const float* x);
static int tree_18(const float* x);
static int tree_19(const float* x);
static int tree_20(const float* x);
static int tree_21(const float* x);
static int tree_22(const float* x);
static int tree_23(const float* x);
static int tree_24(const float* x);
static int tree_25(const float* x);
static int tree_26(const float* x);
static int tree_27(const float* x);
static int tree_28(const float* x);
static int tree_29(const float* x);
static int tree_30(const float* x);
static int tree_31(const float* x);
static int tree_32(const float* x);
static int tree_33(const float* x);
static int tree_34(const float* x);
static int tree_35(const float* x);
static int tree_36(const float* x);
static int tree_37(const float* x);
static int tree_38(const float* x);
static int tree_39(const float* x);
static int tree_40(const float* x);
static int tree_41(const float* x);
static int tree_42(const float* x);
static int tree_43(const float* x);
static int tree_44(const float* x);
static int tree_45(const float* x);
static int tree_46(const float* x);
static int tree_47(const float* x);
static int tree_48(const float* x);
static int tree_49(const float* x);
static int tree_50(const float* x);
static int tree_51(const float* x);
static int tree_52(const float* x);
static int tree_53(const float* x);
static int tree_54(const float* x);
static int tree_55(const float* x);
static int tree_56(const float* x);
static int tree_57(const float* x);
static int tree_58(const float* x);
static int tree_59(const float* x);
static int tree_60(const float* x);
static int tree_61(const float* x);
static int tree_62(const float* x);
static int tree_63(const float* x);
static int tree_64(const float* x);
static int tree_65(const float* x);
static int tree_66(const float* x);
static int tree_67(const float* x);
static int tree_68(const float* x);
static int tree_69(const float* x);
static int tree_70(const float* x);
static int tree_71(const float* x);
static int tree_72(const float* x);
static int tree_73(const float* x);
static int tree_74(const float* x);
static int tree_75(const float* x);
static int tree_76(const float* x);
static int tree_77(const float* x);
static int tree_78(const float* x);
static int tree_79(const float* x);
static int tree_80(const float* x);
static int tree_81(const float* x);
static int tree_82(const float* x);
static int tree_83(const float* x);
static int tree_84(const float* x);
static int tree_85(const float* x);
static int tree_86(const float* x);
static int tree_87(const float* x);
static int tree_88(const float* x);
static int tree_89(const float* x);
static int tree_90(const float* x);
static int tree_91(const float* x);
static int tree_92(const float* x);
static int tree_93(const float* x);
static int tree_94(const float* x);
static int tree_95(const float* x);
static int tree_96(const float* x);
static int tree_97(const float* x);
static int tree_98(const float* x);
static int tree_99(const float* x);
static int tree_100(const float* x);
static int tree_101(const float* x);
static int tree_102(const float* x);
static int tree_103(const float* x);
static int tree_104(const float* x);
static int tree_105(const float* x);
static int tree_106(const float* x);
static int tree_107(const float* x);
static int tree_108(const float* x);
static int tree_109(const float* x);
static int tree_110(const float* x);
static int tree_111(const float* x);
static int tree_112(const float* x);
static int tree_113(const float* x);
static int tree_114(const float* x);
static int tree_115(const float* x);
static int tree_116(const float* x);
static int tree_117(const float* x);
static int tree_118(const float* x);
static int tree_119(const float* x);
static int tree_120(const float* x);
static int tree_121(const float* x);
static int tree_122(const float* x);
static int tree_123(const float* x);
static int tree_124(const float* x);
static int tree_125(const float* x);
static int tree_126(const float* x);
static int tree_127(const float* x);
static int tree_128(const float* x);
static int tree_129(const float* x);
static int tree_130(const float* x);
static int tree_131(const float* x);
static int tree_132(const float* x);
static int tree_133(const float* x);
static int tree_134(const float* x);
static int tree_135(const float* x);
static int tree_136(const float* x);
static int tree_137(const float* x);
static int tree_138(const float* x);
static int tree_139(const float* x);
static int tree_140(const float* x);
static int tree_141(const float* x);
static int tree_142(const float* x);
static int tree_143(const float* x);
static int tree_144(const float* x);
static int tree_145(const float* x);
static int tree_146(const float* x);
static int tree_147(const float* x);
static int tree_148(const float* x);
static int tree_149(const float* x);
static int tree_150(const float* x);
static int tree_151(const float* x);
static int tree_152(const float* x);
static int tree_153(const float* x);
static int tree_154(const float* x);
static int tree_155(const float* x);
static int tree_156(const float* x);
static int tree_157(const float* x);
static int tree_158(const float* x);
static int tree_159(const float* x);
static int tree_160(const float* x);
static int tree_161(const float* x);
static int tree_162(const float* x);
static int tree_163(const float* x);
static int tree_164(const float* x);
static int tree_165(const float* x);
static int tree_166(const float* x);
static int tree_167(const float* x);
static int tree_168(const float* x);
static int tree_169(const float* x);
static int tree_170(const float* x);
static int tree_171(const float* x);
static int tree_172(const float* x);
static int tree_173(const float* x);
static int tree_174(const float* x);
static int tree_175(const float* x);
static int tree_176(const float* x);
static int tree_177(const float* x);
static int tree_178(const float* x);
static int tree_179(const float* x);
static int tree_180(const float* x);
static int tree_181(const float* x);
static int tree_182(const float* x);
static int tree_183(const float* x);
static int tree_184(const float* x);
static int tree_185(const float* x);
static int tree_186(const float* x);
static int tree_187(const float* x);
static int tree_188(const float* x);
static int tree_189(const float* x);
static int tree_190(const float* x);
static int tree_191(const float* x);
static int tree_192(const float* x);
static int tree_193(const float* x);
static int tree_194(const float* x);
static int tree_195(const float* x);
static int tree_196(const float* x);
static int tree_197(const float* x);
static int tree_198(const float* x);
static int tree_199(const float* x);

static int tree_0(const float* x) {
  if (x[13] <= 1.293387f) {
    if (x[21] <= -0.859628f) {
      return 0;
    } else {
      if (x[0] <= -0.094860f) {
        return 3;
      } else {
        if (x[8] <= 0.692193f) {
          return 2;
        } else {
          return 1;
        }
      }
    }
  } else {
    if (x[8] <= 1.049434f) {
      return 2;
    } else {
      if (x[19] <= 0.498072f) {
        return 1;
      } else {
        return 1;
      }
    }
  }
}

static int tree_1(const float* x) {
  if (x[2] <= -0.897143f) {
    return 0;
  } else {
    if (x[8] <= 0.713604f) {
      if (x[2] <= 0.138280f) {
        return 2;
      } else {
        return 3;
      }
    } else {
      return 1;
    }
  }
}

static int tree_2(const float* x) {
  if (x[14] <= -0.813404f) {
    return 3;
  } else {
    if (x[2] <= -0.897143f) {
      return 0;
    } else {
      if (x[8] <= 0.705888f) {
        if (x[19] <= -0.598128f) {
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
  if (x[2] <= -0.897246f) {
    return 0;
  } else {
    if (x[0] <= -0.105116f) {
      return 3;
    } else {
      if (x[8] <= 0.706586f) {
        if (x[10] <= -3.175219f) {
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

static int tree_4(const float* x) {
  if (x[6] <= -0.094860f) {
    if (x[21] <= -0.856290f) {
      return 0;
    } else {
      return 3;
    }
  } else {
    if (x[16] <= -0.710021f) {
      return 1;
    } else {
      return 2;
    }
  }
}

static int tree_5(const float* x) {
  if (x[0] <= -0.094860f) {
    if (x[16] <= 0.512890f) {
      return 0;
    } else {
      return 3;
    }
  } else {
    if (x[15] <= -0.612826f) {
      if (x[13] <= -1.904170f) {
        return 2;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_6(const float* x) {
  if (x[16] <= 0.483039f) {
    if (x[6] <= -0.331217f) {
      return 0;
    } else {
      if (x[17] <= 0.556840f) {
        return 1;
      } else {
        return 2;
      }
    }
  } else {
    if (x[14] <= -1.537939f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_7(const float* x) {
  if (x[2] <= -0.897143f) {
    return 0;
  } else {
    if (x[15] <= 0.472522f) {
      if (x[18] <= 0.899344f) {
        if (x[15] <= -0.612826f) {
          return 2;
        } else {
          if (x[6] <= 0.196331f) {
            return 1;
          } else {
            return 1;
          }
        }
      } else {
        if (x[2] <= 0.036947f) {
          return 2;
        } else {
          if (x[2] <= 0.084013f) {
            return 1;
          } else {
            return 1;
          }
        }
      }
    } else {
      if (x[19] <= -0.208676f) {
        return 3;
      } else {
        return 3;
      }
    }
  }
}

static int tree_8(const float* x) {
  if (x[13] <= -1.839105f) {
    if (x[3] <= 0.251656f) {
      return 2;
    } else {
      return 1;
    }
  } else {
    if (x[20] <= -0.912807f) {
      return 0;
    } else {
      if (x[12] <= -1.412153f) {
        return 3;
      } else {
        if (x[15] <= -0.610531f) {
          return 2;
        } else {
          if (x[6] <= -0.089565f) {
            if (x[5] <= -1.493413f) {
              return 3;
            } else {
              return 3;
            }
          } else {
            return 1;
          }
        }
      }
    }
  }
}

static int tree_9(const float* x) {
  if (x[14] <= 0.920393f) {
    if (x[14] <= -0.813404f) {
      return 3;
    } else {
      if (x[3] <= -0.540432f) {
        if (x[2] <= -1.331860f) {
          return 0;
        } else {
          return 0;
        }
      } else {
        return 2;
      }
    }
  } else {
    return 1;
  }
}

static int tree_10(const float* x) {
  if (x[15] <= 0.472522f) {
    if (x[16] <= -0.709012f) {
      return 1;
    } else {
      if (x[8] <= -0.529095f) {
        return 0;
      } else {
        return 2;
      }
    }
  } else {
    if (x[17] <= -1.419670f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_11(const float* x) {
  if (x[0] <= -0.094928f) {
    if (x[18] <= -0.859706f) {
      return 0;
    } else {
      return 3;
    }
  } else {
    if (x[8] <= 0.700922f) {
      if (x[4] <= -2.334157f) {
        return 2;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_12(const float* x) {
  if (x[15] <= 0.472522f) {
    if (x[3] <= 0.713604f) {
      if (x[18] <= -0.798109f) {
        return 0;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  } else {
    if (x[20] <= -0.198106f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_13(const float* x) {
  if (x[7] <= -0.897246f) {
    return 0;
  } else {
    if (x[3] <= -0.336351f) {
      if (x[0] <= -0.094860f) {
        return 3;
      } else {
        if (x[14] <= 0.384536f) {
          return 2;
        } else {
          return 2;
        }
      }
    } else {
      if (x[21] <= 0.828201f) {
        if (x[15] <= -0.642185f) {
          if (x[8] <= -0.332613f) {
            return 2;
          } else {
            return 2;
          }
        } else {
          if (x[17] <= -0.701735f) {
            return 3;
          } else {
            return 1;
          }
        }
      } else {
        if (x[6] <= 1.719276f) {
          if (x[17] <= 0.668500f) {
            if (x[15] <= -0.511016f) {
              return 1;
            } else {
              return 1;
            }
          } else {
            return 2;
          }
        } else {
          if (x[7] <= -0.108072f) {
            return 2;
          } else {
            return 2;
          }
        }
      }
    }
  }
}

static int tree_14(const float* x) {
  if (x[16] <= -0.709012f) {
    return 1;
  } else {
    if (x[14] <= -0.817133f) {
      return 3;
    } else {
      if (x[18] <= -0.798109f) {
        if (x[2] <= -1.330131f) {
          return 0;
        } else {
          return 0;
        }
      } else {
        return 2;
      }
    }
  }
}

static int tree_15(const float* x) {
  if (x[19] <= -0.923048f) {
    return 0;
  } else {
    if (x[16] <= -0.705654f) {
      return 1;
    } else {
      if (x[2] <= 0.132331f) {
        return 2;
      } else {
        return 3;
      }
    }
  }
}

static int tree_16(const float* x) {
  if (x[15] <= -0.612826f) {
    return 2;
  } else {
    if (x[6] <= -0.085325f) {
      if (x[20] <= -0.748163f) {
        return 0;
      } else {
        return 3;
      }
    } else {
      return 1;
    }
  }
}

static int tree_17(const float* x) {
  if (x[6] <= -0.099820f) {
    if (x[14] <= -0.760086f) {
      if (x[12] <= -3.485035f) {
        return 3;
      } else {
        return 3;
      }
    } else {
      return 0;
    }
  } else {
    if (x[15] <= -0.610717f) {
      if (x[6] <= 0.242474f) {
        return 2;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_18(const float* x) {
  if (x[18] <= -0.862118f) {
    return 0;
  } else {
    if (x[14] <= -0.815175f) {
      return 3;
    } else {
      if (x[16] <= -0.709012f) {
        return 1;
      } else {
        return 2;
      }
    }
  }
}

static int tree_19(const float* x) {
  if (x[16] <= -0.503324f) {
    if (x[14] <= 0.945284f) {
      if (x[2] <= -0.864101f) {
        return 2;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  } else {
    if (x[7] <= -0.612601f) {
      if (x[12] <= -0.705516f) {
        return 0;
      } else {
        return 0;
      }
    } else {
      if (x[6] <= 0.196331f) {
        return 3;
      } else {
        return 2;
      }
    }
  }
}

static int tree_20(const float* x) {
  if (x[19] <= -0.923066f) {
    return 0;
  } else {
    if (x[15] <= 0.469482f) {
      if (x[16] <= -0.705654f) {
        return 1;
      } else {
        return 2;
      }
    } else {
      if (x[18] <= -0.654819f) {
        return 3;
      } else {
        return 3;
      }
    }
  }
}

static int tree_21(const float* x) {
  if (x[7] <= -0.897246f) {
    return 0;
  } else {
    if (x[3] <= 0.710722f) {
      if (x[2] <= 0.132331f) {
        return 2;
      } else {
        return 3;
      }
    } else {
      return 1;
    }
  }
}

static int tree_22(const float* x) {
  if (x[18] <= -0.862663f) {
    return 0;
  } else {
    if (x[21] <= 0.824975f) {
      if (x[0] <= -0.100223f) {
        return 3;
      } else {
        if (x[15] <= -0.611011f) {
          if (x[0] <= 0.193251f) {
            return 2;
          } else {
            return 2;
          }
        } else {
          return 1;
        }
      }
    } else {
      if (x[16] <= -0.705648f) {
        return 1;
      } else {
        if (x[7] <= -0.113434f) {
          return 2;
        } else {
          return 2;
        }
      }
    }
  }
}

static int tree_23(const float* x) {
  if (x[7] <= -0.897143f) {
    return 0;
  } else {
    if (x[16] <= 0.508286f) {
      if (x[16] <= -0.709012f) {
        return 1;
      } else {
        return 2;
      }
    } else {
      if (x[18] <= -0.659550f) {
        return 3;
      } else {
        return 3;
      }
    }
  }
}

static int tree_24(const float* x) {
  if (x[7] <= -0.897246f) {
    return 0;
  } else {
    if (x[16] <= 0.417697f) {
      if (x[14] <= 0.926090f) {
        if (x[7] <= -0.863672f) {
          return 2;
        } else {
          return 2;
        }
      } else {
        return 1;
      }
    } else {
      if (x[15] <= 1.341325f) {
        return 3;
      } else {
        return 3;
      }
    }
  }
}

static int tree_25(const float* x) {
  if (x[20] <= -0.911943f) {
    return 0;
  } else {
    if (x[17] <= 0.425293f) {
      if (x[3] <= 0.214598f) {
        return 3;
      } else {
        return 1;
      }
    } else {
      if (x[17] <= 0.837410f) {
        return 2;
      } else {
        return 2;
      }
    }
  }
}

static int tree_26(const float* x) {
  if (x[3] <= 0.705888f) {
    if (x[16] <= 0.532662f) {
      if (x[15] <= -0.610874f) {
        return 2;
      } else {
        return 0;
      }
    } else {
      if (x[6] <= -1.039616f) {
        return 3;
      } else {
        return 3;
      }
    }
  } else {
    return 1;
  }
}

static int tree_27(const float* x) {
  if (x[0] <= -0.089565f) {
    if (x[2] <= -0.329733f) {
      return 0;
    } else {
      return 3;
    }
  } else {
    if (x[8] <= 0.705888f) {
      if (x[20] <= -0.497218f) {
        return 2;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_28(const float* x) {
  if (x[3] <= 0.713604f) {
    if (x[0] <= -0.094860f) {
      if (x[2] <= -0.328750f) {
        return 0;
      } else {
        return 3;
      }
    } else {
      if (x[7] <= -0.863672f) {
        return 2;
      } else {
        return 2;
      }
    }
  } else {
    return 1;
  }
}

static int tree_29(const float* x) {
  if (x[14] <= 0.935596f) {
    if (x[15] <= -0.639986f) {
      return 2;
    } else {
      if (x[17] <= -0.722392f) {
        if (x[8] <= -0.857765f) {
          return 3;
        } else {
          return 3;
        }
      } else {
        return 0;
      }
    }
  } else {
    return 1;
  }
}

static int tree_30(const float* x) {
  if (x[3] <= 0.713604f) {
    if (x[15] <= -0.610874f) {
      return 2;
    } else {
      if (x[15] <= 0.473274f) {
        if (x[3] <= -1.004730f) {
          return 0;
        } else {
          return 0;
        }
      } else {
        return 3;
      }
    }
  } else {
    return 1;
  }
}

static int tree_31(const float* x) {
  if (x[16] <= 0.483154f) {
    if (x[14] <= 0.935596f) {
      if (x[15] <= -0.639986f) {
        return 2;
      } else {
        return 0;
      }
    } else {
      return 1;
    }
  } else {
    if (x[2] <= 0.273686f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_32(const float* x) {
  if (x[3] <= 0.715290f) {
    if (x[20] <= -0.911943f) {
      return 0;
    } else {
      if (x[16] <= 0.515311f) {
        return 2;
      } else {
        return 3;
      }
    }
  } else {
    return 1;
  }
}

static int tree_33(const float* x) {
  if (x[21] <= -0.862110f) {
    return 0;
  } else {
    if (x[17] <= -0.732595f) {
      return 3;
    } else {
      if (x[13] <= 2.009142f) {
        if (x[15] <= -0.610717f) {
          if (x[2] <= -0.864101f) {
            return 2;
          } else {
            return 2;
          }
        } else {
          return 1;
        }
      } else {
        return 1;
      }
    }
  }
}

static int tree_34(const float* x) {
  if (x[16] <= -0.709012f) {
    return 1;
  } else {
    if (x[15] <= -0.640997f) {
      return 2;
    } else {
      if (x[14] <= -0.759829f) {
        return 3;
      } else {
        return 0;
      }
    }
  }
}

static int tree_35(const float* x) {
  if (x[21] <= -0.862110f) {
    return 0;
  } else {
    if (x[3] <= 0.709468f) {
      if (x[20] <= 0.156237f) {
        if (x[17] <= -0.295707f) {
          return 3;
        } else {
          if (x[19] <= -0.567006f) {
            return 2;
          } else {
            return 2;
          }
        }
      } else {
        if (x[0] <= 0.350119f) {
          if (x[14] <= -1.544954f) {
            return 3;
          } else {
            return 3;
          }
        } else {
          if (x[10] <= -1.589660f) {
            return 2;
          } else {
            return 2;
          }
        }
      }
    } else {
      return 1;
    }
  }
}

static int tree_36(const float* x) {
  if (x[2] <= -0.897246f) {
    return 0;
  } else {
    if (x[8] <= 0.713604f) {
      if (x[14] <= -0.595310f) {
        return 3;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_37(const float* x) {
  if (x[21] <= -0.862110f) {
    return 0;
  } else {
    if (x[16] <= -0.705654f) {
      return 1;
    } else {
      if (x[6] <= -0.067414f) {
        return 3;
      } else {
        return 2;
      }
    }
  }
}

static int tree_38(const float* x) {
  if (x[14] <= 0.935596f) {
    if (x[2] <= -0.897143f) {
      return 0;
    } else {
      if (x[2] <= 0.131245f) {
        return 2;
      } else {
        return 3;
      }
    }
  } else {
    return 1;
  }
}

static int tree_39(const float* x) {
  if (x[15] <= 0.472404f) {
    if (x[20] <= -0.911943f) {
      return 0;
    } else {
      if (x[15] <= -0.642185f) {
        if (x[12] <= -1.420139f) {
          return 2;
        } else {
          return 2;
        }
      } else {
        return 1;
      }
    }
  } else {
    if (x[0] <= -1.039865f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_40(const float* x) {
  if (x[0] <= -0.100223f) {
    if (x[18] <= -0.859706f) {
      return 0;
    } else {
      return 3;
    }
  } else {
    if (x[8] <= 0.709468f) {
      if (x[12] <= -1.437564f) {
        return 2;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_41(const float* x) {
  if (x[2] <= -0.897143f) {
    return 0;
  } else {
    if (x[8] <= 0.709468f) {
      if (x[7] <= 0.123416f) {
        return 2;
      } else {
        return 3;
      }
    } else {
      return 1;
    }
  }
}

static int tree_42(const float* x) {
  if (x[7] <= -0.897143f) {
    return 0;
  } else {
    if (x[18] <= 0.820985f) {
      if (x[2] <= 0.179238f) {
        if (x[3] <= 0.645101f) {
          return 2;
        } else {
          return 1;
        }
      } else {
        return 3;
      }
    } else {
      if (x[15] <= -0.641447f) {
        return 2;
      } else {
        if (x[16] <= 0.508323f) {
          return 1;
        } else {
          if (x[13] <= 0.048190f) {
            return 3;
          } else {
            return 3;
          }
        }
      }
    }
  }
}

static int tree_43(const float* x) {
  if (x[19] <= -0.915164f) {
    return 0;
  } else {
    if (x[17] <= -0.733481f) {
      return 3;
    } else {
      if (x[17] <= 0.425293f) {
        return 1;
      } else {
        return 2;
      }
    }
  }
}

static int tree_44(const float* x) {
  if (x[20] <= -0.911943f) {
    return 0;
  } else {
    if (x[0] <= -0.094860f) {
      return 3;
    } else {
      if (x[2] <= -0.032176f) {
        if (x[5] <= 1.180173f) {
          if (x[15] <= -0.606998f) {
            return 2;
          } else {
            if (x[10] <= -2.422332f) {
              return 1;
            } else {
              return 1;
            }
          }
        } else {
          if (x[12] <= -1.562930f) {
            return 1;
          } else {
            if (x[21] <= 0.098150f) {
              if (x[3] <= -0.418143f) {
                return 2;
              } else {
                return 2;
              }
            } else {
              return 1;
            }
          }
        }
      } else {
        if (x[3] <= 0.851358f) {
          return 2;
        } else {
          return 1;
        }
      }
    }
  }
}

static int tree_45(const float* x) {
  if (x[7] <= -0.892345f) {
    return 0;
  } else {
    if (x[0] <= -0.100319f) {
      return 3;
    } else {
      if (x[3] <= 0.706586f) {
        if (x[8] <= -0.379398f) {
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

static int tree_46(const float* x) {
  if (x[19] <= -0.923048f) {
    return 0;
  } else {
    if (x[15] <= -0.610717f) {
      return 2;
    } else {
      if (x[16] <= 0.314930f) {
        return 1;
      } else {
        return 3;
      }
    }
  }
}

static int tree_47(const float* x) {
  if (x[2] <= -0.897143f) {
    return 0;
  } else {
    if (x[17] <= 0.424079f) {
      if (x[16] <= 0.316642f) {
        return 1;
      } else {
        return 3;
      }
    } else {
      if (x[16] <= -0.674706f) {
        return 2;
      } else {
        return 2;
      }
    }
  }
}

static int tree_48(const float* x) {
  if (x[21] <= -0.862223f) {
    return 0;
  } else {
    if (x[15] <= -0.640076f) {
      return 2;
    } else {
      if (x[16] <= 0.323668f) {
        return 1;
      } else {
        return 3;
      }
    }
  }
}

static int tree_49(const float* x) {
  if (x[21] <= -0.859148f) {
    return 0;
  } else {
    if (x[8] <= 0.705058f) {
      if (x[0] <= -0.084375f) {
        if (x[20] <= -0.191496f) {
          return 3;
        } else {
          return 3;
        }
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_50(const float* x) {
  if (x[15] <= 0.476925f) {
    if (x[7] <= -0.893178f) {
      return 0;
    } else {
      if (x[16] <= -0.710021f) {
        return 1;
      } else {
        return 2;
      }
    }
  } else {
    if (x[2] <= 0.283799f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_51(const float* x) {
  if (x[21] <= -0.854094f) {
    return 0;
  } else {
    if (x[17] <= 0.563775f) {
      if (x[8] <= 0.218734f) {
        return 3;
      } else {
        return 1;
      }
    } else {
      if (x[12] <= -1.418909f) {
        return 2;
      } else {
        return 2;
      }
    }
  }
}

static int tree_52(const float* x) {
  if (x[19] <= -0.915164f) {
    return 0;
  } else {
    if (x[15] <= 0.469482f) {
      if (x[8] <= 0.706586f) {
        if (x[20] <= -0.497218f) {
          return 2;
        } else {
          return 2;
        }
      } else {
        return 1;
      }
    } else {
      if (x[20] <= -0.192517f) {
        return 3;
      } else {
        return 3;
      }
    }
  }
}

static int tree_53(const float* x) {
  if (x[14] <= -0.760086f) {
    return 3;
  } else {
    if (x[6] <= -0.320655f) {
      return 0;
    } else {
      if (x[3] <= 0.706586f) {
        if (x[2] <= -0.859604f) {
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

static int tree_54(const float* x) {
  if (x[2] <= -0.893074f) {
    return 0;
  } else {
    if (x[19] <= 0.025146f) {
      if (x[2] <= -0.290171f) {
        return 2;
      } else {
        if (x[6] <= -0.367844f) {
          return 3;
        } else {
          return 1;
        }
      }
    } else {
      if (x[7] <= 0.516500f) {
        if (x[3] <= 0.785936f) {
          if (x[2] <= 0.242936f) {
            return 2;
          } else {
            return 3;
          }
        } else {
          return 1;
        }
      } else {
        if (x[0] <= 0.321205f) {
          if (x[17] <= -1.422888f) {
            return 3;
          } else {
            return 3;
          }
        } else {
          return 1;
        }
      }
    }
  }
}

static int tree_55(const float* x) {
  if (x[18] <= -0.862118f) {
    return 0;
  } else {
    if (x[15] <= -0.612826f) {
      return 2;
    } else {
      if (x[5] <= -1.427794f) {
        if (x[7] <= 1.439067f) {
          return 1;
        } else {
          if (x[5] <= -1.482820f) {
            return 3;
          } else {
            return 3;
          }
        }
      } else {
        if (x[0] <= -0.122662f) {
          if (x[0] <= -1.035730f) {
            return 3;
          } else {
            return 3;
          }
        } else {
          return 1;
        }
      }
    }
  }
}

static int tree_56(const float* x) {
  if (x[0] <= -0.095043f) {
    if (x[15] <= 0.467715f) {
      return 0;
    } else {
      return 3;
    }
  } else {
    if (x[16] <= -0.709012f) {
      return 1;
    } else {
      return 2;
    }
  }
}

static int tree_57(const float* x) {
  if (x[18] <= -0.862118f) {
    return 0;
  } else {
    if (x[16] <= 0.424530f) {
      if (x[14] <= 0.935596f) {
        if (x[17] <= 0.968957f) {
          return 2;
        } else {
          return 2;
        }
      } else {
        return 1;
      }
    } else {
      if (x[15] <= 1.327556f) {
        return 3;
      } else {
        return 3;
      }
    }
  }
}

static int tree_58(const float* x) {
  if (x[3] <= 0.709468f) {
    if (x[15] <= -0.610874f) {
      return 2;
    } else {
      if (x[19] <= -0.726982f) {
        if (x[18] <= -1.568516f) {
          return 0;
        } else {
          return 0;
        }
      } else {
        return 3;
      }
    }
  } else {
    return 1;
  }
}

static int tree_59(const float* x) {
  if (x[18] <= -0.862118f) {
    return 0;
  } else {
    if (x[17] <= 0.561466f) {
      if (x[3] <= 0.233310f) {
        return 3;
      } else {
        return 1;
      }
    } else {
      if (x[4] <= -2.334157f) {
        return 2;
      } else {
        return 2;
      }
    }
  }
}

static int tree_60(const float* x) {
  if (x[6] <= -0.094928f) {
    if (x[19] <= -0.727001f) {
      if (x[17] <= -0.153960f) {
        return 0;
      } else {
        return 0;
      }
    } else {
      return 3;
    }
  } else {
    if (x[7] <= -0.039607f) {
      if (x[3] <= 0.706586f) {
        return 2;
      } else {
        if (x[8] <= 0.765239f) {
          return 1;
        } else {
          return 1;
        }
      }
    } else {
      if (x[16] <= -0.694869f) {
        return 1;
      } else {
        if (x[10] <= 1.183878f) {
          return 2;
        } else {
          return 2;
        }
      }
    }
  }
}

static int tree_61(const float* x) {
  if (x[0] <= -0.094860f) {
    if (x[16] <= 0.483154f) {
      return 0;
    } else {
      return 3;
    }
  } else {
    if (x[8] <= 0.710024f) {
      if (x[7] <= -0.864101f) {
        return 2;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_62(const float* x) {
  if (x[15] <= 0.476925f) {
    if (x[10] <= -0.866461f) {
      if (x[16] <= -0.705164f) {
        return 1;
      } else {
        if (x[12] <= -1.438794f) {
          return 2;
        } else {
          return 2;
        }
      }
    } else {
      if (x[6] <= -0.324809f) {
        return 0;
      } else {
        if (x[19] <= 0.176579f) {
          if (x[16] <= -0.718277f) {
            return 1;
          } else {
            if (x[21] <= -0.446179f) {
              return 2;
            } else {
              return 2;
            }
          }
        } else {
          if (x[7] <= -0.032176f) {
            if (x[4] <= -0.756793f) {
              return 1;
            } else {
              if (x[6] <= 1.198501f) {
                return 2;
              } else {
                return 2;
              }
            }
          } else {
            if (x[3] <= 0.843434f) {
              return 2;
            } else {
              return 1;
            }
          }
        }
      }
    }
  } else {
    if (x[6] <= -1.039865f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_63(const float* x) {
  if (x[16] <= -0.706664f) {
    return 1;
  } else {
    if (x[7] <= 0.132331f) {
      if (x[19] <= -0.901879f) {
        return 0;
      } else {
        return 2;
      }
    } else {
      if (x[10] <= -1.295306f) {
        return 3;
      } else {
        return 3;
      }
    }
  }
}

static int tree_64(const float* x) {
  if (x[21] <= -0.862110f) {
    return 0;
  } else {
    if (x[16] <= 0.508286f) {
      if (x[15] <= -0.611011f) {
        if (x[12] <= -1.438794f) {
          return 2;
        } else {
          return 2;
        }
      } else {
        return 1;
      }
    } else {
      if (x[7] <= 0.267737f) {
        return 3;
      } else {
        return 3;
      }
    }
  }
}

static int tree_65(const float* x) {
  if (x[16] <= -0.709012f) {
    return 1;
  } else {
    if (x[17] <= 0.424948f) {
      if (x[17] <= -0.725872f) {
        return 3;
      } else {
        return 0;
      }
    } else {
      if (x[13] <= -1.952911f) {
        return 2;
      } else {
        return 2;
      }
    }
  }
}

static int tree_66(const float* x) {
  if (x[19] <= -0.896166f) {
    return 0;
  } else {
    if (x[14] <= 0.920393f) {
      if (x[13] <= -1.088514f) {
        return 2;
      } else {
        if (x[14] <= -0.813404f) {
          return 3;
        } else {
          return 2;
        }
      }
    } else {
      return 1;
    }
  }
}

static int tree_67(const float* x) {
  if (x[0] <= -0.100223f) {
    if (x[20] <= -0.748163f) {
      if (x[19] <= -1.643477f) {
        return 0;
      } else {
        return 0;
      }
    } else {
      return 3;
    }
  } else {
    if (x[17] <= 0.555055f) {
      return 1;
    } else {
      return 2;
    }
  }
}

static int tree_68(const float* x) {
  if (x[14] <= -0.761858f) {
    return 3;
  } else {
    if (x[7] <= -0.897143f) {
      return 0;
    } else {
      if (x[18] <= 0.321931f) {
        if (x[8] <= 0.471268f) {
          return 2;
        } else {
          return 1;
        }
      } else {
        if (x[3] <= 0.729924f) {
          return 2;
        } else {
          return 1;
        }
      }
    }
  }
}

static int tree_69(const float* x) {
  if (x[16] <= -0.709012f) {
    return 1;
  } else {
    if (x[21] <= -0.862223f) {
      return 0;
    } else {
      if (x[0] <= -0.094860f) {
        return 3;
      } else {
        return 2;
      }
    }
  }
}

static int tree_70(const float* x) {
  if (x[16] <= 0.515311f) {
    if (x[8] <= 0.709468f) {
      if (x[8] <= -0.540432f) {
        return 0;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  } else {
    if (x[20] <= -0.198106f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_71(const float* x) {
  if (x[15] <= -0.611011f) {
    return 2;
  } else {
    if (x[7] <= -0.603790f) {
      return 0;
    } else {
      if (x[2] <= 0.334362f) {
        if (x[15] <= 0.441834f) {
          return 1;
        } else {
          if (x[3] <= -0.866693f) {
            return 3;
          } else {
            return 3;
          }
        }
      } else {
        if (x[8] <= 0.645765f) {
          if (x[14] <= -1.540607f) {
            return 3;
          } else {
            return 3;
          }
        } else {
          return 1;
        }
      }
    }
  }
}

static int tree_72(const float* x) {
  if (x[17] <= -0.731325f) {
    return 3;
  } else {
    if (x[18] <= -0.798109f) {
      return 0;
    } else {
      if (x[3] <= 0.728180f) {
        if (x[2] <= -0.863672f) {
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

static int tree_73(const float* x) {
  if (x[8] <= 0.706586f) {
    if (x[21] <= -0.862110f) {
      return 0;
    } else {
      if (x[0] <= -0.084375f) {
        if (x[18] <= -0.647011f) {
          return 3;
        } else {
          return 3;
        }
      } else {
        return 2;
      }
    }
  } else {
    return 1;
  }
}

static int tree_74(const float* x) {
  if (x[16] <= 0.515311f) {
    if (x[8] <= 0.705888f) {
      if (x[7] <= -0.897143f) {
        return 0;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  } else {
    if (x[16] <= 1.395146f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_75(const float* x) {
  if (x[18] <= -0.852958f) {
    return 0;
  } else {
    if (x[17] <= -0.732595f) {
      return 3;
    } else {
      if (x[8] <= 0.706586f) {
        if (x[13] <= -1.952911f) {
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

static int tree_76(const float* x) {
  if (x[0] <= -0.084375f) {
    if (x[17] <= -0.726232f) {
      return 3;
    } else {
      return 0;
    }
  } else {
    if (x[2] <= -0.032176f) {
      if (x[8] <= 0.724600f) {
        if (x[19] <= -0.576960f) {
          return 2;
        } else {
          return 2;
        }
      } else {
        if (x[19] <= -0.077271f) {
          return 1;
        } else {
          return 1;
        }
      }
    } else {
      if (x[6] <= 1.832456f) {
        return 1;
      } else {
        if (x[4] <= 1.172263f) {
          return 2;
        } else {
          return 2;
        }
      }
    }
  }
}

static int tree_77(const float* x) {
  if (x[3] <= 0.710024f) {
    if (x[21] <= -0.862110f) {
      return 0;
    } else {
      if (x[6] <= -0.094630f) {
        if (x[2] <= 0.267737f) {
          return 3;
        } else {
          return 3;
        }
      } else {
        return 2;
      }
    }
  } else {
    return 1;
  }
}

static int tree_78(const float* x) {
  if (x[14] <= 0.935596f) {
    if (x[14] <= -0.819472f) {
      return 3;
    } else {
      if (x[2] <= -0.893074f) {
        return 0;
      } else {
        return 2;
      }
    }
  } else {
    return 1;
  }
}

static int tree_79(const float* x) {
  if (x[2] <= -0.897143f) {
    return 0;
  } else {
    if (x[0] <= -0.105116f) {
      return 3;
    } else {
      if (x[17] <= 0.561466f) {
        return 1;
      } else {
        return 2;
      }
    }
  }
}

static int tree_80(const float* x) {
  if (x[3] <= 0.728180f) {
    if (x[20] <= -0.912748f) {
      return 0;
    } else {
      if (x[3] <= -0.344075f) {
        if (x[17] <= 0.011904f) {
          return 3;
        } else {
          if (x[18] <= -0.525980f) {
            return 2;
          } else {
            return 2;
          }
        }
      } else {
        if (x[2] <= 1.165526f) {
          return 2;
        } else {
          if (x[6] <= -0.430670f) {
            return 3;
          } else {
            return 3;
          }
        }
      }
    }
  } else {
    return 1;
  }
}

static int tree_81(const float* x) {
  if (x[19] <= -0.923048f) {
    return 0;
  } else {
    if (x[0] <= -0.094860f) {
      return 3;
    } else {
      if (x[14] <= 0.935596f) {
        if (x[21] <= -0.521947f) {
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

static int tree_82(const float* x) {
  if (x[8] <= 0.710722f) {
    if (x[16] <= -0.503324f) {
      return 2;
    } else {
      if (x[20] <= -0.748163f) {
        return 0;
      } else {
        return 3;
      }
    }
  } else {
    return 1;
  }
}

static int tree_83(const float* x) {
  if (x[2] <= -0.897143f) {
    return 0;
  } else {
    if (x[15] <= -0.612826f) {
      return 2;
    } else {
      if (x[2] <= 0.332514f) {
        if (x[19] <= -0.137864f) {
          return 3;
        } else {
          return 1;
        }
      } else {
        if (x[17] <= -0.732379f) {
          if (x[5] <= -1.493413f) {
            return 3;
          } else {
            return 3;
          }
        } else {
          return 1;
        }
      }
    }
  }
}

static int tree_84(const float* x) {
  if (x[15] <= -0.612826f) {
    return 2;
  } else {
    if (x[7] <= -0.603686f) {
      return 0;
    } else {
      if (x[0] <= -0.089565f) {
        if (x[18] <= -0.659550f) {
          return 3;
        } else {
          return 3;
        }
      } else {
        return 1;
      }
    }
  }
}

static int tree_85(const float* x) {
  if (x[16] <= 0.523161f) {
    if (x[8] <= -0.540432f) {
      return 0;
    } else {
      if (x[19] <= 0.075328f) {
        if (x[14] <= 0.990995f) {
          return 2;
        } else {
          if (x[7] <= -0.268447f) {
            return 1;
          } else {
            return 1;
          }
        }
      } else {
        if (x[14] <= 0.926063f) {
          return 2;
        } else {
          return 1;
        }
      }
    }
  } else {
    if (x[21] <= -0.681959f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_86(const float* x) {
  if (x[15] <= -0.642185f) {
    return 2;
  } else {
    if (x[16] <= -0.606579f) {
      return 1;
    } else {
      if (x[7] <= -0.329733f) {
        if (x[19] <= -1.645500f) {
          return 0;
        } else {
          return 0;
        }
      } else {
        return 3;
      }
    }
  }
}

static int tree_87(const float* x) {
  if (x[0] <= -0.094860f) {
    if (x[7] <= -0.312585f) {
      return 0;
    } else {
      return 3;
    }
  } else {
    if (x[8] <= 0.709468f) {
      if (x[18] <= -0.525980f) {
        return 2;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_88(const float* x) {
  if (x[7] <= -0.897143f) {
    return 0;
  } else {
    if (x[14] <= 0.920393f) {
      if (x[16] <= 0.508286f) {
        return 2;
      } else {
        return 3;
      }
    } else {
      return 1;
    }
  }
}

static int tree_89(const float* x) {
  if (x[19] <= -0.915183f) {
    return 0;
  } else {
    if (x[3] <= 0.709468f) {
      if (x[16] <= 0.508286f) {
        if (x[17] <= 0.837410f) {
          return 2;
        } else {
          return 2;
        }
      } else {
        return 3;
      }
    } else {
      return 1;
    }
  }
}

static int tree_90(const float* x) {
  if (x[17] <= 0.424948f) {
    if (x[15] <= 0.480649f) {
      if (x[16] <= -0.606856f) {
        return 1;
      } else {
        return 0;
      }
    } else {
      if (x[10] <= -1.295306f) {
        return 3;
      } else {
        return 3;
      }
    }
  } else {
    if (x[0] <= 0.217599f) {
      return 2;
    } else {
      return 2;
    }
  }
}

static int tree_91(const float* x) {
  if (x[15] <= -0.640370f) {
    return 2;
  } else {
    if (x[18] <= -0.862312f) {
      return 0;
    } else {
      if (x[3] <= 0.267080f) {
        return 3;
      } else {
        return 1;
      }
    }
  }
}

static int tree_92(const float* x) {
  if (x[14] <= -0.813404f) {
    return 3;
  } else {
    if (x[18] <= -0.798303f) {
      return 0;
    } else {
      if (x[17] <= 0.423607f) {
        return 1;
      } else {
        return 2;
      }
    }
  }
}

static int tree_93(const float* x) {
  if (x[17] <= -0.731542f) {
    return 3;
  } else {
    if (x[17] <= 0.429919f) {
      if (x[18] <= -0.390255f) {
        if (x[20] <= -1.642354f) {
          return 0;
        } else {
          return 0;
        }
      } else {
        return 1;
      }
    } else {
      if (x[13] <= -1.883108f) {
        return 2;
      } else {
        return 2;
      }
    }
  }
}

static int tree_94(const float* x) {
  if (x[21] <= -0.862110f) {
    return 0;
  } else {
    if (x[0] <= -0.094860f) {
      return 3;
    } else {
      if (x[8] <= 0.710722f) {
        if (x[19] <= -0.598128f) {
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

static int tree_95(const float* x) {
  if (x[21] <= -0.859148f) {
    return 0;
  } else {
    if (x[14] <= 0.935596f) {
      if (x[14] <= -0.609182f) {
        return 3;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_96(const float* x) {
  if (x[0] <= -0.100223f) {
    if (x[14] <= -0.759584f) {
      return 3;
    } else {
      return 0;
    }
  } else {
    if (x[16] <= -0.709012f) {
      return 1;
    } else {
      return 2;
    }
  }
}

static int tree_97(const float* x) {
  if (x[15] <= -0.611011f) {
    return 2;
  } else {
    if (x[6] <= -0.089565f) {
      if (x[18] <= -0.862118f) {
        return 0;
      } else {
        return 3;
      }
    } else {
      return 1;
    }
  }
}

static int tree_98(const float* x) {
  if (x[21] <= -0.859148f) {
    return 0;
  } else {
    if (x[17] <= 0.429919f) {
      if (x[13] <= -1.039831f) {
        if (x[16] <= 0.460662f) {
          return 1;
        } else {
          return 3;
        }
      } else {
        if (x[0] <= -0.040093f) {
          if (x[20] <= -0.191496f) {
            return 3;
          } else {
            return 3;
          }
        } else {
          return 1;
        }
      }
    } else {
      if (x[20] <= -0.518540f) {
        return 2;
      } else {
        return 2;
      }
    }
  }
}

static int tree_99(const float* x) {
  if (x[14] <= 0.935596f) {
    if (x[2] <= -0.892646f) {
      return 0;
    } else {
      if (x[10] <= -1.285333f) {
        return 2;
      } else {
        if (x[14] <= -0.609182f) {
          return 3;
        } else {
          return 2;
        }
      }
    }
  } else {
    return 1;
  }
}

static int tree_100(const float* x) {
  if (x[20] <= -0.904602f) {
    return 0;
  } else {
    if (x[14] <= -0.813404f) {
      return 3;
    } else {
      if (x[8] <= 0.700922f) {
        return 2;
      } else {
        return 1;
      }
    }
  }
}

static int tree_101(const float* x) {
  if (x[7] <= -0.897246f) {
    return 0;
  } else {
    if (x[6] <= -0.094860f) {
      return 3;
    } else {
      if (x[16] <= -0.705654f) {
        return 1;
      } else {
        return 2;
      }
    }
  }
}

static int tree_102(const float* x) {
  if (x[20] <= -0.912748f) {
    return 0;
  } else {
    if (x[16] <= 0.419897f) {
      if (x[15] <= -0.640370f) {
        if (x[12] <= -1.438794f) {
          return 2;
        } else {
          return 2;
        }
      } else {
        return 1;
      }
    } else {
      if (x[19] <= -0.196785f) {
        return 3;
      } else {
        return 3;
      }
    }
  }
}

static int tree_103(const float* x) {
  if (x[2] <= -0.897246f) {
    return 0;
  } else {
    if (x[3] <= 0.709468f) {
      if (x[15] <= 0.312799f) {
        return 2;
      } else {
        return 3;
      }
    } else {
      return 1;
    }
  }
}

static int tree_104(const float* x) {
  if (x[15] <= -0.610717f) {
    return 2;
  } else {
    if (x[14] <= 0.576259f) {
      if (x[16] <= 0.490180f) {
        return 0;
      } else {
        return 3;
      }
    } else {
      return 1;
    }
  }
}

static int tree_105(const float* x) {
  if (x[21] <= -0.862223f) {
    return 0;
  } else {
    if (x[8] <= 0.709468f) {
      if (x[2] <= 0.117071f) {
        return 2;
      } else {
        return 3;
      }
    } else {
      return 1;
    }
  }
}

static int tree_106(const float* x) {
  if (x[10] <= -1.030618f) {
    if (x[3] <= 0.501973f) {
      if (x[14] <= -0.616667f) {
        return 3;
      } else {
        return 2;
      }
    } else {
      if (x[14] <= 1.117279f) {
        return 1;
      } else {
        return 1;
      }
    }
  } else {
    if (x[16] <= 0.515311f) {
      if (x[0] <= -0.325922f) {
        return 0;
      } else {
        if (x[17] <= 0.424549f) {
          return 1;
        } else {
          return 2;
        }
      }
    } else {
      if (x[7] <= 0.284885f) {
        return 3;
      } else {
        return 3;
      }
    }
  }
}

static int tree_107(const float* x) {
  if (x[15] <= 0.472404f) {
    if (x[20] <= -0.911943f) {
      return 0;
    } else {
      if (x[3] <= 0.709468f) {
        if (x[18] <= -0.511047f) {
          return 2;
        } else {
          return 2;
        }
      } else {
        return 1;
      }
    }
  } else {
    if (x[3] <= -0.866693f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_108(const float* x) {
  if (x[16] <= 0.507307f) {
    if (x[16] <= -0.709012f) {
      return 1;
    } else {
      if (x[17] <= 0.554490f) {
        return 0;
      } else {
        return 2;
      }
    }
  } else {
    if (x[12] <= -3.437976f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_109(const float* x) {
  if (x[19] <= -0.923066f) {
    return 0;
  } else {
    if (x[15] <= -0.642185f) {
      return 2;
    } else {
      if (x[16] <= 0.321956f) {
        return 1;
      } else {
        return 3;
      }
    }
  }
}

static int tree_110(const float* x) {
  if (x[2] <= -0.897350f) {
    return 0;
  } else {
    if (x[15] <= -0.612826f) {
      return 2;
    } else {
      if (x[6] <= -0.069343f) {
        if (x[21] <= -0.681959f) {
          return 3;
        } else {
          return 3;
        }
      } else {
        return 1;
      }
    }
  }
}

static int tree_111(const float* x) {
  if (x[21] <= -0.862589f) {
    return 0;
  } else {
    if (x[0] <= -0.094860f) {
      return 3;
    } else {
      if (x[17] <= 0.429919f) {
        return 1;
      } else {
        return 2;
      }
    }
  }
}

static int tree_112(const float* x) {
  if (x[2] <= -0.893178f) {
    return 0;
  } else {
    if (x[17] <= 0.561466f) {
      if (x[16] <= 0.315633f) {
        return 1;
      } else {
        return 3;
      }
    } else {
      if (x[20] <= -0.477893f) {
        return 2;
      } else {
        return 2;
      }
    }
  }
}

static int tree_113(const float* x) {
  if (x[18] <= -0.862312f) {
    return 0;
  } else {
    if (x[0] <= -0.089565f) {
      return 3;
    } else {
      if (x[16] <= -0.709012f) {
        return 1;
      } else {
        return 2;
      }
    }
  }
}

static int tree_114(const float* x) {
  if (x[16] <= -0.709012f) {
    return 1;
  } else {
    if (x[16] <= -0.498691f) {
      return 2;
    } else {
      if (x[18] <= -0.855169f) {
        return 0;
      } else {
        return 3;
      }
    }
  }
}

static int tree_115(const float* x) {
  if (x[3] <= 0.709468f) {
    if (x[2] <= 0.123416f) {
      if (x[2] <= -0.897246f) {
        return 0;
      } else {
        return 2;
      }
    } else {
      if (x[14] <= -1.536239f) {
        return 3;
      } else {
        return 3;
      }
    }
  } else {
    return 1;
  }
}

static int tree_116(const float* x) {
  if (x[16] <= 0.498030f) {
    if (x[18] <= -0.798109f) {
      return 0;
    } else {
      if (x[8] <= 0.706586f) {
        return 2;
      } else {
        return 1;
      }
    }
  } else {
    if (x[19] <= -0.213374f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_117(const float* x) {
  if (x[16] <= 0.515311f) {
    if (x[14] <= 0.945284f) {
      if (x[8] <= -0.536503f) {
        return 0;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  } else {
    if (x[8] <= -0.855423f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_118(const float* x) {
  if (x[8] <= 0.713604f) {
    if (x[16] <= -0.497958f) {
      return 2;
    } else {
      if (x[21] <= -0.862589f) {
        return 0;
      } else {
        return 3;
      }
    }
  } else {
    return 1;
  }
}

static int tree_119(const float* x) {
  if (x[2] <= -0.897461f) {
    return 0;
  } else {
    if (x[14] <= 0.920393f) {
      if (x[15] <= 0.283439f) {
        return 2;
      } else {
        return 3;
      }
    } else {
      return 1;
    }
  }
}

static int tree_120(const float* x) {
  if (x[15] <= -0.612826f) {
    return 2;
  } else {
    if (x[17] <= -0.731542f) {
      return 3;
    } else {
      if (x[16] <= -0.607898f) {
        return 1;
      } else {
        return 0;
      }
    }
  }
}

static int tree_121(const float* x) {
  if (x[16] <= 0.483039f) {
    if (x[21] <= -0.761564f) {
      return 0;
    } else {
      if (x[17] <= 0.561466f) {
        return 1;
      } else {
        return 2;
      }
    }
  } else {
    if (x[18] <= -0.652802f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_122(const float* x) {
  if (x[16] <= -0.710021f) {
    return 1;
  } else {
    if (x[16] <= 0.515311f) {
      if (x[7] <= -0.897143f) {
        return 0;
      } else {
        return 2;
      }
    } else {
      if (x[8] <= -0.866693f) {
        return 3;
      } else {
        return 3;
      }
    }
  }
}

static int tree_123(const float* x) {
  if (x[15] <= 0.472404f) {
    if (x[0] <= -0.331140f) {
      return 0;
    } else {
      if (x[21] <= 0.925320f) {
        if (x[14] <= 0.930081f) {
          if (x[2] <= -0.864101f) {
            return 2;
          } else {
            return 2;
          }
        } else {
          return 1;
        }
      } else {
        if (x[7] <= 0.031356f) {
          return 2;
        } else {
          if (x[13] <= -3.224292f) {
            return 1;
          } else {
            return 1;
          }
        }
      }
    }
  } else {
    if (x[2] <= 0.273686f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_124(const float* x) {
  if (x[14] <= 0.935596f) {
    if (x[19] <= -0.923048f) {
      return 0;
    } else {
      if (x[19] <= 0.174221f) {
        if (x[12] <= -1.472265f) {
          return 3;
        } else {
          if (x[5] <= 0.982729f) {
            if (x[3] <= -0.539393f) {
              return 3;
            } else {
              return 2;
            }
          } else {
            if (x[17] <= -0.033001f) {
              return 3;
            } else {
              if (x[21] <= -0.521947f) {
                return 2;
              } else {
                return 2;
              }
            }
          }
        }
      } else {
        if (x[6] <= 0.422787f) {
          return 3;
        } else {
          if (x[12] <= -0.644633f) {
            return 2;
          } else {
            return 2;
          }
        }
      }
    }
  } else {
    return 1;
  }
}

static int tree_125(const float* x) {
  if (x[6] <= -0.094860f) {
    if (x[20] <= -0.748163f) {
      return 0;
    } else {
      return 3;
    }
  } else {
    if (x[3] <= 0.705888f) {
      if (x[14] <= 0.232967f) {
        return 2;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_126(const float* x) {
  if (x[16] <= -0.706664f) {
    return 1;
  } else {
    if (x[17] <= 0.556812f) {
      if (x[21] <= -0.859148f) {
        if (x[17] <= -0.150781f) {
          return 0;
        } else {
          return 0;
        }
      } else {
        return 3;
      }
    } else {
      if (x[12] <= -1.428214f) {
        return 2;
      } else {
        return 2;
      }
    }
  }
}

static int tree_127(const float* x) {
  if (x[19] <= -0.923048f) {
    return 0;
  } else {
    if (x[15] <= 0.472404f) {
      if (x[3] <= 0.709468f) {
        return 2;
      } else {
        return 1;
      }
    } else {
      if (x[21] <= -0.678622f) {
        return 3;
      } else {
        return 3;
      }
    }
  }
}

static int tree_128(const float* x) {
  if (x[7] <= -0.897143f) {
    return 0;
  } else {
    if (x[8] <= 0.728180f) {
      if (x[7] <= 0.124503f) {
        return 2;
      } else {
        return 3;
      }
    } else {
      return 1;
    }
  }
}

static int tree_129(const float* x) {
  if (x[12] <= -1.153893f) {
    if (x[0] <= -0.198371f) {
      return 3;
    } else {
      if (x[17] <= 0.738584f) {
        return 1;
      } else {
        if (x[15] <= -0.875635f) {
          return 2;
        } else {
          return 2;
        }
      }
    }
  } else {
    if (x[2] <= -0.897350f) {
      return 0;
    } else {
      if (x[17] <= 0.424079f) {
        if (x[3] <= 0.218734f) {
          if (x[8] <= -0.854534f) {
            return 3;
          } else {
            return 3;
          }
        } else {
          return 1;
        }
      } else {
        return 2;
      }
    }
  }
}

static int tree_130(const float* x) {
  if (x[14] <= 0.935596f) {
    if (x[0] <= -0.094860f) {
      if (x[15] <= 0.468871f) {
        return 0;
      } else {
        return 3;
      }
    } else {
      if (x[8] <= -0.418143f) {
        return 2;
      } else {
        return 2;
      }
    }
  } else {
    return 1;
  }
}

static int tree_131(const float* x) {
  if (x[8] <= 0.709468f) {
    if (x[16] <= -0.504792f) {
      return 2;
    } else {
      if (x[18] <= -0.859900f) {
        return 0;
      } else {
        return 3;
      }
    }
  } else {
    return 1;
  }
}

static int tree_132(const float* x) {
  if (x[14] <= -0.813404f) {
    return 3;
  } else {
    if (x[20] <= -0.911943f) {
      return 0;
    } else {
      if (x[15] <= -0.610717f) {
        if (x[16] <= -0.674193f) {
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

static int tree_133(const float* x) {
  if (x[16] <= 0.515311f) {
    if (x[18] <= -0.772740f) {
      return 0;
    } else {
      if (x[14] <= 0.935596f) {
        if (x[7] <= -0.859302f) {
          return 2;
        } else {
          return 2;
        }
      } else {
        return 1;
      }
    }
  } else {
    if (x[16] <= 1.410121f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_134(const float* x) {
  if (x[21] <= -0.862110f) {
    return 0;
  } else {
    if (x[16] <= -0.709012f) {
      return 1;
    } else {
      if (x[14] <= -0.595310f) {
        return 3;
      } else {
        return 2;
      }
    }
  }
}

static int tree_135(const float* x) {
  if (x[15] <= -0.642185f) {
    return 2;
  } else {
    if (x[17] <= -0.733664f) {
      return 3;
    } else {
      if (x[14] <= 0.585305f) {
        if (x[13] <= -0.741455f) {
          return 0;
        } else {
          return 0;
        }
      } else {
        return 1;
      }
    }
  }
}

static int tree_136(const float* x) {
  if (x[16] <= 0.508286f) {
    if (x[17] <= 0.429919f) {
      if (x[8] <= 0.055291f) {
        if (x[0] <= -1.266542f) {
          return 0;
        } else {
          return 0;
        }
      } else {
        return 1;
      }
    } else {
      if (x[3] <= -0.401839f) {
        return 2;
      } else {
        return 2;
      }
    }
  } else {
    if (x[13] <= -1.081705f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_137(const float* x) {
  if (x[8] <= 0.706586f) {
    if (x[0] <= -0.100223f) {
      if (x[20] <= -0.748163f) {
        if (x[5] <= -1.494001f) {
          return 0;
        } else {
          return 0;
        }
      } else {
        return 3;
      }
    } else {
      if (x[0] <= 0.201166f) {
        return 2;
      } else {
        return 2;
      }
    }
  } else {
    return 1;
  }
}

static int tree_138(const float* x) {
  if (x[2] <= -0.893074f) {
    return 0;
  } else {
    if (x[7] <= -0.039258f) {
      if (x[8] <= 0.710024f) {
        if (x[6] <= 0.211651f) {
          return 2;
        } else {
          return 2;
        }
      } else {
        return 1;
      }
    } else {
      if (x[18] <= 0.784959f) {
        if (x[17] <= -0.633479f) {
          if (x[20] <= -0.198106f) {
            return 3;
          } else {
            return 3;
          }
        } else {
          if (x[20] <= 0.152683f) {
            return 1;
          } else {
            return 1;
          }
        }
      } else {
        if (x[14] <= 0.829191f) {
          if (x[15] <= 0.481214f) {
            return 2;
          } else {
            return 3;
          }
        } else {
          if (x[10] <= -2.286011f) {
            return 1;
          } else {
            return 1;
          }
        }
      }
    }
  }
}

static int tree_139(const float* x) {
  if (x[16] <= 0.483039f) {
    if (x[14] <= 0.920393f) {
      if (x[16] <= -0.498691f) {
        return 2;
      } else {
        return 0;
      }
    } else {
      return 1;
    }
  } else {
    if (x[15] <= 1.327556f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_140(const float* x) {
  if (x[20] <= -0.903797f) {
    return 0;
  } else {
    if (x[14] <= -0.819472f) {
      return 3;
    } else {
      if (x[16] <= -0.707366f) {
        return 1;
      } else {
        return 2;
      }
    }
  }
}

static int tree_141(const float* x) {
  if (x[0] <= -0.100223f) {
    if (x[2] <= -0.329733f) {
      return 0;
    } else {
      return 3;
    }
  } else {
    if (x[17] <= 0.429919f) {
      return 1;
    } else {
      return 2;
    }
  }
}

static int tree_142(const float* x) {
  if (x[18] <= -0.862118f) {
    return 0;
  } else {
    if (x[14] <= -0.813404f) {
      return 3;
    } else {
      if (x[16] <= -0.709012f) {
        return 1;
      } else {
        return 2;
      }
    }
  }
}

static int tree_143(const float* x) {
  if (x[16] <= 0.508286f) {
    if (x[17] <= 0.429919f) {
      if (x[8] <= 0.069867f) {
        if (x[18] <= -1.572011f) {
          return 0;
        } else {
          return 0;
        }
      } else {
        return 1;
      }
    } else {
      if (x[20] <= -0.518540f) {
        return 2;
      } else {
        return 2;
      }
    }
  } else {
    if (x[13] <= -1.081705f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_144(const float* x) {
  if (x[20] <= -0.904602f) {
    return 0;
  } else {
    if (x[21] <= 0.931501f) {
      if (x[8] <= -0.337879f) {
        if (x[14] <= -0.536255f) {
          return 3;
        } else {
          if (x[21] <= -0.499036f) {
            return 2;
          } else {
            return 2;
          }
        }
      } else {
        if (x[3] <= 0.696578f) {
          if (x[20] <= -0.400781f) {
            return 2;
          } else {
            return 2;
          }
        } else {
          if (x[13] <= -4.160391f) {
            return 1;
          } else {
            return 1;
          }
        }
      }
    } else {
      if (x[2] <= 0.031356f) {
        return 2;
      } else {
        if (x[16] <= -0.796801f) {
          return 1;
        } else {
          return 1;
        }
      }
    }
  }
}

static int tree_145(const float* x) {
  if (x[8] <= 0.713604f) {
    if (x[15] <= -0.610874f) {
      return 2;
    } else {
      if (x[6] <= -0.834552f) {
        if (x[14] <= -0.767488f) {
          return 3;
        } else {
          if (x[15] <= -0.523406f) {
            return 0;
          } else {
            return 0;
          }
        }
      } else {
        if (x[14] <= -0.754702f) {
          if (x[21] <= -0.293704f) {
            return 3;
          } else {
            return 3;
          }
        } else {
          if (x[21] <= -1.050666f) {
            return 0;
          } else {
            return 0;
          }
        }
      }
    }
  } else {
    return 1;
  }
}

static int tree_146(const float* x) {
  if (x[17] <= 0.563775f) {
    if (x[21] <= -0.862110f) {
      return 0;
    } else {
      if (x[0] <= -0.089565f) {
        if (x[17] <= -1.425499f) {
          return 3;
        } else {
          return 3;
        }
      } else {
        return 1;
      }
    }
  } else {
    if (x[0] <= 0.176291f) {
      return 2;
    } else {
      return 2;
    }
  }
}

static int tree_147(const float* x) {
  if (x[3] <= 0.709468f) {
    if (x[14] <= 0.139497f) {
      if (x[16] <= 0.483154f) {
        return 0;
      } else {
        return 3;
      }
    } else {
      if (x[19] <= -0.598128f) {
        return 2;
      } else {
        return 2;
      }
    }
  } else {
    return 1;
  }
}

static int tree_148(const float* x) {
  if (x[16] <= -0.706664f) {
    return 1;
  } else {
    if (x[7] <= 0.124503f) {
      if (x[15] <= -0.610874f) {
        if (x[10] <= -3.120240f) {
          return 2;
        } else {
          return 2;
        }
      } else {
        return 0;
      }
    } else {
      if (x[17] <= -1.422888f) {
        return 3;
      } else {
        return 3;
      }
    }
  }
}

static int tree_149(const float* x) {
  if (x[6] <= -0.094860f) {
    if (x[8] <= -0.848588f) {
      if (x[15] <= 0.459756f) {
        return 0;
      } else {
        return 3;
      }
    } else {
      if (x[14] <= -0.758526f) {
        return 3;
      } else {
        return 0;
      }
    }
  } else {
    if (x[18] <= 0.421772f) {
      if (x[14] <= 0.990995f) {
        return 2;
      } else {
        if (x[7] <= -0.265147f) {
          return 1;
        } else {
          return 1;
        }
      }
    } else {
      if (x[8] <= 0.782780f) {
        return 2;
      } else {
        return 1;
      }
    }
  }
}

static int tree_150(const float* x) {
  if (x[8] <= 0.705888f) {
    if (x[17] <= 0.422944f) {
      if (x[7] <= -0.322698f) {
        if (x[21] <= -1.539394f) {
          return 0;
        } else {
          return 0;
        }
      } else {
        return 3;
      }
    } else {
      if (x[13] <= -1.944951f) {
        return 2;
      } else {
        return 2;
      }
    }
  } else {
    return 1;
  }
}

static int tree_151(const float* x) {
  if (x[14] <= -0.813404f) {
    return 3;
  } else {
    if (x[16] <= -0.706657f) {
      return 1;
    } else {
      if (x[7] <= -0.897143f) {
        return 0;
      } else {
        return 2;
      }
    }
  }
}

static int tree_152(const float* x) {
  if (x[21] <= -0.862223f) {
    return 0;
  } else {
    if (x[17] <= 0.556840f) {
      if (x[14] <= -0.170842f) {
        return 3;
      } else {
        return 1;
      }
    } else {
      if (x[3] <= -0.406806f) {
        return 2;
      } else {
        return 2;
      }
    }
  }
}

static int tree_153(const float* x) {
  if (x[3] <= 0.709468f) {
    if (x[16] <= 0.498030f) {
      if (x[18] <= -0.798109f) {
        if (x[16] <= -0.472464f) {
          return 0;
        } else {
          return 0;
        }
      } else {
        return 2;
      }
    } else {
      if (x[15] <= 1.340181f) {
        return 3;
      } else {
        return 3;
      }
    }
  } else {
    return 1;
  }
}

static int tree_154(const float* x) {
  if (x[18] <= -0.859706f) {
    return 0;
  } else {
    if (x[6] <= -0.100223f) {
      return 3;
    } else {
      if (x[19] <= 0.025190f) {
        if (x[8] <= 0.418919f) {
          return 2;
        } else {
          if (x[5] <= 1.602721f) {
            return 1;
          } else {
            return 1;
          }
        }
      } else {
        if (x[3] <= 0.783054f) {
          return 2;
        } else {
          return 1;
        }
      }
    }
  }
}

static int tree_155(const float* x) {
  if (x[14] <= 0.918099f) {
    if (x[20] <= -0.912748f) {
      return 0;
    } else {
      if (x[6] <= -0.094860f) {
        return 3;
      } else {
        return 2;
      }
    }
  } else {
    return 1;
  }
}

static int tree_156(const float* x) {
  if (x[15] <= -0.611011f) {
    return 2;
  } else {
    if (x[17] <= -0.725950f) {
      return 3;
    } else {
      if (x[21] <= -0.332506f) {
        if (x[13] <= -0.737523f) {
          return 0;
        } else {
          return 0;
        }
      } else {
        return 1;
      }
    }
  }
}

static int tree_157(const float* x) {
  if (x[14] <= -0.817133f) {
    return 3;
  } else {
    if (x[20] <= -0.903797f) {
      return 0;
    } else {
      if (x[7] <= -0.031081f) {
        if (x[14] <= 0.975793f) {
          return 2;
        } else {
          if (x[13] <= -4.088535f) {
            return 1;
          } else {
            return 1;
          }
        }
      } else {
        if (x[15] <= -0.665371f) {
          return 2;
        } else {
          return 1;
        }
      }
    }
  }
}

static int tree_158(const float* x) {
  if (x[21] <= -0.859262f) {
    return 0;
  } else {
    if (x[16] <= 0.508286f) {
      if (x[17] <= 0.425293f) {
        return 1;
      } else {
        return 2;
      }
    } else {
      if (x[12] <= -3.491110f) {
        return 3;
      } else {
        return 3;
      }
    }
  }
}

static int tree_159(const float* x) {
  if (x[17] <= -0.731542f) {
    return 3;
  } else {
    if (x[3] <= -0.540432f) {
      return 0;
    } else {
      if (x[16] <= -0.709012f) {
        return 1;
      } else {
        return 2;
      }
    }
  }
}

static int tree_160(const float* x) {
  if (x[20] <= -0.912748f) {
    return 0;
  } else {
    if (x[2] <= -0.032176f) {
      if (x[8] <= 0.713604f) {
        return 2;
      } else {
        if (x[17] <= 0.037311f) {
          return 1;
        } else {
          return 1;
        }
      }
    } else {
      if (x[17] <= -0.731542f) {
        if (x[0] <= -1.034972f) {
          return 3;
        } else {
          return 3;
        }
      } else {
        if (x[6] <= 1.832149f) {
          return 1;
        } else {
          if (x[10] <= 1.183878f) {
            return 2;
          } else {
            return 2;
          }
        }
      }
    }
  }
}

static int tree_161(const float* x) {
  if (x[6] <= -0.064863f) {
    if (x[21] <= -0.862110f) {
      if (x[3] <= -1.004024f) {
        return 0;
      } else {
        return 0;
      }
    } else {
      return 3;
    }
  } else {
    if (x[15] <= -0.642949f) {
      if (x[19] <= -0.542730f) {
        return 2;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_162(const float* x) {
  if (x[14] <= 0.935369f) {
    if (x[14] <= 0.155441f) {
      if (x[7] <= -0.612705f) {
        return 0;
      } else {
        if (x[17] <= -0.295707f) {
          return 3;
        } else {
          return 2;
        }
      }
    } else {
      if (x[8] <= -0.410734f) {
        return 2;
      } else {
        return 2;
      }
    }
  } else {
    return 1;
  }
}

static int tree_163(const float* x) {
  if (x[18] <= -0.862663f) {
    return 0;
  } else {
    if (x[6] <= -0.094860f) {
      return 3;
    } else {
      if (x[7] <= -0.026790f) {
        if (x[15] <= -0.611011f) {
          return 2;
        } else {
          if (x[3] <= 0.779815f) {
            return 1;
          } else {
            return 1;
          }
        }
      } else {
        if (x[14] <= 0.815961f) {
          return 2;
        } else {
          return 1;
        }
      }
    }
  }
}

static int tree_164(const float* x) {
  if (x[18] <= -0.862312f) {
    return 0;
  } else {
    if (x[21] <= 0.796271f) {
      if (x[20] <= 0.224057f) {
        if (x[15] <= -0.610717f) {
          if (x[4] <= -2.281665f) {
            return 2;
          } else {
            return 2;
          }
        } else {
          if (x[18] <= 0.002398f) {
            if (x[13] <= -1.054908f) {
              return 3;
            } else {
              return 3;
            }
          } else {
            if (x[17] <= 0.019293f) {
              return 1;
            } else {
              return 1;
            }
          }
        }
      } else {
        if (x[16] <= 0.415041f) {
          if (x[4] <= -0.552077f) {
            return 1;
          } else {
            return 2;
          }
        } else {
          if (x[21] <= -0.391999f) {
            return 3;
          } else {
            return 3;
          }
        }
      }
    } else {
      if (x[17] <= 0.617866f) {
        return 1;
      } else {
        if (x[14] <= 0.393286f) {
          return 2;
        } else {
          return 2;
        }
      }
    }
  }
}

static int tree_165(const float* x) {
  if (x[14] <= -0.815175f) {
    return 3;
  } else {
    if (x[14] <= 0.935596f) {
      if (x[20] <= -0.912748f) {
        return 0;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_166(const float* x) {
  if (x[7] <= -0.891972f) {
    return 0;
  } else {
    if (x[17] <= 0.555154f) {
      if (x[0] <= -0.079233f) {
        return 3;
      } else {
        return 1;
      }
    } else {
      if (x[13] <= -1.904170f) {
        return 2;
      } else {
        return 2;
      }
    }
  }
}

static int tree_167(const float* x) {
  if (x[0] <= -0.094860f) {
    if (x[20] <= -0.748163f) {
      return 0;
    } else {
      return 3;
    }
  } else {
    if (x[3] <= 0.713604f) {
      if (x[7] <= -0.864101f) {
        return 2;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_168(const float* x) {
  if (x[16] <= -0.497958f) {
    if (x[8] <= 0.729924f) {
      if (x[4] <= -2.246234f) {
        return 2;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  } else {
    if (x[2] <= -0.614560f) {
      if (x[19] <= -1.646416f) {
        return 0;
      } else {
        return 0;
      }
    } else {
      if (x[0] <= 0.190968f) {
        return 3;
      } else {
        return 2;
      }
    }
  }
}

static int tree_169(const float* x) {
  if (x[0] <= -0.100223f) {
    if (x[21] <= -0.859148f) {
      if (x[4] <= -2.328908f) {
        return 0;
      } else {
        return 0;
      }
    } else {
      return 3;
    }
  } else {
    if (x[15] <= -0.612826f) {
      if (x[17] <= 0.838872f) {
        return 2;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_170(const float* x) {
  if (x[14] <= -0.760086f) {
    return 3;
  } else {
    if (x[6] <= -0.330104f) {
      return 0;
    } else {
      if (x[16] <= -0.710021f) {
        return 1;
      } else {
        return 2;
      }
    }
  }
}

static int tree_171(const float* x) {
  if (x[16] <= 0.508286f) {
    if (x[18] <= -0.798109f) {
      return 0;
    } else {
      if (x[15] <= -0.611011f) {
        if (x[0] <= 0.193251f) {
          return 2;
        } else {
          return 2;
        }
      } else {
        return 1;
      }
    }
  } else {
    if (x[19] <= -0.208676f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_172(const float* x) {
  if (x[14] <= 0.918099f) {
    if (x[14] <= -0.813404f) {
      return 3;
    } else {
      if (x[0] <= -0.331140f) {
        if (x[15] <= -0.523158f) {
          return 0;
        } else {
          return 0;
        }
      } else {
        return 2;
      }
    }
  } else {
    return 1;
  }
}

static int tree_173(const float* x) {
  if (x[8] <= 0.709468f) {
    if (x[17] <= 0.556495f) {
      if (x[7] <= -0.329733f) {
        return 0;
      } else {
        return 3;
      }
    } else {
      if (x[5] <= -1.495767f) {
        return 2;
      } else {
        return 2;
      }
    }
  } else {
    return 1;
  }
}

static int tree_174(const float* x) {
  if (x[0] <= -0.094860f) {
    if (x[2] <= -0.329733f) {
      return 0;
    } else {
      return 3;
    }
  } else {
    if (x[19] <= 0.066356f) {
      if (x[16] <= -0.712170f) {
        return 1;
      } else {
        if (x[12] <= -1.410404f) {
          return 2;
        } else {
          return 2;
        }
      }
    } else {
      if (x[17] <= 0.560611f) {
        return 1;
      } else {
        return 2;
      }
    }
  }
}

static int tree_175(const float* x) {
  if (x[2] <= -0.892551f) {
    return 0;
  } else {
    if (x[16] <= 0.515311f) {
      if (x[13] <= -1.919132f) {
        return 1;
      } else {
        if (x[16] <= -0.712153f) {
          return 1;
        } else {
          return 2;
        }
      }
    } else {
      if (x[14] <= -1.543362f) {
        return 3;
      } else {
        return 3;
      }
    }
  }
}

static int tree_176(const float* x) {
  if (x[0] <= -0.085325f) {
    if (x[2] <= -0.331692f) {
      return 0;
    } else {
      return 3;
    }
  } else {
    if (x[15] <= -0.642185f) {
      if (x[14] <= 0.226265f) {
        return 2;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_177(const float* x) {
  if (x[7] <= -0.897350f) {
    return 0;
  } else {
    if (x[3] <= 0.710722f) {
      if (x[6] <= -0.094860f) {
        return 3;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_178(const float* x) {
  if (x[21] <= -0.862223f) {
    return 0;
  } else {
    if (x[0] <= -0.094860f) {
      return 3;
    } else {
      if (x[8] <= 0.696578f) {
        return 2;
      } else {
        return 1;
      }
    }
  }
}

static int tree_179(const float* x) {
  if (x[21] <= -0.862110f) {
    return 0;
  } else {
    if (x[3] <= 0.709468f) {
      if (x[16] <= 0.434772f) {
        return 2;
      } else {
        return 3;
      }
    } else {
      return 1;
    }
  }
}

static int tree_180(const float* x) {
  if (x[6] <= -0.089565f) {
    if (x[7] <= -0.322801f) {
      return 0;
    } else {
      return 3;
    }
  } else {
    if (x[16] <= -0.705654f) {
      return 1;
    } else {
      return 2;
    }
  }
}

static int tree_181(const float* x) {
  if (x[17] <= -0.731542f) {
    return 3;
  } else {
    if (x[17] <= 0.563775f) {
      if (x[16] <= -0.609217f) {
        return 1;
      } else {
        return 0;
      }
    } else {
      if (x[7] <= -0.859302f) {
        return 2;
      } else {
        return 2;
      }
    }
  }
}

static int tree_182(const float* x) {
  if (x[14] <= 0.935596f) {
    if (x[17] <= 0.424948f) {
      if (x[15] <= 0.468489f) {
        if (x[20] <= -1.640975f) {
          return 0;
        } else {
          return 0;
        }
      } else {
        return 3;
      }
    } else {
      if (x[6] <= 0.176291f) {
        return 2;
      } else {
        return 2;
      }
    }
  } else {
    return 1;
  }
}

static int tree_183(const float* x) {
  if (x[15] <= -0.640838f) {
    return 2;
  } else {
    if (x[0] <= -0.094928f) {
      if (x[18] <= -0.862118f) {
        return 0;
      } else {
        return 3;
      }
    } else {
      return 1;
    }
  }
}

static int tree_184(const float* x) {
  if (x[16] <= -0.705654f) {
    return 1;
  } else {
    if (x[14] <= -0.813404f) {
      return 3;
    } else {
      if (x[20] <= -0.903797f) {
        return 0;
      } else {
        return 2;
      }
    }
  }
}

static int tree_185(const float* x) {
  if (x[14] <= -0.813404f) {
    return 3;
  } else {
    if (x[8] <= -0.542026f) {
      return 0;
    } else {
      if (x[14] <= 0.935596f) {
        return 2;
      } else {
        return 1;
      }
    }
  }
}

static int tree_186(const float* x) {
  if (x[15] <= -0.612826f) {
    return 2;
  } else {
    if (x[16] <= -0.606579f) {
      return 1;
    } else {
      if (x[7] <= -0.329733f) {
        return 0;
      } else {
        return 3;
      }
    }
  }
}

static int tree_187(const float* x) {
  if (x[16] <= 0.507531f) {
    if (x[20] <= -0.904602f) {
      return 0;
    } else {
      if (x[17] <= 0.561466f) {
        return 1;
      } else {
        return 2;
      }
    }
  } else {
    if (x[18] <= -0.650390f) {
      return 3;
    } else {
      return 3;
    }
  }
}

static int tree_188(const float* x) {
  if (x[14] <= -0.760086f) {
    return 3;
  } else {
    if (x[16] <= -0.498691f) {
      if (x[3] <= 0.709468f) {
        if (x[7] <= -0.863371f) {
          return 2;
        } else {
          return 2;
        }
      } else {
        return 1;
      }
    } else {
      if (x[17] <= -0.152518f) {
        return 0;
      } else {
        return 0;
      }
    }
  }
}

static int tree_189(const float* x) {
  if (x[18] <= -0.862118f) {
    return 0;
  } else {
    if (x[0] <= -0.089565f) {
      return 3;
    } else {
      if (x[15] <= -0.612826f) {
        return 2;
      } else {
        return 1;
      }
    }
  }
}

static int tree_190(const float* x) {
  if (x[15] <= -0.611011f) {
    return 2;
  } else {
    if (x[8] <= 0.231973f) {
      if (x[21] <= -0.859262f) {
        return 0;
      } else {
        return 3;
      }
    } else {
      return 1;
    }
  }
}

static int tree_191(const float* x) {
  if (x[14] <= -0.761355f) {
    return 3;
  } else {
    if (x[3] <= 0.728180f) {
      if (x[3] <= -0.540432f) {
        return 0;
      } else {
        return 2;
      }
    } else {
      return 1;
    }
  }
}

static int tree_192(const float* x) {
  if (x[14] <= -0.813404f) {
    return 3;
  } else {
    if (x[20] <= -0.911943f) {
      return 0;
    } else {
      if (x[3] <= 0.709468f) {
        return 2;
      } else {
        return 1;
      }
    }
  }
}

static int tree_193(const float* x) {
  if (x[2] <= -0.897143f) {
    return 0;
  } else {
    if (x[3] <= 0.709468f) {
      if (x[2] <= 0.131245f) {
        return 2;
      } else {
        return 3;
      }
    } else {
      return 1;
    }
  }
}

static int tree_194(const float* x) {
  if (x[6] <= -0.094860f) {
    if (x[15] <= 0.468871f) {
      return 0;
    } else {
      return 3;
    }
  } else {
    if (x[18] <= 0.392908f) {
      if (x[7] <= -0.273205f) {
        return 2;
      } else {
        return 1;
      }
    } else {
      if (x[8] <= 0.761950f) {
        return 2;
      } else {
        return 1;
      }
    }
  }
}

static int tree_195(const float* x) {
  if (x[21] <= -0.859148f) {
    return 0;
  } else {
    if (x[17] <= 0.561466f) {
      if (x[3] <= 0.210810f) {
        if (x[4] <= -2.286915f) {
          return 3;
        } else {
          return 3;
        }
      } else {
        return 1;
      }
    } else {
      if (x[4] <= -2.277729f) {
        return 2;
      } else {
        return 2;
      }
    }
  }
}

static int tree_196(const float* x) {
  if (x[6] <= -0.094928f) {
    if (x[21] <= -0.859148f) {
      return 0;
    } else {
      return 3;
    }
  } else {
    if (x[17] <= 0.424549f) {
      return 1;
    } else {
      return 2;
    }
  }
}

static int tree_197(const float* x) {
  if (x[14] <= -0.813404f) {
    return 3;
  } else {
    if (x[6] <= -0.330104f) {
      return 0;
    } else {
      if (x[21] <= 0.862036f) {
        if (x[16] <= -0.708207f) {
          return 1;
        } else {
          if (x[15] <= -0.892148f) {
            return 2;
          } else {
            return 2;
          }
        }
      } else {
        if (x[0] <= 1.723670f) {
          return 1;
        } else {
          if (x[3] <= 0.469391f) {
            return 2;
          } else {
            return 2;
          }
        }
      }
    }
  }
}

static int tree_198(const float* x) {
  if (x[16] <= -0.709012f) {
    return 1;
  } else {
    if (x[15] <= -0.640702f) {
      return 2;
    } else {
      if (x[16] <= 0.507531f) {
        return 0;
      } else {
        return 3;
      }
    }
  }
}

static int tree_199(const float* x) {
  if (x[6] <= -0.094860f) {
    if (x[18] <= -0.859706f) {
      return 0;
    } else {
      return 3;
    }
  } else {
    if (x[12] <= 1.352965f) {
      if (x[8] <= 0.709468f) {
        return 2;
      } else {
        return 1;
      }
    } else {
      if (x[7] <= 0.274844f) {
        return 2;
      } else {
        return 1;
      }
    }
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
  tree_9,
  tree_10,
  tree_11,
  tree_12,
  tree_13,
  tree_14,
  tree_15,
  tree_16,
  tree_17,
  tree_18,
  tree_19,
  tree_20,
  tree_21,
  tree_22,
  tree_23,
  tree_24,
  tree_25,
  tree_26,
  tree_27,
  tree_28,
  tree_29,
  tree_30,
  tree_31,
  tree_32,
  tree_33,
  tree_34,
  tree_35,
  tree_36,
  tree_37,
  tree_38,
  tree_39,
  tree_40,
  tree_41,
  tree_42,
  tree_43,
  tree_44,
  tree_45,
  tree_46,
  tree_47,
  tree_48,
  tree_49,
  tree_50,
  tree_51,
  tree_52,
  tree_53,
  tree_54,
  tree_55,
  tree_56,
  tree_57,
  tree_58,
  tree_59,
  tree_60,
  tree_61,
  tree_62,
  tree_63,
  tree_64,
  tree_65,
  tree_66,
  tree_67,
  tree_68,
  tree_69,
  tree_70,
  tree_71,
  tree_72,
  tree_73,
  tree_74,
  tree_75,
  tree_76,
  tree_77,
  tree_78,
  tree_79,
  tree_80,
  tree_81,
  tree_82,
  tree_83,
  tree_84,
  tree_85,
  tree_86,
  tree_87,
  tree_88,
  tree_89,
  tree_90,
  tree_91,
  tree_92,
  tree_93,
  tree_94,
  tree_95,
  tree_96,
  tree_97,
  tree_98,
  tree_99,
  tree_100,
  tree_101,
  tree_102,
  tree_103,
  tree_104,
  tree_105,
  tree_106,
  tree_107,
  tree_108,
  tree_109,
  tree_110,
  tree_111,
  tree_112,
  tree_113,
  tree_114,
  tree_115,
  tree_116,
  tree_117,
  tree_118,
  tree_119,
  tree_120,
  tree_121,
  tree_122,
  tree_123,
  tree_124,
  tree_125,
  tree_126,
  tree_127,
  tree_128,
  tree_129,
  tree_130,
  tree_131,
  tree_132,
  tree_133,
  tree_134,
  tree_135,
  tree_136,
  tree_137,
  tree_138,
  tree_139,
  tree_140,
  tree_141,
  tree_142,
  tree_143,
  tree_144,
  tree_145,
  tree_146,
  tree_147,
  tree_148,
  tree_149,
  tree_150,
  tree_151,
  tree_152,
  tree_153,
  tree_154,
  tree_155,
  tree_156,
  tree_157,
  tree_158,
  tree_159,
  tree_160,
  tree_161,
  tree_162,
  tree_163,
  tree_164,
  tree_165,
  tree_166,
  tree_167,
  tree_168,
  tree_169,
  tree_170,
  tree_171,
  tree_172,
  tree_173,
  tree_174,
  tree_175,
  tree_176,
  tree_177,
  tree_178,
  tree_179,
  tree_180,
  tree_181,
  tree_182,
  tree_183,
  tree_184,
  tree_185,
  tree_186,
  tree_187,
  tree_188,
  tree_189,
  tree_190,
  tree_191,
  tree_192,
  tree_193,
  tree_194,
  tree_195,
  tree_196,
  tree_197,
  tree_198,
  tree_199
};

static int rf_predict(float mq2, float mq4, float mq7, float mq135,
                      float temp, float hum) {
  float raw[4]={mq2,mq4,mq7,mq135};
  if(!_init){rf_reset();_init=1;}

  /* EMA asymétrique : monte vite, descend lentement */
  for(int i=0;i<4;i++){
    if(_ema[i]<0.0f){_ema[i]=raw[i];continue;}
    float a=(raw[i]>_ema[i])?RF_EMA_RISE:RF_EMA_FALL;
    _ema[i]=a*raw[i]+(1.0f-a)*_ema[i];
  }

  /* Compensation T/H */
  float c[4];
  for(int i=0;i<4;i++){
    float F=1.0f+RF_AT[i]*(temp-RF_T_REF)+RF_AH[i]*(hum-RF_H_REF);
    if(F<0.70f)F=0.70f; if(F>1.40f)F=1.40f;
    c[i]=_ema[i]/F;
    if(c[i]<0.0f)c[i]=0.0f; if(c[i]>4095.0f)c[i]=4095.0f;
  }

  /* Dérivées temporelles */
  float d[4];
  for(int i=0;i<4;i++){d[i]=c[i]-_prev[i];_prev[i]=c[i];}

  /* Deltas par rapport aux baselines */
  float mq2_d  =c[0]-RF_B_MQ2;
  float mq7_d  =c[2]-RF_B_MQ7;
  float mq135_d=c[3]-RF_B_MQ135;
  float mq4_f  =(c[1]>10.0f)?1.0f:0.0f;

  /* Rapports inter-capteurs */
  float R_MQ135_MQ7 = c[3]/(c[2]+1e-6f);
  float R_MQ7_MQ2   = c[2]/(c[0]+1e-6f);
  float R_MQ7_MQ135 = c[2]/(c[3]+1e-6f);
  float R_MQ2_MQ7   = c[0]/(c[2]+1e-6f);

  /* Stats globales */
  float sum_c=c[0]+c[1]+c[2]+c[3];
  float mean4=sum_c/4.0f;
  float var=0.0f;
  for(int i=0;i<4;i++) var+=(c[i]-mean4)*(c[i]-mean4);
  float std_c=sqrtf(var/4.0f);
  float max_c=c[0];
  for(int i=1;i<4;i++) if(c[i]>max_c) max_c=c[i];
  float gi=c[0]*0.25f+c[1]*0.20f+c[2]*0.25f+c[3]*0.30f;

  /* Vecteur features [22] */
  float x[RF_N_FEATURES]={
    c[0],c[1],c[2],c[3],
    temp,hum,
    mq2_d,mq7_d,mq135_d,mq4_f,
    d[0],d[1],d[2],d[3],
    R_MQ135_MQ7,R_MQ7_MQ2,R_MQ7_MQ135,R_MQ2_MQ7,
    sum_c,std_c,max_c,gi
  };

  /* Normalisation Z-Score */
  for(int i=0;i<RF_N_FEATURES;i++)
    x[i]=(x[i]-RF_MEAN[i])/RF_STD[i];

  /* Vote Random Forest */
  int votes[RF_N_CLASSES]={0};
  for(int t=0;t<RF_N_TREES;t++){
    int cls=_trees[t](x);
    if(cls>=0&&cls<RF_N_CLASSES) votes[cls]++;
  }
  int raw_cls=0;
  for(int i=1;i<RF_N_CLASSES;i++)
    if(votes[i]>votes[raw_cls]) raw_cls=i;

  /* Filtre majoritaire sur RF_CONFIRM_N lectures */
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
