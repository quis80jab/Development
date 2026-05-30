#!/usr/bin/env python3
"""Render the due-diligence checklist to PDF using reportlab."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_FD = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DejaVu", _FD + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", _FD + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold",
                              italic="DejaVu", boldItalic="DejaVu-Bold")
REG, BOLD = "DejaVu", "DejaVu-Bold"

NAVY = colors.HexColor("#0b3d5c")
LIGHT = colors.HexColor("#eef4f8")
AMBER_BG = colors.HexColor("#fff4e5")
AMBER = colors.HexColor("#d9822b")
RED = colors.HexColor("#b3261e")
RED_BG = colors.HexColor("#fdeceb")
GREY = colors.HexColor("#555555")
LINE = colors.HexColor("#d6d6d6")

styles = getSampleStyleSheet()
styles["Normal"].fontName = REG
S = {}
S["title"] = ParagraphStyle("title", parent=styles["Normal"], fontName=BOLD,
                            fontSize=17, textColor=NAVY, leading=20, spaceAfter=2)
S["sub"] = ParagraphStyle("sub", parent=styles["Normal"], fontSize=9.5, textColor=GREY, leading=12)
S["meta"] = ParagraphStyle("meta", parent=styles["Normal"], fontSize=8, textColor=colors.grey,
                           leading=11, spaceAfter=8)
S["h2"] = ParagraphStyle("h2", parent=styles["Normal"], fontName=BOLD,
                         fontSize=12, textColor=NAVY, leading=14, spaceBefore=12, spaceAfter=5)
S["lead"] = ParagraphStyle("lead", parent=styles["Normal"], fontSize=9.5, leading=13)
S["body"] = ParagraphStyle("body", parent=styles["Normal"], fontSize=9, leading=12)
S["cell"] = ParagraphStyle("cell", parent=styles["Normal"], fontSize=8.7, leading=11)
S["cellwhy"] = ParagraphStyle("cellwhy", parent=styles["Normal"], fontSize=8.2, leading=10,
                              textColor=GREY)
S["th"] = ParagraphStyle("th", parent=styles["Normal"], fontName=BOLD,
                         fontSize=8.5, textColor=colors.white, leading=11)
S["chk"] = ParagraphStyle("chk", parent=styles["Normal"], fontSize=11, textColor=NAVY,
                          alignment=1)
S["foot"] = ParagraphStyle("foot", parent=styles["Normal"], fontSize=7.5, textColor=colors.grey,
                           leading=10)

story = []


def callout(text, bg, bar):
    p = Paragraph(text, S["lead"])
    t = Table([[p]], colWidths=[170 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 3, bar),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def checklist(rows):
    data = [[Paragraph("✓", S["th"]), Paragraph("What to look for", S["th"]),
             Paragraph("Why it matters", S["th"])]]
    for what, why in rows:
        data.append([Paragraph("☐", S["chk"]),
                     Paragraph(what, S["cell"]),
                     Paragraph(why, S["cellwhy"])])
    t = Table(data, colWidths=[9 * mm, 100 * mm, 61 * mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


# ---- Header
story.append(Paragraph("Aircraft Maintenance Shop Takeover &mdash; Due Diligence Checklist", S["title"]))
story.append(Paragraph('Florida-panhandle A&amp;P/IA shop (suspected <b>Oyster Aviation @ KAAF</b>) &nbsp;·&nbsp; "What to look for" before committing', S["sub"]))
story.append(Paragraph("Prepared for Arachnid Systems &nbsp;|&nbsp; Ben &nbsp;|&nbsp; 2026-05-30 &nbsp;|&nbsp; Internal / exploratory", S["meta"]))

story.append(callout(
    "<b>Frame this correctly.</b> This is <b>not a sale</b> &mdash; the owner wants an A&amp;P/IA to "
    "<b>take over</b> a turnkey shop (“not selling, not hiring, just can't do it anymore”). "
    "Evaluate it as a low-cost <b>capability &amp; test-bed</b> play for ATLAS &mdash; a captive hangar, "
    "real aircraft, and a certification on-ramp &mdash; <b>not</b> as an MRO business acquisition. "
    "The single gating requirement is supplying a certificated A&amp;P/IA to operate it.", LIGHT, NAVY))
story.append(Spacer(1, 6))
story.append(callout(
    "<b>Confirm identity first.</b> The Reddit post says only “Florida panhandle” &mdash; it does "
    "<b>not</b> name Oyster Aviation or KAAF. Verify which shop and field this actually is before "
    "anything else; the whole airfield thesis depends on it.", AMBER_BG, AMBER))
story.append(Spacer(1, 4))

sections = [
    ("1. Deal structure &amp; terms", [
        ('Exactly what “take over” means &mdash; money, no money, or lease assignment + equipment handoff?', "Determines whether this is ~free or a real purchase."),
        ("Asset vs. equity transfer; what entity / liabilities (if any) come with it", "Avoid inheriting debts, tax, or legal exposure."),
        ("Whether the owner will stay on (transition / earnout / consulting)", "Key-person continuity — see §6."),
        ("Any exclusivity; how many other parties he's talking to", "Sets urgency and negotiating leverage."),
    ]),
    ("2. Certifications &amp; regulatory (the real prize)", [
        ("Which certificates exist: independent A&amp;P/IA individuals vs. a Part 145 repair station", "A&amp;P/IA is personal to the mechanic; a 145 cert is an asset. Very different value."),
        ("Do certificates / authority <b>transfer</b> on ownership change, or must we re-credential?", "A&amp;P/IA does NOT transfer with a building — you need your own certificated person."),
        ("Ratings / limitations, ops specs, any open FAA findings or enforcement history", "Hidden compliance liabilities."),
        ("Path to add an <b>autonomous-inspection</b> workflow under that authority", "The strategic reason to care — ATLAS sign-off route."),
    ]),
    ("3. The hangar &amp; airport lease", [
        ("Lease term, rent, renewal options, and <b>transferability / assignment</b> rights", "You inherit a leasehold, not land — county can block transfer."),
        ("Landlord = Franklin County? FAA <b>grant-assurance</b> obligations on the field", "Restricts permitted uses, subleasing, exclusive-rights deals."),
        ("Hangar condition, true 5-plane capacity, power / utilities, security", "Fit for ATLAS robotics + ITAR / air-gapped work? Likely needs upgrades."),
        ("Field suitability: non-towered, 3&times; 5,000+ ft runways, near-zero based traffic (KAAF)", "The actual strategic asset — quiet flight-test / UAS environment."),
    ]),
    ("4. Equipment, parts &amp; physical assets", [
        ('Itemized equipment list + condition + calibration certs (“all except hand tools”)', "Confirm what conveys; calibration drives airworthiness sign-offs."),
        ('Parts-room inventory value &amp; traceability (“partially stocked”)', "Untraceable / SUP parts are a liability, not an asset."),
        ("Tooling owned vs. leased; software / maintenance-tracking licenses", "Hidden recurring costs or non-transferable licenses."),
        ("Environmental / hazmat: fuel, solvents, oils, disposal records", "Contamination liability can dwarf the deal value."),
    ]),
    ("5. Financials &amp; the existing book", [
        ('The “planes in the queue” — how many, contracted vs. verbal, $ value', "Immediate-revenue claim — verify it's real and will stay."),
        ('Trailing revenue, margin, and the “low fixed costs” figure (rent, utilities, insurance)', "Baseline operating economics."),
        ("Customer concentration &amp; whether clients follow the new operator", "Goodwill may walk with the owner."),
        ("Insurance: hangar-keepers, product / completed-ops liability, premiums", "MRO liability is significant; sets carrying cost."),
    ]),
    ("6. People &amp; key-person risk  [HIGHEST RISK]", [
        ("Who currently holds the A&amp;P/IA — owner only? Any staff staying?", "“Can't do it anymore” = the capability may leave with him."),
        ("Can <b>Arachnid</b> supply / hire a certificated A&amp;P/IA to run it? At what cost?", "The gating constraint — no IA, no shop."),
        ("Retention / transition terms for the owner (training, customer intros)", "Protects continuity and goodwill."),
        ("Local A&amp;P labor availability (national shortage; ~1/3 AMT seats unfilled)", "Rural panhandle hiring may be hard."),
    ]),
    ("7. Strategic fit with ATLAS / Arachnid", [
        ("Realistic bridge from piston-GA work &rarr; ATLAS's fighter / transport / widebody targets", "Cessna / Piper ≠ defense fleet; validation overlap is partial."),
        ("Can the site support ITAR / air-gapped / secured work, or stay commercial-only?", "Open public field conflicts with defense posture."),
        ("Value of captive aircraft access + labeled defect data for model training", "Core upside — quantify it."),
        ("Management bandwidth: who runs a services business without distracting R&amp;D?", "Mission-drift risk vs. tiny financial weight."),
    ]),
]

for title, rows in sections:
    story.append(Paragraph(title, S["h2"]))
    story.append(checklist(rows))

# ---- Go / No-Go
story.append(Paragraph("Go / No-Go &mdash; the decisive test", S["h2"]))
gng = (
    "<b>PROCEED only if ALL are true:</b><br/>"
    "&bull; Identity &amp; terms confirmed, and total cost (incl. lease + an A&amp;P/IA hire) is low.<br/>"
    "&bull; Lease is transferable and permits Arachnid's intended use.<br/>"
    "&bull; We can secure a certificated A&amp;P/IA operator.<br/>"
    "&bull; There is a credible path from this shop to <b>accelerating ATLAS validation / certification</b> vs. our current partner-access model.<br/><br/>"
    "<b>WALK AWAY if:</b> the work stays piston-GA with no bridge to defense / commercial platforms &bull; "
    "the IA capability can't be secured &bull; the lease is non-transferable &bull; or it becomes a management "
    "distraction relative to its financial weight."
)
gtab = Table([[Paragraph(gng, S["body"])]], colWidths=[170 * mm])
gtab.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), RED_BG),
    ("BOX", (0, 0), (-1, -1), 1.2, RED),
    ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ("TOPPADDING", (0, 0), (-1, -1), 8),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
]))
story.append(gtab)
story.append(Spacer(1, 10))
story.append(Paragraph(
    "Sources &amp; full analysis: <i>oyster-aviation-kaaf-acquisition-analysis.md</i>, "
    "<i>market-research-landscape.md</i>, <i>EXEC-SUMMARY-one-pager.md</i>. &nbsp; "
    "Caveats: shop identity (Oyster / KAAF) is inferred, not confirmed; ATLAS specs / partners drawn from "
    "public website; market figures from third-party research vendors (directional). For internal use.",
    S["foot"]))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(16 * mm, 12 * mm, 194 * mm, 12 * mm)
    canvas.setFont(REG, 7.5)
    canvas.setFillColor(colors.grey)
    canvas.drawString(16 * mm, 8 * mm, "Arachnid Systems — Internal / Exploratory")
    canvas.drawRightString(194 * mm, 8 * mm, "Page %d" % doc.page)
    canvas.restoreState()


doc = BaseDocTemplate("due-diligence-checklist.pdf", pagesize=A4,
                      leftMargin=16 * mm, rightMargin=16 * mm,
                      topMargin=16 * mm, bottomMargin=16 * mm)
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=footer)])
doc.build(story)
print("PDF written")
