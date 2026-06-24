"""
PDF Export Service.

Generates patient-friendly health data reports as PDF.
Strips all internal database fields (_id, patient_id, verification_hash, etc.).
"""

import io
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER


class PDFExportService:
    """Generates patient health data PDF reports."""

    def generate_report(self, patient: dict, records: list) -> bytes:
        """
        Generate a PDF health report for a patient.

        Args:
            patient: Decrypted patient profile
            records: List of decrypted healthcare records

        Returns:
            PDF file as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
        styles = getSampleStyleSheet()
        elements = []

        # Custom styles
        title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=18, spaceAfter=6)
        subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=10, textColor=colors.grey, alignment=TA_CENTER)
        heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], fontSize=13, spaceAfter=8, spaceBefore=16)
        normal_style = styles["Normal"]
        small_style = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, textColor=colors.grey)

        # ─── HEADER ──────────────────────────────────────────────
        elements.append(Paragraph("DPDP Healthcare Platform", title_style))
        elements.append(Paragraph("Patient Health Data Report", subtitle_style))
        elements.append(Paragraph(
            f"Generated: {datetime.now(timezone.utc).strftime('%d %B %Y, %H:%M UTC')}",
            subtitle_style
        ))
        elements.append(Paragraph("✓ DPDP Act Compliant · Data Portability Export", subtitle_style))
        elements.append(Spacer(1, 12))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
        elements.append(Spacer(1, 12))

        # ─── PATIENT INFORMATION ──────────────────────────────────
        elements.append(Paragraph("Patient Information", heading_style))

        patient_data = [
            ["Full Name", patient.get("full_name", "—")],
            ["Phone Number", patient.get("phone_number", "—") or "—"],
            ["Blood Group", patient.get("blood_group", "—") or "—"],
            ["Address", patient.get("address", "—") or "—"],
            ["Allergies", ", ".join(patient.get("allergies", [])) or "None recorded"],
        ]

        t = Table(patient_data, colWidths=[120, 350])
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))

        # ─── HEALTH RECORDS ───────────────────────────────────────
        elements.append(Paragraph("Health Records", heading_style))

        active_records = [r for r in records if not r.get("redacted", False)]

        if not active_records:
            elements.append(Paragraph("No health records available.", normal_style))
        else:
            for i, record in enumerate(active_records, 1):
                elements.append(Paragraph(
                    f"<b>{i}. {record.get('title', 'Untitled')}</b> "
                    f"<i>({self._humanize(record.get('record_type', ''))})</i>",
                    normal_style
                ))
                elements.append(Spacer(1, 4))

                details = []
                created = record.get("created_at", "")
                if created:
                    try:
                        dt = datetime.fromisoformat(created)
                        details.append(f"Date: {dt.strftime('%d %b %Y')}")
                    except (ValueError, TypeError):
                        pass

                symptoms = record.get("symptoms", [])
                if symptoms and symptoms != ["none"]:
                    details.append(f"Symptoms: {', '.join(symptoms)}")

                codes = record.get("diagnosis_codes", [])
                if codes:
                    details.append(f"Diagnosis Codes: {', '.join(codes)}")

                if details:
                    elements.append(Paragraph(" · ".join(details), small_style))
                    elements.append(Spacer(1, 3))

                desc = record.get("description", "")
                if desc:
                    elements.append(Paragraph(desc, normal_style))
                    elements.append(Spacer(1, 3))

                notes = record.get("treatment_notes", "")
                if notes:
                    elements.append(Paragraph(f"<b>Treatment:</b> {notes}", normal_style))

                elements.append(Spacer(1, 10))
                if i < len(active_records):
                    elements.append(HRFlowable(width="80%", thickness=0.5, color=colors.Color(0.9, 0.9, 0.9)))
                    elements.append(Spacer(1, 6))

        # ─── PRIVACY & SECURITY ───────────────────────────────────
        elements.append(Spacer(1, 12))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("Privacy & Security", heading_style))

        security_items = [
            "✓ AES-256 Encryption — All personal data encrypted at rest",
            "✓ Blockchain Integrity Verification — Records anchored on-chain",
            "✓ Immutable Audit Trail — Every access logged with hash chain",
            "✓ DPDP Data Portability — Compliant with Section 11 (Right to Access)",
        ]
        for item in security_items:
            elements.append(Paragraph(item, normal_style))
            elements.append(Spacer(1, 4))

        # ─── FOOTER ──────────────────────────────────────────────
        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(
            f"Generated by DPDP Healthcare Platform · {datetime.now(timezone.utc).isoformat()}",
            small_style
        ))
        elements.append(Paragraph(
            "This document is a portable copy of your health data under DPDP Act Section 11.",
            small_style
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def _humanize(value: str) -> str:
        return value.replace("_", " ").title() if value else ""
