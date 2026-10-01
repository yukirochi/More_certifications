from pathlib import Path
import pymupdf
import os
import re

pdf_folder = Path('pdfs')
images_folder = Path('images')
README = Path("README.md")
IMAGES = Path("images")
COLUMNS_PER_ROW = 2


def build_cell(img_filename):
    return (
        f'    <td align="center" width="50%">\n'
        f'      <img src="images/{img_filename}" alt="{img_filename}" width="100%"/>\n'
        f'      <br/>\n'
        f'      <sub><b>{img_filename}</b></sub>\n'
        f'    </td>\n'
    )


def insert_cell(content, img_filename):
    """Return content with one new cell added, or None if no table exists."""
    table_end = content.find("</table>")
    table_start = content.rfind("<table", 0, table_end)
    if table_end == -1 or table_start == -1:
        return None

    row_start = content.rfind("<tr", table_start, table_end)
    row_end = content.rfind("</tr>", table_start, table_end)
    cells_in_last_row = len(re.findall(r"<td", content[row_start:row_end]))

    cell = build_cell(img_filename)

    if cells_in_last_row < COLUMNS_PER_ROW:
        insert_at = row_end
        new_html = cell + "  "
    else:
        insert_at = table_end
        new_html = f"  <tr>\n{cell}  </tr>\n"

    return content[:insert_at] + new_html + content[insert_at:]


def find_missing_images(content):
    """Images in the folder that the README doesn't reference yet."""
    return sorted(
        img.name
        for img in IMAGES.glob("*.png")
        if f"images/{img.name}" not in content
    )


def add_certificate_to_md(img_filename):
    content = README.read_text(encoding="utf-8")

    # The image we were asked to add, plus any others that are missing
    to_add = set(find_missing_images(content))
    if f"images/{img_filename}" not in content:
        to_add.add(img_filename)

    if not to_add:
        print("Nothing to add, all images are already in the README.")
        return

    for name in sorted(to_add):
        new_content = insert_cell(content, name)
        if new_content is None:
            print("Error: no <table> found in README.md")
            return
        content = new_content
        print(f"Added '{name}'")

    README.write_text(content, encoding="utf-8")
    print(f"Saved {len(to_add)} image(s) to {README.resolve()}")

for pdf in pdf_folder.iterdir():
    found = False
    
    for image in images_folder.iterdir():
        clean_image_name = re.sub(r'-[0-9]\.png$','',image.name)
        if pdf.name.removesuffix(".pdf") == clean_image_name:
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
            add_certificate_to_md(output_filename)
        break   



