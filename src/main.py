import re
import traceback
from collections import OrderedDict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from utils.io import extract_pdf_text, load_from_json, write_to_json
from utils.regex import number, romanian_t, space, subjects


def flatten_text(text: str) -> str:
    idx = text.find("Ministerul")
    text = text[:idx] if idx != -1 else text
    return re.sub(rf"{space}\n{space}", " ", text).strip()


def flatten_dict(d):
    if isinstance(d, dict):
        return {k: flatten_dict(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [flatten_dict(v) for v in d]
    elif isinstance(d, str):
        return flatten_text(d)
    else:
        return d


def parse_with_regex(text: str, regex: str) -> str:
    match = re.search(
        regex,
        text,
        re.DOTALL,
    )

    if not match:
        raise ValueError("No match!")
    return match.group(1)


def parse_numbered_sections(text: str, numbering_style: str) -> dict | str:
    if numbering_style == "number":
        regex = r"\n?((?:[0-9]|10))\.\s+(.*?)(?=\s+\d+\s+puncte|\n(?:[0-9]|10)\.\s+|\Z)"
        first_match = r"(?:[0-9]|10)\.\s+"
    elif numbering_style == "barem":
        regex = r"\n?(\d+)\.\s+(.*?)(?=\n\d+\.|\Z)"
        first_match = r"\d+\."
    elif numbering_style == "uppercase":
        regex = r"\n?([A-Z])\.\s+(.*?)(?=\n[A-Z]\.|\Z)"
        first_match = r"[A-Z]\.\s+"
    elif numbering_style == "uppercase_no_dot":
        regex = r"\n?([A-Z])\s+\d+\s+puncte\s*(.*?)(?=\n[A-Z]\s+\d+\s+puncte|\Z)"
        first_match = r"[A-Z]\s+\d+\s+puncte"
    elif numbering_style == "lowercase":
        regex = r"\n?([a-z])\)\s+(.*?)(?=\n[a-z]\)|\Z)"
        first_match = r"[a-z]\)\s+"
    elif numbering_style == "letter":
        regex = r"\n?([A-Za-z])\.\s+(.*?)(?=\n[A-Za-z]\.|\Z)"
        first_match = r"[A-Za-z]\.\s+"
    else:
        raise ValueError("numbering_style must be 'number', 'uppercase' or 'lowercase'")

    matches = re.findall(regex, text, re.DOTALL)
    response = {}

    first_exercise_match = re.search(first_match, text)
    if first_exercise_match:
        pre_text = text[: first_exercise_match.start()].strip()
        if pre_text:
            response["enunt"] = pre_text
    else:
        return text

    for idx, content in matches:
        key = f"exercitiul_{idx.strip()}"
        if key in response:
            response[key] += "\n" + content
        else:
            response[key] = content

    return response


def parse_task(
    text: str, numbering_style: str = "number", delete_points: bool = True
) -> dict:
    text = re.sub(
        rf"Ministerul{space}Educa{romanian_t}iei.*?Pagina{space}{number}{space}din{space}{number}",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if delete_points and numbering_style != "uppercase_no_dot":
        text = re.sub(r"\d+\s+(?:de\s+)?puncte", "", text)

    if numbering_style == "none":
        return text
    return parse_numbered_sections(text, numbering_style)


def parse_subtask(
    text: str,
    numbering_style_task: str = "uppercase",
    numbering_style_subtask: str = "number",
) -> dict:
    tasks = parse_task(text, numbering_style_task)
    if isinstance(tasks, str):
        return parse_task(text, numbering_style_subtask)

    parsed = {}
    for key, exercise_text in tasks.items():
        if key == "enunt":
            parsed["enunt"] = exercise_text
            continue

        subtask = parse_task(exercise_text, numbering_style_subtask)
        if isinstance(subtask, str):
            parsed[key] = exercise_text
            continue

        subtask_renamed = {}
        for subkey, value in subtask.items():
            if subkey == "enunt":
                subtask_renamed["enunt"] = value
            else:
                subtask_renamed[f"subpunctul_{subkey.replace('exercitiul_', '')}"] = (
                    value
                )

        parsed[key] = subtask_renamed

    return parsed


def parse_simple_task(text):
    return parse_task(text, "none")


def parse_task_uppercase(text):
    return parse_task(text, "uppercase")


def parse_task_uppercase_no_dot(text):
    return parse_task(text, "uppercase_no_dot")


def parse_task_letter(text):
    return parse_task(text, "letter")


def parse_subtask_uppercase_number(text):
    return parse_subtask(text, "uppercase", "number")


def parse_subtask_uppercase_no_dot_number(text):
    return parse_subtask(text, "uppercase_no_dot", "number")


def parse_subtask_uppercase_no_dot_lowercase(text):
    return parse_subtask(text, "uppercase_no_dot", "lowercase")


def parse_simple_barem(text: str) -> dict:
    return parse_task(text, "none", False)


def parse_barem(text: str) -> dict:
    return parse_task(text, "barem", False)


def parse_barem_uppercase(text):
    return parse_task(text, "uppercase", False)


def parse_barem_uppercase_no_dot(text):
    return parse_task(text, "uppercase_no_dot", False)


def parse_barem_letter(text):
    return parse_task(text, "letter", False)


def parse(parsers: list, model: list, barem: list) -> dict:
    result = {}
    for i in range(len(parsers)):
        key = f"subiectul_{i + 1}"
        result[key] = dict()
        parse_subiect, parse_barem = parsers[i]
        result[key]["subiect"] = parse_subiect(model[i])
        result[key]["barem"] = parse_barem(barem[i])
    return result


def extract_subjects(text: str) -> dict:
    result = {}
    for i in range(len(subjects)):
        if i < len(subjects) - 1:
            finish = subjects[i + 1]
            pattern = rf"{subjects[i]}(.*?)(?={finish})"
        else:
            pattern = rf"{subjects[i]}(.*)"

        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if not match:
            raise ValueError(f"Subiectul {i + 1} nu a fost gasit")

        result[i] = match.group(1).strip()

    return result


def process_version(args):
    parsers, version_path = args
    version_result_path = version_path / "result.json"
    try:
        if version_result_path.exists():
            return version_path.name, load_from_json(version_result_path), "Loaded"
        subiect_path = version_path / "subiect.pdf"
        barem_path = version_path / "barem.pdf"
        if not subiect_path.exists() or not barem_path.exists():
            raise FileNotFoundError(f"Missing subiect/barem in {version_path}")
        result = parse(
            parsers,
            extract_subjects(extract_pdf_text(subiect_path, normalize=True)),
            extract_subjects(extract_pdf_text(barem_path, normalize=True)),
        )
        write_to_json(version_result_path, flatten_dict(result))
        return version_path.name, result, "Processed"
    except Exception:
        traceback.print_exc()
        return version_path.name, None, "Failed"


def process_field(field_path: Path, max_workers: int = 4):
    parser_map = {
        "biologie_anatomie": [
            (parse_subtask_uppercase_no_dot_number, parse_barem_uppercase_no_dot),
            (parse_subtask_uppercase_no_dot_lowercase, parse_barem_uppercase_no_dot),
            (parse_task, parse_barem),
        ],
        "biologie_vegetala_animala": [
            (parse_subtask_uppercase_no_dot_number, parse_barem_uppercase_no_dot),
            (parse_subtask_uppercase_no_dot_lowercase, parse_barem_uppercase_no_dot),
            (parse_task, parse_barem),
        ],
        "economie": [
            (parse_subtask, parse_barem),
            (parse_simple_task, parse_simple_barem),
            (parse_task, parse_barem),
        ],
        "istorie": [
            (parse_task, parse_barem),
            (parse_task, parse_barem),
            (parse_task, parse_barem),
        ],
        "filosofie": [
            (parse_task, parse_barem),
            (parse_task_uppercase, parse_barem_uppercase),
            (parse_subtask, parse_barem_uppercase),
        ],
        "logica": [
            (parse_simple_task, parse_simple_barem),
            (parse_simple_task, parse_simple_barem),
            (parse_simple_task, parse_simple_barem),
        ],
        "psihologie": [
            (parse_task, parse_barem),
            (parse_simple_task, parse_simple_barem),
            (parse_simple_task, parse_simple_barem),
        ],
        "sociologie": [
            (parse_simple_task, parse_simple_barem),
            (parse_task_letter, parse_barem_letter),
            (parse_task, parse_barem),
        ],
    }

    field = field_path.name
    if field not in parser_map:
        raise KeyError(f"No parser found for field '{field}'")
    parsers = parser_map[field]

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
            tasks.append((year, parsers, version_path))

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {}
        for year, parser, version_path in tasks:
            future = executor.submit(process_version, (parser, version_path))
            future_to_task[future] = year
        for future in as_completed(future_to_task):
            year = future_to_task[future]
            version, result, status = future.result()
            aggregated[year][version] = result
            print(f"{status} {field}/{year}/{version}")

    aggregated = OrderedDict(sorted(aggregated.items(), key=lambda x: x[0]))
    for year, versions in aggregated.items():
        aggregated[year] = dict(sorted(versions.items(), key=lambda x: x[0]))
    write_to_json(field_path / "result.json", flatten_dict(aggregated))


def main():
    finished = [
        "biologie_anatomie",
        "biologie_vegetala_animala",
        "economie",
        "filosofie",
        "istorie",
        # "logica",
        "psihologie",
        "sociologie",
    ]
    for field_path in Path("data").iterdir():
        if field_path.is_dir():
            if field_path.name in finished:
                continue
            process_field(field_path)


if __name__ == "__main__":
    main()
