import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

from app.core.config import settings


class ReportGenerator:

    @staticmethod
    def generate_pdf_report(scan_id: int, scan_data: dict) -> str:
        """Builds a professional forensic PDF report from a saved scan record."""

        report_filename = f"forensic_report_{scan_id}.pdf"
        report_path = os.path.join(settings.REPORT_DIR, report_filename)

        doc = SimpleDocTemplate(
            report_path, pagesize=A4,
            topMargin=20 * mm, bottomMargin=18 * mm,
            leftMargin=18 * mm, rightMargin=18 * mm,
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "TitleStyle", parent=styles["Heading1"],
            fontSize=18, textColor=colors.HexColor("#0b0f19"), spaceAfter=2,
        )
        subtitle_style = ParagraphStyle(
            "SubtitleStyle", parent=styles["Normal"],
            fontSize=9, textColor=colors.HexColor("#555555"), spaceAfter=14,
        )
        section_style = ParagraphStyle(
            "SectionStyle", parent=styles["Heading2"],
            fontSize=12, textColor=colors.HexColor("#0b0f19"),
            spaceBefore=14, spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "BodyStyle", parent=styles["Normal"], fontSize=10, leading=14,
        )
        disclaimer_style = ParagraphStyle(
            "DisclaimerStyle", parent=styles["Normal"],
            fontSize=8, textColor=colors.HexColor("#777777"), leading=11,
        )

        elements = []

        elements.append(Paragraph("AI Media Forensic Analysis Report", title_style))
        elements.append(Paragraph(
            f"Report ID: FR-{scan_id:06d} &nbsp;|&nbsp; Generated: "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style
        ))
        elements.append(HRFlowable(width="100%", color=colors.HexColor("#0b0f19"), thickness=1.2))
        elements.append(Spacer(1, 10))

        # --- Asset Summary ---
        elements.append(Paragraph("1. Asset Summary", section_style))
        ai_scores = scan_data.get("ai_detection_scores", {})
        summary_rows = [
            ["Filename", scan_data.get("filename", "N/A")],
            ["Media Type", scan_data.get("media_type", "N/A")],
            ["Final Verdict", ai_scores.get("detected_type", "N/A")],
        ]
        summary_table = Table(summary_rows, colWidths=[45 * mm, 120 * mm])
        summary_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#555555")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ]))
        elements.append(summary_table)

        # --- Detection Scores ---
        elements.append(Paragraph("2. AI Detection Scores", section_style))
        score_rows = [["Metric", "Value"]]
        score_fields = [
            ("AI Probability", "ai_probability"),
            ("Human Probability", "human_probability"),
            ("Confidence Score", "confidence_score"),
            ("Manipulation Score", "manipulation_score"),
        ]
        for label, key in score_fields:
            val = ai_scores.get(key)
            if val is not None:
                score_rows.append([label, f"{round(val * 100)}%"])
        score_rows.append(["Model Used", ai_scores.get("model_used", "N/A")])

        score_table = Table(score_rows, colWidths=[80 * mm, 85 * mm])
        score_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b0f19")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ]))
        elements.append(score_table)

        # --- C2PA Section ---
        c2pa = scan_data.get("c2pa_analysis", {})
        elements.append(Paragraph("3. Content Credentials (C2PA)", section_style))
        if c2pa.get("has_c2pa") and c2pa.get("is_ai_generated"):
            c2pa_text = (
                f"<b>Cryptographically confirmed AI-generated.</b> "
                f"Signed by <b>{c2pa.get('issuer', 'Unknown')}</b> using generator "
                f"<b>{c2pa.get('generator', 'Unknown')}</b>. "
                f"Validation state: {c2pa.get('validation_state', 'Unknown')}."
            )
        elif c2pa.get("has_c2pa"):
            c2pa_text = (
                f"C2PA manifest present (issuer: {c2pa.get('issuer', 'Unknown')}) "
                f"but not flagged as AI-generated content."
            )
        else:
            c2pa_text = (
                "No C2PA content credentials manifest was found in this file. "
                "This is not proof of authenticity, as such metadata is commonly "
                "stripped when files are re-saved, screenshotted, or forwarded "
                "through messaging apps."
            )
        elements.append(Paragraph(c2pa_text, body_style))

        # --- Metadata Section ---
        elements.append(Paragraph("4. Metadata Analysis", section_style))
        metadata = scan_data.get("metadata_analysis", {})
        meta_rows = []
        for k, v in metadata.items():
            if k == "exif":
                continue
            meta_rows.append([str(k), str(v)])
        if meta_rows:
            meta_table = Table(meta_rows, colWidths=[60 * mm, 105 * mm])
            meta_table.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#555555")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#eeeeee")),
            ]))
            elements.append(meta_table)

        # --- Final Recommendation ---
        elements.append(Paragraph("5. Final Recommendation", section_style))
        elements.append(Paragraph(scan_data.get("final_recommendation", "N/A"), body_style))

        # --- Disclaimer ---
        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="100%", color=colors.HexColor("#dddddd"), thickness=0.8))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(
            "Disclaimer: This report is generated by an automated AI detection system. "
            "No detection method is 100% accurate. Results should be treated as one input "
            "among several for high-stakes decisions and reviewed by a qualified human "
            "analyst before being relied upon for legal, financial, or security purposes.",
            disclaimer_style
        ))

        doc.build(elements)
        return report_path