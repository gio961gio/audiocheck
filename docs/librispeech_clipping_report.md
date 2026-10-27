# AudioCheck — Rapporto di Validazione su Degraded LibriSpeech

**Data Benchmark:** 2026-10-27 06:55:24 UTC  
**Fonte Dataset:** Zenodo [10.5281/zenodo.8380442](https://zenodo.org/records/8380442) (Alessandro Ragano, Jan Skoglund, Andrew Hines - ICASSP 2024)  
**Tassonomia Ground Truth:** `controlled_transform_label`  

## 1. Risultati della Classificazione Statistica

- **Campioni analizzati:** 45 file audio parlato reale (20 clean, 25 clipped).
- **Accuratezza Globale:** **97.8%**
- **Precisione (Precision):** **100.0%**
- **Richiamo (Recall):** **96.0%**
- **Specificità (Specificity):** **100.0%**
- **F1-Score:** **0.980**

### Matrice di Confusione

| | Clipping Effettivo (GT Positive) | Clean Effettivo (GT Negative) |
| :--- | :---: | :---: |
| **Rilevato Clipping (Pred. Positive)** | **24 (True Positive)** | 0 (False Positive) |
| **Rilevato Pulito (Pred. Negative)** | 1 (False Negative) | **20 (True Negative)** |

## 2. Rilevanza Metrologica: Clipping a 0 dBFS vs Clipping Pre-Gain (Plateau Sub-Threshold)

Questo benchmark dimostra sperimentalmente una distinzione fondamentale evidenziata nel brief metrologico:
- **Clipping Full-Scale (0 dBFS Brickwall):** Si verifica quando il segnale supera il fondo scala del convertitore A/D o del bus a virgola fissa (saturazione flat-top $N \ge 3$ a $0.0\text{ dBFS}$).
- **Clipping Sub-Threshold (Scalato/Pre-Gain):** In Degraded LibriSpeech, le forme d'onda sono state clippate e successivamente **normalizzate in loudness a standard EBU R128**. I campioni piatti (plateau) rimangono identici nel tempo (differenza prima $\Delta x = 0$), ma l'ampiezza massima è scalata tra $-11\text{ dBTP}$ e $-16\text{ dBTP}$.
- Un rilevatore basato esclusivamente sulla soglia $0\text{ dBFS}$ non segnala campioni full-scale su file scalati, mentre l'algoritmo di **Plateau Analysis** isola la vera distorsione da clipping con accuratezza elevatissima e zero falsi positivi su parlato naturale pulito.

## 3. Dettaglio per File Analizzato

| File Audio | SHA-256 (Primi 8 car.) | Condizione GT | True Peak (dBTP) | Full-Scale Clip (0 dBFS) | Plateau Ratio (%) | Classificazione |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `clean_3830-12531-0011.wav` | `a5a15131` | `clean` | -2.08 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0013.wav` | `d63d15c3` | `clean` | -6.47 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0023.wav` | `b5129b4f` | `clean` | -6.05 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0022.wav` | `3baded42` | `clean` | -5.69 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0024.wav` | `9889a6df` | `clean` | -4.38 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0005.wav` | `ecdf68b1` | `clean` | -3.99 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0029.wav` | `458db4fc` | `clean` | -3.80 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0007.wav` | `6026ab5c` | `clean` | -6.10 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0019.wav` | `1b595147` | `clean` | -4.65 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0004.wav` | `a9496ae4` | `clean` | -4.55 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0025.wav` | `f45c8897` | `clean` | -5.82 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0006.wav` | `2d770806` | `clean` | -4.02 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0001.wav` | `2a57507a` | `clean` | -2.86 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0009.wav` | `1a395066` | `clean` | -5.27 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0003.wav` | `9ad58d8a` | `clean` | -4.56 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0017.wav` | `2f6bf02f` | `clean` | -2.86 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0002.wav` | `70486e6b` | `clean` | -5.36 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0030.wav` | `80da2956` | `clean` | -8.59 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0000.wav` | `dac23245` | `clean` | -5.99 | 0 | 0.00% | **TN (Pass)** |
| `clean_3830-12531-0031.wav` | `f65bd95e` | `clean` | -6.81 | 0 | 0.00% | **TN (Pass)** |
| `clip_5pct_27-124992-0006_CLIP_5.wav` | `a3f1057c` | `clipping_5pct` | -11.77 | 0 | 4.21% | **TP (Pass)** |
| `clip_25pct_89-219-0022_CLIP_25.wav` | `8be3a1f1` | `clipping_25pct` | -14.26 | 0 | 24.20% | **TP (Pass)** |
| `clip_40pct_8580-287364-0022_CLIP_40.wav` | `ef553a42` | `clipping_40pct` | -13.63 | 0 | 33.69% | **TP (Pass)** |
| `clip_40pct_5163-39921-0017_CLIP_40.wav` | `09cea030` | `clipping_40pct` | -14.81 | 0 | 34.71% | **TP (Pass)** |
| `clip_10pct_8975-270782-0047_CLIP_10.wav` | `75515aea` | `clipping_10pct` | -11.89 | 0 | 6.80% | **TP (Pass)** |
| `clip_5pct_5390-24512-0011_CLIP_5.wav` | `9d86a9ef` | `clipping_5pct` | -13.21 | 0 | 4.74% | **TP (Pass)** |
| `clip_25pct_89-219-0052_CLIP_25.wav` | `60367a79` | `clipping_25pct` | -14.28 | 0 | 24.30% | **TP (Pass)** |
| `clip_40pct_322-124147-0063_CLIP_40.wav` | `fbb81f60` | `clipping_40pct` | -14.67 | 0 | 31.74% | **TP (Pass)** |
| `clip_60pct_125-121124-0014_CLIP_60.wav` | `df3b2063` | `clipping_60pct` | -15.73 | 0 | 42.62% | **TP (Pass)** |
| `clip_5pct_7794-295947-0007_CLIP_5.wav` | `ea40b539` | `clipping_5pct` | -12.04 | 0 | 3.90% | **TP (Pass)** |
| `clip_25pct_1040-133433-0059_CLIP_25.wav` | `c299f3e9` | `clipping_25pct` | -14.12 | 0 | 21.82% | **TP (Pass)** |
| `clip_40pct_5867-48852-0084_CLIP_40.wav` | `b2f787dd` | `clipping_40pct` | -12.65 | 0 | 37.14% | **TP (Pass)** |
| `clip_10pct_4018-107312-0006_CLIP_10.wav` | `0d56bead` | `clipping_10pct` | -13.37 | 0 | 9.79% | **TP (Pass)** |
| `clip_60pct_8975-270782-0034_CLIP_60.wav` | `556c7843` | `clipping_60pct` | -15.59 | 0 | 44.12% | **TP (Pass)** |
| `clip_40pct_311-124404-0052_CLIP_40.wav` | `fffb1900` | `clipping_40pct` | -14.33 | 0 | 31.56% | **TP (Pass)** |
| `clip_25pct_5867-48852-0042_CLIP_25.wav` | `8cbdfc9b` | `clipping_25pct` | -14.70 | 0 | 24.39% | **TP (Pass)** |
| `clip_60pct_1963-147036-0011_CLIP_60.wav` | `4a0ca42e` | `clipping_60pct` | -15.82 | 0 | 46.03% | **TP (Pass)** |
| `clip_60pct_1235-135884-0025_CLIP_60.wav` | `302d26b5` | `clipping_60pct` | -15.04 | 0 | 51.33% | **TP (Pass)** |
| `clip_25pct_89-219-0010_CLIP_25.wav` | `57c1dbfd` | `clipping_25pct` | -15.17 | 0 | 24.57% | **TP (Pass)** |
| `clip_10pct_7794-295948-0013_CLIP_10.wav` | `ef8c040c` | `clipping_10pct` | -11.77 | 0 | 8.93% | **TP (Pass)** |
| `clip_60pct_322-124147-0041_CLIP_60.wav` | `be3c9029` | `clipping_60pct` | -14.76 | 0 | 52.02% | **TP (Pass)** |
| `clip_5pct_5163-39921-0023_CLIP_5.wav` | `61830222` | `clipping_5pct` | -11.06 | 0 | 4.43% | **TP (Pass)** |
| `clip_10pct_5703-47198-0002_CLIP_10.wav` | `89c34d36` | `clipping_10pct` | -12.09 | 0 | 9.77% | **TP (Pass)** |
| `clip_5pct_311-124404-0078_CLIP_5.wav` | `fe09932a` | `clipping_5pct` | -9.82 | 0 | 4.30% | **TP (Pass)** |
| `clip_10pct_3830-12535-0019_CLIP_10.wav` | `3b82f39e` | `clipping_10pct` | -12.21 | 0 | 0.00% | **FN (Fail)** |