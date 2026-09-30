"""
Meeting Report Generator & Exporter (Milestone 4 - Task 6)
Exports complete meeting intelligence (details, summary, decisions,
action items, participants, deadlines) to PDF and CSV formats.
"""

import csv
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger(__name__)


def format_duration(seconds: float) -> str:
    """Format duration in seconds into mm:ss or hh:mm:ss."""
    try:
        s = int(round(float(seconds)))
        hrs = s // 3600
        mins = (s % 3600) // 60
        secs = s % 60
        if hrs > 0:
            return f"{hrs:02d}h {mins:02d}m {secs:02d}s"
        return f"{mins:02d}m {secs:02d}s"
    except Exception:
        return f"{seconds}s"


def generate_meeting_csv(meeting_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Generate a comprehensive structured CSV report containing all meeting intelligence.
    
    Args:
        meeting_data: Complete dictionary of meeting intelligence.
        output_path: Optional file path to write CSV directly.
        
    Returns:
        CSV string content.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # 1. Meeting Overview
    writer.writerow(["=== MEETING INTELLIGENCE REPORT ==="])
    writer.writerow(["Meeting ID", meeting_data.get("id", "")])
    writer.writerow(["Title", meeting_data.get("title", "Meeting")])
    writer.writerow(["Date", meeting_data.get("created_at", "")])
    writer.writerow(["Duration", format_duration(meeting_data.get("duration", 0))])
    writer.writerow(["Source File", meeting_data.get("original_filename", "N/A")])
    writer.writerow(["Export Generated At", datetime.now().isoformat()])
    writer.writerow([])

    # 2. Executive Summary
    writer.writerow(["=== EXECUTIVE SUMMARY ==="])
    summary_text = meeting_data.get("summary", "")
    writer.writerow(["Summary Text", summary_text])
    writer.writerow([])

    # 3. Key Decisions
    writer.writerow(["=== KEY DECISIONS ==="])
    decisions = meeting_data.get("decisions") or meeting_data.get("key_decisions") or []
    if decisions:
        writer.writerow(["#", "Decision Description"])
        for idx, dec in enumerate(decisions, 1):
            writer.writerow([idx, dec])
    else:
        writer.writerow(["No formal decisions recorded."])
    writer.writerow([])

    # 4. Action Items & Responsibilities
    writer.writerow(["=== ACTION ITEMS & DELIVERABLES ==="])
    actions = meeting_data.get("action_items", [])
    if actions:
        writer.writerow(["Action Item", "Owner / Assignee", "Deadline", "Priority", "Status"])
        for a in actions:
            if isinstance(a, dict):
                writer.writerow([
                    a.get("action", ""),
                    a.get("owner") or "Unassigned",
                    a.get("deadline") or "None",
                    a.get("priority") or "Medium",
                    a.get("status") or "Pending"
                ])
            else:
                writer.writerow([str(a), "Unassigned", "None", "Medium", "Pending"])
    else:
        writer.writerow(["No action items tracked."])
    writer.writerow([])

    # 5. Participants & Roles
    writer.writerow(["=== PARTICIPANTS & ROLES ==="])
    participants = meeting_data.get("participants", [])
    if participants:
        writer.writerow(["Name", "Canonical Name", "Role / Responsibilities"])
        for p in participants:
            if isinstance(p, dict):
                writer.writerow([
                    p.get("name", ""),
                    p.get("canonical_name", p.get("name", "")),
                    p.get("role") or "Participant"
                ])
            else:
                writer.writerow([str(p), str(p), "Participant"])
    else:
        writer.writerow(["No explicit participants identified."])

    csv_content = output.getvalue()
    output.close()

    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(csv_content, encoding="utf-8")
        logger.info(f"Saved CSV report to {output_path}")

    return csv_content


def generate_meeting_pdf(meeting_data: Dict[str, Any], output_path: Optional[str] = None) -> bytes:
    """
    Generate an executive-grade PDF report using ReportLab.
    
    Args:
        meeting_data: Complete dictionary of meeting intelligence.
        output_path: Optional file path to write PDF directly.
        
    Returns:
        PDF bytes buffer.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom Executive Typography Styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0f172a'),
            alignment=TA_LEFT
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748b'),
            alignment=TA_LEFT
        )
        h2_style = ParagraphStyle(
            'SectionH2',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=17,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor('#334155')
        )
        body_bold = ParagraphStyle(
            'BodyBold',
            parent=body_style,
            fontName='Helvetica-Bold'
        )
        th_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#ffffff')
        )
        td_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#1e293b')
        )

        story = []

        # Header Title
        story.append(Paragraph("EXECUTIVE MEETING INTELLIGENCE REPORT", subtitle_style))
        story.append(Spacer(1, 4))
        m_title = meeting_data.get("title", "Meeting Intelligence")
        story.append(Paragraph(f"<b>{m_title}</b>", title_style))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#4f46e5'), spaceBefore=2, spaceAfter=10))

        # Metadata Table
        created_at = meeting_data.get("created_at") or datetime.now().isoformat()
        if "T" in created_at:
            created_at = created_at.replace("T", " ")[:19]
        dur_str = format_duration(meeting_data.get("duration", 0))
        source_file = meeting_data.get("original_filename") or "Audio / Transcript Upload"
        meeting_id = meeting_data.get("id") or "N/A"

        meta_data = [
            [
                Paragraph(f"<b>Meeting ID:</b> {meeting_id}", td_style),
                Paragraph(f"<b>Date & Time:</b> {created_at}", td_style)
            ],
            [
                Paragraph(f"<b>Source:</b> {source_file}", td_style),
                Paragraph(f"<b>Duration:</b> {dur_str}", td_style)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[270, 270])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 12))

        # 1. Executive Summary
        story.append(Paragraph("1. Executive Summary", h2_style))
        summary_text = meeting_data.get("summary") or "No executive summary available."
        story.append(Paragraph(summary_text.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 10))

        # 2. Key Decisions
        story.append(Paragraph("2. Key Decisions & Strategic Alignments", h2_style))
        decisions = meeting_data.get("decisions") or meeting_data.get("key_decisions") or []
        if decisions:
            for idx, dec in enumerate(decisions, 1):
                story.append(Paragraph(f"<b>• Decision {idx}:</b> {dec}", body_style))
                story.append(Spacer(1, 2))
        else:
            story.append(Paragraph("<i>No formal decisions were recorded in this session.</i>", body_style))
        story.append(Spacer(1, 10))

        # 3. Action Items & Deliverables
        story.append(Paragraph("3. Action Items, Deadlines & Accountability", h2_style))
        actions = meeting_data.get("action_items", [])
        if actions:
            action_table_data = [[
                Paragraph("Action Item", th_style),
                Paragraph("Assignee", th_style),
                Paragraph("Deadline", th_style),
                Paragraph("Priority", th_style),
                Paragraph("Status", th_style)
            ]]
            for a in actions:
                if isinstance(a, dict):
                    act_desc = a.get("action", "")
                    owner = a.get("owner") or "Unassigned"
                    deadline = a.get("deadline") or "None"
                    priority = a.get("priority") or "Medium"
                    status = a.get("status") or "Pending"
                else:
                    act_desc = str(a)
                    owner, deadline, priority, status = "Unassigned", "None", "Medium", "Pending"

                action_table_data.append([
                    Paragraph(act_desc, td_style),
                    Paragraph(owner, td_style),
                    Paragraph(deadline, td_style),
                    Paragraph(priority, td_style),
                    Paragraph(status, td_style)
                ])

            action_table = Table(action_table_data, colWidths=[200, 85, 95, 80, 80])
            action_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f8fafc')]),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(action_table)
        else:
            story.append(Paragraph("<i>No action items extracted for this meeting.</i>", body_style))
        story.append(Spacer(1, 10))

        # 4. Participants & Roles
        story.append(Paragraph("4. Meeting Participants & Contribution", h2_style))
        participants = meeting_data.get("participants", [])
        if participants:
            part_table_data = [[
                Paragraph("Participant Name", th_style),
                Paragraph("Canonical Name", th_style),
                Paragraph("Role / Assigned Scope", th_style)
            ]]
            for p in participants:
                if isinstance(p, dict):
                    name = p.get("name", "Unknown")
                    canon = p.get("canonical_name", name)
                    role = p.get("role") or "Participant"
                else:
                    name, canon, role = str(p), str(p), "Participant"

                part_table_data.append([
                    Paragraph(name, td_style),
                    Paragraph(canon, td_style),
                    Paragraph(role, td_style)
                ])

            part_table = Table(part_table_data, colWidths=[180, 180, 180])
            part_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f8fafc')]),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(part_table)
        else:
            story.append(Paragraph("<i>No participant details recorded.</i>", body_style))

        # Footer spacer & disclaimer
        story.append(Spacer(1, 16))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=4, spaceAfter=6))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#94a3b8'),
            alignment=TA_CENTER
        )
        story.append(Paragraph(f"Generated by AI Career Intelligence Platform • Confidential • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        if output_path:
            out_file = Path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_bytes(pdf_bytes)
            logger.info(f"Saved PDF report to {output_path}")

        return pdf_bytes

    except Exception as e:
        logger.exception(f"ReportLab PDF generation error: {e}")
        # Fallback basic PDF byte stream
        return _generate_fallback_pdf(meeting_data, output_path)


def _generate_fallback_pdf(meeting_data: Dict[str, Any], output_path: Optional[str] = None) -> bytes:
    """Minimal plain-text PDF fallback if ReportLab fails."""
    title = meeting_data.get("title", "Meeting Report")
    summary = meeting_data.get("summary", "")
    content = f"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<<>>>>endobj\n4 0 obj<</Length 150>>stream\nBT /F1 12 Tf 50 700 Td ({title}) Tj 0 -20 Td ({summary[:100]}) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000056 00000 n \n0000000111 00000 n \n0000000212 00000 n \ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n415\n%%EOF"
    pdf_bytes = content.encode("utf-8")
    if output_path:
        Path(output_path).write_bytes(pdf_bytes)
    return pdf_bytes


class MeetingReportExporter:
    """Class wrapper for report generation and exports."""

    @staticmethod
    def export_pdf(meeting_data: Dict[str, Any], output_path: Optional[str] = None) -> bytes:
        return generate_meeting_pdf(meeting_data, output_path)

    @staticmethod
    def export_csv(meeting_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        return generate_meeting_csv(meeting_data, output_path)
