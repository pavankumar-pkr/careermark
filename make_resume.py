from reportlab.pdfgen import canvas

c = canvas.Canvas("test_resume.pdf")
c.drawString(100, 750, "Name: Boyini Pavan Kumar")
c.drawString(100, 730, "Education: B.Tech in Computer Science and Engineering")
c.drawString(100, 710, "College: Vardhaman College of Engineering")
c.drawString(100, 690, "Graduation Year: 2027")
c.drawString(100, 670, "Age: 21")
c.save()

print("test_resume.pdf created successfully!")
