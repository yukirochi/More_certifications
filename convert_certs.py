#!/usr/bin/env python3
"""
Certificate Conversion and README Synchronizer

Checks for unconverted PDF certificates in the 'pdfs/' directory,
converts them to high-resolution PNG images in 'images/', and
updates the certificates table in 'README.md'.
"""

import argparse
import os
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


def get_default_alt(pdf_filename: str) -> str:
    """Generate a clean alt text from the PDF filename."""
    stem = Path(pdf_filename).stem
    # Remove common trailing numbers or hashes if any, or keep clean stem
    return stem


def convert_pdf_to_image(pdf_path: Path, output_img_path: Path, dpi: int = 300) -> bool:
    """Convert the first page of a PDF file to a PNG image using PyMuPDF."""
    if fitz is None:
        raise RuntimeError(
            "PyMuPDF (fitz) is not installed. Please install it using: pip install pymupdf"
        )

    try:
        doc = fitz.open(str(pdf_path))
        if len(doc) == 0:
            print(f"  [!] Warning: {pdf_path.name} has no pages.")
            return False

        page = doc[0]
        pix = page.get_pixmap(dpi=dpi)
        output_img_path.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(output_img_path))
        doc.close()
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to convert {pdf_path.name}: {e}", file=sys.stderr)
        return False


def parse_readme_certs(readme_content: str):
    """
    Parse existing certificate entries from the table in README.md.
    Returns a list of dicts: [{'pdf': ..., 'src': ..., 'alt': ...}, ...]
    """
    entries = []
    # Match all td cells
    cell_matches = re.findall(r'<td[^>]*>([\s\S]*?)</td>', readme_content, re.IGNORECASE)
    
    for cell in cell_matches:
        img_match = re.search(r'<img\s+([^>]+)>', cell, re.IGNORECASE)
        pdf_match = re.search(r'<sub>\s*<b>\s*([^<]+?)\s*</b>\s*</sub>', cell, re.IGNORECASE)
        
        if img_match and pdf_match:
            img_attrs = img_match.group(1)
            src_m = re.search(r'src=["\']([^"\']+)["\']', img_attrs)
            alt_m = re.search(r'alt=["\']([^"\']*)["\']', img_attrs)
            
            src = src_m.group(1) if src_m else ""
            alt = alt_m.group(1) if alt_m else ""
            pdf = pdf_match.group(1).strip()
            
            if pdf:
                entries.append({
                    "pdf": pdf,
                    "src": src,
                    "alt": alt
                })
    return entries


def format_readme_table(entries: list) -> str:
    """Format the list of certificate entries into an HTML table (2 columns)."""
    lines = ["<table>"]
    
    for i in range(0, len(entries), 2):
        lines.append("  <tr>")
        
        # Column 1
        item1 = entries[i]
        lines.append('    <td align="center" width="50%">')
        lines.append(f'      <img src="{item1["src"]}" alt="{item1["alt"]}" width="100%"/>')
        lines.append("      <br/>")
        lines.append(f'      <sub><b>{item1["pdf"]}</b></sub>')
        lines.append("    </td>")
        
        # Column 2
        if i + 1 < len(entries):
            item2 = entries[i + 1]
            lines.append('    <td align="center" width="50%">')
            lines.append(f'      <img src="{item2["src"]}" alt="{item2["alt"]}" width="100%"/>')
            lines.append("      <br/>")
            lines.append(f'      <sub><b>{item2["pdf"]}</b></sub>')
            lines.append("    </td>")
        else:
            # Odd number of items: empty right cell
            lines.append('    <td align="center" width="50%">')
            lines.append("    </td>")
            
        lines.append("  </tr>")
        
    lines.append("</table>")
    return "\n".join(lines)


def update_readme(readme_path: Path, all_entries: list) -> bool:
    """Update README.md with formatted certificates table."""
    if not readme_path.exists():
        content = f"### Certificates\n\n<br>\n{format_readme_table(all_entries)}\n"
        readme_path.write_text(content, encoding="utf-8")
        return True

    content = readme_path.read_text(encoding="utf-8")
    table_pattern = re.compile(r"<table>[\s\S]*?</table>", re.IGNORECASE)
    new_table_str = format_readme_table(all_entries)

    if table_pattern.search(content):
        updated_content = table_pattern.sub(new_table_str, content)
    else:
        # If no table exists, append under ### Certificates or at the end
        if "### Certificates" in content:
            updated_content = content.replace("### Certificates", f"### Certificates\n\n<br>\n{new_table_str}")
        else:
            updated_content = content.rstrip() + f"\n\n### Certificates\n\n<br>\n{new_table_str}\n"

    readme_path.write_text(updated_content, encoding="utf-8")
    return True


def sync_certificates(
    pdf_dir: Path,
    img_dir: Path,
    readme_path: Path,
    dpi: int = 300,
    force: bool = False,
    dry_run: bool = False,
):
    """Main synchronization logic."""
    print("=" * 60)
    print("Certificate Sync & Conversion Tool")
    print("=" * 60)
    print(f"PDF Directory   : {pdf_dir}")
    print(f"Images Directory: {img_dir}")
    print(f"README Path     : {readme_path}")
    print(f"DPI Resolution  : {dpi}")
    print(f"Force Reconvert : {force}")
    print(f"Dry Run Mode    : {dry_run}")
    print("-" * 60)

    # 1. Collect all PDF files from pdf_dir (and root if pdfs folder doesn't have all)
    if not pdf_dir.exists():
        pdf_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(list(pdf_dir.glob("*.pdf")), key=lambda p: p.name.lower())
    
    # Also check base dir for any loose PDFs
    base_dir = readme_path.parent
    loose_pdfs = [p for p in base_dir.glob("*.pdf") if p.is_file() and p.parent != pdf_dir]
    if loose_pdfs:
        print(f"Found {len(loose_pdfs)} loose PDF(s) in root directory. Moving to '{pdf_dir.name}/'...")
        for p in loose_pdfs:
            target = pdf_dir / p.name
            if not dry_run:
                p.rename(target)
            print(f"  -> Moved: {p.name} to {target}")
        pdf_files = sorted(list(pdf_dir.glob("*.pdf")), key=lambda p: p.name.lower())

    print(f"Total PDFs found: {len(pdf_files)}")

    # 2. Read README.md and get existing entries
    existing_entries = []
    if readme_path.exists():
        existing_entries = parse_readme_certs(readme_path.read_text(encoding="utf-8"))
    print(f"Existing README entries: {len(existing_entries)}")

    # Map existing entries by PDF filename and image filename for quick lookup
    existing_pdf_set = {entry["pdf"].lower(): entry for entry in existing_entries}
    existing_img_set = {Path(entry["src"]).name.lower(): entry for entry in existing_entries}

    # 3. Check for unconverted PDFs and convert them
    converted_count = 0
    img_dir.mkdir(parents=True, exist_ok=True)

    for pdf_path in pdf_files:
        stem = pdf_path.stem
        img_name = f"{stem}-1.png"
        img_path = img_dir / img_name

        needs_conversion = force or not img_path.exists()

        if needs_conversion:
            print(f"[CONVERTING] {pdf_path.name} -> images/{img_name}...")
            if not dry_run:
                success = convert_pdf_to_image(pdf_path, img_path, dpi=dpi)
                if success:
                    converted_count += 1
            else:
                converted_count += 1
        else:
            # Already converted
            pass

    print(f"Total PDFs converted: {converted_count}")

    # 4. Determine final entries list for README
    # We want to preserve existing entries and their order/alt texts,
    # then append any new PDFs that aren't yet in README.
    final_entries = list(existing_entries)
    added_to_readme = 0

    for pdf_path in pdf_files:
        pdf_name = pdf_path.name
        stem = pdf_path.stem
        img_rel_path = f"images/{stem}-1.png"

        # Check if already present in README
        if pdf_name.lower() in existing_pdf_set:
            continue
        if Path(img_rel_path).name.lower() in existing_img_set:
            continue

        # New certificate
        alt_text = get_default_alt(pdf_name)
        new_entry = {
            "pdf": pdf_name,
            "src": img_rel_path,
            "alt": alt_text,
        }
        final_entries.append(new_entry)
        added_to_readme += 1
        print(f"[README ADD] Added: {pdf_name} (alt: '{alt_text}')")

    # 5. Write updated README.md
    if added_to_readme > 0 or force:
        print(f"\nUpdating README.md with {len(final_entries)} total certificates...")
        if not dry_run:
            update_readme(readme_path, final_entries)
            print("[SUCCESS] README.md updated successfully.")
        else:
            print("[DRY RUN] Skipped writing to README.md.")
    else:
        print("\nREADME.md is already up to date.")

    print("-" * 60)
    print("Summary:")
    print(f"  - Total PDFs: {len(pdf_files)}")
    print(f"  - Newly Converted: {converted_count}")
    print(f"  - Added to README: {added_to_readme}")
    print(f"  - Total in README: {len(final_entries)}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Convert unconverted certificate PDFs to PNG images and update README.md table."
    )
    parser.add_argument(
        "--pdf-dir",
        type=str,
        default="pdfs",
        help="Directory containing PDF files (default: pdfs)",
    )
    parser.add_argument(
        "--img-dir",
        type=str,
        default="images",
        help="Directory to save converted PNG images (default: images)",
    )
    parser.add_argument(
        "--readme",
        type=str,
        default="README.md",
        help="Path to README.md (default: README.md)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="DPI resolution for image rendering (default: 300)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-conversion of all PDFs and rebuild README table",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check what would be done without modifying files",
    )

    args = parser.parse_args()

    # Determine paths relative to script location or current working directory
    base_path = Path.cwd()
    pdf_dir = (base_path / args.pdf_dir).resolve()
    img_dir = (base_path / args.img_dir).resolve()
    readme_path = (base_path / args.readme).resolve()

    sync_certificates(
        pdf_dir=pdf_dir,
        img_dir=img_dir,
        readme_path=readme_path,
        dpi=args.dpi,
        force=args.force,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
