import os
from pathlib import Path

import fitz


def process_field(field_path: Path):
    for year_path in field_path.iterdir():
        if not year_path.is_dir():
            continue
        for variant_path in year_path.iterdir():
            if not variant_path.is_dir():
                continue
            pdf_file_path = variant_path / "subiect.pdf"
            if not pdf_file_path.exists():
                continue

            pdf_file = fitz.open(pdf_file_path)
            print(f"Processing {pdf_file_path}")

            images_found = False
            for page_index in range(len(pdf_file)):
                page = pdf_file.load_page(page_index)
                image_list = page.get_images(full=True)

                if not image_list:
                    continue

                if not images_found:
                    output_dir = (
                        field_path / f"{year_path.name}/{variant_path.name}" / "images"
                    )
                    os.makedirs(output_dir, exist_ok=True)
                    images_found = True
                    print(f"Creating folder {output_dir}")

                for image_index, img in enumerate(image_list, start=1):
                    xref = img[0]
                    base_image = pdf_file.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]

                    image_name = f"image{page_index + 1}_{image_index}.{image_ext}"
                    output_path = output_dir / image_name
                    with open(output_path, "wb") as image_file:
                        image_file.write(image_bytes)


for field_path in Path("data").iterdir():
    if field_path.is_dir():
        process_field(field_path)
