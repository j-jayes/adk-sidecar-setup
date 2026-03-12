"""Generate a test lease PDF for end-to-end testing using reportlab."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

output_path = "tests/test-lease.pdf"

doc = SimpleDocTemplate(output_path, pagesize=letter)
styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "CustomTitle", parent=styles["Title"], fontSize=16, spaceAfter=12
)
heading_style = ParagraphStyle(
    "CustomHeading", parent=styles["Heading2"], fontSize=13, spaceAfter=6
)
body_style = ParagraphStyle(
    "CustomBody", parent=styles["Normal"], fontSize=10, spaceAfter=4
)
bold_style = ParagraphStyle(
    "CustomBold", parent=styles["Normal"], fontSize=10, spaceAfter=4
)

content = []

content.append(Paragraph("RESIDENTIAL LEASE AGREEMENT (TEST DATA)", title_style))
content.append(Spacer(1, 8))
content.append(Paragraph("<b>Date of Agreement:</b> January 15, 2009", body_style))
content.append(Spacer(1, 12))

sections = [
    ("1. The Parties", [
        "<b>Landlord (Lessor):</b> The United States Federal Government",
        "<b>Tenant (Lessee):</b> Michelle Obama",
    ]),
    ("2. The Premises", [
        "The Landlord hereby leases to the Tenant the property located at:",
        "<b>Property Address:</b> 1600 Pennsylvania Avenue NW, Washington, DC 20500",
        "<b>Description:</b> A 132-room executive mansion, including the East Wing residential quarters.",
    ]),
    ("3. Term of Lease", [
        "The lease term shall commence and expire on the following dates:",
        "<b>Start Date:</b> January 20, 2009",
        "<b>End Date:</b> January 20, 2017",
    ]),
    ("4. Rent Amount", [
        "<b>Monthly Rent:</b> $0.00",
        "<b>Rent Due Date:</b> The 1st of each month.",
        "<i>Note: Tenant is responsible for personal food and grocery expenses.</i>",
    ]),
    ("5. Security Deposit", [
        "<b>Deposit Amount:</b> $0.00",
        "<b>Terms:</b> No security deposit is required for this property.",
    ]),
    ("6. Use of Property", [
        "The Premises shall be used strictly as a primary residence and for official "
        "executive state functions. The Tenant agrees not to use the property for "
        "any unlawful purposes.",
    ]),
    ("7. Utilities and Maintenance", [
        "<b>Landlord Responsibilities:</b> The Landlord shall be responsible for all utilities, "
        "groundskeeping, and structural maintenance (managed via the National Park Service).",
        "<b>Tenant Responsibilities:</b> The Tenant shall maintain the residential quarters "
        "in a clean and sanitary condition.",
    ]),
    ("8. Signatures", [
        "<b>Landlord Representative:</b> ___________________________",
        "<i>Chief Justice of the United States (Witness)</i>",
        "Date: ___________",
        "",
        "<b>Tenant:</b> ___________________________",
        "<i>Michelle Obama</i>",
        "Date: ___________",
    ]),
]

for heading, lines in sections:
    content.append(Paragraph(heading, heading_style))
    for line in lines:
        if line:
            content.append(Paragraph(line, body_style))
    content.append(Spacer(1, 10))

doc.build(content)
print(f"Generated: {output_path}")
