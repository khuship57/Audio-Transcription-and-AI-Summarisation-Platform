import base64
import io
from fpdf import FPDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black
from reportlab.lib.units import inch
import re

class PDFGenerator:
    def __init__(self):
        # Initialize styles for reportlab
        self.styles = getSampleStyleSheet()
        
        # Create custom styles for professional appearance
        self.title_style = ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=28,
            textColor=HexColor('#2c3e50'),
            spaceAfter=20,
            alignment=1,  # Center alignment
            fontName='Helvetica-Bold',
        )
        
        self.section_header_style = ParagraphStyle(
            name='CustomSectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=HexColor('#34495e'),
            spaceBefore=15,
            spaceAfter=8,
            fontName='Helvetica-Bold',
            borderWidth=0,
            borderColor=HexColor('#bdc3c7'),
            borderPadding=5,
            backColor=HexColor('#ecf0f1'),
        )
        
        self.subsection_header_style = ParagraphStyle(
            name='CustomSubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#2980b9'),
            spaceBefore=12,
            spaceAfter=6,
            fontName='Helvetica-Bold',
            leftIndent=10,
        )
        
        self.body_style = ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=black,
            spaceBefore=3,
            spaceAfter=3,
            fontName='Helvetica',
            alignment=0,  # Left alignment
            leftIndent=15,
            rightIndent=15,
        )
        
        self.bullet_style = ParagraphStyle(
            name='CustomBullet',
            parent=self.styles['Normal'],
            fontSize=11,
            leftIndent=25,
            firstLineIndent=0,
            spaceBefore=1,  # Reduced from 2
            spaceAfter=1,   # Reduced from 2
            bulletIndent=15,
            fontName='Helvetica',
        )
        
        self.duration_style = ParagraphStyle(
            name='CustomDuration',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=HexColor('#7f8c8d'),
            spaceBefore=5,
            spaceAfter=15,
            alignment=1,  # Center alignment
            fontName='Helvetica-Oblique',
        )

    def sanitize_text(self, text):
        """Replace problematic Unicode characters with ASCII alternatives"""
        replacements = {
            'â€¢': '*',      # bullet
            'â€"': '-',      # en dash
            'â€"': '--',     # em dash
            '"': '"',      # left double quote
            '"': '"',      # right double quote
            ''': "'",      # left single quote
            ''': "'",      # right single quote
            'â€¦': '...',    # ellipsis
            'â˜‘': '[x]',    # checked checkbox
            'â–¡': '[ ]',    # empty checkbox
            'â†’': '->',     # right arrow
            'â‡’': '=>',     # double right arrow
            'âœ"': 'v',      # check mark
            'âœ—': 'x',      # cross mark
            'â‰ˆ': '~',      # approximately equal
            'â‰ ': '!=',     # not equal
            'â‰¤': '<=',     # less than or equal
            'â‰¥': '>=',     # greater than or equal
        }

        for char, replacement in replacements.items():
            text = text.replace(char, replacement)

        # Handle any remaining non-ASCII characters
        return ''.join(c if ord(c) < 128 else '_' for c in text)

    def markdown_to_pdf_reportlab(self, markdown_text):
        """Convert markdown to PDF using ReportLab with professional formatting"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter, 
            rightMargin=0.75*inch, 
            leftMargin=0.75*inch, 
            topMargin=0.75*inch, 
            bottomMargin=0.75*inch
        )
        story = []

        lines = markdown_text.split('\n')
        list_items = []
        in_list = False
        first_heading = True
        meeting_duration_found = False
        current_section = ""  # Track current section for styling

        for line in lines:
            line = line.strip()
            # Skip horizontal rules
            if line == '---':
                continue
            if not line:
                if in_list:
                    # All bullet points should be black
                    story.append(ListFlowable(
                        list_items, 
                        bulletType='bullet', 
                        leftIndent=25, 
                        bulletFontSize=10,
                        bulletColor=black
                    ))
                    list_items = []
                    in_list = False
                story.append(Spacer(1, 3))  # Reduced spacing
                continue

            # Process main title (first # heading)
            if line.startswith('# ') and first_heading:
                if in_list:
                    story.append(ListFlowable(
                        list_items, 
                        bulletType='bullet', 
                        leftIndent=25, 
                        bulletFontSize=10,
                        bulletColor=black
                    ))
                    list_items = []
                    in_list = False
                
                title_text = line[2:].strip()
                story.append(Paragraph(title_text, self.title_style))
                story.append(Spacer(1, 10))
                first_heading = False

            # Process section headers (## headings)
            elif line.startswith('## '):
                if in_list:
                    story.append(ListFlowable(
                        list_items, 
                        bulletType='bullet', 
                        leftIndent=25, 
                        bulletFontSize=10,
                        bulletColor=black
                    ))
                    list_items = []
                    in_list = False
                
                header_text = line[3:].strip()
                current_section = header_text  # Track current section
                story.append(Paragraph(header_text, self.section_header_style))

            # Process subsection headers (### headings) - now treated as regular subsections
            elif line.startswith('### '):
                if in_list:
                    story.append(ListFlowable(
                        list_items, 
                        bulletType='bullet', 
                        leftIndent=25, 
                        bulletFontSize=10,
                        bulletColor=black
                    ))
                    list_items = []
                    in_list = False
                
                subheader_text = line[4:].strip()
                current_section = subheader_text  # Track current section
                story.append(Paragraph(subheader_text, self.subsection_header_style))

            # Process main title as section header for subsequent # headings
            elif line.startswith('# '):
                if in_list:
                    story.append(ListFlowable(
                        list_items, 
                        bulletType='bullet', 
                        leftIndent=25, 
                        bulletFontSize=10,
                        bulletColor=black
                    ))
                    list_items = []
                    in_list = False
                
                header_text = line[2:].strip()
                current_section = header_text  # Track current section
                story.append(Paragraph(header_text, self.section_header_style))

            # Process list items
            elif line.startswith('- ') or line.startswith('* '):
                content = line[2:].strip()

                # Handle checkboxes
                if content.startswith('[ ] '):
                    content = 'â˜ ' + content[4:]  # Empty checkbox
                elif content.startswith('[x] ') or content.startswith('[X] '):
                    content = 'â˜' + content[4:]  # Checked checkbox

                # Apply formatting to list item content
                if '**' in content or '*' in content:
                    content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
                    content = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', content)

                # All bullet points use standard black bullet style
                list_items.append(ListItem(Paragraph(content, self.bullet_style)))
                in_list = True

            # Regular paragraph text
            else:
                if in_list:
                    story.append(ListFlowable(
                        list_items, 
                        bulletType='bullet', 
                        leftIndent=25, 
                        bulletFontSize=10,
                        bulletColor=black
                    ))
                    list_items = []
                    in_list = False

                # Check if this is meeting duration info
                if 'Meeting Duration:' in line or 'Duration:' in line:
                    story.append(Paragraph(line, self.duration_style))
                    meeting_duration_found = True
                else:
                    # Handle bold and italic text
                    if '**' in line or '*' in line:
                        line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                        line = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', line)

                    story.append(Paragraph(line, self.body_style))

        # Don't forget to add the last list if we're still in one
        if in_list and list_items:
            story.append(ListFlowable(
                list_items, 
                bulletType='bullet', 
                leftIndent=25, 
                bulletFontSize=10,
                bulletColor=black
            ))

        # Build the PDF
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data

    def markdown_to_pdf(self, markdown_text):
        """Convert markdown to PDF using ReportLab with fallbacks"""
        try:
            return self.markdown_to_pdf_reportlab(markdown_text)
        except Exception as e:
            try:
                # Try again with sanitized text
                sanitized_text = self.sanitize_text(markdown_text)
                return self.markdown_to_pdf_reportlab(sanitized_text)
            except Exception as e2:
                return self._create_simple_pdf(markdown_text)

    def _create_simple_pdf(self, markdown_text):
        """Fallback method with maximum compatibility"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Sanitize the text to ensure it's ASCII-only
        lines = self.sanitize_text(markdown_text).split('\n')

        for line in lines:
            # Skip empty lines
            if not line.strip():
                pdf.ln(5)
                continue

            # Process headers and text with simple formatting
            if line.startswith('# '):
                pdf.set_font("Arial", 'B', 24)
                pdf.multi_cell(0, 10, line[2:])
                pdf.ln(5)
            elif line.startswith('## '):
                pdf.set_font("Arial", 'B', 18)
                pdf.multi_cell(0, 10, line[3:])
                pdf.ln(3)
            elif line.startswith('- ') or line.startswith('* '):
                pdf.set_font("Arial", '', 12)
                content = line[2:]
                pdf.multi_cell(0, 5, "- " + content)
            else:
                pdf.set_font("Arial", '', 12)
                pdf.multi_cell(0, 5, line)

        try:
            return pdf.output(dest='S').encode('latin1')
        except Exception as e:
            # Create an absolutely minimal PDF as last resort
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(40, 10, 'Meeting Summary')
            pdf.ln(15)
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 10, 'Please download the Markdown version instead.')
            return pdf.output(dest='S').encode('latin1')
        
    def create_download_link(self, pdf_bytes):
        return base64.b64encode(pdf_bytes).decode()