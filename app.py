"""
app.py – Streamlit-kalkulator for bergforankring
Kjør med: streamlit run app.py
"""
import streamlit as st
import math
import datetime
from beregning import beregn, Inndata, Resultater, STAG_DB, BERGARTER, BERGKVALITET, PI

st.set_page_config(
    page_title="Bergforankring – innboringslengde",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main { padding-top: 1rem; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] { padding: 8px 20px; border-radius: 8px; }
div[data-testid="metric-container"] { background: #f5f8fc; border-radius: 8px; padding: 12px; border: 1px solid #d0dce8; }
.result-ok    { color: #1a7a2a; font-weight: 600; }
.result-fail  { color: #c0392b; font-weight: 600; }
.result-dim   { color: #1a3a5c; font-weight: 700; }
.formula-box  { background: #f5f8fc; border-left: 4px solid #378ADD; padding: 12px 16px; border-radius: 0 8px 8px 0; font-family: monospace; font-size: 0.9em; line-height: 1.8; margin: 8px 0; }
.warn-box     { background: #fff8ee; border: 1px solid #f0c060; border-radius: 8px; padding: 10px 14px; font-size: 0.9em; }
.fail-box     { background: #fff0f0; border: 1px solid #f0a0a0; border-radius: 8px; padding: 10px 14px; font-size: 0.9em; }
.info-box     { background: #eef4ff; border: 1px solid #c0d8f0; border-radius: 8px; padding: 10px 14px; font-size: 0.9em; }
.dim-box      { background: #ddeeff; border: 2px solid #1a3a5c; border-radius: 8px; padding: 14px 18px; }
h3            { color: #1a3a5c; }
</style>
""", unsafe_allow_html=True)

# ── Sidepanel: stagtype ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⛏️ Bergforankring")
    st.markdown("**V220 · EC2/EC3 · IPV-INGGEO-002 A02**")
    st.divider()

    st.markdown("### Stagtype")
    stag_navn = [s["navn"] for s in STAG_DB]
    valgt_idx = st.selectbox("Velg stagtype", range(len(STAG_DB)),
                              format_func=lambda i: STAG_DB[i]["navn"], index=2)
    st_data = STAG_DB[valgt_idx]
    st.caption(f"Kilde: {st_data['src']} · As = {st_data['As']} mm²")

    st.divider()
    st.markdown("### Geometri og last")
    ds_mm   = st.number_input("d_s – stagdiameter (mm)", value=float(st_data["ds"]), min_value=10.0, max_value=200.0, step=1.0)
    dh_mm   = st.number_input("d_h – borehullsdiam. (mm)", value=float(st_data["dh"]), min_value=20.0, max_value=250.0, step=1.0)
    alpha   = st.slider("α – ankervinkel (°)", 0, 90, 45)
    Fk      = st.number_input("F_k – stagkraft (kN)", value=150.0, min_value=1.0, step=5.0)
    gammaF  = st.number_input("γ_F – lastfaktor", value=1.35, min_value=1.0, max_value=1.5, step=0.05)
    eta_p   = st.number_input("η – prøvelastfaktor (≥ 1,10)", value=1.10, min_value=1.0, max_value=2.0, step=0.05)

    st.divider()
    st.markdown("### Ståldata")
    fyk     = st.number_input("f_yk (MPa)", value=float(st_data["fyk"]), step=10.0)
    fuk     = st.number_input("f_uk (MPa)", value=float(st_data["fuk"]), step=10.0)
    As      = st.number_input("As – nettoareal (mm²)", value=float(st_data["As"]), step=1.0)
    Ag      = st.number_input("Ag – brutto stammeareal (mm²)", value=float(st_data["Ag"]), step=1.0,
                               help="Ugjenget del – brukes kun for forspente stangstag (EC3 del 5)")
    gammaS  = st.number_input("γ_s – partialfaktor stål", value=float(st_data["gs"]), step=0.05)

    kat = st_data["kat"]
    if kat == "forspentstag_EC3del5":
        with st.expander("EC3 del 5 – partialfaktorer"):
            kt     = st.number_input("k_t – reduksjonsfaktor gjenget del", value=0.9, step=0.05)
            gamM0  = st.number_input("γ_M0 (ugjenget del)", value=1.05, step=0.05)
            gamM2  = st.number_input("γ_M2 (gjenget del)", value=1.25, step=0.05)
    else:
        kt, gamM0, gamM2 = 0.9, 1.05, 1.25

    fa = st.number_input("f_a – reduksjonsfaktor konstr.deler (1,0 = ingen red.)",
                          value=1.0, min_value=0.5, max_value=1.0, step=0.05,
                          help="EC7 NA.A.19: 0,6 for permanente, 0,9 for midlertidige ankere")

    n_lisser = int(st_data.get("n", 1))
    lisse_mont = st_data.get("mont", "stang")
    if kat == "lissestag":
        n_lisser  = st.number_input("n – antall lisser", value=n_lisser, min_value=1, step=1)
        lisse_mont = st.selectbox("Lissemontering", ["perm", "mid"],
                                   format_func=lambda x: "Permanent (avstandsh.)" if x=="perm" else "Midlertidig (bunt)")
        Pt01k = st.number_input("P_t0,1k – 0,1%-strekkgrense (kN)", value=0.0, step=10.0)
        Ptk   = st.number_input("P_tk – bruddlast (kN)", value=0.0, step=10.0)
    else:
        Pt01k, Ptk = 0.0, 0.0

# ── Global beregning (tilgjengelig i alle faner) ──────────────────────────────
# Bergdata og mørteldata samles her slik at inn og r er globale variabler
    st.divider()
    st.markdown("### 🪨 Bergdata – uttrekk")
    st.markdown("""<div style='background:#fff8ee;border:1px solid #f0c060;border-radius:8px;
        padding:8px 12px;font-size:12px;color:#7a4010;margin-bottom:10px'>
        <b>τ_k bruddplan (kPa)</b> – velges etter oppsprekkingsgrad (V220 tab. 11.6.4.5-2).
        Ikke heftfasthet mørtel/berg.</div>""", unsafe_allow_html=True)
    bergkval = st.radio("Bergkvalitet", list(BERGKVALITET.keys()), index=0)
    bk = BERGKVALITET[bergkval]
    tauBerg = st.number_input("τ_k bruddplan (kPa)", value=float(bk["tauK"]), min_value=10.0, max_value=300.0, step=10.0)
    psi_max = bk["psi_maks"]
    psi = st.slider(f"ψ – bruddvinkel (°, maks {psi_max}°)", 10, 60, psi_max)
    if psi > psi_max:
        st.warning(f"ψ = {psi}° overskrider anbefalt maks {psi_max}°")
    gammaM_berg = st.number_input("γ_M,berg (anbef. 2–3)", value=3.0, min_value=1.0, max_value=5.0, step=0.5)

    st.divider()
    st.markdown("### 🔩 Mørteldata")
    bergart = st.selectbox("Bergart", list(BERGARTER.keys()), index=2)
    tauMB = st.number_input("τ_k mørtel/berg (MPa)", value=BERGARTER[bergart]["tauMB"], step=0.1)
    bruk_EC2 = st.toggle("Heft stål/mørtel etter EC2", value=False)
    if bruk_EC2:
        fc_cube = st.number_input("f_c,cube mørtel (MPa)", value=50.0, step=5.0)
        eta1    = st.number_input("η₁ – borehullfaktor", value=0.7, min_value=0.3, max_value=1.0, step=0.05)
        tauSM   = 0.0
    else:
        fc_cube, eta1 = 50.0, 0.7
        tauSM = st.number_input("τ_k stål/mørtel (MPa)", value=float(st_data["tsm"]), step=0.1)
    gammaM_mortel = st.number_input("γ_m,mørtel", value=1.25, min_value=1.0, max_value=2.0, step=0.05)

# ── Global beregning – tilgjengelig i ALLE faner ──────────────────────────────
inn = Inndata(
    stagkategori=kat, stagname=st_data["navn"], stagsrc=st_data["src"],
    ds_mm=ds_mm, dh_mm=dh_mm, alpha_deg=float(alpha),
    Fk_kN=Fk, gammaF=gammaF, eta_proeve=eta_p,
    fyk_MPa=fyk, fuk_MPa=fuk, As_mm2=As, Ag_mm2=Ag,
    gammaS=gammaS, gammaM0=gamM0, gammaM2=gamM2, kt=kt, fa=fa,
    Pt01k_kN=Pt01k, Ptk_kN=Ptk,
    n_lisser=int(n_lisser), lisse_montering=lisse_mont,
    tauK_berg_kPa=tauBerg, psi_deg=float(psi), gammaM_berg=gammaM_berg,
    tauK_sm_MPa=tauSM, tauK_mb_MPa=tauMB, gammaM_mortel=gammaM_mortel,
    bruk_EC2_heft=bruk_EC2, fc_cube_MPa=fc_cube if bruk_EC2 else 50.0, eta1=eta1,
)
r = beregn(inn)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_kalk, tab_metode, tab_mat, tab_rapport = st.tabs(
    ["📐 Kalkulator", "📖 Metode og formler", "📋 Materialdata", "📄 Rapport / PDF"])

with tab_kalk:

    # ── Nøkkeltall ────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### Resultater")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("P_d (dim. strekk)", f"{r.Pd_kN:.1f} kN")
    m2.metric("P_p (prøvelast)", f"{r.Pp_kN:.1f} kN")
    m3.metric("R_itd (indre kap.)", f"{r.Ritd_kN:.0f} kN")
    m4.metric("λ_dim (dim. innboring)", f"{r.lDim_m:.2f} m", delta="styrende" if r.lamDim else None)

    # ── Grensesnitt ────────────────────────────────────────────────────────────
    st.markdown("#### Kontroll – alle grensesnitt")

    # ① Indre kapasitet
    with st.expander("① Indre kapasitet stag", expanded=True):
        if kat == "kamstaal_passiv":
            ec3_txt = f"0,8·f_uk = {0.8*fuk:.0f} MPa {'>' if r.ec3_betingelse_ok else '≤'} 0,9·f_yk = {0.9*fyk:.0f} MPa → {'flytgrense gjelder' if r.ec3_betingelse_ok else 'bruddspenning styrer'}"
            st.markdown(f"""<div class="formula-box">
EC3 betingelse:  {ec3_txt}
R_itk = As × f_yk = {As:.0f} mm² × {fyk:.0f} MPa = {r.Ritk_kN:.1f} kN
R_itd = R_itk / γ_s × f_a = {r.Ritk_kN:.1f} / {gammaS} × {fa} = {r.Ritd_kN:.1f} kN
Kontroll: P_d = {r.Pd_kN:.1f} kN {'≤' if r.strek_ok else '>'} R_itd = {r.Ritd_kN:.1f} kN</div>""", unsafe_allow_html=True)
        elif kat == "forspentstag_EC3del5":
            st.markdown(f"""<div class="formula-box">
EC3 del 5 kap. 7.2 (IPV kap. 2.2):
F_tt,Rd = k_t × f_uk × As / γ_M2 = {kt} × {fuk:.0f} × {As:.0f} / {gamM2} = {r.Fttrd_kN:.1f} kN  (gjenget del)
F_tg,Rd = Ag × f_yk / γ_M0     = {Ag:.0f} × {fyk:.0f} / {gamM0} = {r.Ftgrd_kN:.1f} kN  (ugjenget del)
F_t,Rd  = min(F_tt,Rd, F_tg,Rd) × f_a = {r.Ritd_kN:.1f} kN
Kontroll: P_d = {r.Pd_kN:.1f} kN {'≤' if r.strek_ok else '>'} F_t,Rd = {r.Ritd_kN:.1f} kN</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="formula-box">
Lissestag EC2: F_t,Rd = P_t0,1k / γ_S × f_a = {Pt01k:.1f} / {gammaS} × {fa} = {r.Ritd_kN:.1f} kN
Kontroll: P_d = {r.Pd_kN:.1f} kN {'≤' if r.strek_ok else '>'} F_t,Rd = {r.Ritd_kN:.1f} kN</div>""", unsafe_allow_html=True)
            if not r.Pp_innenfor_grenser:
                st.markdown(f'<div class="fail-box">⚠️ Prøvelastbegrensning overskredet: {r.Pp_grense_merknad}</div>', unsafe_allow_html=True)
        klasse = "result-ok" if r.strek_ok else "result-fail"
        st.markdown(f'<span class="{klasse}">{"✓ OK" if r.strek_ok else "✗ IKKE OK"}</span>', unsafe_allow_html=True)

    # ③ L1
    with st.expander("③ L1 – inngysingslengde stål/mørtel", expanded=True):
        fbd_info = f"f_bd (EC2) = {r.fbd_MPa:.3f} MPa (η₁={eta1}, η₂={r.eta2:.2f})" if bruk_EC2 else f"τ_d,s/m = {r.fbd_MPa:.3f} MPa (= {tauSM:.2f}/γ)"
        st.markdown(f"""<div class="formula-box">
{fbd_info}
{r.L1_grunnlag}
L1 = P / (f_bd × d_s × π) = {r.L1_m:.3f} m
</div>""", unsafe_allow_html=True)
        if kat == "kamstaal_passiv":
            st.info("📌 IPV kap. 4.2: Innstøpingslengden beregnes med flytelast, ikke γ_F·F_k")
        klasse = "result-ok" if not r.L1_styrende else "result-fail"
        st.markdown(f'<span class="{klasse}">{"✗ Styrende" if r.L1_styrende else "✓ OK"}</span> — L1 = {r.L1_m:.3f} m', unsafe_allow_html=True)

    # ④ L2
    with st.expander("④ L2 – inngysingslengde mørtel/berg", expanded=True):
        tauD_mb = tauMB / gammaM_mortel
        st.markdown(f"""<div class="formula-box">
τ_d,m/b = {tauMB:.2f} / {gammaM_mortel:.2f} = {tauD_mb:.3f} MPa
L2 = P_d / (τ_d,m/b × d_h × π) = {r.Pd_kN:.1f} / ({tauD_mb:.3f} × {dh_mm:.0f} × π) = {r.L2_m:.3f} m
</div>""", unsafe_allow_html=True)
        klasse = "result-ok" if not r.L2_styrende else "result-fail"
        st.markdown(f'<span class="{klasse}">{"✗ Styrende" if r.L2_styrende else "✓ OK"}</span> — L2 = {r.L2_m:.3f} m', unsafe_allow_html=True)

    # ⑥ λ berguttrekk
    with st.expander("⑥ λ – bergstabilitet mot uttrekk", expanded=True):
        sinA = math.sin(float(alpha)*PI/180)
        # Beregn ψ_eff lokalt (trygt selv om beregning.py er eldre versjon)
        psi_eff_deg = float(psi) * sinA if float(alpha) < 90 else float(psi)
        psi_redusert = float(alpha) < 90
        tanP_eff = math.tan(psi_eff_deg * PI / 180)
        num  = gammaM_berg * r.Pp_kN * 1000
        den  = tauBerg * 1000 * PI * tanP_eff * sinA

        # Advarsel ved lav ankervinkel
        if float(alpha) < 30:
            st.error(f"⚠️ α = {float(alpha):.0f}° < 30°: Beregningsmetoden er uegnet iht. V220 tabell 11.6.4.5-3.")
        elif float(alpha) <= 40:
            st.warning(f"⚠️ α = {float(alpha):.0f}° (30°–40°): Beregnet λ er usikker iht. V220 tabell 11.6.4.5-3.")

        # Vis ψ-reduksjon hvis aktuelt
        if psi_redusert:
            st.info(
                f"V220 tab. 11.6.4.5-3: For α = {float(alpha):.0f}° < 90° reduseres bruddvinkelen: "
                f"ψ_eff = ψ × sin(α) = {psi:.0f}° × sin({float(alpha):.0f}°) = **{psi_eff_deg:.2f}°**  "
                f"(formel 11.6.4.5-6)"
            )

        psi_linje = (f"ψ_eff = ψ × sin(α) = {psi:.0f}° × {sinA:.4f} = {psi_eff_deg:.2f}°  "
                     f"[V220 tab. 11.6.4.5-3]" if psi_redusert else f"ψ = {psi:.0f}°")
        ref = "V220 11.6.4.5-6" if psi_redusert else "V220 11.6.4.5-5"
        st.markdown(f"""<div class="formula-box">
{psi_linje}
λ = √( γ_M × P_p / (τ_k × π × tan(ψ_eff) × sin(α)) )  [{ref}]
  = √( {gammaM_berg:.1f} × {r.Pp_kN*1000:.0f} N / ({tauBerg*1000:.0f} Pa × π × tan({psi_eff_deg:.2f}°) × sin({float(alpha):.0f}°)) )
  = √( {num:.0f} / {den:.2f} )
  = {r.lam_m:.3f} m
</div>""", unsafe_allow_html=True)
        klasse = "result-fail" if r.lamDim else "result-ok"
        st.markdown(f'<span class="{klasse}">{"✗ Dimensjonerende" if r.lamDim else "✓ OK"}</span> — λ = {r.lam_m:.3f} m', unsafe_allow_html=True)

    # ── Dimensjonerende innboringslengde ──────────────────────────────────────
    st.divider()
    utn_L1  = r.L1_m  / r.lDim_m * 100 if r.lDim_m > 0 else 0
    utn_L2  = r.L2_m  / r.lDim_m * 100 if r.lDim_m > 0 else 0
    utn_lam = r.lam_m / r.lDim_m * 100 if r.lDim_m > 0 else 0
    utn_str = r.Pd_kN / r.Ritd_kN * 100 if r.Ritd_kN > 0 else 0

    st.markdown(f"""<div class="dim-box">
<h3 style="margin:0 0 8px 0">λ_dim = max(L_d, λ) = max({r.Ld_m:.3f}, {r.lam_m:.3f}) = <b>{r.lDim_m:.2f} m</b></h3>
<p style="margin:4px 0;font-size:0.9em">Indre kapasitet: <b>{'✓ OK' if r.strek_ok else '✗ IKKE OK'}</b> &nbsp;·&nbsp; Styrende grensesnitt: <b>{'λ berguttrekk' if r.lamDim else ('L1 stål/mørtel' if r.L1_styrende else 'L2 mørtel/berg')}</b></p>
</div>""", unsafe_allow_html=True)

    st.markdown("#### Kapasitetsutnyttelse")
    c1, c2, c3, c4 = st.columns(4)
    c1.progress(min(utn_L1/100, 1.0),  text=f"L1: {utn_L1:.0f}%")
    c2.progress(min(utn_L2/100, 1.0),  text=f"L2: {utn_L2:.0f}%")
    c3.progress(min(utn_lam/100, 1.0), text=f"λ: {utn_lam:.0f}%")
    c4.progress(min(utn_str/100, 1.0), text=f"Stag: {utn_str:.0f}%")

    # ── "Finn innboring for full stålutnyttelse" ──────────────────────────────
    st.divider()
    if st.button("🔩 Vis innboringslengde ved full stålutnyttelse"):
        Fk_full = r.Ritd_kN / gammaF
        inn_full = Inndata(**{**inn.__dict__, "Fk_kN": Fk_full})
        r_full = beregn(inn_full)
        st.info(
            f"Ved full stålutnyttelse: F_k = R_itd/γ_F = {r.Ritd_kN:.0f}/{gammaF:.2f} = **{Fk_full:.1f} kN** "
            f"→ λ_dim = **{r_full.lDim_m:.2f} m** (λ berguttrekk = {r_full.lam_m:.3f} m, L_d = {r_full.Ld_m:.3f} m)"
        )

with tab_metode:
    st.markdown("## Metode og formler")
    st.markdown("""
**Grunnlag:** SVV håndbok V220 (2023) kap. 11.6.4.5 · EC2/EC3/EC7 · IPV-INGGEO-002 A02 (2025-09-18)

---
### Viktig endring i IPV A02 vs. tidligere grunnlag

| Parameter | Tidligere (NGI 2021) | IPV A02 (2025) |
|---|---|---|
| Indre kap. stangstag | EC3 del 1-1, én γs | EC3 del 5: F_tt,Rd og F_tg,Rd separat |
| L1 kamstålbolter | P_d = γF·Fk | Flytelast P_flyt = As·fyk |
| η2-korreksjon ø>32mm | Ikke implementert | η2 = (132−ø)/100 |
| Prøvelastbegrensning | Ikke kontrollert | Pp ≤ 0,80·Ptk og 0,95·Pt01k |

---
### Formelreferanser

**① Indre kapasitet (EC3 del 5, IPV kap. 2.2)**
```
Forspentstag: F_t,Rd = min( kt·fua·As/γM2,  Ag·fy/γM0 ) · fa
Kamstålbolt:  R_itd  = As·fyk / γs · fa  (EC3 del 1-1)
Lissestag:    F_t,Rd = Pt0,1k / γS · fa  (EC2)
```

**③ L1 – stål/mørtel (V220 11.6.4.5-1/3, IPV kap. 4.2)**
```
Kamstålbolt (passiv): L1 = As·fyk / (fbd·ds·π)       [flytelast!]
Forspentstag:          L1 = Pp / (fbd·ds·π)
Lisse permanent:       L1 = Pp / (n·fbd·dlisse·π)
Lisse midlertidig:     L1 = Pp / (fbd·dekv·π),  dekv = √(1,2·n)·dlisse
```

**④ L2 – mørtel/berg (V220 11.6.4.5-4)**
```
L2 = Pd / (τd,m/b · dh · π)
```

**⑥ λ – berguttrekk (V220 11.6.4.5-5)**
```
λ = √( γM · Pp / (τk · π · tan(ψ) · sin(α)) )
τk i kPa (tab. 11.6.4.5-2) – ikke heftfasthet mørtel/berg!
```

**Resultat**
```
Ld    = max(L1, L2)
λdim  = max(Ld, λ)
```
    """)

with tab_mat:
    st.markdown("## Materialdata")
    import pandas as pd

    rows = []
    for s in STAG_DB:
        inn_tmp = Inndata(
            stagkategori=s["kat"], ds_mm=s["ds"], dh_mm=s["dh"],
            fyk_MPa=s["fyk"], fuk_MPa=s["fuk"], As_mm2=s["As"], Ag_mm2=s["Ag"],
            gammaS=s["gs"], gammaM0=1.05, gammaM2=1.25, kt=0.9, fa=1.0,
        )
        r_tmp = beregn(inn_tmp)
        rows.append({
            "Stagtype": s["navn"],
            "Kategori": {"kamstaal_passiv": "Passiv kamstål", "forspentstag_EC3del5": "Forspentstag EC3 del 5", "lissestag": "Lissestag"}[s["kat"]],
            "d_s (mm)": s["ds"],
            "d_h (mm)": s["dh"],
            "As (mm²)": s["As"],
            "f_yk (MPa)": s["fyk"],
            "f_uk (MPa)": s["fuk"],
            "γ_s": s["gs"],
            "R_itd (kN)": f"{r_tmp.Ritd_kN:.0f}",
            "Kilde As": s["src"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### Bergarter – heftfasthet mørtel/berg (V220 tab. 11.6.4.5-1)")
    st.dataframe(pd.DataFrame([{"Bergart": k, "τ_k mørtel/berg (MPa)": v["tauMB"], "γ (kN/m³)": v["gamma"]}
                                for k,v in BERGARTER.items()]), use_container_width=True, hide_index=True)

    st.markdown("### Bergkvalitet – bruddplan (V220 tab. 11.6.4.5-2)")
    st.dataframe(pd.DataFrame([{"Beskrivelse": k, "τ_k bruddplan (kPa)": v["tauK"], "ψ_maks (°)": v["psi_maks"]}
                                for k,v in BERGKVALITET.items()]), use_container_width=True, hide_index=True)

# ── Rapport-fane (legges til etter tab_mat) ───────────────────────────────────
# OBS: Denne blokken forutsetter at tab_kalk, tab_metode, tab_mat allerede er
# definert ovenfor. Vi injiserer rapport som fjerde fane ved å rekonstruere tabs.


# ── RAPPORT-FANE ───────────────────────────────────────────────────────────────
with tab_rapport:
    st.markdown("## 📄 Generer beregningsnotat (PDF)")
    st.markdown("Fyll inn prosjektinformasjon og klikk **Generer PDF**. "
                "Rapporten inneholder alle mellomregninger med korrekte symboler og referanser til V220/Eurokodene.")

    with st.form("rapport_form"):
        st.markdown("### Prosjektinformasjon")
        col_a, col_b = st.columns(2)
        with col_a:
            r_prosjekt = st.text_input("Prosjektnavn", placeholder="Fv42 GHT – Fanggjerde nord")
            r_av       = st.text_input("Beregnet av",  placeholder="Initialer / Navn")
            r_dato     = st.date_input("Dato", value=datetime.date.today())
        with col_b:
            r_docnr    = st.text_input("Dokumentnummer", placeholder="DOK-001")
            r_kont     = st.text_input("Kontrollert av", placeholder="Initialer / Navn")
            r_rev      = st.text_input("Revisjon", value="00")
        r_desc = st.text_input("Beskrivelse / ankeridentifikator",
                               placeholder="f.eks. Enkeltanker A1 – sørveggen rekke 2, α=45°")
        generer = st.form_submit_button("⚙️ Generer PDF", type="primary", use_container_width=True)

    if generer:
        from rapport import generer_pdf
        meta = dict(
            prosjekt=r_prosjekt or "–",
            docnr=r_docnr or "–",
            rev=r_rev or "00",
            av=r_av or "–",
            kont=r_kont or "–",
            dato=str(r_dato),
            desc=r_desc,
        )
        with st.spinner("Genererer PDF..."):
            try:
                pdf_bytes = generer_pdf(inn, r, meta)
                filnavn = f"Beregningsnotat_{(r_docnr or 'rapport').replace(' ','_')}_{r_dato}.pdf"
                st.success(f"PDF klar – {len(pdf_bytes)//1024} kB")
                st.download_button(
                    label="⬇️ Last ned beregningsnotat (PDF)",
                    data=pdf_bytes,
                    file_name=filnavn,
                    mime="application/pdf",
                    use_container_width=True,
                )
                st.caption(f"Stagtype: {inn.stagname} · λ_dim = {r.lDim_m:.2f} m · "
                           f"{'✓ Stag OK' if r.strek_ok else '✗ Sjekk stag'}")
            except Exception as e:
                st.error(f"Feil ved PDF-generering: {e}")
                raise
    else:
        st.info("Fyll inn prosjektinformasjon og klikk **Generer PDF** for å laste ned beregningsnotatet.")
        st.markdown("""
**Rapporten inneholder:**
- Fullstendig inndata-tabell med enheter og kildehenvisninger
- Beregning av laster (P_p, P_d)
- Indre kapasitet etter korrekt metode (EC3 del 1-1 / EC3 del 5 / EC2)
- Inngysingslengder L₁ og L₂ med alle mellomregninger
- Berguttrekk λ med innsatte tallverdier
- Oppsummeringstabell med utnyttelsesgrader
- Referanseliste (V220, EC2/3/7, IPV A02, NGI)
""")
