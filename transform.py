from pathlib import Path
import pymupdf
import os

pdf_folder = Path('pdfs')
images_folder = Path('images')
new_images = []
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

def add_certificate_to_md(file_path, img_filename):
    # 1. Read the markdown file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if a table actually exists in the file
    if "</table>" not in content:
        print("Error: No </table> tag found in the file.")
        return

    # 2. Define the new table data (td) block with proper indentation
    new_td = f"""    <td align="center" width="50%">
      <img src="images/{img_filename}" alt="{img_filename}" width="100%"/>
      <br/>
      <sub><b>{img_filename}</b></sub>
    </td>"""

    # 3. Find where the table ends
    table_end = content.find("</table>")
    table_start = content.rfind("<table>", 0, table_end)

    # 4. Find the last row (<tr>...</tr>) inside the table
    last_tr_start = content.rfind("<tr>", table_start, table_end)
    last_tr_end = content.rfind("</tr>", table_start, table_end)
    last_tr_content = content[last_tr_start:last_tr_end]
    
    # 5. Count how many columns (<td>) are in the last row
    td_count = last_tr_content.count("<td")
    
    if td_count == 1:
        # The last row only has 1 item. Add this to the same row.
        # We insert the new <td> right before the last </tr>
        print("Found a half-empty row. Adding to the existing row...")
        insertion_point = last_tr_end
        updated_content = content[:insertion_point] + new_td + "\n  " + content[insertion_point:]
    else:
        # The last row is full (2 items). Create a brand new row.
        # We insert a new <tr> right before </table>
        print("Last row is full. Creating a new row...")
        new_tr = f"  <tr>\n{new_td}\n  </tr>\n"
        insertion_point = table_end
        updated_content = content[:insertion_point] + new_tr + content[insertion_point:]

    # 6. Save the changes back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
        
    print(f"Successfully added '{img_filename}' to the table!")

