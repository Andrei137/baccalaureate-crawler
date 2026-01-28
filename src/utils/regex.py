space = r"\s*"
fill = r"[\s_]*"
dash = rf"{space}(?:-|–){space}"
romanian_t = r"(?:ţ|ț)"
subjects = [
    rf"Subiectul I{fill}\(30 de puncte\)",
    rf"Subiectul al II{dash}lea{fill}\(30 de puncte\)",
    rf"Subiectul al III{dash}lea{fill}\(30 de puncte\)",
]
