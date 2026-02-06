from PyPDF2 import PdfReader, PdfWriter

input_pdf = "testdoc.pdf"
output_pdf = "cours1_.pdf"

reader = PdfReader(input_pdf)
writer = PdfWriter()

START_PAGE = 0   # page 6
END_PAGE = 16    # page 16 (non incluse en Python)

for i in range(START_PAGE, min(END_PAGE, len(reader.pages))):
    writer.add_page(reader.pages[i])

with open(output_pdf, "wb") as f:
    writer.write(f)

print("PDF créé avec succès : pages 6 à 16.")