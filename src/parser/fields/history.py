import re

from src.utils.parser import flatten_text, parse_barem, parse_tasks, parse_with_regex
from src.utils.regex import romanian_t, space


def tasks_with_source(text: str) -> dict:
    intro_regex = (
        rf"Citi{romanian_t}i,?{space}cu aten{romanian_t}ie,?{space}(?:sursa|sursele)"
        rf"(?:{space}(?:istorice|istorică))?{space}de{space}mai{space}jos{space}:"
    )
    return {
        "sursa": parse_with_regex(
            re.sub(intro_regex, "", text, flags=re.IGNORECASE),
            r"(.*?)(?=Pornind)",
        ),
        "cerința": parse_tasks(text),
    }


def single_task(text: str) -> dict:
    return {"cerința": flatten_text(text)}


class History:
    @staticmethod
    def parse(model: list, barem: list) -> dict:
        result = {}
        parsers = [
            tasks_with_source,
            tasks_with_source,
            single_task,
        ]
        for i in range(len(parsers)):
            result[f"subiectul_{i + 1}"] = parsers[i](model[i])
            result[f"subiectul_{i + 1}"]["barem"] = parse_barem(barem[i])
        return result
