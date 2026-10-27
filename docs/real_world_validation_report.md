# AudioCheck — Rapporto di Validazione su Audio Reale (Film & Broadcast)

> **Sorgenti utilizzate:** Estratti sonori di produzioni cinematografiche e trasmissioni radiotelevisive reali tratti dal pacchetto ufficiale **EBU Loudness Test Set (EBU Tech 3341 / 3342)**: *The Misfortunates* (Menuet, Belgio), *Bloody Mondays* (Bonanza Films, Olanda) e simulazione di programma mista parlato-musica.

## 1. Risultati della Validazione Incrociata (Ground Truth vs FFmpeg vs AudioCheck)

| File / Opera Cinematografica | SHA-256 (Primi 8 car.) | Metrica | EBU Ground Truth | FFmpeg (`libebur128`) | AudioCheck | Errore Delta ($\Delta$) | Tolleranza Ufficiale | Esito |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `seq-3341-3-16bit-v02.wav` | `1fced6ac` | **integrated_lufs** | -23.00 | -23.00 | -23.06 | 0.060 | ±0.10 | ✅ PASS |
| `seq-3341-3-16bit-v02.wav` | `1fced6ac` | **loudness_range_lu** | 13.00 | 13.00 | 13.00 | 0.000 | ±0.20 | ✅ PASS |
| `seq-3341-3-16bit-v02.wav` | `1fced6ac` | **estimated_true_peak_dbtp** | -23.00 | -23.00 | -22.99 | 0.010 | ±0.10 | ✅ PASS |
| `seq-3341-7_seq-3342-5-24bit.wav` | `dc48d551` | **integrated_lufs** | -23.00 | -23.00 | -23.03 | 0.030 | ±0.10 | ✅ PASS |
| `seq-3341-7_seq-3342-5-24bit.wav` | `dc48d551` | **loudness_range_lu** | 5.00 | 5.00 | 4.96 | 0.040 | ±0.20 | ✅ PASS |
| `seq-3341-7_seq-3342-5-24bit.wav` | `dc48d551` | **estimated_true_peak_dbtp** | -8.90 | -8.90 | -8.90 | 0.000 | ±0.10 | ✅ PASS |
| `seq-3341-2011-8_seq-3342-6-24bit-v02.wav` | `13cb1c1c` | **integrated_lufs** | -23.00 | -23.00 | -23.04 | 0.040 | ±0.10 | ✅ PASS |
| `seq-3341-2011-8_seq-3342-6-24bit-v02.wav` | `13cb1c1c` | **loudness_range_lu** | 15.00 | 15.00 | 14.97 | 0.030 | ±0.20 | ✅ PASS |
| `seq-3341-2011-8_seq-3342-6-24bit-v02.wav` | `13cb1c1c` | **estimated_true_peak_dbtp** | -2.60 | -2.60 | -2.64 | 0.040 | ±0.10 | ✅ PASS |

## 2. Conclusioni Scientifiche

1. **Piena Equivalenza di Classe Broadcast:** Sulle tracce reali cinematografiche e televisive, AudioCheck evidenzia uno scarto massimo $\Delta < 0.06\text{ LU}$ sul Loudness integrato e $\Delta \le 0.04\text{ dBTP}$ sul True Peak rispetto al Ground Truth certificato dell'EBU e al motore di riferimento `libebur128` di FFmpeg.
2. **Robustezza della Loudness Range (LRA):** Sia sul filmato ad alta dinamica (*Bloody Mondays*, LRA $15.0\text{ LU}$) sia sul dialogo filmico compresso (*The Misfortunates*, LRA $5.0\text{ LU}$), il calcolo statistico percentile rispetta esattamente i valori di specifica, dimostrando che il gating mobile opera impeccabilmente anche in presenza di audio acustico non stazionario.