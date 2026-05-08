# Bergforankring – beregningsverktøy

## Filer
- `beregning.py` – beregningsmotor (all formellogikk)
- `app.py`       – Streamlit-grensesnitt
- `gen_rapport_from_json.py` – PDF-generator (ligger i Claude-prosjektet)

## Kom i gang

### Krav
```
pip install streamlit pandas reportlab
```

### Start kalkulatoren
```
streamlit run app.py
```
Åpnes automatisk på http://localhost:8501

## Endringer fra HTML-versjon (IPV-INGGEO-002 A02, 2025-09-18)

1. **Indre kapasitet stangstag** bruker nå EC3 del 5 (F_tt,Rd og F_tg,Rd separat)
2. **L1 kamstålbolter** dimensjoneres med flytelast, ikke P_d = γF·Fk
3. **η2-korreksjon** for ø > 32 mm ved EC2-beregning av heftfasthet
4. **Prøvelastbegrensning** kontrolleres for lissestag (Pp ≤ 0,80·Ptk)
5. **Reduksjonsfaktor f_a** (EC7 NA.A.19) er implementert

## Referanser
- SVV håndbok V220 (2023) kap. 11.6.4.5
- NS-EN 1992-1-1, 1993-1-1, 1997-1
- IPV-INGGEO-002 Bergforankring A02 (Norconsult 2025-09-18)
- NGI rapport 20210114-01-R (2021)
- NS 3576-3:2012
