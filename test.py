from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
def ctr(filename="test_resume.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y = height - inch
    c.setFont("sans-serif", 24)
    c.drawString(inch, y, "John Doe")
    y -= 0.3 * inch
    c.setFont("sans-serif", 10)
    c.drawString(inch, y, "Email: mlsc.cv@example.com | Phone: +91 1234567XXX")
    y -= 0.5 * inch
    c.setFont("sans-serif", 14)
    c.drawString(inch, y, "Professional Summary")
    y -= 0.2 * inch
    c.setFont("sans-serif", 10)
    summary = "Experienced Software Developer with 5 years of experience in full-stack development."
    c.drawString(inch, y, summary)
    y -= 0.4 * inch
    c.setFont("sans-serif", 14)
    c.drawString(inch, y, "Technical Skills")
    y -= 0.2 * inch
    c.setFont("sans-serif", 10)
    skills = [
        "Programming: Python, Java, JavaScript, SQL",
        "Frameworks: Django, Flask, React, Node.js",
        "Databases: PostgreSQL, MongoDB, Redis",
        "Cloud: AWS, Docker, Kubernetes",
        "Tools: Git, CI/CD, Jenkins, Agile"
    ]
    for skill in skills:
        c.drawString(inch, y, "• " + skill)
        y -= 0.2 * inch
    y -= 0.2 * inch
    c.setFont("sans-serif", 14)
    c.drawString(inch, y, "Work Experience")
    y -= 0.3 * inch
    c.setFont("sans-serif", 12)
    c.drawString(inch, y, "Senior Python Developer")
    y -= 0.2 * inch
    c.setFont("sans-serif-Oblique", 10)
    c.drawString(inch, y, "Tech Corp Inc. | January 2020 - Present")
    y -= 0.2 * inch
    c.setFont("sans-serif", 10)
    responsibilities = [
        "Developed RESTful APIs using Django and Flask",
        "Implemented microservices architecture with Docker and Kubernetes",
        "Led team of 5 developers in Agile environment",
        "Improved application performance by 40% using Redis caching"
    ]
    for resp in responsibilities:
        c.drawString(inch + 0.2*inch, y, "• " + resp)
        y -= 0.2 * inch
    y -= 0.2 * inch
    c.setFont("sans-serif", 12)
    c.drawString(inch, y, "Software Developer")
    y -= 0.2 * inch
    c.setFont("sans-serif-Oblique", 10)
    c.drawString(inch, y, "StartUp XYZ | June 2018 - December 2019")
    y -= 0.2 * inch
    c.setFont("sans-serif", 10)
    responsibilities2 = [
        "Built web applications using Python, JavaScript, and PostgreSQL",
        "Implemented CI/CD pipelines using Jenkins",
        "Worked with AWS services (EC2, S3, Lambda)"
    ]
    for resp in responsibilities2:
        c.drawString(inch + 0.2*inch, y, "• " + resp)
        y -= 0.2 * inch
    y -= 0.3 * inch
    c.setFont("sans-serif", 14)
    c.drawString(inch, y, "Education")
    y -= 0.2 * inch
    c.setFont("sans-serif", 11)
    c.drawString(inch, y, "Bachelor of Science in Computer Science")
    y -= 0.2 * inch
    c.setFont("sans-serif", 10)
    c.drawString(inch, y, "University of Technology | 2014 - 2018")
    c.save()
    print(f"test resume generated: {filename}")

if __name__ == "__main__":
    ctr("test_resume.pdf")
