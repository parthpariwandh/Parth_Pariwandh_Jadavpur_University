"""Build the static clinician dashboard and the two required PDFs."""

from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
NAVY = colors.HexColor("#1f4e79")
TEAL = colors.HexColor("#0f6c6c")
SAND = colors.HexColor("#f4f1ea")
RULE = colors.HexColor("#d5dbe3")


def dashboard() -> None:
    ehr = pd.read_csv(ROOT / "sample_data" / "synthetic_ehr.csv")
    cgm = pd.read_csv(ROOT / "sample_data" / "synthetic_cgm.csv")
    test = pd.read_csv(ROOT / "results" / "test_predictions.csv")
    picks = ["SYN-109", "SYN-044"]
    cards = []
    for pid in picks:
        row = ehr[ehr.patient_id == pid].iloc[0]
        series = cgm[(cgm.patient_id == pid) & (cgm.minute_from_meal >= -60)]
        pred = test[test.patient_id == pid].iloc[0]
        pts = " ".join(
            f"{int(r.minute_from_meal)},{160 - (r.cgm_mg_dl - 80) * 0.55:.1f}" for r in series.itertuples()
        )
        flag = "Flag: peak forecast at or above 180 mg/dL" if pred.predicted_peak_mg_dl >= 180 else "Flag: peak forecast below 180 mg/dL"
        cards.append(
            f"""<section>
            <h2>{pid}</h2>
            <p>Age {int(row.age)}, {row.sex}, BMI {row.bmi}, HbA1c {row.hba1c_pct}%, fasting {row.fasting_glucose_mg_dl} mg/dL, meal {int(row.meal_carbs_g)} g, sleep {row.sleep_h} h, HR {row.resting_hr_bpm} bpm.</p>
            <p><strong>{flag}.</strong> Twin peak {pred.predicted_peak_mg_dl:.0f} mg/dL. Physiology probability {pred.phys_proba:.2f}. Observed label {int(pred.spike_120min)}.</p>
            <svg viewBox="-70 20 200 160" width="100%" height="180">
              <line x1="0" y1="160" x2="130" y2="160" stroke="#999"/>
              <line x1="0" y1="{160 - (180-80)*0.55:.1f}" x2="130" y2="{160 - (180-80)*0.55:.1f}" stroke="#c45911" stroke-dasharray="3 3"/>
              <polyline fill="none" stroke="#1f4e79" stroke-width="2" points="{pts}"/>
              <text x="0" y="16" font-size="10">CGM, minutes from meal. Dashed line is 180 mg/dL.</text>
            </svg>
            </section>"""
        )
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>GlycoTwin-IN clinician view</title>
<style>
body {{ font-family: Georgia, serif; margin: 32px auto; max-width: 920px; color: #1c2834; background: #f7f5f0; }}
header {{ border-bottom: 3px solid #1f4e79; padding-bottom: 12px; }}
section {{ background: white; padding: 16px 18px; margin: 16px 0; border: 1px solid #d5dbe3; }}
.note {{ background: #fff4e5; padding: 10px 12px; }}
</style></head><body>
<header><h1>GlycoTwin-IN clinician view</h1>
<p>Synthetic virtual patients. Decision support sketch, not a medical device.</p></header>
<p class="note">Operational flag: forecast glucose at or above 180 mg/dL within 120 minutes of a logged meal. This cut follows a commonly cited post-meal target. It is not a diagnosis.</p>
{''.join(cards)}
</body></html>"""
    (ROOT / "docs" / "clinician_dashboard.html").write_text(html)


def box(c, x, y, w, h, title, body, fill):
    c.setStrokeColor(NAVY)
    c.setFillColor(fill)
    c.roundRect(x, y, w, h, 6, fill=1, stroke=1)
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 9)
    c.drawString(x + 8, y + h - 14, title)
    c.setFont("Times-Roman", 8)
    c.setFillColor(colors.HexColor("#243140"))
    text = c.beginText(x + 8, y + h - 28)
    text.setLeading(11)
    for line in body.split("\n"):
        text.textLine(line)
    c.drawText(text)


def arrow(c, x1, y1, x2, y2):
    c.setStrokeColor(TEAL)
    c.setFillColor(TEAL)
    c.setLineWidth(1.2)
    c.line(x1, y1, x2, y2)
    c.circle(x2, y2, 2.2, fill=1, stroke=0)


def architecture(path: Path) -> None:
    page = landscape(A4)
    c_width, c_height = page
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=page)
    c.setFillColor(NAVY)
    c.rect(0, c_height - 18 * mm, c_width, 18 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Times-Bold", 16)
    c.drawString(16 * mm, c_height - 11 * mm, "GlycoTwin-IN architecture — implemented prototype")
    c.setFont("Times-Roman", 9)
    c.drawRightString(c_width - 16 * mm, c_height - 11 * mm, "Parth Pariwandh, Jadavpur University")
    # row y positions
    y1, y2, y3 = 118 * mm, 62 * mm, 18 * mm
    w, h = 58 * mm, 42 * mm
    box(c, 12 * mm, y1, w, h, "Physical entity", "Simulated adult with\ntype 2 diabetes.\nNot a connected patient.", SAND)
    box(c, 78 * mm, y1, w, h, "Static stream", "Synthetic EHR:\nage, sex, BMI, HbA1c,\nfasting glucose, meds.", colors.white)
    box(c, 144 * mm, y1, w, h, "Dynamic stream", "Synthetic CGM, 5 min.\nSleep, resting HR,\nsteps in prior 2 h.", colors.white)
    box(c, 210 * mm, y1, w, h, "Ingestion", "CSV cohort loader.\nPre-meal window\nheld out from label.", colors.white)
    box(c, 12 * mm, y2, w, h, "Twin state", "G glucose, X insulin\naction. EHR prior on\nSI, SG, Gb.", SAND)
    box(c, 78 * mm, y2, w, h, "State update", "Bounded fit of SI on\nthe last 60 min CGM.\nActivity scales SI.", colors.white)
    box(c, 144 * mm, y2, w, h, "Bergman forecast", "120 min roll-forward\nafter logged carbs.\nPeak and time >= 180.", colors.white)
    box(c, 210 * mm, y2, w, h, "Decision layer", "Physiology logistic\non peak and time.\nGB compared, not better.", colors.white)
    box(c, 45 * mm, y3, 70 * mm, 36 * mm, "Clinician view", "Streamlit app and static\nHTML dashboard. Scenario\ncarb slider. Disclaimer.", colors.white)
    box(c, 125 * mm, y3, 70 * mm, 36 * mm, "Evaluation", "48 held-out synthetic\npatients. AUROC, AUPRC,\nBrier, peak MAE.", colors.white)
    box(c, 205 * mm, y3, 62 * mm, 36 * mm, "Not implemented", "No live wearable,\nno EHR integration,\nno clinical validation.", colors.HexColor("#f8e8e8"))
    arrow(c, 70 * mm, y1 + 21 * mm, 78 * mm, y1 + 21 * mm)
    arrow(c, 136 * mm, y1 + 21 * mm, 144 * mm, y1 + 21 * mm)
    arrow(c, 202 * mm, y1 + 21 * mm, 210 * mm, y1 + 21 * mm)
    arrow(c, 239 * mm, y1, 239 * mm, y2 + h)
    arrow(c, 70 * mm, y2 + 21 * mm, 78 * mm, y2 + 21 * mm)
    arrow(c, 136 * mm, y2 + 21 * mm, 144 * mm, y2 + 21 * mm)
    arrow(c, 202 * mm, y2 + 21 * mm, 210 * mm, y2 + 21 * mm)
    c.setFont("Times-Italic", 8)
    c.setFillColor(colors.HexColor("#555"))
    c.drawString(16 * mm, 8 * mm, "Solid boxes are in the repository. The red box is explicitly out of scope for this proof of concept. Data origin: synthetic.")
    c.save()


def presentation(path: Path) -> None:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Cover", fontName="Times-Bold", fontSize=22, textColor=NAVY, leading=26, spaceAfter=8))
    styles.add(ParagraphStyle(name="Sub", fontName="Times-Italic", fontSize=11, textColor=TEAL, leading=14, spaceAfter=8))
    styles.add(ParagraphStyle(name="H", fontName="Times-Bold", fontSize=14, textColor=NAVY, leading=18, spaceBefore=2, spaceAfter=6))
    styles.add(ParagraphStyle(name="Body", fontName="Times-Roman", fontSize=11, leading=15, textColor=colors.HexColor("#243140"), alignment=TA_JUSTIFY, spaceAfter=6))
    styles.add(ParagraphStyle(name="Small", fontName="Times-Roman", fontSize=9, leading=12, textColor=colors.HexColor("#333"), spaceAfter=3))
    styles.add(ParagraphStyle(name="BulletBody", fontName="Times-Roman", fontSize=11, leading=14, textColor=colors.HexColor("#243140")))

    def bullets(items):
        flow = []
        for item in items:
            flow.append(ListItem(Paragraph(item, styles["BulletBody"]), leftIndent=8))
        return ListFlowable(flow, bulletType="bullet", start="•", leftIndent=14, bulletFontName="Times-Roman", bulletFontSize=11, spaceBefore=2, spaceAfter=6)

    def footer(canvas, doc):
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, landscape(A4)[0], 10 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Times-Roman", 8)
        canvas.drawString(12 * mm, 4 * mm, "GlycoTwin-IN  ·  Digital Twin Challenge 2026  ·  Parth Pariwandh, Jadavpur University")
        canvas.drawRightString(landscape(A4)[0] - 12 * mm, 4 * mm, str(doc.page))

    story = []
    story.append(Spacer(1, 18 * mm))
    story.append(Paragraph("GlycoTwin-IN", styles["Cover"]))
    story.append(Paragraph("A hybrid Bergman digital twin for two-hour postprandial hyperglycaemia risk", styles["Sub"]))
    story.append(Paragraph("Digital Twin Challenge 2026 — Prototype and code submission. Happiest Health. Individual entry.", styles["Body"]))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Parth Pariwandh<br/>Final-year B.E. Mechanical Engineering, Jadavpur University<br/>Team size: 1", styles["Body"]))
    story.append(Paragraph("Simulation proof of concept. Not a medical device. Not for clinical use.", styles["Small"]))
    story.append(PageBreak())

    story.append(Paragraph("Problem", styles["H"]))
    story.append(Paragraph("India has a large and still rising burden of diabetes. ICMR-INDIAB-17 estimated a weighted prevalence of 11.4% among adults 20 years and older, corresponding to about 101 million people with diabetes and 136 million with prediabetes (Anjana et al., Lancet Diabetes & Endocrinology, 2023). Post-meal glucose excursions are a routine management problem, but clinic HbA1c does not show what a specific meal will do in the next two hours.", styles["Body"]))
    story.append(Paragraph("The prototype asks a narrow question: given a synthetic EHR snapshot and a wearable-like stream, will glucose reach 180 mg/dL within 120 minutes of a logged meal? The 180 mg/dL line is an operational flag aligned with a commonly cited 1–2 hour post-meal target, not a diagnostic claim.", styles["Body"]))
    story.append(PageBreak())

    story.append(Paragraph("Why a digital twin, not only a classifier", styles["H"]))
    story.append(bullets([
        "The physical entity is an adult with type 2 diabetes. In this build that entity is simulated.",
        "The twin state is plasma glucose and remote insulin action, initialised from the EHR prior.",
        "The last 60 minutes of CGM update insulin sensitivity. A declared carbohydrate load is then rolled forward 120 minutes.",
        "The clinician sees a trajectory and a flag, not only a probability.",
        "A gradient-boosting classifier was compared. On the held-out synthetic split it did not beat the physiology score.",
    ]))
    story.append(Paragraph("Implemented now: batch synthetic streams, offline update, scenario slider. Not implemented: a live wearable, a hospital EHR connection, or bidirectional therapy control.", styles["Body"]))
    story.append(PageBreak())

    story.append(Paragraph("Model", styles["H"]))
    story.append(Paragraph("The Bergman minimal model is the twin. G is glucose (mg/dL), X is insulin action (1/min), SI is insulin sensitivity (1/min per µU/mL), SG is glucose effectiveness (1/min), and Ra is meal glucose appearance (mg/dL/min).", styles["Body"]))
    story.append(Paragraph("dG/dt = −(SG + X) G + SG Gb + Ra(t)", styles["Body"]))
    story.append(Paragraph("dX/dt = −p2 X + p2 SI (I − Ib)", styles["Body"]))
    story.append(Paragraph("The generator adds a sleep and heart-rate stress term and sensor noise that the twin does not contain, so the twin is misspecified relative to the data. All 160 patients are synthetic. Parameter ranges are literature-informed bounds, not samples from ICMR microdata.", styles["Body"]))
    story.append(PageBreak())

    story.append(Paragraph("Measured results — simulation study", styles["H"]))
    story.append(Paragraph("Train 112 / test 48 synthetic patients, seed 2026. Spike prevalence in the test split was 0.73, so accuracy alone would be misleading. Bootstrap intervals are percentile intervals from 1,000 resamples of the same 48 patients.", styles["Body"]))
    header = styles["Small"]
    rows = [[
        Paragraph("<b>Model</b>", header),
        Paragraph("<b>AUROC</b>", header),
        Paragraph("<b>95% bootstrap</b>", header),
        Paragraph("<b>AUPRC</b>", header),
        Paragraph("<b>Brier</b>", header),
        Paragraph("<b>F1</b>", header),
    ], [
        Paragraph("EHR logistic", header), Paragraph("0.945", header), Paragraph("0.870–0.998", header), Paragraph("0.980", header), Paragraph("0.115", header), Paragraph("0.892", header),
    ], [
        Paragraph("Twin physiology", header), Paragraph("0.976", header), Paragraph("0.926–1.000", header), Paragraph("0.992", header), Paragraph("0.068", header), Paragraph("0.925", header),
    ], [
        Paragraph("Hybrid gradient boosting", header), Paragraph("0.936", header), Paragraph("0.853–0.994", header), Paragraph("0.978", header), Paragraph("0.089", header), Paragraph("0.930", header),
    ]]
    table = Table(rows, colWidths=[48 * mm, 28 * mm, 40 * mm, 28 * mm, 28 * mm, 24 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7eef5")),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Peak forecast error on the test split: MAE 17.1 mg/dL, RMSE 25.7 mg/dL. The intervals are wide because the test set is small. These are not clinical performance figures.", styles["Body"]))
    story.append(Image(str(ROOT / "results" / "auroc_comparison.png"), width=130 * mm, height=72 * mm))
    story.append(PageBreak())

    story.append(Paragraph("What a judge can run", styles["H"]))
    story.append(bullets([
        "Public repository: Parth_Pariwandh_Jadavpur_University.",
        "python scripts/run_experiment.py regenerates the cohort, twin table, and metrics.",
        "streamlit run app.py opens the clinician scenario view.",
        "docs/clinician_dashboard.html is a static view of two held-out virtual patients.",
        "docs/architecture_diagram.pdf and docs/project_presentation.pdf are the required documents.",
    ]))
    story.append(Paragraph("Licence: MIT. No patient identifiers, credentials, or private records are in the repository.", styles["Body"]))
    story.append(Paragraph("Limitation to say aloud: the video link is a submission item the author must record and upload. This prototype does not claim a completed clinical study.", styles["Body"]))

    doc = SimpleDocTemplate(
        str(path),
        pagesize=landscape(A4),
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title="GlycoTwin-IN presentation",
        author="Parth Pariwandh",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    (ROOT / "docs").mkdir(exist_ok=True)
    dashboard()
    architecture(ROOT / "docs" / "architecture_diagram.pdf")
    presentation(ROOT / "docs" / "project_presentation.pdf")
    print("docs written")
