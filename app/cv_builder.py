"""Generate a candidate CV from validated plain-text fields."""
import io
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from html import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

FIELDS = {
    'name': ('Nom complet', 100), 'title': ('Titre professionnel', 150),
    'email': ('Email', 254), 'phone': ('Téléphone', 50), 'city': ('Ville', 100),
    'summary': ('Profil', 1200), 'education': ('Formation', 2500),
    'experience': ('Expériences et stages', 3500), 'projects': ('Projets', 2500),
    'skills': ('Compétences', 1500), 'languages': ('Langues', 600),
    'certifications': ('Certifications', 1000)
}

def generate_cv(data):
    fontdir=Path(__file__).parent/'fonts'
    if 'CVSans' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('CVSans',str(fontdir/'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('CVSans-Bold',str(fontdir/'DejaVuSans-Bold.ttf')))
    buffer=io.BytesIO()
    doc=SimpleDocTemplate(buffer,pagesize=A4,rightMargin=45,leftMargin=45,topMargin=42,bottomMargin=42,title='CV - '+data['name'],author=data['name'])
    navy=colors.HexColor('#183137');teal=colors.HexColor('#177c68')
    normal=ParagraphStyle('CVBody',fontName='CVSans',fontSize=10,leading=15,textColor=navy,spaceAfter=9)
    name=ParagraphStyle('CVName',parent=normal,fontName='CVSans-Bold',fontSize=24,leading=29,spaceAfter=8)
    title=ParagraphStyle('CVTitle',parent=normal,fontSize=13,leading=18,textColor=teal)
    heading=ParagraphStyle('CVSection',parent=normal,fontName='CVSans-Bold',fontSize=11,leading=16,textColor=teal,spaceBefore=12,spaceAfter=7,keepWithNext=True)
    def safe(value):
        # ReportLab paragraph markup is never accepted from form input.
        return escape(value).replace('\n','<br/>')
    story=[Paragraph(safe(data['name']),name)]
    if data.get('title'):story.append(Paragraph(safe(data['title']),title))
    contact=' | '.join(data[k] for k in ['email','phone','city'] if data.get(k))
    if contact:story.append(Paragraph(safe(contact),normal))
    story.extend([Spacer(1,6),HRFlowable(width='100%',thickness=1,color=teal),Spacer(1,8)])
    for key in ['summary','experience','education','projects','skills','languages','certifications']:
        if data.get(key):
            story.append(Paragraph(FIELDS[key][0].upper(),heading))
            # Separate paragraphs allow clean page breaks for long CVs.
            for line in data[key].splitlines():
                if line.strip():story.append(Paragraph(safe(line),normal))
    def footer(canvas,document):
        canvas.setFont('CVSans',8);canvas.setFillColor(colors.HexColor('#738084'))
        canvas.drawRightString(A4[0]-45,25,str(document.page))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return buffer.getvalue()
