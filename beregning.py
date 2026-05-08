"""
beregning.py – Beregningsmotor for bergforankring
Alle formler samlet på ett sted, brukes av både Streamlit og PDF-generator.
Referanser: V220 kap. 11.6.4.5, EC2/EC3, IPV-INGGEO-002 A02 (2025-09-18)
"""
import math
from dataclasses import dataclass, field
from typing import Literal

PI = math.pi

# ── Stagkategorier ─────────────────────────────────────────────────────────
StagKategori = Literal["kamstaal_passiv", "forspentstag_EC3del5", "lissestag"]

@dataclass
class Inndata:
    # Stagtype
    stagkategori: StagKategori = "kamstaal_passiv"
    stagname: str = "Kamstål B500NC Ø32"
    stagsrc: str = "NS 3576-3"

    # Geometri
    ds_mm: float = 32.0          # Stagdiameter [mm]
    dh_mm: float = 45.0          # Borehullsdiameter [mm]
    alpha_deg: float = 45.0      # Ankervinkel mot bergoverflate [°]

    # Last
    Fk_kN: float = 150.0         # Karakteristisk stagkraft [kN]
    gammaF: float = 1.35         # Lastfaktor ULS
    eta_proeve: float = 1.10     # Prøvelastfaktor (≥ 1,10)

    # Ståldata
    fyk_MPa: float = 500.0       # Karakteristisk flytespenning
    fuk_MPa: float = 550.0       # Karakteristisk bruddspenning
    As_mm2: float = 804.0        # Nettoareal (stammeareal for kamstål, spennoareal for gjenget del)
    Ag_mm2: float = 804.0        # Brutto stammeareal (ugjenget del, EC3 del 5)
    gammaS: float = 1.15         # Partialfaktor stål (flytdel)
    gammaM0: float = 1.05        # Partialfaktor ugjenget del (EC3 del 5)
    gammaM2: float = 1.25        # Partialfaktor gjenget del (EC3 del 5)
    kt: float = 0.9              # Reduksjonsfaktor gjenget del (EC3 del 5)
    fa: float = 1.0              # Reduksjonsfaktor konstruksjonsdeler (EC7 NA.A.19, 0,6–0,9)

    # Lissestag
    Pt01k_kN: float = 0.0        # Karakteristisk 0,1%-strekkgrense (lissestag)
    Ptk_kN: float = 0.0          # Karakteristisk bruddlast (lissestag)
    n_lisser: int = 1
    lisse_montering: Literal["stang", "perm", "mid"] = "stang"

    # Bergdata (bruddplan) – V220 tab. 11.6.4.5-2
    tauK_berg_kPa: float = 150.0  # Skjærmotstand langs bruddplan [kPa]
    psi_deg: float = 45.0         # Bruddvinkel [°]
    gammaM_berg: float = 3.0      # Materialfaktor bergmasse

    # Mørteldata
    tauK_sm_MPa: float = 2.4      # Heftfasthet stål/mørtel [MPa]
    tauK_mb_MPa: float = 1.5      # Heftfasthet mørtel/berg [MPa]
    gammaM_mortel: float = 1.25   # Partialfaktor mørtel
    bruk_EC2_heft: bool = False    # Beregn heft stål/mørtel etter EC2
    fc_cube_MPa: float = 50.0     # Terningfasthet mørtel (EC2-metode)
    eta1: float = 0.7             # Borehullfaktor EC2

    # Prosjektinfo
    prosjekt: str = ""
    docnr: str = ""
    rev: str = "00"
    av: str = ""
    kont: str = ""
    dato: str = ""
    desc: str = ""


@dataclass
class Resultater:
    # Laster
    Pp_kN: float = 0.0
    Pd_kN: float = 0.0

    # Indre kapasitet
    Ritk_kN: float = 0.0
    Ritd_kN: float = 0.0
    Fttrd_kN: float = 0.0   # Gjenget del (EC3 del 5)
    Ftgrd_kN: float = 0.0   # Ugjenget del (EC3 del 5)
    ec3_betingelse_ok: bool = True
    strek_ok: bool = True

    # Prøvelastbegrensninger (IPV kap. 2.3.1.1)
    Pp_grense_08Ptk: float = 0.0
    Pp_grense_095Pt01k: float = 0.0
    Pp_innenfor_grenser: bool = True
    Pp_grense_merknad: str = ""

    # Heftfasthet
    fbd_MPa: float = 0.0         # Dimensjonerende heftfasthet stål/mørtel
    eta2: float = 1.0            # Diameterkorreksjon EC2

    # Inngysingslengder
    L1_m: float = 0.0
    L2_m: float = 0.0
    Ld_m: float = 0.0
    L1_grunnlag: str = ""        # Beskrivelse av hvilken last L1 er basert på

    # Berguttrekk
    lam_m: float = 0.0
    lDim_m: float = 0.0

    # Status
    lamDim: bool = False         # True hvis berguttrekk er dimensjonerende
    L1_styrende: bool = False
    L2_styrende: bool = False


def beregn_fbd_EC2(fc_cube_MPa: float, eta1: float, ds_mm: float) -> tuple[float, float]:
    """Beregn dimensjonerende heftfasthet stål/mørtel etter EC2 pkt. 8.4.2 og IPV kap. 2.3.2.2"""
    fck = fc_cube_MPa * 0.8
    # fctk0,05 etter EC2 tabell 3.1
    if fck <= 50:
        fctk005 = 0.21 * (fck ** (2/3))
    else:
        fctk005 = 2.12 * math.log(1 + (fck + 8) / 10)
    fctk005 = max(fctk005, 0.1)
    alpha_ct = 0.85
    gamma_c = 1.5
    fctd = alpha_ct * fctk005 / gamma_c
    # η2 – korreksjon for diameter > 32 mm (IPV kap. 2.3.2.2)
    eta2 = 1.0 if ds_mm <= 32 else (132 - ds_mm) / 100
    eta2 = max(eta2, 0.0)
    fbd = 2.25 * eta1 * eta2 * fctd
    return fbd, eta2


def beregn(inn: Inndata) -> Resultater:
    r = Resultater()
    ds = inn.ds_mm / 1000
    dh = inn.dh_mm / 1000
    alpha = inn.alpha_deg * PI / 180
    psi = inn.psi_deg * PI / 180
    tauBerg = inn.tauK_berg_kPa * 1000  # Pa
    sinA = math.sin(alpha)
    tanP = math.tan(psi)

    # ── Laster ───────────────────────────────────────────────────────────────
    r.Pp_kN = inn.eta_proeve * inn.Fk_kN
    r.Pd_kN = inn.gammaF * inn.Fk_kN

    # ── Indre kapasitet ───────────────────────────────────────────────────────
    if inn.stagkategori == "kamstaal_passiv":
        # Passiv kamstålbolt – EC3 del 1-1, enkel kontroll
        ec3_ok = 0.8 * inn.fuk_MPa > 0.9 * inn.fyk_MPa
        r.ec3_betingelse_ok = ec3_ok
        if ec3_ok:
            r.Ritk_kN = inn.As_mm2 * inn.fyk_MPa / 1000
        else:
            r.Ritk_kN = inn.As_mm2 * inn.fuk_MPa * (0.8 / 0.9) / 1000
        r.Ritd_kN = r.Ritk_kN / inn.gammaS * inn.fa
        r.strek_ok = r.Pd_kN <= r.Ritd_kN

    elif inn.stagkategori == "forspentstag_EC3del5":
        # Forspentstag – EC3 del 5 kap. 7.2 (IPV kap. 2.2)
        # Gjenget del
        r.Fttrd_kN = inn.kt * inn.fuk_MPa * inn.As_mm2 / inn.gammaM2 / 1000
        # Ugjenget del
        r.Ftgrd_kN = inn.Ag_mm2 * inn.fyk_MPa / inn.gammaM0 / 1000
        r.Ritd_kN = min(r.Fttrd_kN, r.Ftgrd_kN) * inn.fa
        r.Ritk_kN = r.Ritd_kN * max(inn.gammaM0, inn.gammaM2)  # approx
        r.ec3_betingelse_ok = True  # ikke aktuelt for EC3 del 5
        r.strek_ok = r.Pd_kN <= r.Ritd_kN

    elif inn.stagkategori == "lissestag":
        # Lissestag – EC2 del 1-1
        r.Ritk_kN = inn.Pt01k_kN
        r.Ritd_kN = inn.Pt01k_kN / inn.gammaS * inn.fa
        r.ec3_betingelse_ok = True
        r.strek_ok = r.Pd_kN <= r.Ritd_kN
        # Prøvelastbegrensninger (IPV kap. 2.3.1.1)
        if inn.Ptk_kN > 0:
            r.Pp_grense_08Ptk = 0.80 * inn.Ptk_kN
            r.Pp_grense_095Pt01k = 0.95 * inn.Pt01k_kN
            ok1 = r.Pp_kN <= r.Pp_grense_08Ptk
            ok2 = r.Pp_kN <= r.Pp_grense_095Pt01k
            r.Pp_innenfor_grenser = ok1 and ok2
            if not ok1:
                r.Pp_grense_merknad = f"P_p ({r.Pp_kN:.1f} kN) > 0,80·P_tk ({r.Pp_grense_08Ptk:.1f} kN)"
            elif not ok2:
                r.Pp_grense_merknad = f"P_p ({r.Pp_kN:.1f} kN) > 0,95·P_t0,1k ({r.Pp_grense_095Pt01k:.1f} kN)"

    # ── Heftfasthet stål/mørtel ───────────────────────────────────────────────
    if inn.bruk_EC2_heft:
        r.fbd_MPa, r.eta2 = beregn_fbd_EC2(inn.fc_cube_MPa, inn.eta1, inn.ds_mm)
    else:
        r.fbd_MPa = inn.tauK_sm_MPa / inn.gammaM_mortel
        r.eta2 = 1.0 if inn.ds_mm <= 32 else (132 - inn.ds_mm) / 100

    tauD_mb = inn.tauK_mb_MPa / inn.gammaM_mortel * 1e6  # Pa

    # ── L1 – inngysingslengde stål/mørtel ─────────────────────────────────────
    fbd_Pa = r.fbd_MPa * 1e6
    if inn.stagkategori == "kamstaal_passiv":
        # IPV kap. 4.2: dimensjonerende last = flytelast (uavhengig av F_k)
        Pflyt_kN = inn.As_mm2 * inn.fyk_MPa / 1000
        r.L1_grunnlag = f"Flytelast P_flyt = {Pflyt_kN:.1f} kN (IPV kap. 4.2)"
        r.L1_m = (Pflyt_kN * 1000) / (fbd_Pa * ds * PI)
    elif inn.stagkategori == "forspentstag_EC3del5":
        if inn.lisse_montering == "perm":
            r.L1_m = (r.Pp_kN * 1000) / (inn.n_lisser * fbd_Pa * ds * PI)
            r.L1_grunnlag = f"Prøvelast P_p = {r.Pp_kN:.1f} kN, {inn.n_lisser} lisser med avstandsholdere"
        elif inn.lisse_montering == "mid":
            dekv = math.sqrt(1.2 * inn.n_lisser) * ds
            r.L1_m = (r.Pp_kN * 1000) / (fbd_Pa * dekv * PI)
            r.L1_grunnlag = f"Prøvelast P_p = {r.Pp_kN:.1f} kN, bunt d_ekv = {dekv*1000:.1f} mm"
        else:
            r.L1_m = (r.Pp_kN * 1000) / (fbd_Pa * ds * PI)
            r.L1_grunnlag = f"Prøvelast P_p = {r.Pp_kN:.1f} kN (forspentstag)"
    elif inn.stagkategori == "lissestag":
        if inn.lisse_montering == "perm":
            r.L1_m = (r.Pp_kN * 1000) / (inn.n_lisser * fbd_Pa * ds * PI)
            r.L1_grunnlag = f"Prøvelast P_p = {r.Pp_kN:.1f} kN, {inn.n_lisser} lisser m/avstandsh."
        else:
            dekv = math.sqrt(1.2 * inn.n_lisser) * ds
            r.L1_m = (r.Pp_kN * 1000) / (fbd_Pa * dekv * PI)
            r.L1_grunnlag = f"Prøvelast P_p = {r.Pp_kN:.1f} kN, bunt d_ekv = {dekv*1000:.1f} mm"

    # ── L2 – inngysingslengde mørtel/berg ─────────────────────────────────────
    r.L2_m = (r.Pd_kN * 1000) / (tauD_mb * dh * PI)
    r.Ld_m = max(r.L1_m, r.L2_m)
    r.L1_styrende = r.L1_m >= r.L2_m
    r.L2_styrende = r.L2_m > r.L1_m

    # ── λ – bergstabilitet mot uttrekk ────────────────────────────────────────
    denom = tauBerg * PI * tanP * sinA
    r.lam_m = math.sqrt(max(0, inn.gammaM_berg * r.Pp_kN * 1000 / denom))
    r.lDim_m = max(r.Ld_m, r.lam_m)
    r.lamDim = r.lam_m >= r.Ld_m

    return r


# ── Materialdata ──────────────────────────────────────────────────────────────
STAG_DB = [
    dict(key="r20",  navn="Kamstål B500NC Ø20",     kat="kamstaal_passiv",      ds=20,  dh=32,  fyk=500, fuk=550, As=314,  Ag=314,  gs=1.15, tsm=2.4, src="NS 3576-3"),
    dict(key="r25",  navn="Kamstål B500NC Ø25",     kat="kamstaal_passiv",      ds=25,  dh=35,  fyk=500, fuk=550, As=491,  Ag=491,  gs=1.15, tsm=2.4, src="NS 3576-3"),
    dict(key="r32",  navn="Kamstål B500NC Ø32",     kat="kamstaal_passiv",      ds=32,  dh=45,  fyk=500, fuk=550, As=804,  Ag=804,  gs=1.15, tsm=2.4, src="NS 3576-3"),
    dict(key="r38",  navn="Kamstål B500NC Ø38",     kat="kamstaal_passiv",      ds=38,  dh=51,  fyk=500, fuk=550, As=1134, Ag=1134, gs=1.15, tsm=2.4, src="NS 3576-3"),
    dict(key="m24",  navn="M24 S670/800",            kat="forspentstag_EC3del5", ds=24,  dh=35,  fyk=670, fuk=800, As=353,  Ag=452,  gs=1.05, tsm=2.4, src="NGI tab. 9"),
    dict(key="m27",  navn="M27 S670/800",            kat="forspentstag_EC3del5", ds=27,  dh=38,  fyk=670, fuk=800, As=459,  Ag=573,  gs=1.05, tsm=2.4, src="NGI tab. 9"),
    dict(key="m30",  navn="M30 S670/800",            kat="forspentstag_EC3del5", ds=30,  dh=42,  fyk=670, fuk=800, As=561,  Ag=707,  gs=1.05, tsm=2.4, src="NGI tab. 9"),
    dict(key="m36",  navn="M36 S670/800",            kat="forspentstag_EC3del5", ds=36,  dh=51,  fyk=670, fuk=800, As=817,  Ag=1018, gs=1.05, tsm=2.4, src="NGI tab. 9"),
    dict(key="g32",  navn="GEWI Ø32 St670/800",      kat="forspentstag_EC3del5", ds=32,  dh=45,  fyk=670, fuk=800, As=693,  Ag=804,  gs=1.05, tsm=2.4, src="Leverandør"),
    dict(key="g40",  navn="GEWI Ø40 St670/800",      kat="forspentstag_EC3del5", ds=40,  dh=56,  fyk=670, fuk=800, As=1140, Ag=1257, gs=1.05, tsm=2.4, src="Leverandør"),
    dict(key="ibo30",navn="IBO Ø30 R32 (selvborende)",kat="kamstaal_passiv",     ds=30,  dh=76,  fyk=550, fuk=630, As=452,  Ag=452,  gs=1.15, tsm=2.0, src="Leverandør"),
    dict(key="l3p",  navn="Lissestag 3×0.6\" perm.", kat="lissestag",            ds=15.24,dh=90, fyk=1670,fuk=1860,As=420, Ag=420,  gs=1.10, tsm=2.4, src="EC2 vedl. C", n=3, mont="perm"),
    dict(key="l7p",  navn="Lissestag 7×0.6\" perm.", kat="lissestag",            ds=15.24,dh=115,fyk=1670,fuk=1860,As=980, Ag=980,  gs=1.10, tsm=2.4, src="EC2 vedl. C", n=7, mont="perm"),
    dict(key="l3m",  navn="Lissestag 3×0.6\" midle.",kat="lissestag",            ds=15.24,dh=90, fyk=1670,fuk=1860,As=420, Ag=420,  gs=1.10, tsm=2.4, src="EC2 vedl. C", n=3, mont="mid"),
]

BERGARTER = {
    "Granitt":   dict(tauMB=2.0, gamma=26),
    "Gabbro":    dict(tauMB=2.5, gamma=28),
    "Gneis":     dict(tauMB=1.5, gamma=26),
    "Kvartsitt": dict(tauMB=2.5, gamma=22),
    "Sandstein": dict(tauMB=1.2, gamma=23),
    "Kalkstein": dict(tauMB=2.0, gamma=26),
    "Leirskifer":dict(tauMB=0.5, gamma=24),
}

BERGKVALITET = {
    "Meget godt berg (1 sprekkesett, σ_c > 50 MPa)":  dict(tauK=150, psi_maks=45),
    "Middels berg (2 sprekkesett, σ_c 15–50 MPa)":    dict(tauK=75,  psi_maks=40),
    "Dårlig berg (3 sprekkesett, σ_c < 15 MPa)":      dict(tauK=50,  psi_maks=30),
}
