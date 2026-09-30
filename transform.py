from pathlib import Path
import pymupdf
import os

pdf_folder = Path('pdfs')
images_folder = Path('images')

for pdf in pdf_folder.iterdir():
    found = False
    for image in images_folder.iterdir():
        if pdf.name.removesuffix(".pdf") == image.name[:-5]:
            found = True
            break

    if not found:
        pdf_doc = pymupdf.open(f'pdfs/{pdf.name}')

        for page_num in range(len(pdf_doc)):
            page = pdf_doc.load_page(page_num)

            pix = page.get_pixmap(dpi=300)

            output_filename = f'{pdf.name.removesuffix(".pdf")}-{page_num}.png'

            output_path = os.path.join('images', output_filename)

            pix.save(output_path)
        break   
