"""
rapport.py – PDF-rapportgenerator for bergforankring
Inneholder:
  • Hoveddel: beregningsnotat (kap. 1–8)
  • Vedlegg A: Formelreferanser (stagkategori-filtrert)
  • Vedlegg B: Materialdata (alle stagtyper, bergarter, bergkvalitet)
Alle kapitler og vedlegg filtreres etter valgt stagkategori.
"""
import io, math, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, KeepTogether, PageBreak)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

PI = math.pi
W, H = A4

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
GREY2  = colors.HexColor('#e8edf3')

# ── Stiler ────────────────────────────────────────────────────────────────────
def _sty(base='Normal', **kw):
    from reportlab.lib.styles import getSampleStyleSheet
    styles = getSampleStyleSheet()
    p = styles.get(base, styles['Normal'])
    return ParagraphStyle('_'+str(id(kw)), parent=p, **kw)

N   = _sty(fontSize=8.5, leading=12.5, fontName='Helvetica')
NR  = _sty(fontSize=8.5, leading=12.5, fontName='Helvetica', alignment=TA_RIGHT)
NC  = _sty(fontSize=8.5, leading=12.5, fontName='Helvetica', alignment=TA_CENTER)
B   = _sty(fontSize=8.5, leading=12.5, fontName='Helvetica-Bold')
SM  = _sty(fontSize=7.5, leading=10,   fontName='Helvetica',
           textColor=colors.HexColor('#555555'))
SMR = _sty(fontSize=7.5, leading=10,   fontName='Helvetica',
           textColor=colors.HexColor('#555555'), alignment=TA_RIGHT)
H2s = _sty(fontSize=11,  leading=15,   fontName='Helvetica-Bold',
           textColor=NAVY, spaceBefore=14, spaceAfter=5)
H3s = _sty(fontSize=9.5, leading=13,   fontName='Helvetica-Bold',
           textColor=NAVY, spaceBefore=10, spaceAfter=4)
H4s = _sty(fontSize=8.5, leading=12,   fontName='Helvetica-Bold',
           textColor=NAVY, spaceBefore=7,  spaceAfter=3)
MN  = _sty(fontSize=7.8, leading=12.5, fontName='Courier',
           backColor=LGREY, leftIndent=8, rightIndent=8,
           borderPad=5, spaceAfter=6)
NT  = _sty(fontSize=7.5, leading=10.5, fontName='Helvetica-Oblique',
           textColor=colors.HexColor('#555555'), spaceAfter=4)
RF  = _sty(fontSize=7.5, leading=11,   fontName='Helvetica',
           textColor=colors.HexColor('#444444'))

# ── Hjelpefunksjoner ─────────────────────────────────────────────────────────
def P(txt, sty=None):  return Paragraph(txt, sty or N)
def PR(txt, fn='Courier', **kw):
    return Paragraph(txt, _sty(fontSize=8.5, leading=12, fontName=fn,
                               alignment=TA_RIGHT, **kw))
def mono(lines): return Paragraph('<br/>'.join(lines), MN)

def h2(story, txt):
    story.append(Spacer(1, 4))
    story.append(P(txt, H2s))
    story.append(HRFlowable(width='100%', thickness=1.5, color=NAVY, spaceAfter=6))

def h3(story, txt):
    story.append(P(txt, H3s))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GRID, spaceAfter=5))

def h4(story, txt):
    story.append(P(txt, H4s))

def vedlegg_hdr(story, bokstav, tittel):
    """Ny side med tydelig vedlegg-header"""
    story.append(PageBreak())
    boks = Table([[
        P(f'<font size="11" color="#ffffff"><b>Vedlegg {bokstav}</b></font>', NC),
        P(f'<font size="11" color="#1a3a5c"><b>{tittel}</b></font>', N),
    ]], colWidths=[28*mm, 142*mm])
    boks.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(0,0), NAVY),
        ('BACKGROUND',(1,0),(1,0), LBLUE),
        ('TOPPADDING',(0,0),(-1,-1), 10),
        ('BOTTOMPADDING',(0,0),(-1,-1), 10),
        ('LEFTPADDING',(0,0),(-1,-1), 10),
        ('RIGHTPADDING',(0,0),(-1,-1), 10),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('BOX',(0,0),(-1,-1), 1, NAVY),
    ]))
    story.append(boks)
    story.append(Spacer(1, 10))

def std_table(rows, cw, sec_rows=None, warn_rows=None, fail_rows=None,
              dim_rows=None, alt=True):
    t = Table(rows, colWidths=cw, repeatRows=1)
    bg = [colors.white, LGREY] if alt else [colors.white]
    ts = TableStyle([
        ('BACKGROUND',(0,0),(-1,0), NAVY),
        ('TEXTCOLOR',(0,0),(-1,0), colors.white),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,0), 8),
        ('FONTNAME',(0,1),(-1,-1),'Helvetica'),
        ('FONTSIZE',(0,1),(-1,-1), 8.5),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), bg),
        ('GRID',(0,0),(-1,-1), 0.3, GRID),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1), 3.5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 3.5),
        ('LEFTPADDING',(0,0),(-1,-1), 6),
        ('RIGHTPADDING',(0,0),(-1,-1), 6),
    ])
    for r in (sec_rows or []):
        ts.add('SPAN',(0,r),(len(cw)-1,r))
        ts.add('BACKGROUND',(0,r),(len(cw)-1,r), LBLUE)
        ts.add('FONTNAME',(0,r),(len(cw)-1,r),'Helvetica-Bold')
    for r in (warn_rows or []): ts.add('BACKGROUND',(0,r),(-1,r), WARN)
    for r in (fail_rows or []): ts.add('BACKGROUND',(0,r),(-1,r), FAIL)
    for r in (dim_rows  or []):
        ts.add('BACKGROUND',(0,r),(-1,r), LBLUE)
        ts.add('FONTNAME',(0,r),(-1,r),'Helvetica-Bold')
    t.setStyle(ts)
    return t

# ── Symboler (ReportLab XML) ─────────────────────────────────────────────────
def sub(t): return f'<sub rise="-2" size="7">{t}</sub>'
def sup(t): return f'<sup rise="3" size="7">{t}</sup>'

Pd_s  = f'P{sub("d")}'
Pp_s  = f'P{sub("p")}'
Fk_s  = f'F{sub("k")}'
Ritd  = f'R{sub("itd")}'
Ritk  = f'R{sub("itk")}'
As_s  = f'A{sub("s")}'
Ag_s  = f'A{sub("g")}'
fyk_s = f'f{sub("yk")}'
fuk_s = f'f{sub("uk")}'
gs_s  = f'&#947;{sub("s")}'
L1_s  = f'L{sub("1")}'
L2_s  = f'L{sub("2")}'
Ld_s  = f'L{sub("d")}'
lam_s = f'&#955;'
lDim  = f'&#955;{sub("dim")}'
tdsm  = f'&#964;{sub("d,s/m")}'
tdmb  = f'&#964;{sub("d,m/b")}'
tksm  = f'&#964;{sub("k,s/m")}'
tkmb  = f'&#964;{sub("k,m/b")}'
tkb   = f'&#964;{sub("k,berg")}'
psi_s = f'&#968;'
alp_s = f'&#945;'
gamF  = f'&#947;{sub("F")}'
gamM  = f'&#947;{sub("M")}'
gamm  = f'&#947;{sub("m")}'
eta_s = f'&#951;'
sqrt  = '&#8730;'
pi_s  = '&#960;'
times = '&#215;'
leq   = '&#8804;'
geq   = '&#8805;'
arr   = '&#8594;'
mul   = '&#183;'
phi   = '&#966;'


# ══════════════════════════════════════════════════════════════════════════════
# HOVEDDEL – beregningsnotat
# ══════════════════════════════════════════════════════════════════════════════

def _del_hdr(story, prosjekt, docnr, rev, av, kont, dato, desc):
    hdr = Table([[
        P(f'<font size="14" color="#1a3a5c"><b>Beregningsnotat</b></font><br/>'
          f'<font size="8" color="#666666">Forankring i berg – innboringslengde</font>', N),
        P(f'<font size="7.5" color="#444444">'
          f'<b>Prosjekt:</b> {prosjekt}<br/>'
          f'<b>Dok.nr:</b> {docnr} &nbsp; <b>Rev:</b> {rev}<br/>'
          f'<b>Beregnet:</b> {av} &nbsp; <b>Kontrollert:</b> {kont}<br/>'
          f'<b>Dato:</b> {dato}</font>', N)
    ]], colWidths=[95*mm, 75*mm])
    hdr.setStyle(TableStyle([
        ('ALIGN',(1,0),(1,0),'RIGHT'),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))
    story.append(hdr)
    story.append(HRFlowable(width='100%', thickness=2.5, color=NAVY, spaceAfter=8))
    if desc:
        story.append(P(desc, SM))
        story.append(Spacer(1, 4))


def _kap1_grunnlag(story, inn):
    h3(story, "1. Grunnlag og metode")
    kat_txt = {
        'kamstaal_passiv':      'Passiv kamst&#229;lbolt (EC3 del 1-1 / IPV kap. 4.2)',
        'forspentstag_EC3del5': 'Forspentstag / GEWI (EC3 del 5, kap. 7.2 / IPV kap. 2.2)',
        'lissestag':            'Lissestag (EC2 del 1-1 / IPV kap. 2.2.2)',
    }[inn.stagkategori]
    story.append(P(
        f'Beregning utf&#248;rt iht. SVV h&#229;ndbok <b>V220 (2023)</b> kap. 11.6.4.5, '
        f'<b>EC2</b> (NS-EN 1992-1-1+NA:2021), <b>EC3</b> (NS-EN 1993-1-1+NA:2015 og del 5) '
        f'og <b>EC7</b> (NS-EN 1997-1+NA:2020). '
        f'Stagkategori: <b>{kat_txt}</b>. '
        f'Materialfaktorer og beregningsmetodikk etter '
        f'<b>IPV-INGGEO-002 Bergforankring A02</b> (Norconsult, 2025-09-18). '
        f'{As_s} for kamstal B500NC = {pi_s}&#183;d{sup("2")}/4 per NS 3576-3:2012. '
        f'Se Vedlegg A for formelreferanser og Vedlegg B for materialdata.', NT))
    story.append(P(
        f'Dimensjonerende innboringslengde: '
        f'{lDim} = max({Ld_s}, {lam_s}), der '
        f'{Ld_s} = max({L1_s}, {L2_s}).', NT))


def _kap2_inndata(story, inn):
    h3(story, "2. Inndata")

    def row(lbl, val, unit, src):
        return [P(lbl, N), PR(str(val)), P(unit, NR), P(src, SM)]

    def srow(lbl):
        return [P(f'<b>{lbl}</b>', _sty(fontSize=7.5, leading=10,
                fontName='Helvetica-Bold', textColor=NAVY)), '', '', '']

    at_txt = {
        'stang': 'Stangst&#229;l / bolt',
        'perm':  'Lisse – permanent (avstandsholdere)',
        'mid':   'Lisse – midlertidig (bunt)',
    }[inn.lisse_montering]

    rows = [
        [P(t, _sty(fontSize=8, fontName='Helvetica-Bold', textColor=colors.white))
         for t in ['Parameter', 'Verdi', 'Enhet', 'Kilde / ref.']],
        srow('Staggeometri og st&#229;ldata'),
        row('Stagtype', inn.stagname, '–', inn.stagsrc),
        row(f'Stagdiameter d{sub("s")}', f'{inn.ds_mm:.0f}', 'mm', 'Valgt'),
        row(f'Borehullsdiameter d{sub("h")}', f'{inn.dh_mm:.0f}', 'mm', 'Valgt'),
        row(f'Nettoareal {As_s}', f'{inn.As_mm2:.0f}', 'mm&#178;', inn.stagsrc),
    ]
    if inn.stagkategori == 'forspentstag_EC3del5':
        rows.append(row(f'Brutto stammeareal {Ag_s} (ugjenget)', f'{inn.Ag_mm2:.0f}',
                        'mm&#178;', 'Leverand&#248;r'))
    rows += [
        row(f'Karakt. flytespenning {fyk_s}', f'{inn.fyk_MPa:.0f}', 'MPa', 'NS 3576-3 / prod.'),
        row(f'Karakt. bruddspenning {fuk_s}', f'{inn.fuk_MPa:.0f}', 'MPa', 'NS 3576-3 / prod.'),
        row(f'Partialfaktor st&#229;l {gs_s}', f'{inn.gammaS:.2f}', '–', 'EC3 / NGI'),
    ]
    if inn.stagkategori == 'forspentstag_EC3del5':
        rows += [
            row(f'k{sub("t")} – reduksjonsfaktor gjenget del', f'{inn.kt:.2f}', '–', 'EC3 del 5'),
            row(f'&#947;{sub("M0")} – partialfaktor ugjenget del', f'{inn.gammaM0:.2f}', '–', 'EC3 del 5'),
            row(f'&#947;{sub("M2")} – partialfaktor gjenget del', f'{inn.gammaM2:.2f}', '–', 'EC3 del 5'),
        ]
    if inn.stagkategori == 'lissestag':
        rows += [
            row(f'P{sub("t0,1k")} – karakt. 0,1%-strekkgrense', f'{inn.Pt01k_kN:.1f}', 'kN', 'Leverand&#248;r'),
            row(f'P{sub("tk")} – karakt. bruddlast', f'{inn.Ptk_kN:.1f}', 'kN', 'Leverand&#248;r'),
            row(f'n – antall lisser', f'{inn.n_lisser}', '–', 'Valgt'),
            row('Lissemontering', at_txt, '–', '–'),
        ]
    rows += [
        row(f'Reduksjonsfaktor f{sub("a")} (EC7 NA.A.19)', f'{inn.fa:.2f}', '–', 'EC7 NA'),
        row(f'Ankervinkel {alp_s}', f'{inn.alpha_deg:.0f}', '°', 'Prosjekt'),
        srow('Laster'),
        row(f'Karakt. stagkraft {Fk_s}', f'{inn.Fk_kN:.0f}', 'kN', 'Prosjekt'),
        row(f'Lastfaktor {gamF}', f'{inn.gammaF:.2f}', '–', 'EC7'),
        row(f'Pr&#248;velastfaktor {eta_s} ({geq} 1,10)', f'{inn.eta_proeve:.2f}', '–', 'V220 / EC7'),
        srow('Bergdata – uttrekk (V220 tab. 11.6.4.5-2)'),
        row(f'Karakt. heftfasthet bruddplan {tkb}', f'{inn.tauK_berg_kPa:.0f}', 'kPa', 'V220 tab. 11.6.4.5-2'),
        row(f'Bruddvinkel {psi_s}', f'{inn.psi_deg:.0f}', '°', 'V220 tab. 11.6.4.5-2'),
        row(f'Materialfaktor berg {gamM}', f'{inn.gammaM_berg:.1f}', '–', 'V220 / NGI'),
        srow('M&#248;rteldata – inngysingslengde (V220 tab. 11.6.4.5-1)'),
        row(f'Karakt. heftfasthet m&#248;rtel/berg {tkmb}', f'{inn.tauK_mb_MPa:.1f}', 'MPa', 'V220 tab. 11.6.4.5-1'),
        row(f'Karakt. heftfasthet st&#229;l/m&#248;rtel {tksm}', f'{inn.tauK_sm_MPa:.1f}', 'MPa', 'V220'),
        row(f'Partialfaktor m&#248;rtel {gamm}', f'{inn.gammaM_mortel:.2f}', '–', 'V220 / EC2'),
    ]
    if inn.bruk_EC2_heft:
        rows += [
            row(f'Terningfasthet m&#248;rtel f{sub("c,cube")}', f'{inn.fc_cube_MPa:.0f}', 'MPa', 'EC2'),
            row(f'&#951;{sub("1")} – borehullfaktor', f'{inn.eta1:.2f}', '–', 'EC2 / IPV'),
        ]

    # Finn seksjonsrader
    sec = [i for i, ro in enumerate(rows)
           if len(ro) == 4 and ro[1] == '' and ro[2] == '' and ro[3] == '']
    cw = [82*mm, 22*mm, 14*mm, 50*mm]
    story.append(std_table(rows, cw, sec_rows=sec))
    story.append(Spacer(1, 4))


def _kap3_laster(story, inn, res):
    h3(story, "3. Beregnede laster")
    story.append(mono([
        f'{Pp_s} = {eta_s} {times} {Fk_s} = {inn.eta_proeve:.2f} {times} {inn.Fk_kN:.0f} kN'
        f' = <b>{res.Pp_kN:.1f} kN</b>   (pr&#248;velast – grunnlag for {lam_s})',
        f'{Pd_s} = {gamF} {times} {Fk_s} = {inn.gammaF:.2f} {times} {inn.Fk_kN:.0f} kN'
        f' = <b>{res.Pd_kN:.1f} kN</b>   (dim. strekk – grunnlag for {L1_s}, {L2_s})',
    ]))


def _kap4_indre(story, inn, res):
    h3(story, "4. Kontroll &#9312; – Indre kapasitet stag")

    if inn.stagkategori == 'kamstaal_passiv':
        story.append(P(
            f'Iht. EC3 del 1-1 / NGI 20210114-01-R kap. 4.3. '
            f'Betingelse for &#229; benytte flytgrense: 0,8{mul}{fuk_s} &gt; 0,9{mul}{fyk_s}.',NT))
        ec3_lhs = 0.8 * inn.fuk_MPa
        ec3_rhs = 0.9 * inn.fyk_MPa
        ec3_ok  = ec3_lhs > ec3_rhs
        story.append(mono([
            f'EC3:  0,8 {times} {inn.fuk_MPa:.0f} = {ec3_lhs:.0f} MPa'
            f'  {"&gt;" if ec3_ok else leq}  0,9 {times} {inn.fyk_MPa:.0f} = {ec3_rhs:.0f} MPa'
            f'  {arr}  <b>{"OK – flytgrense gjelder" if ec3_ok else "bruddspenning styrer"}</b>',
            '',
            f'{Ritk} = {As_s} {times} {fyk_s} = {inn.As_mm2:.0f} mm&#178; {times} {inn.fyk_MPa:.0f} MPa'
            f' = {res.Ritk_kN:.1f} kN',
            f'{Ritd} = {Ritk} / {gs_s} {times} f{sub("a")} = {res.Ritk_kN:.1f} / {inn.gammaS:.2f}'
            f' {times} {inn.fa:.2f} = <b>{res.Ritd_kN:.1f} kN</b>',
            '',
            f'Kontroll:  {Pd_s} = {res.Pd_kN:.1f} kN'
            f'  {"&nbsp;" + leq if res.strek_ok else "&nbsp;&gt;"}'
            f'  {Ritd} = {res.Ritd_kN:.1f} kN'
            f'  {arr}  <b>{"OK &#10003;" if res.strek_ok else "IKKE OK &#10007;"}</b>',
        ]))

    elif inn.stagkategori == 'forspentstag_EC3del5':
        story.append(P(
            f'Iht. EC3 del 5 kap. 7.2 (IPV-INGGEO-002 A02 kap. 2.2). '
            f'To separate kapasiteter beregnes – laveste verdi er dimensjonerende:', NT))
        story.append(mono([
            f'<b>Gjenget del:</b>',
            f'F{sub("tt,Rd")} = k{sub("t")} {times} {fuk_s} {times} {As_s} / &#947;{sub("M2")}',
            f'         = {inn.kt:.2f} {times} {inn.fuk_MPa:.0f} MPa {times} {inn.As_mm2:.0f} mm&#178;'
            f' / {inn.gammaM2:.2f}  =  <b>{res.Fttrd_kN:.1f} kN</b>',
            '',
            f'<b>Ugjenget del:</b>',
            f'F{sub("tg,Rd")} = {Ag_s} {times} {fyk_s} / &#947;{sub("M0")}',
            f'         = {inn.Ag_mm2:.0f} mm&#178; {times} {inn.fyk_MPa:.0f} MPa'
            f' / {inn.gammaM0:.2f}  =  <b>{res.Ftgrd_kN:.1f} kN</b>',
            '',
            f'F{sub("t,Rd")} = min({res.Fttrd_kN:.1f}, {res.Ftgrd_kN:.1f})'
            f' {times} f{sub("a")} = <b>{res.Ritd_kN:.1f} kN</b>',
            '',
            f'Kontroll:  {Pd_s} = {res.Pd_kN:.1f} kN'
            f'  {"&nbsp;" + leq if res.strek_ok else "&nbsp;&gt;"}'
            f'  F{sub("t,Rd")} = {res.Ritd_kN:.1f} kN'
            f'  {arr}  <b>{"OK &#10003;" if res.strek_ok else "IKKE OK &#10007;"}</b>',
        ]))

    else:  # lissestag
        story.append(P(
            f'Lissestag – EC2 del 1-1 (IPV kap. 2.2.2). '
            f'Dimensjonerende strekkspenning: F{sub("t,Rd")} = P{sub("t0,1k")} / {gs_s} {times} f{sub("a")}.', NT))
        story.append(mono([
            f'F{sub("t,Rd")} = P{sub("t0,1k")} / {gs_s} {times} f{sub("a")}'
            f' = {inn.Pt01k_kN:.1f} / {inn.gammaS:.2f} {times} {inn.fa:.2f}'
            f' = <b>{res.Ritd_kN:.1f} kN</b>',
            '',
            f'Kontroll:  {Pd_s} = {res.Pd_kN:.1f} kN'
            f'  {"&nbsp;" + leq if res.strek_ok else "&nbsp;&gt;"}'
            f'  F{sub("t,Rd")} = {res.Ritd_kN:.1f} kN'
            f'  {arr}  <b>{"OK &#10003;" if res.strek_ok else "IKKE OK &#10007;"}</b>',
        ]))
        if inn.Ptk_kN > 0:
            story.append(mono([
                f'<b>Pr&#248;velastbegrensninger (IPV kap. 2.3.1.1):</b>',
                f'{Pp_s} = {res.Pp_kN:.1f} kN  {leq}  0,80 {times} P{sub("tk")} = {0.8*inn.Ptk_kN:.1f} kN'
                f'  {arr}  <b>{"OK &#10003;" if res.Pp_kN <= 0.8*inn.Ptk_kN else "IKKE OK &#10007;"}</b>',
                f'{Pp_s} = {res.Pp_kN:.1f} kN  {leq}  0,95 {times} P{sub("t0,1k")} = {0.95*inn.Pt01k_kN:.1f} kN'
                f'  {arr}  <b>{"OK &#10003;" if res.Pp_kN <= 0.95*inn.Pt01k_kN else "IKKE OK &#10007;"}</b>',
            ]))


def _kap5_inngysingslengde(story, inn, res):
    h3(story, f"5. Kontroll &#9313;&#9314; – Inngysingslengde (heftgrensesnitt)")
    eta2_txt = (f', &#951;{sub("2")} = {res.eta2:.2f} (EC2, &#248; &gt; 32 mm)'
                if inn.bruk_EC2_heft or inn.ds_mm > 32 else '')
    story.append(P(
        f'Dimensjonerende heftfastheter: '
        f'{tdsm} = {res.fbd_MPa:.3f} MPa'
        f'{eta2_txt}'
        f'  {mul}  '
        f'{tdmb} = {inn.tauK_mb_MPa:.1f} / {inn.gammaM_mortel:.2f}'
        f' = {inn.tauK_mb_MPa/inn.gammaM_mortel:.3f} MPa', NT))

    # L1
    l1 = [f'<b>&#9313; {L1_s} – St&#229;l/m&#248;rtel</b>  [V220 11.6.4.5-1/3]:',
          f'Grunnlag: {res.L1_grunnlag}']
    if inn.stagkategori == 'kamstaal_passiv':
        Pflyt = inn.As_mm2 * inn.fyk_MPa / 1000
        l1 += [
            f'{L1_s} = {As_s} {times} {fyk_s} / ({tdsm} {times} d{sub("s")} {times} {pi_s})',
            f'     = ({inn.As_mm2:.0f} {times} {inn.fyk_MPa:.0f}) / ({res.fbd_MPa:.3f}'
            f' {times} {inn.ds_mm:.0f} {times} {pi_s})',
            f'     = <b>{res.L1_m:.3f} m</b>',
            f'(Flytelast per IPV kap. 4.2 – ikke {gamF}{times}{Fk_s})',
        ]
    else:
        l1 += [
            f'{L1_s} = {Pp_s} / ({tdsm} {times} d{sub("s")} {times} {pi_s})',
            f'     = {res.Pp_kN:.1f} / ({res.fbd_MPa:.3f} {times} {inn.ds_mm:.1f} {times} {pi_s})',
            f'     = <b>{res.L1_m:.3f} m</b>',
        ]
    l1 += [
        '',
        f'<b>&#9314; {L2_s} – M&#248;rtel/berg</b>  [V220 11.6.4.5-4]:',
        f'{L2_s} = {Pd_s} / ({tdmb} {times} d{sub("h")} {times} {pi_s})',
        f'     = {res.Pd_kN:.1f} / ({inn.tauK_mb_MPa/inn.gammaM_mortel:.3f}'
        f' {times} {inn.dh_mm:.0f} {times} {pi_s})',
        f'     = <b>{res.L2_m:.3f} m</b>',
        '',
        f'<b>&#9315; {Ld_s} = max({L1_s}, {L2_s}) = max({res.L1_m:.3f}, {res.L2_m:.3f})'
        f' = <b>{res.Ld_m:.3f} m</b></b>',
    ]
    story.append(mono(l1))


def _kap6_berguttrekk(story, inn, res):
    h3(story, f"6. Kontroll &#9318; – Bergstabilitet mot uttrekk ({lam_s})")
    story.append(P(
        f'Kjeglemodell iht. V220 formel 11.6.4.5-5. '
        f'{tkb} = {inn.tauK_berg_kPa:.0f} kPa er bergmassens skj&#230;rmotstand langs '
        f'bruddkjeglens overflate (V220 tab. 11.6.4.5-2) – ikke heftfasthet m&#248;rtel/berg. '
        f'sin({alp_s}) inng&#229;r for vinklet anker.', NT))
    sinA = math.sin(inn.alpha_deg * PI / 180)
    tanP = math.tan(inn.psi_deg  * PI / 180)
    num  = inn.gammaM_berg * res.Pp_kN * 1000
    den  = inn.tauK_berg_kPa * 1000 * PI * tanP * sinA
    story.append(mono([
        f'{lam_s} = {sqrt}( {gamM} {times} {Pp_s} / ({tkb} {times} {pi_s}'
        f' {times} tan({psi_s}) {times} sin({alp_s})) )',
        '',
        f'    = {sqrt}( {inn.gammaM_berg:.1f} {times} {res.Pp_kN*1000:.0f} N',
        f'       / ({inn.tauK_berg_kPa*1000:.0f} Pa {times} {pi_s}'
        f' {times} tan({inn.psi_deg:.0f}°) {times} sin({inn.alpha_deg:.0f}°)) )',
        '',
        f'    = {sqrt}( {num:.0f} / {den:.2f} )',
        '',
        f'    = <b>{res.lam_m:.3f} m</b>',
    ]))


def _kap7_oppsummering(story, inn, res):
    h3(story, "7. Oppsummering – dimensjonerende innboringslengde")

    def pct(v):
        return f'{v/res.lDim_m*100:.0f}%' if res.lDim_m > 0 else '–'

    def hc(t):
        return P(t, _sty(fontSize=8, fontName='Helvetica-Bold', textColor=colors.white))

    rows = [
        [hc(t) for t in ['Grensesnitt', 'Lengde (m)', 'Utn.', 'Status', 'Formel']],
        [P(f'&#9313; {L1_s} – st&#229;l/m&#248;rtel', N),
         PR(f'{res.L1_m:.3f}'), PR(pct(res.L1_m)),
         P('<b>Styrende</b>' if res.L1_styrende else 'OK', N),
         P('V220 11.6.4.5-1/3', SM)],
        [P(f'&#9314; {L2_s} – m&#248;rtel/berg', N),
         PR(f'{res.L2_m:.3f}'), PR(pct(res.L2_m)),
         P('<b>Styrende</b>' if res.L2_styrende else 'OK', N),
         P('V220 11.6.4.5-4', SM)],
        [P(f'&#9315; {Ld_s} = max({L1_s}, {L2_s})', B),
         PR(f'{res.Ld_m:.3f}', fn='Courier-Bold'), PR('–'),
         P('–', N), P('Dim. inngysingslengde', SM)],
        [P(f'&#9318; {lam_s} – bergstabilitet', N),
         PR(f'{res.lam_m:.3f}'), PR(pct(res.lam_m)),
         P('<b>Dimensjonerende</b>' if res.lamDim else 'OK', N),
         P('V220 11.6.4.5-5', SM)],
        [P(f'<b>{lDim} = max({Ld_s}, {lam_s})</b>', B),
         P(f'<b>{res.lDim_m:.2f}</b>',
           _sty(fontSize=10, fontName='Courier-Bold', alignment=TA_RIGHT, textColor=NAVY)),
         PR('–'),
         P('<b>&#8592; Anbefalt</b>',
           _sty(fontSize=8.5, fontName='Helvetica-Bold', textColor=NAVY)),
         P('Dimensjonerende', SM)],
    ]
    cw = [72*mm, 22*mm, 14*mm, 36*mm, 24*mm]
    wr = [1] if res.L1_styrende else ([2] if res.L2_styrende else [])
    fr = [4] if res.lamDim else []
    story.append(std_table(rows, cw, warn_rows=wr, fail_rows=fr, dim_rows=[5]))
    story.append(Spacer(1, 7))

    ok_txt = (f'&#10003;  OK  – {Pd_s} {leq} {Ritd}' if res.strek_ok
              else f'&#10007;  IKKE OK  – {Pd_s} &gt; {Ritd}')
    ok_col = '#1a6b2a' if res.strek_ok else '#c0392b'
    rb = Table([[
        P(f'<font size="7.5" color="#333333">Dimensjonerende innboringslengde i berg</font><br/>'
          f'<font size="20" color="#1a3a5c"><b>{lDim} = {res.lDim_m:.2f} m</b></font>', N),
        P(f'<font size="7.5" color="#333333">Indre kapasitet stag</font><br/>'
          f'<font size="10" color="{ok_col}"><b>{ok_txt}</b></font>', N),
    ]], colWidths=[82*mm, 86*mm])
    rb.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1), 2, NAVY),
        ('BACKGROUND',(0,0),(-1,-1), LBLUE),
        ('TOPPADDING',(0,0),(-1,-1), 9), ('BOTTOMPADDING',(0,0),(-1,-1), 9),
        ('LEFTPADDING',(0,0),(-1,-1), 12), ('RIGHTPADDING',(0,0),(-1,-1), 12),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LINEAFTER',(0,0),(0,0), 0.5, GRID),
    ]))
    story.append(rb)


def _kap8_referanser(story, inn):
    h3(story, "8. Referanser")
    refs = [
        '[1] Statens vegvesen (2023). <b>H&#229;ndbok V220</b> – Geoteknikk i vegbygging, kap. 11.6.4.',
        '[2] NS-EN 1992-1-1:2004+A1:2014+NA:2021. <b>Eurokode 2</b> – Betongkonstruksjoner.',
        '[3] NS-EN 1993-1-1:2005+A1:2014+NA:2015. <b>Eurokode 3 del 1-1</b> – St&#229;lkonstruksjoner.',
        '[4] NS-EN 1993-1-11:2006+NA:2010. <b>Eurokode 3 del 5</b> – Trekkelementer.',
        '[5] NS-EN 1997-1:2004+A1:2013+NA:2020. <b>Eurokode 7</b> – Geoteknisk prosjektering.',
        '[6] NGI (2021). Rapport <b>20210114-01-R</b> – Forankring av skredsikringskonstruksjoner.',
        '[7] Norconsult (2025). <b>IPV-INGGEO-002 Bergforankring</b>, versjon A02, 2025-09-18.',
        '[8] NS 3576-3:2012. Armerings st&#229;l – M&#229;l og egenskaper – Del 3: <b>Kamstal B500NC</b>.',
    ]
    # Vis kun EC3 del 5-referansen for forspentstag
    for i, r in enumerate(refs):
        if i == 3 and inn.stagkategori != 'forspentstag_EC3del5':
            continue
        story.append(P(r, RF))
    story.append(Spacer(1, 6))


def _footer(story, prosjekt, docnr, rev, av, kont, dato):
    story.append(HRFlowable(width='100%', thickness=0.5, color=GRID,
                            spaceBefore=8, spaceAfter=4))
    ft = Table([[
        P(f'{prosjekt} | {docnr} Rev. {rev}',
          _sty(fontSize=7, fontName='Helvetica',
               textColor=colors.HexColor('#888888'))),
        P(f'Sign. {av} | Kontroll {kont} | {dato}',
          _sty(fontSize=7, fontName='Helvetica',
               textColor=colors.HexColor('#888888'), alignment=TA_RIGHT)),
    ]], colWidths=[84*mm, 84*mm])
    ft.setStyle(TableStyle([
        ('LEFTPADDING',(0,0),(-1,-1),0),
        ('RIGHTPADDING',(0,0),(-1,-1),0),
    ]))
    story.append(ft)


# ══════════════════════════════════════════════════════════════════════════════
# VEDLEGG A – Formelreferanser (stagkategori-filtrert)
# ══════════════════════════════════════════════════════════════════════════════

def _vedlegg_A(story, inn):
    vedlegg_hdr(story, 'A', 'Formelreferanser')

    kat = inn.stagkategori

    # ── A.1 Laster ─────────────────────────────────────────────────────────
    h3(story, "A.1  Beregnede laster")
    story.append(std_table([
        [P(t, _sty(fontSize=8, fontName='Helvetica-Bold', textColor=colors.white))
         for t in ['Symbol', 'Formel', 'Enhet', 'Ref.']],
        [P(Pp_s, B), P(f'{Pp_s} = {eta_s} {times} {Fk_s}', N), P('kN', NR),
         P('V220 / EC7', SM)],
        [P(Pd_s, B), P(f'{Pd_s} = {gamF} {times} {Fk_s}', N), P('kN', NR),
         P('EC7', SM)],
    ], [20*mm, 90*mm, 18*mm, 42*mm]))
    story.append(P(
        f'{Pp_s} (pr&#248;velast) er grunnlag for berguttrekk {lam_s}. '
        f'{Pd_s} (dim. strekk) er grunnlag for inngysingslengdene {L1_s} og {L2_s}. '
        f'Krav: {eta_s} {geq} 1,10.', NT))
    story.append(Spacer(1, 6))

    # ── A.2 Indre kapasitet ─────────────────────────────────────────────────
    h3(story, "A.2  Indre kapasitet stag &#9312;")

    if kat == 'kamstaal_passiv':
        h4(story, "Passiv kamst&#229;lbolt – EC3 del 1-1")
        story.append(std_table([
            [P(t, _sty(fontSize=8, fontName='Helvetica-Bold', textColor=colors.white))
             for t in ['Symbol', 'Formel', 'Enhet', 'Ref.']],
            [P('Betingelse', B),
             P(f'0,8 {times} {fuk_s} &gt; 0,9 {times} {fyk_s}', N), P('–', NR),
             P('EC3 7.2.2', SM)],
            [P(Ritk, B), P(f'{Ritk} = {As_s} {times} {fyk_s}', N), P('kN', NR),
             P('EC3', SM)],
            [P(Ritd, B), P(f'{Ritd} = {Ritk} / {gs_s} {times} f{sub("a")}', N), P('kN', NR),
             P('EC3 / EC7', SM)],
            [P('Kontroll', B), P(f'{Pd_s} {leq} {Ritd}', N), P('–', NR), P('–', SM)],
        ], [20*mm, 90*mm, 18*mm, 42*mm]))
        story.append(P(
            f'{As_s} = {pi_s} {times} d{sub("s")}{sup("2")} / 4 etter NS 3576-3:2012 (kamstal B500NC). '
            f'Dersom 0,8{mul}{fuk_s} {leq} 0,9{mul}{fyk_s} benyttes: {Ritk} = {As_s} {times} {fuk_s} {times} (0,8/0,9).', NT))

    elif kat == 'forspentstag_EC3del5':
        h4(story, "Forspentstag / GEWI – EC3 del 5 kap. 7.2")
        story.append(std_table([
            [P(t, _sty(fontSize=8, fontName='Helvetica-Bold', textColor=colors.white))
             for t in ['Symbol', 'Formel', 'Enhet', 'Ref.']],
            [P(f'F{sub("tt,Rd")}', B),
             P(f'F{sub("tt,Rd")} = k{sub("t")} {times} {fuk_s} {times} {As_s} / &#947;{sub("M2")}', N),
             P('kN', NR), P('EC3 del 5 7.2', SM)],
            [P(f'F{sub("tg,Rd")}', B),
             P(f'F{sub("tg,Rd")} = {Ag_s} {times} {fyk_s} / &#947;{sub("M0")}', N),
             P('kN', NR), P('EC3 del 5 7.2', SM)],
            [P(f'F{sub("t,Rd")}', B),
             P(f'F{sub("t,Rd")} = min(F{sub("tt,Rd")}, F{sub("tg,Rd")}) {times} f{sub("a")}', N),
             P('kN', NR), P('EC3 del 5', SM)],
            [P('Kontroll', B), P(f'{Pd_s} {leq} F{sub("t,Rd")}', N), P('–', NR), P('–', SM)],
        ], [20*mm, 90*mm, 18*mm, 42*mm]))
        story.append(P(
            f'{As_s} = spenningsareal (gjenget del, ISO 262). '
            f'{Ag_s} = nominelt stammeareal (ugjenget del). '
            f'k{sub("t")} = 0,9, &#947;{sub("M0")} = 1,05, &#947;{sub("M2")} = 1,25.', NT))

    else:  # lissestag
        h4(story, "Lissestag – EC2 del 1-1")
        story.append(std_table([
            [P(t, _sty(fontSize=8, fontName='Helvetica-Bold', textColor=colors.white))
             for t in ['Symbol', 'Formel', 'Enhet', 'Ref.']],
            [P(f'F{sub("t,Rd")}', B),
             P(f'F{sub("t,Rd")} = P{sub("t0,1k")} / {gs_s} {times} f{sub("a")}', N),
             P('kN', NR), P('EC2 / IPV', SM)],
            [P('Kontroll', B), P(f'{Pd_s} {leq} F{sub("t,Rd")}', N), P('–', NR), P('–', SM)],
            [P(f'Pr&#248;velast', B),
             P(f'{Pp_s} {leq} 0,80 {times} P{sub("tk")}', N), P('kN', NR),
             P('IPV 2.3.1.1', SM)],
            [P('', N),
             P(f'{Pp_s} {leq} 0,95 {times} P{sub("t0,1k")}', N), P('kN', NR),
             P('IPV 2.3.1.1', SM)],
        ], [20*mm, 90*mm, 18*mm, 42*mm]))
        story.append(P(
            f'P{sub("t0,1k")} = karakteristisk 0,1%-strekkgrense for spennst&#229;let. '
            f'&#947;{sub("s")} = 1,10 for spennst&#229;l iht. EC2. '
            f'Pr&#248;velastbegrensningene gjelder for lissestag iht. IPV kap. 2.3.1.1.', NT))

    story.append(Spacer(1, 6))

    # ── A.3 L1 ─────────────────────────────────────────────────────────────
    h3(story, f"A.3  Inngysingslengde {L1_s} – st&#229;l/m&#248;rtel &#9313;")

    if kat == 'kamstaal_passiv':
        story.append(P(
            f'For passive kamst&#229;lbolter dimensjoneres {L1_s} med flytelast (IPV kap. 4.2), '
            f'ikke med {gamF}{times}{Fk_s}:', NT))
        story.append(std_table([
            [P(t, _sty(fontSize=8, fontName='Helvetica-Bold', textColor=colors.white))
             for t in ['Formel', 'Enhet', 'Ref.']],
            [P(f'{L1_s} = {As_s} {times} {fyk_s} / ({tdsm} {times} d{sub("s")} {times} {pi_s})',N),
             P('m', NR), P('V220 11.6.4.5-1 / IPV 4.2', SM)],
            [P(f'{tdsm} = {tksm} / {gamm}', N), P('MPa', NR), P('V220', SM)],
        ], [122*mm, 14*mm, 34*mm]))
    elif kat == 'forspentstag_EC3del5':
        story.append(P(
            f'For forspente stangstag benyttes pr&#248;velast {Pp_s} som dimensjonerende last:', NT))
        story.append(std_table([
            [P(t, _sty(fontSize=8, fontName='Helvetica-Bold', textColor=colors.white))
             for t in ['Montering', 'Formel', 'Ref.']],
            [P('Stangstag', N),
             P(f'{L1_s} = {Pp_s} / ({tdsm} {times} d{sub("s")} {times} {pi_s})', N),
             P('V220 11.6.4.5-3', SM)],
        ], [28*mm, 100*mm, 42*mm]))
    else:  # lissestag
        story.append(std_table([
            [P(t, _sty(fontSize=8, fontName='Helvetica-Bold', textColor=colors.white))
             for t in ['Montering', 'Formel', 'Ref.']],
            [P('Permanent (avstandsh.)', N),
             P(f'{L1_s} = {Pp_s} / (n {times} {tdsm} {times} d{sub("lisse")} {times} {pi_s})', N),
             P('V220 11.6.4.5-3', SM)],
            [P('Midlertidig (bunt)', N),
             P(f'd{sub("ekv")} = {sqrt}(1,2 {times} n) {times} d{sub("lisse")}, '
               f'{L1_s} = {Pp_s} / ({tdsm} {times} d{sub("ekv")} {times} {pi_s})', N),
             P('V220 11.6.4.5-1', SM)],
        ], [30*mm, 100*mm, 40*mm]))

    story.append(Spacer(1, 4))

    # ── A.4 L2 ─────────────────────────────────────────────────────────────
    h3(story, f"A.4  Inngysingslengde {L2_s} – m&#248;rtel/berg &#9314;")
    story.append(std_table([
        [P(t, _sty(fontSize=8, fontName='Helvetica-Bold', textColor=colors.white))
         for t in ['Formel', 'Enhet', 'Ref.']],
        [P(f'{L2_s} = {Pd_s} / ({tdmb} {times} d{sub("h")} {times} {pi_s})', N),
         P('m', NR), P('V220 11.6.4.5-4', SM)],
        [P(f'{tdmb} = {tkmb} / {gamm}', N), P('MPa', NR), P('V220 tab. 11.6.4.5-1', SM)],
    ], [122*mm, 14*mm, 34*mm]))
    story.append(P(
        f'{tkmb} er heftfastheten mellom m&#248;rtel og borehullsvegg i <b>MPa</b> '
        f'(V220 tab. 11.6.4.5-1). Dette er <b>ikke</b> det samme som {tkb} i kPa '
        f'for berguttrekk (tab. 11.6.4.5-2).', NT))
    story.append(Spacer(1, 6))

    # ── A.5 Berguttrekk ─────────────────────────────────────────────────────
    h3(story, f"A.5  Bergstabilitet mot uttrekk ({lam_s}) &#9318;")
    story.append(std_table([
        [P(t, _sty(fontSize=8, fontName='Helvetica-Bold', textColor=colors.white))
         for t in ['Formel', 'Enhet', 'Ref.']],
        [P(f'{lam_s} = {sqrt}( {gamM} {times} {Pp_s} / ({tkb} {times} {pi_s}'
           f' {times} tan({psi_s}) {times} sin({alp_s})) )', N),
         P('m', NR), P('V220 11.6.4.5-5', SM)],
    ], [122*mm, 14*mm, 34*mm]))
    story.append(P(
        f'{tkb} er bergmassens skj&#230;rmotstand langs bruddkjeglens overflate i <b>kPa</b> '
        f'(V220 tab. 11.6.4.5-2). '
        f'{psi_s} = bruddvinkel. sin({alp_s}) korreksjon for vinklet anker. '
        f'{gamM} = materialfaktor bergmasse (anbefalt 2–3).', NT))
    story.append(Spacer(1, 6))

    # ── A.6 Dim. lengde ─────────────────────────────────────────────────────
    h3(story, f"A.6  Dimensjonerende innboringslengde")
    story.append(std_table([
        [P(t, _sty(fontSize=8, fontName='Helvetica-Bold', textColor=colors.white))
         for t in ['Trinn', 'Formel', 'Ref.']],
        [P('1', NC),
         P(f'{Ld_s} = max({L1_s}, {L2_s})', N), P('V220 11.6.4.5', SM)],
        [P('2', NC),
         P(f'{lDim} = max({Ld_s}, {lam_s})', N), P('V220 11.6.4.5', SM)],
    ], [12*mm, 118*mm, 40*mm]))
    story.append(P(
        f'Ved stagrekke (n {geq} 2 stag) benyttes V220 formel 11.6.4.5-9 for '
        f'berguttrekk av rekken samlet.', NT))


# ══════════════════════════════════════════════════════════════════════════════
# VEDLEGG B – Materialdata
# ══════════════════════════════════════════════════════════════════════════════

def _vedlegg_B(story, inn):
    from beregning import STAG_DB, BERGARTER, BERGKVALITET, beregn, Inndata

    vedlegg_hdr(story, 'B', 'Materialdata og tabellgrunnlag')

    kat = inn.stagkategori
    kat_navn = {
        'kamstaal_passiv':      'Passive kamst&#229;lbolter',
        'forspentstag_EC3del5': 'Forspente stangstag',
        'lissestag':            'Lissestag',
    }

    # ── B.1 Stagtyper (filtrert etter kategori) ──────────────────────────────
    h3(story, f"B.1  Stagtyper – {kat_navn[kat]}")
    story.append(P(
        f'Tabellen viser stagtyper i valgt kategori med kapasitet beregnet for standard '
        f'parametere (V220, {gamF}=1,35, f{sub("a")}=1,0).', NT))

    stag_i_kat = [s for s in STAG_DB if s['kat'] == kat]

    hc = lambda t: P(t, _sty(fontSize=7.5, fontName='Helvetica-Bold', textColor=colors.white))

    if kat == 'kamstaal_passiv':
        rows_b = [[hc(t) for t in ['Stagtype', 'd_s', 'd_h', 'As', 'fyk', 'fuk', 'γs', 'Ritd', 'Kilde']]]
        for s in stag_i_kat:
            inn_tmp = Inndata(stagkategori=s['kat'], ds_mm=s['ds'], dh_mm=s['dh'],
                              fyk_MPa=s['fyk'], fuk_MPa=s['fuk'],
                              As_mm2=s['As'], Ag_mm2=s['Ag'], gammaS=s['gs'])
            from beregning import beregn
            res_tmp = beregn(inn_tmp)
            rows_b.append([
                P(s['navn'], SM),
                PR(f'{s["ds"]:.0f}', fn='Helvetica'), PR(f'{s["dh"]:.0f}', fn='Helvetica'),
                PR(f'{s["As"]:.0f}', fn='Helvetica'), PR(f'{s["fyk"]:.0f}', fn='Helvetica'),
                PR(f'{s["fuk"]:.0f}', fn='Helvetica'), PR(f'{s["gs"]:.2f}', fn='Helvetica'),
                PR(f'{res_tmp.Ritd_kN:.0f}', fn='Helvetica-Bold'),
                P(s['src'], SM),
            ])
        cw_b = [40*mm, 10*mm, 10*mm, 12*mm, 12*mm, 12*mm, 11*mm, 14*mm, 49*mm]
        story.append(std_table(rows_b, cw_b))
        story.append(P(
            f'{As_s} = {pi_s}{times}d{sub("s")}{sup("2")}/4 (nominelt stammeareal, NS 3576-3:2012). '
            f'{Ritd} beregnet med f{sub("a")}=1,0, {gamF}=1,35.', NT))

    elif kat == 'forspentstag_EC3del5':
        rows_b = [[hc(t) for t in ['Stagtype', 'd_s', 'd_h', 'As', 'Ag', 'fyk', 'fuk', 'Ftt,Rd', 'Ftg,Rd', 'Ft,Rd']]]
        for s in stag_i_kat:
            inn_tmp = Inndata(stagkategori=s['kat'], ds_mm=s['ds'], dh_mm=s['dh'],
                              fyk_MPa=s['fyk'], fuk_MPa=s['fuk'],
                              As_mm2=s['As'], Ag_mm2=s['Ag'], gammaS=s['gs'])
            res_tmp = beregn(inn_tmp)
            rows_b.append([
                P(s['navn'], SM),
                PR(f'{s["ds"]:.0f}', fn='Helvetica'), PR(f'{s["dh"]:.0f}', fn='Helvetica'),
                PR(f'{s["As"]:.0f}', fn='Helvetica'), PR(f'{s["Ag"]:.0f}', fn='Helvetica'),
                PR(f'{s["fyk"]:.0f}', fn='Helvetica'), PR(f'{s["fuk"]:.0f}', fn='Helvetica'),
                PR(f'{res_tmp.Fttrd_kN:.0f}', fn='Helvetica'),
                PR(f'{res_tmp.Ftgrd_kN:.0f}', fn='Helvetica'),
                PR(f'{res_tmp.Ritd_kN:.0f}', fn='Helvetica-Bold'),
            ])
        cw_b = [34*mm,9*mm,9*mm,11*mm,11*mm,11*mm,11*mm,15*mm,15*mm,14*mm]
        story.append(std_table(rows_b, cw_b))
        story.append(P(
            f'{As_s} = spenningsareal (gjenget del, ISO 262). '
            f'{Ag_s} = nominelt stammeareal (ugjenget). '
            f'k{sub("t")}=0,9, &#947;{sub("M0")}=1,05, &#947;{sub("M2")}=1,25.', NT))

    else:  # lissestag
        rows_b = [[hc(t) for t in ['Stagtype', 'dlisse', 'dh', 'n', 'As,tot', 'fyk', 'fuk', 'γs', 'Kilde']]]
        for s in stag_i_kat:
            rows_b.append([
                P(s['navn'], SM),
                PR(f'{s["ds"]:.2f}', fn='Helvetica'), PR(f'{s["dh"]:.0f}', fn='Helvetica'),
                PR(f'{s.get("n",1)}', fn='Helvetica'), PR(f'{s["As"]:.0f}', fn='Helvetica'),
                PR(f'{s["fyk"]:.0f}', fn='Helvetica'), PR(f'{s["fuk"]:.0f}', fn='Helvetica'),
                PR(f'{s["gs"]:.2f}', fn='Helvetica'), P(s['src'], SM),
            ])
        cw_b = [38*mm,14*mm,10*mm,10*mm,14*mm,12*mm,12*mm,11*mm,49*mm]
        story.append(std_table(rows_b, cw_b))

    story.append(Spacer(1, 8))

    # ── B.2 Heftfasthet mørtel/berg ─────────────────────────────────────────
    h3(story, "B.2  Heftfasthet m&#248;rtel/berg – V220 tabell 11.6.4.5-1")
    story.append(P(
        f'Karakteristisk heftfasthet {tkmb} i kontaktsonen mellom st&#248;rknet m&#248;rtel '
        f'og borehullsvegg. Forutsetter m&#248;rtel min. B30. '
        f'Dimensjonerende: {tdmb} = {tkmb} / {gamm}.', NT))
    rows_berg = [
        [hc(t) for t in ['Bergart', 'τk,m/b (MPa)', 'γ (kN/m³)', 'τd,m/b (MPa, γm=1,25)']],
    ]
    for navn, data in BERGARTER.items():
        rows_berg.append([
            P(navn, N),
            PR(f'{data["tauMB"]:.1f}', fn='Helvetica-Bold'),
            PR(f'{data["gamma"]}', fn='Helvetica'),
            PR(f'{data["tauMB"]/1.25:.2f}', fn='Helvetica'),
        ])
    cw_bg = [45*mm, 35*mm, 30*mm, 60*mm]
    story.append(std_table(rows_berg, cw_bg))
    story.append(Spacer(1, 8))

    # ── B.3 Bergkvalitet / bruddplan ────────────────────────────────────────
    h3(story, "B.3  Bergkvalitet og skj&#230;rmotstand – V220 tabell 11.6.4.5-2")
    story.append(P(
        f'Karakteristisk skj&#230;rmotstand {tkb} langs bruddkjeglens overflate i <b>kPa</b>. '
        f'Velges etter oppsprekkingsgrad og bergets enkeltaksiale trykkfasthet &#963;{sub("c")}. '
        f'Dette er <b>ikke</b> heftfastheten mørtel/berg (tab. 11.6.4.5-1).', NT))
    rows_bk = [
        [hc(t) for t in ['Bergkvalitet', 'Sprekkesett', 'σc (MPa)', 'τk (kPa)', 'ψmaks (°)']],
    ]
    bk_data = [
        ('Meget godt berg', '1', '&gt; 50', '100–200', '45'),
        ('Middels berg',    '2', '15–50',   '50–100',  '40'),
        ('D&#229;rlig berg','3', '&lt; 15', '50',      '30'),
    ]
    for row_bk in bk_data:
        rows_bk.append([P(row_bk[0], N)] + [PR(v, fn='Helvetica') for v in row_bk[1:]])
    story.append(std_table(rows_bk, [50*mm, 28*mm, 22*mm, 28*mm, 22*mm]))
    story.append(Spacer(1, 8))

    # ── B.4 Partialfaktorer ─────────────────────────────────────────────────
    h3(story, "B.4  Partialfaktorer")
    rows_pf = [
        [hc(t) for t in ['Parameter', 'Symbol', 'Verdi', 'Kilde']],
    ]
    pf_alle = [
        ('Lastfaktor ULS', gamF, '1,35', 'EC7'),
        ('Pr&#248;velastfaktor', f'{eta_s} ({geq}1,10)', '1,10', 'V220 / EC7'),
        ('Partialfaktor bergmasse', gamM, '2,0–3,0', 'V220 / NGI'),
        ('Partialfaktor m&#248;rtel', gamm, '1,25', 'V220 / EC2'),
    ]
    if kat == 'kamstaal_passiv':
        pf_alle += [
            (f'Partialfaktor st&#229;l – statisk last', f'&#947;{sub("s")}', '1,15', 'EC3'),
            (f'Partialfaktor st&#229;l – impulslast (NGI)', f'&#947;{sub("s")}', '1,35', 'NGI tab. 4'),
        ]
    elif kat == 'forspentstag_EC3del5':
        pf_alle += [
            (f'Reduksjonsfaktor gjenget del', f'k{sub("t")}', '0,90', 'EC3 del 5'),
            (f'Partialfaktor ugjenget del', f'&#947;{sub("M0")}', '1,05', 'EC3 del 5'),
            (f'Partialfaktor gjenget del', f'&#947;{sub("M2")}', '1,25', 'EC3 del 5'),
        ]
    elif kat == 'lissestag':
        pf_alle += [
            (f'Partialfaktor spennst&#229;l', f'&#947;{sub("s")}', '1,10', 'EC2'),
        ]
    pf_alle.append(
        (f'Reduksjonsfaktor konstruksjonsdeler f{sub("a")}', f'f{sub("a")}',
         '0,6 (perm.) / 0,9 (midle.)', 'EC7 NA.A.19'),
    )
    for lbl, sym, val, kil in pf_alle:
        rows_pf.append([P(lbl, N), P(sym, NC), PR(val, fn='Helvetica'), P(kil, SM)])
    story.append(std_table(rows_pf, [70*mm, 28*mm, 38*mm, 34*mm]))


# ══════════════════════════════════════════════════════════════════════════════
# HOVED – generer_pdf()
# ══════════════════════════════════════════════════════════════════════════════

def generer_pdf(inn, res, meta: dict) -> bytes:
    """
    inn  : Inndata-objekt
    res  : Resultater-objekt
    meta : dict med prosjekt, docnr, rev, av, kont, dato, desc
    Returnerer PDF som bytes (klar for st.download_button)
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=16*mm, bottomMargin=14*mm,
        title=f"Beregningsnotat – {meta.get('prosjekt','')}"
    )

    prosjekt = meta.get('prosjekt', '–')
    docnr    = meta.get('docnr',    '–')
    rev      = meta.get('rev',      '00')
    av       = meta.get('av',       '–')
    kont     = meta.get('kont',     '–')
    dato     = meta.get('dato',     datetime.date.today().isoformat())
    desc     = meta.get('desc',     '')

    story = []

    # ── Hoveddel ──────────────────────────────────────────────────────────────
    _del_hdr(story, prosjekt, docnr, rev, av, kont, dato, desc)
    _kap1_grunnlag(story, inn)
    _kap2_inndata(story, inn)
    _kap3_laster(story, inn, res)
    _kap4_indre(story, inn, res)
    _kap5_inngysingslengde(story, inn, res)
    _kap6_berguttrekk(story, inn, res)
    _kap7_oppsummering(story, inn, res)
    _kap8_referanser(story, inn)
    _footer(story, prosjekt, docnr, rev, av, kont, dato)

    # ── Vedlegg A ─────────────────────────────────────────────────────────────
    _vedlegg_A(story, inn)
    _footer(story, prosjekt, docnr, rev, av, kont, dato)

    # ── Vedlegg B ─────────────────────────────────────────────────────────────
    _vedlegg_B(story, inn)
    _footer(story, prosjekt, docnr, rev, av, kont, dato)

    doc.build(story)
    return buf.getvalue()
