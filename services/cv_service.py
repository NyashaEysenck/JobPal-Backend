# services/cv_service.py
from fpdf import FPDF
from datetime import datetime
import os
from io import BytesIO

class ModernCV(FPDF):
    """
    Custom PDF class extending FPDF for generating modern-styled CVs.

    Encapsulates styling and common PDF elements (header, footer).
    """

    def __init__(self):
        """Initializes the PDF document with custom colors and auto page break."""
        super().__init__()
        self.primary_color = (70, 130, 180)  # SteelBlue for headings
        self.secondary_color = (100, 100, 100)  # DarkGray for subtext/footer
        self.set_auto_page_break(auto=True, margin=15) # Automatically create new pages

    def header(self):
        """Defines the header for each page (except the first)."""
        # A common practice is to skip the header on the very first page of a CV.
        if self.page_no() == 1:
            return

        self.set_font('Arial', 'B', 10)
        self.set_text_color(*self.secondary_color)
        # Using a placeholder for APP_NAME, assuming it's passed or loaded in the main app
        # For this standalone service, we'll make it generic or load from config if needed.
        self.cell(0, 10, f"Professional CV - Page {self.page_no()}", 0, 0, 'C')

    def footer(self):
        """Defines the footer for each page."""
        self.set_y(-15) # Position 15mm from bottom
        self.set_font('Arial', 'I', 8)
        self.set_text_color(*self.secondary_color)
        self.cell(0, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d')}", 0, 0, 'C')

def generate_cv_pdf(data, filepath):
    """
    Generates a professional CV PDF based on the provided data.

    Args:
        data (dict): A dictionary containing CV details (name, email, summary, education, experience, skills).
        filepath (str): The full path including filename where the PDF should be saved.
    """
    pdf = ModernCV()
    pdf.add_page()

    # --- Personal Information Section ---
    pdf.set_font("Arial", 'B', 24)
    pdf.set_text_color(*pdf.primary_color)
    pdf.cell(0, 15, txt=data.get('name', 'Your Name'), ln=1, align='C')

    pdf.set_font("Arial", size=12)
    pdf.set_text_color(*pdf.secondary_color)
    contact_info = f"{data.get('email', '')} | {data.get('phone', '')}"
    pdf.cell(0, 10, txt=contact_info, ln=1, align='C')
    pdf.ln(15)

    # --- Professional Summary Section ---
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(*pdf.primary_color)
    pdf.cell(0, 10, txt="PROFESSIONAL SUMMARY", ln=1)
    pdf.set_line_width(0.5)
    pdf.set_draw_color(*pdf.primary_color)
    pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
    pdf.ln(8)

    pdf.set_font("Arial", size=11)
    pdf.set_text_color(0, 0, 0)  # Black text
    pdf.multi_cell(0, 6, txt=data.get('summary', ''))
    pdf.ln(12)

    # --- Education Section ---
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(*pdf.primary_color)
    pdf.cell(0, 10, txt="EDUCATION", ln=1)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
    pdf.ln(8)

    for edu in data.get('education', []):
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 7, txt=edu.get('institution', ''), ln=1)

        pdf.set_font("Arial", size=11)
        pdf.set_text_color(*pdf.secondary_color)
        pdf.cell(0, 6, txt=f"{edu.get('degree', '')} | {edu.get('year', '')}", ln=1)

        if edu.get('description'):
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 5, txt=edu['description'])
            pdf.set_font("Arial", size=11) # Reset font
        pdf.ln(5)

    # --- Work Experience Section ---
    # Only add if there's actual experience data
    if data.get('experience') and any(exp.get('company', '').strip() for exp in data['experience']):
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(*pdf.primary_color)
        pdf.cell(0, 10, txt="WORK EXPERIENCE", ln=1)
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
        pdf.ln(8)

        for exp in data['experience']:
            if not exp.get('company', '').strip():
                continue # Skip empty entries

            pdf.set_font("Arial", 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 7, txt=exp.get('company', ''), ln=1)

            pdf.set_font("Arial", size=11)
            pdf.set_text_color(*pdf.secondary_color)
            date_range = f"{exp.get('startDate', '')} - {exp.get('endDate', 'Present')}"
            pdf.cell(0, 6, txt=f"{exp.get('position', '')} | {date_range}", ln=1)

            if exp.get('description'):
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Arial", size=10)
                pdf.multi_cell(0, 5, txt=exp['description'])
                pdf.set_font("Arial", size=11) # Reset font
            pdf.ln(5)

    # --- Skills Section ---
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(*pdf.primary_color)
    pdf.cell(0, 10, txt="SKILLS", ln=1)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
    pdf.ln(8)

    pdf.set_font("Arial", size=11)
    pdf.set_text_color(0, 0, 0)
    # Filter out empty strings before joining
    skills = " • ".join([skill.strip() for skill in data.get('skills', []) if skill.strip()])
    pdf.multi_cell(0, 7, txt=skills)

    # Save the generated PDF to the specified filepath.
    pdf.output(filepath)

