#!/usr/bin/env python
"""Generate a 6-page PDF slide deck for demo.
"""
from pathlib import Path


def create_pdf(path: Path):
    # Use reportlab to create PDF with simple layout.
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        from reportlab.lib.units import inch
    except Exception as e:
        print("Required reportlab package not found.", e)
        return

    doc = SimpleDocTemplate(str(path), pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    flowables = []

    # Page 1
    flowables.append(Paragraph('<b>"Context, Problem & Evidence"</b>', styles['Title']))
    flowables.append(Spacer(1, 0.2 * inch))
    flowables.append(Paragraph('• Context: Our learning platform has observed a high dropout rate among students dealing with complex AI concepts.', styles['BodyText']))
    flowables.append(Spacer(1, 0.1 * inch))
    flowables.append(Paragraph('• Problem: Students struggle to locate relevant information within course material.', styles['BodyText']))
    flowables.append(Spacer(1, 0.1 * inch))
    flowables.append(Paragraph('<b>EVIDENCE (from survey)</b>', styles['Heading2']))
    flowables.append(Paragraph('• 41/200 hội thoại (~20.5%) chứa “mất thời gian” khi tìm kiếm thông tin.', styles['BodyText']))
    flowables.append(Paragraph('• 17/25 người khảo sát phàn nàn về “độ sâu hiểu” khi học bản thân.', styles['BodyText']))
    flowables.append(Paragraph('• Quote from Alice Nguyen: "Tôi không biết phải làm gì sau khi lướt qua slide."', styles['BodyText']))

    # Page 2
    flowables.append(Paragraph('<b>\n\n"Lát cắt giải pháp"</b>', styles['Title']))
    flowables.append(Spacer(1, 0.2 * inch))
    flowables.append(Paragraph('• One-sentence solution: <i>Integrate context-aware semantic search to surface precise slide content.</i>', styles['BodyText']))
    flowables.append(Spacer(1, 0.1 * inch))
    flowables.append(Paragraph('<b>Architecture Overview</b>', styles['Heading2']))
    flowables.append(Paragraph('• Frontend: React + Streamlit for interactive UI.', styles['BodyText']))
    flowables.append(Paragraph('• Backend: FastAPI + PyMuPDF for PDF rendering, semantic vector store (FAISS).', styles['BodyText']))
    flowables.append(Paragraph('• AI Service: OpenAI GPT-4.1-mini orchestrated by workflow engine.', styles['BodyText']))

    # Page 3
    flowables.append(Paragraph('<b>\n\n"4 pain points & user experience solutions"', styles['Title']))
    flowables.append(Spacer(1, 0.2 * inch))
    pain_points = [
        ('Finding relevant slide', 'Slice the search to current lesson & highlight matching page'),
        ('Ambiguous queries', 'Trigger clarify flow for pronoun resolution'),
        ('Slow <br/>response', 'Cache recent embeddings & use improved retrieval model'),
        ('User fatigue', 'Auto-show contextual summary before deep dive')
    ]
    for title, solution in pain_points:
        flowables.append(Paragraph(f'<b>{title}</b>', styles['Heading2']))
        flowables.append(Paragraph(solution, styles['BodyText']))
        flowables.append(Spacer(1, 0.1 * inch))

    # Page 4
    flowables.append(Paragraph('<b>\n\n"Measurement & Quality Bar"', styles['Title']))
    flowables.append(Spacer(1, 0.2 * inch))
    flowables.append(Paragraph('Quality Bar (CP4): <i>95% match on golden set & <=1 failure per 5 queries</i>', styles['BodyText']))
    flowables.append(Spacer(1, 0.1 * inch))
    flowables.append(Paragraph('<b>Result Table</b>', styles['Heading2']))
    table_data = [
        ['Metric', 'Achieved', 'Target'],
        ['Precision@1', '92%', '95%'],
        ['Recall@5', '87%', '90%'],
        ['Failure (hard) count', '1', '0']
    ]
    from reportlab.platypus import Table, TableStyle
    t = Table(table_data, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#CCCCCC'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#000000'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, '#888888'),
    ]))
    flowables.append(t)

    # Page 5
    flowables.append(Paragraph('<b>\n\n"Lessons & Feedback"', styles['Title']))
    flowables.append(Spacer(1, 0.2 * inch))
    flowables.append(Paragraph('• Missed case: “Complex query” caused 1 hard failure.', styles['BodyText']))
    flowables.append(Paragraph('• R6 Feedback: 12/15 users cite "too many steps to get answer."', styles['BodyText']))
    flowables.append(Paragraph('• Quote: "System should auto-suggest next slide." – Ben Thompson, Lead UX.', styles['BodyText']))

    # Page 6
    flowables.append(Paragraph('<b>\n\n"Roadmap & Contributions"', styles['Title']))
    flowables.append(Spacer(1, 0.2 * inch))
    flowables.append(Paragraph('- Next sprint: Implement hard‑case auto‑highlight & feedback loop.', styles['BodyText']))
    flowables.append(Paragraph('- Re‑engineer vector store for 10× speed.', styles['BodyText']))
    flowables.append(Paragraph('- Team: Alice, Ben, Charlie working on AI promise, backend, and UX.', styles['BodyText']))

    doc.build(flowables)
    print(f'PDF generated at {path}')


if __name__ == '__main__':
    create_pdf(Path('demo-slides.pdf'))