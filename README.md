# 🔬 Détection et Identification des Gaz par Machine Learning

![Python](https://img.shields.io/badge/Python-3.10-blue)
![ESP32](https://img.shields.io/badge/ESP32-Arduino-red)
![License](https://img.shields.io/badge/License-MIT-green)

## 👨‍🎓 Informations académiques

| | |
|---|---|
| **Établissement** | Université Mouloud Mammeri de Tizi-Ouzou (UMMTO) |
| **Faculté** | Génie Électrique et Informatique |
| **Département** | Électronique |
| **Spécialité** | Électronique des Systèmes Embarqués |
| **Auteurs** | YOUNSI Mohamed & HENNAD Samir |
| **Promotion** | 2025/2026 |

---

## 📌 Description

Système embarqué de détection et classification des gaz
(Air Pur, CO, CH₄, Fumée) à base de capteurs MOS série MQ
et d'algorithmes de Machine Learning déployés sur ESP32.

---

## 🏆 Résultats obtenus

| Modèle | Précision | Temps d'entraînement |
|--------|-----------|----------------------|
| KNN | 95.13 % | 0.5 s |
| SVM | 95.60 % | 0.64 s |
| MLP | 95.60 % | 5.57 s |
| **Random Forest** | **99.58 %** | **1.32 s** |

---

## 🛠️ Matériel utilisé

| Composant | Référence |
|-----------|-----------|
| Microcontrôleur | ESP32 |
| Capteur fumée / GPL | MQ-2 |
| Capteur méthane | MQ-4 |
| Capteur CO | MQ-7 |
| Capteur qualité d'air | MQ-135 |
| Capteur T° / Humidité | AHT21 |
| Afficheur | LCD 16×2 (I²C) |

---

## 📁 Structure du projet
gas-detection-MOS-ESP32/
├── Python_Colab/
├── Arduino_ESP32/
├── Dataset/
└── Results/

---

## 📊 Dataset

Feed Dataset — ThingSpeak Channel 3101098
🔗 https://thingspeak.mathworks.com/channels/3101098

---

## 📚 Références principales

- Kingma & Ba (2015) — Adam: A Method for Stochastic Optimization
- Goodfellow et al. (2016) — Deep Learning — MIT Press
- Pedregosa et al. (2011) — Scikit-learn — JMLR vol. 12

---

## 📄 Licence
Ce projet est sous licence MIT
