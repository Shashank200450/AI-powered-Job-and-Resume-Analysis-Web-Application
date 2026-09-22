from fpdf import FPDF
import os

def generate_sample_resume(output_path='static/sample_resume.pdf'):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    
    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(180, 8, "ALEX MORGAN", align="C", new_x="LMARGIN", new_y="NEXT")
    
    # Contact
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(180, 5, "San Francisco, CA | alex.morgan@email.com | (555) 234-5678 | github.com/alexmorgan", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)
    
    # Summary
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(180, 6, "PROFESSIONAL SUMMARY", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    summary = (
        "Dedicated Software Engineer with 4+ years of hands-on experience in Full Stack development, "
        "REST APIs, and distributed systems. Expert in Java, Python, C++, DSA, Spring Boot, Django, Flask, "
        "and React with proven track record in cloud architecture and database optimization."
    )
    pdf.multi_cell(180, 4.5, summary, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    
    # Skills
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(180, 6, "TECHNICAL SKILLS", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    skills = [
        "- Programming Skills: Java, Python, C++, DSA, JavaScript, TypeScript, SQL, HTML, CSS",
        "- Frameworks: Spring Boot, Django, Flask, React, Angular, Node.js, Express.js",
        "- Databases & Cloud: PostgreSQL, MongoDB, MySQL, Docker, Kubernetes, AWS, Redis",
        "- Methodologies: Agile/Scrum, CI/CD pipelines, System Design, Unit Testing, Git"
    ]
    for sk in skills:
        pdf.cell(180, 4.5, sk, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    
    # Experience
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(180, 6, "PROFESSIONAL EXPERIENCE", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(180, 5, "Senior Software Engineer | CloudScale Inc. (2022 - Present)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    exp1 = [
        "- Designed and implemented scalable microservices using Python (Django, Flask) and Spring Boot.",
        "- Built dynamic, responsive user interfaces using React and modern CSS, improving user retention by 25%.",
        "- Managed NoSQL data pipelines in MongoDB and relational databases in PostgreSQL."
    ]
    for line in exp1:
        pdf.cell(180, 4.5, line, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(180, 5, "Software Engineer | TechNova Solutions (2020 - 2022)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    exp2 = [
        "- Developed backend RESTful endpoints in Java with Spring Boot, serving 1M+ daily requests.",
        "- Implemented complex algorithms and data structures (DSA) to optimize search and caching layers.",
        "- Automated testing and deployment with Docker containers and GitHub Actions."
    ]
    for line in exp2:
        pdf.cell(180, 4.5, line, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Education
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(180, 6, "EDUCATION", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(180, 5, "B.S. in Computer Science | University of California, Berkeley", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(180, 4.5, "Relevant Coursework: Data Structures & Algorithms, Operating Systems, Database Systems, Web Architecture", new_x="LMARGIN", new_y="NEXT")

    pdf.output(output_path)
    print(f"Sample resume created: {output_path}")

if __name__ == '__main__':
    generate_sample_resume()
