# Bergforankring – beregningsverktøy v2

## Filer
- `beregning.py` – beregningsmotor (all formellogikk, deles av app og PDF)
- `rapport.py`   – PDF-rapportgenerator med fin typografi (ReportLab)
- `app.py`       – Streamlit-grensesnitt med fire faner
- `requirements.txt` – Python-avhengigheter

## Kom i gang lokalt
```bash
pip install streamlit pandas reportlab
streamlit run app.py
```
Åpnes på http://localhost:8501

## Deploy på Streamlit Community Cloud
1. Push alle filer til GitHub-repo
2. Gå til share.streamlit.io → "New app"
3. Velg repo, branch=main, fil=app.py → Deploy

## Faner i appen
- **Kalkulator** – beregning med live resultater og formelvisning
- **Rapport / PDF** – fyll inn prosjektinfo og last ned PDF direkte
- **Metode og formler** – formelreferanser og tabeller
- **Materialdata** – oversikt over alle stagtyper med R_itd

## Faglig grunnlag (IPV-INGGEO-002 A02, 2025-09-18)
- Forspentstag: EC3 del 5 (F_tt,Rd og F_tg,Rd separat)
- Kamstålbolter: L1 dimensjoneres med flytelast (IPV kap. 4.2)
- η2-korreksjon for ø > 32 mm (EC2 / IPV kap. 2.3.2.2)
- Prøvelastbegrensning Pp ≤ 0,80·Ptk (IPV kap. 2.3.1.1)
- Reduksjonsfaktor f_a (EC7 NA.A.19)

## Referanser
SVV V220 (2023) · EC2/EC3/EC7 · IPV-INGGEO-002 A02 · NGI 20210114-01-R · NS 3576-3:2012
