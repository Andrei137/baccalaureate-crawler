import re
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from .fields.history import History
from src.utils.io import extract_pdf_text, load_from_json, write_to_json
from src.utils.regex import subjects


def extract_subjects(text: str) -> dict:
    result = {}
    for i in range(len(subjects)):
        finish = subjects[i + 1] if i < len(subjects) - 1 else "Prob(?:ă|a) scrisă"
        match = re.search(
            rf"{subjects[i]}(.*?)(?={finish})", text, re.DOTALL | re.IGNORECASE
        )
        if not match:
            raise ValueError(f"Subiectul {i + 1} nu a fost gasit")
        result[i] = match.group(1)
    return result


def process_version_safe(args):
    parser, version_path = args
    version_result_path = version_path / "result.json"
    try:
        if version_result_path.exists():
            return version_path.name, load_from_json(version_result_path), "Loaded"
        subiect_path = version_path / "subiect.pdf"
        barem_path = version_path / "barem.pdf"
        if not subiect_path.exists() or not barem_path.exists():
            raise FileNotFoundError(f"Missing subiect/barem in {version_path}")
        result = parser.parse(
            extract_subjects(extract_pdf_text(subiect_path, normalize=True)),
            extract_subjects(extract_pdf_text(barem_path, normalize=True)),
        )
        write_to_json(version_result_path, result)
        return version_path.name, result, "Processed"
    except Exception:
        traceback.print_exc()
        return version_path.name, None, "Failed"


def process_field(field_path: Path, max_workers: int = 4):
    parser_map = {"istorie": History}

    field = field_path.name
    if field not in parser_map:
        raise KeyError(f"No parser found for field '{field}'")
    parser = parser_map[field]

    aggregated = {}
    year_paths = [
        p for p in sorted(field_path.iterdir(), key=lambda p: p.name) if p.is_dir()
    ]
    tasks = []
    for year_path in year_paths:
        year = year_path.name
        aggregated[year] = {}
        version_paths = [
            p for p in sorted(year_path.iterdir(), key=lambda p: p.name) if p.is_dir()
        ]
        for version_path in version_paths:
            tasks.append((year, parser, version_path))

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {}
        for year, parser, version_path in tasks:
            future = executor.submit(process_version_safe, (parser, version_path))
            future_to_task[future] = year
        for future in as_completed(future_to_task):
            year = future_to_task[future]
            version, result, status = future.result()
            aggregated[year][version] = result
            print(f"{status} {year}/{version}")
    write_to_json(field_path / "result.json", aggregated)


def main():
    DATA_DIR = Path("data")

    for field_path in DATA_DIR.iterdir():
        if field_path.is_dir():
            process_field(field_path)


if __name__ == "__main__":
    main()
