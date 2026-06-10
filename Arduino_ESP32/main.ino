/*
 * ╔══════════════════════════════════════════════════════════════╗
 * ║  ESP32 — Surveillance Gaz + T/H  — VERSION FINALE           ║
 * ║  Capteurs : AHT21 (I2C) + MQ2 + MQ4 + MQ7 + MQ135         ║
 * ║  Classification : Random Forest embarqué (rf_gaz.h)         ║
 * ║                                                              ║
 * ║  ⚠️  CE CODE NÉCESSITE OBLIGATOIREMENT : rf_gaz.h           ║
 * ║  rf_gaz.h est généré par : train_rf_gaz.py                  ║
 * ║  Modèle : Random Forest (200 arbres, précision 99.58%)      ║
 * ║  Classes : 0=Air Pur | 1=CH4 | 2=Fumée | 3=CO              ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 *  Câblage :
 *  ┌─────────────┬───────────┬────────────────────────────────┐
 *  │ Composant   │ GPIO ESP32│ Remarque                       │
 *  ├─────────────┼───────────┼────────────────────────────────┤
 *  │ AHT21 SDA   │ GPIO 21   │ I2C – pull-up 4.7 kΩ sur 3.3V │
 *  │ AHT21 SCL   │ GPIO 22   │ I2C – pull-up 4.7 kΩ sur 3.3V │
 *  │ LCD  SDA    │ GPIO 21   │ I2C partagé avec AHT21         │
 *  │ LCD  SCL    │ GPIO 22   │ I2C partagé avec AHT21         │
 *  │ MQ2  AOUT   │ GPIO 34   │ Diviseur de tension → 3.3V     │
 *  │ MQ4  AOUT   │ GPIO 35   │ Diviseur de tension → 3.3V     │
 *  │ MQ7  AOUT   │ GPIO 32   │ Diviseur de tension → 3.3V     │
 *  │ MQ135 AOUT  │ GPIO 33   │ Diviseur de tension → 3.3V     │
 *  └─────────────┴───────────┴────────────────────────────────┘
 *
 *  Bibliothèques requises :
 *  - Adafruit AHTX0
 *  - Adafruit BusIO
 *  - LiquidCrystal_I2C
 *
 *  ⚠️  Placer rf_gaz.h dans le même dossier que ce fichier .ino
 */

// ── Bibliothèques ─────────────────────────────────────────────────
#include <Wire.h>                // Communication I2C (AHT21 + LCD)
#include <Adafruit_AHTX0.h>     // Capteur température/humidité AHT21
#include <LiquidCrystal_I2C.h>  // Afficheur LCD 16x2 via I2C
#include "rf_gaz.h"             // Modèle Random Forest embarqué

// ── Broches des capteurs MOS ──────────────────────────────────────
#define PIN_MQ2    34   // Capteur fumée / GPL
#define PIN_MQ4    35   // Capteur méthane (CH4)
#define PIN_MQ7    32   // Capteur monoxyde de carbone (CO)
#define PIN_MQ135  33   // Capteur qualité d'air général
#define SDA_PIN    21   // Ligne de données I2C
#define SCL_PIN    22   // Ligne d'horloge I2C

// ── Timing ───────────────────────────────────────────────────────
#define INTERVAL_MS  1500    // Intervalle entre deux mesures (1.5 s)
#define WARMUP_MS    30000UL // Préchauffage capteurs MOS (30 s)

// ── Filtre majoritaire ───────────────────────────────────────────
// Evite les fausses détections : on garde la classe
// la plus fréquente sur les 5 dernières lectures
#define VOTE_WINDOW  5

// ── Baselines air pur ────────────────────────────────────────────
// Valeurs de référence des capteurs en air propre
// Utilisées pour calculer le delta (variation par rapport à l'air pur)
#define RF_MQ2_BASE    400.0f
#define RF_MQ4_BASE      0.0f
#define RF_MQ7_BASE    369.0f
#define RF_MQ135_BASE  312.0f

// ── Objets matériels ─────────────────────────────────────────────
Adafruit_AHTX0 aht;                    // Capteur AHT21
LiquidCrystal_I2C lcd(0x27, 16, 2);   // LCD 16x2, adresse I2C = 0x27

// ── Buffer du filtre majoritaire ─────────────────────────────────
static int     _vote_buf[VOTE_WINDOW] = {0};
static uint8_t _vote_idx  = 0;
static bool    _vote_full = false;

// ── Prototypes des fonctions ──────────────────────────────────────
float lire_adc(uint8_t pin);
int   filtre_majoritaire(int classe);
void  afficher_bandeau();
void  afficher_lcd(float temp, float hum, int classe);
void  afficher_serie(float temp, float hum,
                     float mq2, float mq4, float mq7, float mq135,
                     int classe);

// ════════════════════════════════════════════════════════════════
// reset_vote : remet à zéro le filtre majoritaire local
// (les EMA internes de rf_gaz.h sont gérées par rf_reset())
static void reset_vote() {
  for (int i = 0; i < VOTE_WINDOW; i++) _vote_buf[i] = 0;
  _vote_idx  = 0;
  _vote_full = false;
}

// ════════════════════════════════════════════════════════════════
void setup() {

  // ── Initialisation communication série (débogage) ────────────
  Serial.begin(115200);
  delay(500);

  // ── Initialisation bus I2C ────────────────────────────────────
  Wire.begin(SDA_PIN, SCL_PIN);

  // ── Initialisation LCD 16x2 ───────────────────────────────────
  lcd.init();          // Démarre le LCD
  lcd.backlight();     // Active le rétroéclairage
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("  Gaz Detector  ");
  lcd.setCursor(0, 1);
  lcd.print(" Initialisation ");
  delay(2000);

  // ── Initialisation AHT21 ──────────────────────────────────────
  if (!aht.begin()) {
    Serial.println(F("[ERREUR] AHT21 non détecté !"));
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("ERREUR AHT21 !");
    while (true) delay(1000); // Arrêt si capteur absent
  }
  Serial.println(F("[OK] AHT21 initialisé"));

  // ── Configuration ADC ESP32 ───────────────────────────────────
  analogSetAttenuation(ADC_11db);  // Plage 0 - 3.3V
  analogReadResolution(12);        // Résolution 12 bits (0 - 4095)

  // ── Réinitialisation du modèle RF et du filtre ────────────────
  rf_reset();    // Remet à zéro les EMA internes de rf_gaz.h
  reset_vote();  // Remet à zéro le filtre majoritaire local

  afficher_bandeau();

  // ── Préchauffage des capteurs MOS (30 secondes) ───────────────
  // Les capteurs MOS nécessitent un temps de chauffe
  // pour stabiliser leur résistance interne
  Serial.println(F("[INFO] Préchauffage 30 s en cours..."));
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Prechauffage...");

  unsigned long t0 = millis();
  uint8_t tick = 0;
  while (millis() - t0 < WARMUP_MS) {
    delay(1000);
    tick++;
    Serial.print(tick);
    Serial.print(F("s "));

    // Affichage du compte à rebours sur le LCD
    lcd.setCursor(0, 1);
    lcd.print("Reste: ");
    lcd.print(30 - tick);
    lcd.print(" s   ");
  }

  Serial.println(F("\n[OK] Préchauffage terminé — démarrage classification"));
  Serial.println();

  // ── Redémarrage propre après préchauffage ─────────────────────
  rf_reset();
  reset_vote();

  // Message de démarrage sur LCD
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("  Systeme pret  ");
  lcd.setCursor(0, 1);
  lcd.print(" Classification ");
  delay(2000);
  lcd.clear();
}

// ════════════════════════════════════════════════════════════════
void loop() {

  // ── Contrôle du timing ────────────────────────────────────────
  // On exécute une mesure toutes les INTERVAL_MS millisecondes
  static unsigned long dernierTemps = 0;
  unsigned long maintenant = millis();
  if (maintenant - dernierTemps < INTERVAL_MS) return;
  dernierTemps = maintenant;

  // ── Lecture température et humidité (AHT21) ───────────────────
  sensors_event_t humidity_evt, temp_evt;
  aht.getEvent(&humidity_evt, &temp_evt);
  float temperature = temp_evt.temperature;
  float humidite    = humidity_evt.relative_humidity;

  // ── Lecture capteurs gaz (moyenne de 16 échantillons) ─────────
  // La moyenne réduit le bruit de l'ADC de l'ESP32
  float mq2   = lire_adc(PIN_MQ2);
  float mq4   = lire_adc(PIN_MQ4);
  float mq7   = lire_adc(PIN_MQ7);
  float mq135 = lire_adc(PIN_MQ135);

  // ── Classification par Random Forest ──────────────────────────
  // rf_predict() applique en interne :
  // 1. Lissage EMA
  // 2. Compensation température/humidité
  // 3. Extraction des 16 features
  // 4. Normalisation Z-Score
  // 5. Vote majoritaire des 200 arbres
  int classe = filtre_majoritaire(
    rf_predict(mq2, mq4, mq7, mq135, temperature, humidite)
  );

  // ── Affichage des résultats ────────────────────────────────────
  afficher_lcd(temperature, humidite, classe);
  afficher_serie(temperature, humidite, mq2, mq4, mq7, mq135, classe);
}

// ════════════════════════════════════════════════════════════════
// lire_adc : lecture ADC avec moyenne sur 16 échantillons
// Réduit le bruit de conversion analogique-numérique
float lire_adc(uint8_t pin) {
  uint32_t somme = 0;
  for (uint8_t i = 0; i < 16; i++) {
    somme += analogRead(pin);
    delayMicroseconds(100);
  }
  return (float)(somme >> 4); // Division par 16
}

// ════════════════════════════════════════════════════════════════
// filtre_majoritaire : retourne la classe la plus fréquente
// sur les VOTE_WINDOW (5) dernières prédictions
// Evite les changements de classe dus au bruit des capteurs
int filtre_majoritaire(int classe) {
  _vote_buf[_vote_idx] = classe;
  _vote_idx = (_vote_idx + 1) % VOTE_WINDOW;
  if (_vote_idx == 0) _vote_full = true;

  int taille = _vote_full ? VOTE_WINDOW : _vote_idx;
  int comptes[RF_N_CLASSES] = {0};
  for (int i = 0; i < taille; i++) {
    int c = _vote_buf[i];
    if (c >= 0 && c < RF_N_CLASSES) comptes[c]++;
  }
  int best = 0;
  for (int i = 1; i < RF_N_CLASSES; i++)
    if (comptes[i] > comptes[best]) best = i;
  return best;
}

// ════════════════════════════════════════════════════════════════
// afficher_lcd : affiche température, humidité et gaz détecté
// sur l'écran LCD 16x2
//
//  Ligne 1 : T:25.3C  H:60%
//  Ligne 2 : GAZ: Air Pur
void afficher_lcd(float temp, float hum, int classe) {

  // ── Ligne 1 : Température et Humidité ────────────────────────
  lcd.setCursor(0, 0);
  lcd.print("T:");
  lcd.print(temp, 1);
  lcd.print((char)223); // Symbole degré °
  lcd.print("C H:");
  lcd.print((int)hum);
  lcd.print("%   ");

  // ── Ligne 2 : Gaz détecté avec alerte ────────────────────────
  lcd.setCursor(0, 1);
  switch (classe) {
    case 0:
      lcd.print("GAZ: Air Pur    ");
      break;
    case 1:
      lcd.print("! DANGER: CH4 ! ");
      break;
    case 2:
      lcd.print("! ALERTE: Fumee!");
      break;
    case 3:
      lcd.print("! DANGER: CO !  ");
      break;
    default:
      lcd.print("GAZ: Inconnu    ");
      break;
  }
}

// ════════════════════════════════════════════════════════════════
// afficher_bandeau : entête affiché une seule fois au démarrage
// dans le moniteur série
void afficher_bandeau() {
  Serial.println();
  Serial.println(F("╔══════════════════════════════════════════════════════════╗"));
  Serial.println(F("║   ESP32 — Surveillance Gaz RF v3                         ║"));
  Serial.println(F("║   AHT21 | MQ2 | MQ4 | MQ7 | MQ135 | LCD 16x2           ║"));
  Serial.println(F("║   Classes : Air Pur | CH4 | Fumée | CO                   ║"));
  Serial.println(F("╚══════════════════════════════════════════════════════════╝"));
  Serial.println();
  Serial.println(F("ms       | T(°C)| H(%)| MQ2  | MQ4  | MQ7  |MQ135 | GAZ PRÉDIT"));
  Serial.println(F("─────────────────────────────────────────────────────────────────"));
}

// ════════════════════════════════════════════════════════════════
// afficher_serie : affiche les mesures dans le moniteur série
// Toutes les 10 mesures, un résumé complet est affiché
void afficher_serie(float temp, float hum,
                    float mq2, float mq4, float mq7, float mq135,
                    int classe) {

  // ── Message d'alerte selon la classe détectée ─────────────────
  const char* alerte;
  switch (classe) {
    case 0:  alerte = "  [OK]";                          break;
    case 1:  alerte = "  [!] ATTENTION : CH4 detecte";  break;
    case 2:  alerte = "  [!] ATTENTION : Fumee";         break;
    case 3:  alerte = "  [!] DANGER    : CO detecte";    break;
    default: alerte = "  [?]";                           break;
  }

  // ── Affichage ligne par ligne ─────────────────────────────────
  Serial.print(millis());
  Serial.print(F(" | "));
  Serial.print(temp, 1);
  Serial.print(F(" | "));
  Serial.print(hum, 0);
  Serial.print(F(" | "));
  Serial.print((int)mq2);
  Serial.print(F(" | "));
  Serial.print((int)mq4);
  Serial.print(F(" | "));
  Serial.print((int)mq7);
  Serial.print(F(" | "));
  Serial.print((int)mq135);
  Serial.print(F(" | "));
  Serial.print(rf_class_name(classe));
  Serial.println(alerte);

  // ── Résumé complet toutes les 10 mesures ──────────────────────
  static uint8_t compteur = 0;
  if (++compteur >= 10) {
    compteur = 0;
    Serial.println();
    Serial.println(F("┌──────────────── RÉSUMÉ ─────────────────────────┐"));
    Serial.print(F("│  Température  : ")); Serial.print(temp, 2); Serial.println(F(" °C"));
    Serial.print(F("│  Humidité     : ")); Serial.print(hum, 1);  Serial.println(F(" %"));
    Serial.print(F("│  MQ2  (Fumée) : ")); Serial.print((int)mq2);
    Serial.print(F("  [delta: ")); Serial.print(mq2 - RF_MQ2_BASE, 0); Serial.println(F("]"));
    Serial.print(F("│  MQ4  (CH4)   : ")); Serial.print((int)mq4);
    Serial.print(F("  [delta: ")); Serial.print(mq4 - RF_MQ4_BASE, 0); Serial.println(F("]"));
    Serial.print(F("│  MQ7  (CO)    : ")); Serial.print((int)mq7);
    Serial.print(F("  [delta: ")); Serial.print(mq7 - RF_MQ7_BASE, 0); Serial.println(F("]"));
    Serial.print(F("│  MQ135        : ")); Serial.print((int)mq135);
    Serial.print(F("  [delta: ")); Serial.print(mq135 - RF_MQ135_BASE, 0); Serial.println(F("]"));
    Serial.print(F("│  ► GAZ PRÉDIT : ")); Serial.print(rf_class_name(classe));
    Serial.println(alerte);
    Serial.println(F("└─────────────────────────────────────────────────┘"));
    Serial.println();
  }
}
