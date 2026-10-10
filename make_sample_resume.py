"""Makes a dummy resume PDF so you can test the parser without using your real one."""
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

LINES = [
    ("Rahul Sharma", 16),
    ("rahul@example.com | Hyderabad | github.com/rahul-demo", 10),
    ("SUMMARY", 12),
    ("B.Tech AI & Data Science fresher interested in data analytics roles.", 10),
    ("SKILLS", 12),
    ("Python, SQL, Excel, Tableau, Pandas, Git", 10),
    ("PROJECTS", 12),
    ("- Sales Dashboard: built a Tableau dashboard on retail sales data.", 10),
    ("- Rainfall Analysis: cleaned data with Pandas and plotted trends.", 10),
    ("EDUCATION", 12),
    ("B.Tech in Artificial Intelligence & Data Science, 2022-2026", 10),
    ("CERTIFICATIONS", 12),
    ("Data Analytics with Tableau - SmartBridge", 10),
]

c = canvas.Canvas("sample_resume.pdf", pagesize=A4)
y = 800
for text, size in LINES:
    c.setFont("Helvetica-Bold" if size > 10 else "Helvetica", size)
    c.drawString(50, y, text)
    y -= size + 10
c.save()
print("Created sample_resume.pdf")
