"""
rapport.py – PDF-rapportgenerator for bergforankring
Brukes av app.py via: pdf_bytes = generer_pdf(inn, res, meta)
"""
import io, math, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, KeepTogether)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

PI = math.pi

# ── Fargepalett ───────────────────────────────────────────────────────────────
NAVY   = colors.HexColor('#1a3a5c')
BLUE   = colors.HexColor('#378ADD')
LBLUE  = colors.HexColor('#ddeeff')
LGREY  = colors.HexColor('#f5f8fc')
GRID   = colors.HexColor('#b0c8e0')
WARN   = colors.HexColor('#fff8e8')
FAIL   = colors.HexColor('#fff0f0')
GREEN  = colors.HexColor('#1a6b2a')
RED    = colors.HexColor('#c0392b')

# ── Hjelpere ──────────────────────────────────────────────────────────────────
def _sty(base='Normal', **kw):
    styles = getSampleStyleSheet()
    p = styles.get(base, styles['Normal'])
    return ParagraphStyle('_'+str(id(kw)), parent=p, **kw)

N  = _sty(fontSize=8.5, leading=12, fontName='Helvetica')
NR = _sty(fontSize=8.5, leading=12, fontName='Helvetica', alignment=TA_RIGHT)
B  = _sty(fontSize=8.5, leading=12, fontName='Helvetica-Bold')
SM = _sty(fontSize=7.5, leading=10, fontName='Helvetica',
          textColor=colors.HexColor('#555555'))
H3 = _sty(fontSize=9.5, leading=13, fontName='Helvetica-Bold',
          textColor=NAVY, spaceBefore=10, spaceAfter=4)
MN = _sty(fontSize=8,   leading=13, fontName='Courier',
          backColor=LGREY, leftIndent=8, rightIndent=8,
          borderPad=4, spaceAfter=6)
NT = _sty(fontSize=7.5, leading=10.5, fontName='Helvetica-Oblique',
          textColor=colors.HexColor('#555555'), spaceAfter=4)
RF = _sty(fontSize=7,   leading=10,  fontName='Helvetica',
          textColor=colors.HexColor('#555555'))

def P(txt, sty=None): return Paragraph(txt, sty or N)
def PR(txt, fontName='Courier', **kw):
    return Paragraph(txt, _sty(fontSize=8.5, leading=12,
                               fontName=fontName, alignment=TA_RIGHT, **kw))
def mono(lines):      return Paragraph('<br/>'.join(lines), MN)

def h3(story, txt):
    story.append(P(txt, H3))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GRID, spaceAfter=5))

def std_table(rows, cw, sec_rows=None, warn_rows=None, fail_rows=None, dim_rows=None):
    t = Table(rows, colWidths=cw, repeatRows=1)
    ts = TableStyle([
        ('BACKGROUND',(0,0),(-1,0), NAVY),
        ('TEXTCOLOR',(0,0),(-1,0), colors.white),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,0), 8),
        ('FONTNAME',(0,1),(-1,-1),'Helvetica'),
        ('FONTSIZE',(0,1),(-1,-1), 8.5),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, LGREY]),
        ('GRID',(0,0),(-1,-1), 0.3, GRID),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1), 3),
        ('BOTTOMPADDING',(0,0),(-1,-1), 3),
        ('LEFTPADDING',(0,0),(-1,-1), 6),
        ('RIGHTPADDING',(0,0),(-1,-1), 6),
    ])
    for r in (sec_rows or []):
        ts.add('SPAN',(0,r),(len(cw)-1,r))
        ts.add('BACKGROUND',(0,r),(len(cw)-1,r), LBLUE)
        ts.add('FONTNAME',(0,r),(len(cw)-1,r),'Helvetica-Bold')
    for r in (warn_rows or []):  ts.add('BACKGROUND',(0,r),(-1,r), WARN)
    for r in (fail_rows or []):  ts.add('BACKGROUND',(0,r),(-1,r), FAIL)
    for r in (dim_rows  or []):
        ts.add('BACKGROUND',(0,r),(-1,r), LBLUE)
        ts.add('FONTNAME',(0,r),(-1,r),'Helvetica-Bold')
    t.setStyle(ts)
    return t

def frac(num, den):
    """Inline brøk som liten tabell"""
    t = Table([[P(num, _sty(fontSize=7.5, leading=9, alignment=TA_CENTER))],
               [P(den, _sty(fontSize=7.5, leading=9, alignment=TA_CENTER))]],
              colWidths=[None])
    t.setStyle(TableStyle([
        ('LINEBELOW',(0,0),(0,0), 0.8, colors.black),
        ('LEFTPADDING',(0,0),(-1,-1), 2),
        ('RIGHTPADDING',(0,0),(-1,-1), 2),
        ('TOPPADDING',(0,0),(-1,-1), 0),
        ('BOTTOMPADDING',(0,0),(-1,-1), 1),
    ]))
    return t

# Symboler som ReportLab-XML
def sub(t):  return f'<sub rise="-2" size="7">{t}</sub>'
def sup(t):  return f'<sup rise="3" size="7">{t}</sup>'
def b(t):    return f'<b>{t}</b>'

# Vanlige symboler
Pd   = f'P{sub("d")}'
Pp   = f'P{sub("p")}'
Fk   = f'F{sub("k")}'
Ritd = f'R{sub("itd")}'
Ritk = f'R{sub("itk")}'
As_s = f'A{sub("s")}'
Ag_s = f'A{sub("g")}'
fyk_s= f'f{sub("yk")}'
fuk_s= f'f{sub("uk")}'
gs_s = f'&#947;{sub("s")}'
L1_s = f'L{sub("1")}'
L2_s = f'L{sub("2")}'
Ld_s = f'L{sub("d")}'
lam  = f'&#955;'
lDim = f'&#955;{sub("dim")}'
tdsm = f'&#964;{sub("d,s/m")}'
tdmb = f'&#964;{sub("d,m/b")}'
tksm = f'&#964;{sub("k,s/m")}'
tkmb = f'&#964;{sub("k,m/b")}'
tkb  = f'&#964;{sub("k,berg")}'
psi  = f'&#968;'
alpha= f'&#945;'
gamF = f'&#947;{sub("F")}'
gamM = f'&#947;{sub("M")}'
gamm = f'&#947;{sub("m")}'
eta  = f'&#951;'
sqrt = '&#8730;'
pi_s = '&#960;'
times= '&#215;'
leq  = '&#8804;'
geq  = '&#8805;'
arr  = '&#8594;'
mul  = '&#183;'


# ── Hoved: generer PDF ────────────────────────────────────────────────────────
def generer_pdf(inn, res, meta: dict) -> bytes:
    """
    inn  : Inndata-objekt
    res  : Resultater-objekt
    meta : dict med prosjekt, docnr, rev, av, kont, dato, desc
    Returnerer PDF som bytes (klar for st.download_button)
    """
    from beregning import beregn_fbd_EC2

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=16*mm, bottomMargin=14*mm,
        title=f"Beregningsnotat – {meta.get('prosjekt','')}"
    )
    story = []

    prosjekt = meta.get('prosjekt','–')
    docnr    = meta.get('docnr','–')
    rev      = meta.get('rev','00')
    av       = meta.get('av','–')
    kont     = meta.get('kont','–')
    dato     = meta.get('dato', datetime.date.today().isoformat())
    desc     = meta.get('desc','')

    # ── HEADER ────────────────────────────────────────────────────────────────
    hdr = Table([[
        P(f'<font size="14" color="#1a3a5c"><b>Beregningsnotat</b></font><br/>'
          f'<font size="8" color="#666666">Forankring i berg – innboringslengde</font>', N),
        P(f'<font size="7.5" color="#444444">'
          f'<b>Prosjekt:</b> {prosjekt}<br/>'
          f'<b>Dok.nr:</b> {docnr} &nbsp; <b>Rev:</b> {rev}<br/>'
          f'<b>Beregnet:</b> {av} &nbsp; <b>Kontrollert:</b> {kont}<br/>'
          f'<b>Dato:</b> {dato}</font>', N)
    ]], colWidths=[95*mm, 75*mm])
    hdr.setStyle(TableStyle([('ALIGN',(1,0),(1,0),'RIGHT'),('VALIGN',(0,0),(-1,-1),'TOP')]))
    story.append(hdr)
    story.append(HRFlowable(width='100%', thickness=2, color=NAVY, spaceAfter=8))
    if desc:
        story.append(P(desc, SM))
        story.append(Spacer(1, 4))

    # ── 1. GRUNNLAG ───────────────────────────────────────────────────────────
    h3(story, "1. Grunnlag og metode")
    kat_txt = {'kamstaal_passiv': 'Passiv kamstålbolt (EC3 del 1-1)',
               'forspentstag_EC3del5': 'Forspentstag / GEWI (EC3 del 5, kap. 7.2)',
               'lissestag': 'Lissestag (EC2 del 1-1)'}[inn.stagkategori]
    story.append(P(
        f'Beregning utf&#248;rt iht. SVV h&#229;ndbok V220 (2023) kap. 11.6.4.5, '
        f'EC2 (NS-EN 1992-1-1+NA:2021), EC3 (NS-EN 1993-1-1+NA:2015) og EC7 (NS-EN 1997-1+NA:2020). '
        f'Stagkategori: <b>{kat_txt}</b>. '
        f'{As_s} for kamstal B500NC = {pi_s}&#183;d{sup("2")}/4 (NS 3576-3:2012). '
        f'{lDim} = max({Ld_s}, {lam}). '
        f'Beregnet iht. IPV-INGGEO-002 Bergforankring, versjon A02 (Norconsult 2025-09-18).', NT))

    # ── 2. INNDATA ────────────────────────────────────────────────────────────
    h3(story, "2. Inndata")

    def row(lbl, val, unit, src):
        return [P(lbl, N), PR(str(val)), P(unit, NR), P(src, SM)]

    def srow(lbl):
        return [P(f'<b>{lbl}</b>', _sty(fontSize=7.5, leading=10,
                fontName='Helvetica-Bold', textColor=NAVY)), '', '', '']

    at_txt = {'stang':'Stangst&#229;l / bolt',
              'perm': 'Lisse – permanent (avstandsholdere)',
              'mid':  'Lisse – midlertidig (bunt)'}[inn.lisse_montering]

    rows2 = [
        [P(t, _sty(fontSize=8, fontName='Helvetica-Bold', textColor=colors.white))
         for t in ['Parameter','Verdi','Enhet','Kilde / ref.']],
        srow('Staggeometri og st&#229;ldata'),
        row('Stagtype', inn.stagname, '–', inn.stagsrc),
        row(f'Stagdiameter d{sub("s")}', f'{inn.ds_mm:.0f}', 'mm', 'Valgt'),
        row(f'Borehullsdiameter d{sub("h")}', f'{inn.dh_mm:.0f}', 'mm', 'Valgt'),
        row(f'Nettoareal {As_s}', f'{inn.As_mm2:.0f}', 'mm&#178;', inn.stagsrc),
    ]
    if inn.stagkategori == 'forspentstag_EC3del5':
        rows2.append(row(f'Brutto stammeareal {Ag_s} (ugjenget del)', f'{inn.Ag_mm2:.0f}', 'mm&#178;', 'Leverand&#248;r'))
    rows2 += [
        row(f'Karakt. flytespenning {fyk_s}', f'{inn.fyk_MPa:.0f}', 'MPa', 'NS 3576-3 / prod.'),
        row(f'Karakt. bruddspenning {fuk_s}', f'{inn.fuk_MPa:.0f}', 'MPa', 'NS 3576-3 / prod.'),
        row(f'Partialfaktor st&#229;l {gs_s}', f'{inn.gammaS:.2f}', '–', 'EC3 / NGI'),
    ]
    if inn.stagkategori == 'forspentstag_EC3del5':
        rows2 += [
            row(f'k{sub("t")} – red.faktor gjenget del', f'{inn.kt:.2f}', '–', 'EC3 del 5'),
            row(f'&#947;{sub("M0")} – partialfaktor ugjenget del', f'{inn.gammaM0:.2f}', '–', 'EC3 del 5'),
            row(f'&#947;{sub("M2")} – partialfaktor gjenget del', f'{inn.gammaM2:.2f}', '–', 'EC3 del 5'),
        ]
    rows2 += [
        row(f'Reduksjonsfaktor f{sub("a")} (EC7 NA.A.19)', f'{inn.fa:.2f}', '–', 'EC7 NA'),
        row(f'Ankervinkel {alpha}', f'{inn.alpha_deg:.0f}', '°', 'Prosjekt'),
        srow('Laster'),
        row(f'Karakt. stagkraft {Fk}', f'{inn.Fk_kN:.0f}', 'kN', 'Prosjekt'),
        row(f'Lastfaktor {gamF}', f'{inn.gammaF:.2f}', '–', 'EC7'),
        row(f'Pr&#248;velastfaktor {eta} ({geq} 1,10)', f'{inn.eta_proeve:.2f}', '–', 'V220 / EC7'),
        srow('Bergdata – uttrekk (V220 tab. 11.6.4.5-2)'),
        row(f'Bergkvalitet', '–', '–', 'Ing.geol. vurdering'),
        row(f'Heftfasthet bruddplan {tkb}', f'{inn.tauK_berg_kPa:.0f}', 'kPa', 'V220 tab. 11.6.4.5-2'),
        row(f'Bruddvinkel {psi}', f'{inn.psi_deg:.0f}', '°', 'V220 tab. 11.6.4.5-2'),
        row(f'Materialfaktor berg {gamM}', f'{inn.gammaM_berg:.1f}', '–', 'V220 / NGI'),
        srow('M&#248;rteldata – inngysingslengde (V220 tab. 11.6.4.5-1)'),
        row(f'Heftfasthet m&#248;rtel/berg {tkmb}', f'{inn.tauK_mb_MPa:.1f}', 'MPa', 'V220 tab. 11.6.4.5-1'),
        row(f'Heftfasthet st&#229;l/m&#248;rtel {tksm}', f'{inn.tauK_sm_MPa:.1f}', 'MPa', 'V220'),
        row(f'Partialfaktor m&#248;rtel {gamm}', f'{inn.gammaM_mortel:.2f}', '–', 'V220 / EC2'),
    ]
    sec = [i for i,r in enumerate(rows2) if len(r)==4 and r[1]=='' and r[2]=='' and r[3]=='']
    cw2 = [82*mm, 22*mm, 14*mm, 50*mm]
    story.append(std_table(rows2, cw2, sec_rows=sec))
    story.append(Spacer(1, 4))

    # ── 3. LASTER ─────────────────────────────────────────────────────────────
    h3(story, "3. Beregnede laster")
    story.append(mono([
        f'{Pp} = {eta} {times} {Fk} = {inn.eta_proeve:.2f} {times} {inn.Fk_kN:.0f} kN = <b>{res.Pp_kN:.1f} kN</b>   (pr&#248;velast – grunnlag for {lam})',
        f'{Pd} = {gamF} {times} {Fk} = {inn.gammaF:.2f} {times} {inn.Fk_kN:.0f} kN = <b>{res.Pd_kN:.1f} kN</b>   (dim. strekk – grunnlag for {L1_s}, {L2_s})',
    ]))

    # ── 4. INDRE KAPASITET ────────────────────────────────────────────────────
    h3(story, f"4. Kontroll &#9312; – Indre kapasitet stag")
    if inn.stagkategori == 'kamstaal_passiv':
        story.append(P(f'Iht. EC3 del 1-1 / NGI 20210114-01-R kap. 4.3. '
                       f'Betingelse: 0,8{mul}{fuk_s} &gt; 0,9{mul}{fyk_s}.', NT))
        ec3_lhs = 0.8*inn.fuk_MPa; ec3_rhs = 0.9*inn.fyk_MPa
        ec3_ok  = ec3_lhs > ec3_rhs
        story.append(mono([
            f'EC3: 0,8 {times} {inn.fuk_MPa:.0f} = {ec3_lhs:.0f} MPa '
            f'{"&gt;" if ec3_ok else leq} 0,9 {times} {inn.fyk_MPa:.0f} = {ec3_rhs:.0f} MPa '
            f'{arr} <b>{"OK – flytgrense gjelder" if ec3_ok else "bruddspenning styrer"}</b>',
            '',
            f'{Ritk} = {As_s} {times} {fyk_s} = {inn.As_mm2:.0f} mm&#178; {times} {inn.fyk_MPa:.0f} MPa = {res.Ritk_kN:.1f} kN',
            f'{Ritd} = {Ritk} / {gs_s} {times} f{sub("a")} = {res.Ritk_kN:.1f} / {inn.gammaS:.2f} {times} {inn.fa:.2f} = <b>{res.Ritd_kN:.1f} kN</b>',
            '',
            f'Kontroll: {Pd} = {res.Pd_kN:.1f} kN {"&nbsp;" + leq if res.strek_ok else "&nbsp;&gt;"} {Ritd} = {res.Ritd_kN:.1f} kN {arr} <b>{"OK &#10003;" if res.strek_ok else "IKKE OK &#10007;"}</b>',
        ]))
    elif inn.stagkategori == 'forspentstag_EC3del5':
        story.append(P(f'Iht. EC3 del 5 kap. 7.2 (IPV-INGGEO-002 A02 kap. 2.2). '
                       f'To separate kapasiteter beregnes – laveste verdi er dimensjonerende.', NT))
        story.append(mono([
            f'<b>Gjenget del:</b>',
            f'F{sub("tt,Rd")} = k{sub("t")} {times} f{sub("uk")} {times} {As_s} / &#947;{sub("M2")}',
            f'         = {inn.kt:.2f} {times} {inn.fuk_MPa:.0f} MPa {times} {inn.As_mm2:.0f} mm&#178; / {inn.gammaM2:.2f}',
            f'         = <b>{res.Fttrd_kN:.1f} kN</b>',
            '',
            f'<b>Ugjenget del:</b>',
            f'F{sub("tg,Rd")} = {Ag_s} {times} {fyk_s} / &#947;{sub("M0")}',
            f'         = {inn.Ag_mm2:.0f} mm&#178; {times} {inn.fyk_MPa:.0f} MPa / {inn.gammaM0:.2f}',
            f'         = <b>{res.Ftgrd_kN:.1f} kN</b>',
            '',
            f'F{sub("t,Rd")} = min({res.Fttrd_kN:.1f}, {res.Ftgrd_kN:.1f}) {times} f{sub("a")} = <b>{res.Ritd_kN:.1f} kN</b>',
            f'Kontroll: {Pd} = {res.Pd_kN:.1f} kN {"&nbsp;" + leq if res.strek_ok else "&nbsp;&gt;"} F{sub("t,Rd")} = {res.Ritd_kN:.1f} kN {arr} <b>{"OK &#10003;" if res.strek_ok else "IKKE OK &#10007;"}</b>',
        ]))
    else:
        story.append(mono([
            f'Lissestag – EC2 del 1-1:',
            f'F{sub("t,Rd")} = P{sub("t0,1k")} / {gs_s} {times} f{sub("a")} = {inn.Pt01k_kN:.1f} / {inn.gammaS:.2f} {times} {inn.fa:.2f} = <b>{res.Ritd_kN:.1f} kN</b>',
            '',
            f'Kontroll: {Pd} = {res.Pd_kN:.1f} kN {"&nbsp;" + leq if res.strek_ok else "&nbsp;&gt;"} F{sub("t,Rd")} = {res.Ritd_kN:.1f} kN {arr} <b>{"OK &#10003;" if res.strek_ok else "IKKE OK &#10007;"}</b>',
        ]))
        if not res.Pp_innenfor_grenser:
            story.append(P(f'&#9888; Pr&#248;velastbegrensning (IPV kap. 2.3.1.1): {res.Pp_grense_merknad}',
                           _sty(fontSize=8, fontName='Helvetica-Bold', textColor=RED,
                                backColor=FAIL, borderPad=6, leftIndent=4)))

    # ── 5. INNGYSINGSLENGDE ───────────────────────────────────────────────────
    h3(story, f"5. Kontroll &#9313;&#9314; – Inngysingslengde (heftgrensesnitt)")
    story.append(P(
        f'Dim. heftfastheter: {tdsm} = {inn.tauK_sm_MPa:.2f}/{inn.gammaM_mortel:.2f} = {res.fbd_MPa:.3f} MPa'
        + (f' (&#951;{sub("2")} = {res.eta2:.2f}, EC2)' if inn.bruk_EC2_heft else '')
        + f'  {mul}  {tdmb} = {inn.tauK_mb_MPa:.1f}/{inn.gammaM_mortel:.2f} = {inn.tauK_mb_MPa/inn.gammaM_mortel:.3f} MPa', NT))

    # L1
    l1_lines = [f'<b>&#9313; {L1_s} – St&#229;l/m&#248;rtel</b>  [V220 11.6.4.5-1/3]:',
                f'Grunnlag: {res.L1_grunnlag}']
    if inn.stagkategori == 'kamstaal_passiv':
        Pflyt = inn.As_mm2 * inn.fyk_MPa / 1000
        l1_lines += [
            f'{L1_s} = {As_s} {times} {fyk_s} / ({tdsm} {times} d{sub("s")} {times} {pi_s})',
            f'     = ({inn.As_mm2:.0f} {times} {inn.fyk_MPa:.0f}) / ({res.fbd_MPa:.3f} {times} {inn.ds_mm:.0f} {times} {pi_s})',
            f'     = <b>{res.L1_m:.3f} m</b>',
        ]
    else:
        l1_lines += [
            f'{L1_s} = {Pp} / ({tdsm} {times} d{sub("s")} {times} {pi_s})',
            f'     = {res.Pp_kN:.1f} / ({res.fbd_MPa:.3f} {times} {inn.ds_mm:.1f} {times} {pi_s})',
            f'     = <b>{res.L1_m:.3f} m</b>',
        ]
    l1_lines += [
        '',
        f'<b>&#9314; {L2_s} – M&#248;rtel/berg</b>  [V220 11.6.4.5-4]:',
        f'{L2_s} = {Pd} / ({tdmb} {times} d{sub("h")} {times} {pi_s})',
        f'     = {res.Pd_kN:.1f} / ({inn.tauK_mb_MPa/inn.gammaM_mortel:.3f} {times} {inn.dh_mm:.0f} {times} {pi_s})',
        f'     = <b>{res.L2_m:.3f} m</b>',
        '',
        f'<b>&#9315; {Ld_s} = max({L1_s}, {L2_s}) = max({res.L1_m:.3f}, {res.L2_m:.3f}) = <b>{res.Ld_m:.3f} m</b></b>',
    ]
    story.append(mono(l1_lines))

    # ── 6. BERGSTABILITET ─────────────────────────────────────────────────────
    h3(story, f"6. Kontroll &#9318; – Bergstabilitet mot uttrekk ({lam})")
    story.append(P(
        f'Kjeglemodell iht. V220 formel 11.6.4.5-5. '
        f'{tkb} = {inn.tauK_berg_kPa:.0f} kPa er bergmassens skj&#230;rmotstand langs '
        f'bruddkjeglens overflate (V220 tab. 11.6.4.5-2) – ikke heftfasthet m&#248;rtel/berg. '
        f'sin({alpha}) inng&#229;r for vinklet anker.', NT))
    sinA = math.sin(inn.alpha_deg*PI/180)
    tanP = math.tan(inn.psi_deg*PI/180)
    num  = inn.gammaM_berg * res.Pp_kN * 1000
    den  = inn.tauK_berg_kPa*1000 * PI * tanP * sinA
    story.append(mono([
        f'{lam} = {sqrt}( {gamM} {times} {Pp} / ({tkb} {times} {pi_s} {times} tan({psi}) {times} sin({alpha})) )',
        '',
        f'    = {sqrt}( {inn.gammaM_berg:.1f} {times} {res.Pp_kN*1000:.0f} N',
        f'       / ({inn.tauK_berg_kPa*1000:.0f} Pa {times} {pi_s} {times} tan({inn.psi_deg:.0f}°) {times} sin({inn.alpha_deg:.0f}°)) )',
        '',
        f'    = {sqrt}( {num:.0f} / {den:.2f} )',
        '',
        f'    = <b>{res.lam_m:.3f} m</b>',
    ]))

    # ── 7. OPPSUMMERING ───────────────────────────────────────────────────────
    h3(story, "7. Oppsummering – dimensjonerende innboringslengde")

    def pct(v): return f'{v/res.lDim_m*100:.0f}%' if res.lDim_m > 0 else '–'

    def hdr_cell(t): return P(t, _sty(fontSize=8, fontName='Helvetica-Bold', textColor=colors.white))
    rows_r = [
        [hdr_cell(t) for t in ['Grensesnitt','Lengde (m)','Utn.','Status','Formel']],
        [P(f'&#9313; {L1_s} – st&#229;l/m&#248;rtel', N),
         PR(f'{res.L1_m:.3f}'), PR(pct(res.L1_m)),
         P('<b>Styrende</b>' if res.L1_styrende else 'OK', N),
         P('V220 11.6.4.5-1/3', SM)],
        [P(f'&#9314; {L2_s} – m&#248;rtel/berg', N),
         PR(f'{res.L2_m:.3f}'), PR(pct(res.L2_m)),
         P('<b>Styrende</b>' if res.L2_styrende else 'OK', N),
         P('V220 11.6.4.5-4', SM)],
        [P(f'&#9315; {Ld_s} = max({L1_s}, {L2_s})', B),
         PR(f'{res.Ld_m:.3f}', fontName='Courier-Bold'), PR('–'), P('–', N),
         P('Dim. inngysingslengde', SM)],
        [P(f'&#9318; {lam} – bergstabilitet', N),
         PR(f'{res.lam_m:.3f}'), PR(pct(res.lam_m)),
         P('<b>Dimensjonerende</b>' if res.lamDim else 'OK', N),
         P('V220 11.6.4.5-5', SM)],
        [P(f'<b>{lDim} = max({Ld_s}, {lam})</b>', B),
         P(f'<b>{res.lDim_m:.2f}</b>', _sty(fontSize=10, fontName='Courier-Bold',
                                             alignment=TA_RIGHT, textColor=NAVY)),
         PR('–'),
         P('<b>&#8592; Anbefalt</b>', _sty(fontSize=8.5, fontName='Helvetica-Bold', textColor=NAVY)),
         P('Dimensjonerende', SM)],
    ]
    cw_r = [72*mm, 22*mm, 14*mm, 36*mm, 24*mm]
    warn_r = [1] if res.L1_styrende else ([2] if res.L2_styrende else [])
    fail_r = [3] if res.lamDim else []
    story.append(std_table(rows_r, cw_r, warn_rows=warn_r, fail_rows=fail_r, dim_rows=[5]))
    story.append(Spacer(1, 6))

    # Resultat-boks
    ok_col = GREEN if res.strek_ok else RED
    ok_txt = ('&#10003;  OK  –  P_d ' + leq + ' R_itd') if res.strek_ok else '&#10007;  IKKE OK  –  P_d &gt; R_itd'
    rb = Table([[
        P(f'<font size="7.5" color="#333333">Dimensjonerende innboringslengde i berg</font><br/>'
          f'<font size="20" color="#1a3a5c"><b>{lDim} = {res.lDim_m:.2f} m</b></font>', N),
        P(f'<font size="7.5" color="#333333">Indre kapasitet stag</font><br/>'
          f'<font size="10" color="#{"1a6b2a" if res.strek_ok else "c0392b"}"><b>{ok_txt}</b></font>', N),
    ]], colWidths=[82*mm, 86*mm])
    rb.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1), 2, NAVY),
        ('BACKGROUND',(0,0),(-1,-1), LBLUE),
        ('TOPPADDING',(0,0),(-1,-1), 8), ('BOTTOMPADDING',(0,0),(-1,-1), 8),
        ('LEFTPADDING',(0,0),(-1,-1), 10), ('RIGHTPADDING',(0,0),(-1,-1), 10),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LINEAFTER',(0,0),(0,0), 0.5, GRID),
    ]))
    story.append(rb)
    story.append(Spacer(1, 8))

    # ── 8. REFERANSER ─────────────────────────────────────────────────────────
    h3(story, "8. Referanser")
    for r in [
        '[1] Statens vegvesen (2023). H&#229;ndbok V220 – Geoteknikk i vegbygging, kap. 11.6.4.',
        '[2] NS-EN 1992-1-1:2004+A1:2014+NA:2021. Eurokode 2 – Betongkonstruksjoner.',
        '[3] NS-EN 1993-1-1:2005+A1:2014+NA:2015. Eurokode 3 – St&#229;lkonstruksjoner del 1-1.',
        '[4] NS-EN 1993-1-11:2006+NA:2010. Eurokode 3 – St&#229;lkonstruksjoner del 5 (trekkelementer).',
        '[5] NS-EN 1997-1:2004+A1:2013+NA:2020. Eurokode 7 – Geoteknisk prosjektering.',
        '[6] NGI (2021). Rapport 20210114-01-R – Forankring av skredsikringskonstruksjoner.',
        '[7] Norconsult (2025). IPV-INGGEO-002 Bergforankring, versjon A02.',
        '[8] NS 3576-3:2012. Armerings st&#229;l – M&#229;l og egenskaper – Del 3: Kamstal B500NC.',
    ]: story.append(P(r, RF))
    story.append(Spacer(1, 6))

    # Footer
    story.append(HRFlowable(width='100%', thickness=0.5, color=GRID, spaceBefore=6, spaceAfter=4))
    ft = Table([[
        P(f'{prosjekt} | {docnr} Rev. {rev}',
          _sty(fontSize=7, fontName='Helvetica', textColor=colors.HexColor('#888888'))),
        P(f'Sign. {av} | Kontroll {kont} | {dato}',
          _sty(fontSize=7, fontName='Helvetica', textColor=colors.HexColor('#888888'),
               alignment=TA_RIGHT)),
    ]], colWidths=[84*mm, 84*mm])
    ft.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]))
    story.append(ft)

    doc.build(story)
    return buf.getvalue()
