space = r"\s*"
fill = r"[\s_]*"
number = r"\d+"
dash = rf"{space}(?:-|–){space}"
romanian_t = r"(?:ţ|ț)"
roman_I = r"(?:I|!|l|\|)"
subjects = [
    rf"Subiectul {roman_I}{fill}\(?{number}{fill}de{fill}puncte\)",
    rf"Subiectul al {roman_I}{roman_I}{fill}{dash}{fill}lea{fill}\(?{number}{fill}de{fill}puncte\)",
    rf"Subiectul al {roman_I}{roman_I}{roman_I}{fill}{dash}{fill}lea{fill}\(?{number}{fill}de{fill}puncte\)",
]
