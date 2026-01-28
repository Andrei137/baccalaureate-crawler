space = r"\s*"
fill = r"[\s_]*"
number = r"\d+"
dash = rf"{space}(?:-|–){space}"
romanian_t = r"(?:ţ|ț)"
subjects = [
    rf"Subiectul I{fill}\({number} de puncte\)",
    rf"Subiectul al II{dash}lea{fill}\({number} de puncte\)",
    rf"Subiectul al III{dash}lea{fill}\({number} de puncte\)",
]
