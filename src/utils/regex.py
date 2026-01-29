space = r"\s*"
fill = r"[\s_]*"
number = r"\d+"
dash = rf"{space}(?:-|–){space}"
romanian_t = r"(?:ţ|ț)"
roman_I = r"(?:I|!|l|\|)"
subjects = [
    rf"Subiectul {roman_I}{fill}\({number} de puncte\)",
    rf"Subiectul al {roman_I}{roman_I}{dash}lea{fill}\({number} de puncte\)",
    rf"Subiectul al {roman_I}{roman_I}{roman_I}{dash}lea{fill}\({number} de puncte\)",
]
