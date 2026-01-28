import re

from src.utils.regex import space


def flatten_text(text: str) -> str:
    return re.sub(rf"{space}\n{space}", " ", text).strip()


def parse_with_regex(text: str, regex: str) -> str:
    match = re.search(
        regex,
        text,
        re.DOTALL,
    )

    if not match:
        raise ValueError("No match!")
    return flatten_text(match.group(1))


def parse_numbered_sections(text: str, stop_lookahead: str) -> dict:
    matches = re.findall(
        rf"\n(\d+)\.\s+(.*?)(?={stop_lookahead})",
        text,
        re.DOTALL,
    )
    if not matches:
        return flatten_text(text)

    response = {}
    for idx, content in matches:
        response[f"exercițiul_{idx}"] = flatten_text(content)
    return response


def parse_tasks(text: str) -> dict:
    return parse_numbered_sections(
        text,
        stop_lookahead=r"\s+\d+\s+puncte|\n\d+\.|\Z",
    )


def parse_barem(text: str) -> dict:
    return parse_numbered_sections(
        text,
        stop_lookahead=r"\n\d+\.|\Z",
    )
