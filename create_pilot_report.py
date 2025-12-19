from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Create Clinical Pilot Report Template PDF
pilot_pdf = "Clinical_Pilot_Report_Template.pdf"
c = canvas.Canvas(pilot_pdf, pagesize=landscape(A4))
w, h = landscape(A4)
c.setFont("Helvetica-Bold", 20)
c.drawString(1*inch, h-1*inch, "Clinical Pilot Report — Aviothic.ai")
c.setFont("Helvetica", 12)
y = h-1.6*inch
pilot_lines = [
"Hospital: [Hospital Name]",
"Study period: [Start Date] - [End Date]",
"Principal Investigator: [Name]",
"Summary:",
"- Objective: Evaluate Aviothic.ai for detection of malignant breast lesions in screening mammography.",
"- Dataset: [n] anonymized cases; modality: digital mammography; views: CC/MLO.",
"Performance Metrics:",
"- AUC: [AUC value]",
"- Sensitivity: [value]",
"- Specificity: [value]",
"- PPV / NPV: [values]",
"Study Procedure:",
"1. Hospital uploads anonymized cases via onboarding portal.",
"2. Aviothic.ai runs inference and returns Grad-CAM + PDF report.",
"3. Radiologist reviews AI output and records feedback in portal.",
"4. Feedback is stored for retraining and audit.",
"Clinical Reviewer Comments:",
"- [Reviewer observations and notes]",
"Signatures:",
"- Clinical Lead: ____________________ Date: ________",
"- Aviothic.ai Representative: ______________ Date: ________"
]
for line in pilot_lines:
    c.drawString(1*inch, y, line)
    y -= 18
c.save()

print(f"Clinical Pilot Report Template created: {pilot_pdf}")