import re

def parse_intern_text(text):
    data = {}

    text_lower = text.lower()

    # ID
    id_match = re.search(r"id[:\s]+(\d+)", text_lower)
    if id_match:
        data["ID"] = id_match.group(1)

    # NAME
    name_match = re.search(
        r"id[:\s]*\d+\s+([A-Z][a-z]+\s[A-Z][a-z]+)\s+is\s+a",
        text,
        re.IGNORECASE
    )

    if name_match:
        data["Name"] = name_match.group(1).strip()

    # INTERN TYPE
    if "student" in text_lower:
        data["intern_type"] = "Student"
    elif "intern" in text_lower:
        data["intern_type"] = "Intern"

    # PAID / UNPAID
    if "unpaid" in text_lower:
        data["Paid/Unpaid"] = "Unpaid"
    elif "paid" in text_lower:
        data["Paid/Unpaid"] = "Paid"

    # LOCATION
    location_match = re.search(r"from\s+([A-Za-z]+)", text)
    if location_match:
        data["location"] = location_match.group(1)

    # DURATION
    duration_match = re.search(r"(\d+)\s*months?", text_lower)
    if duration_match:
        data["duration"] = duration_match.group(1)

    # STATUS
    if "pursuing" in text_lower:
        data["status"] = "Pursuing"
    elif "relieved" in text_lower:
        data["status"] = "Relieved"

    # FTE
    fte_match = re.search(r"fte.*?(yes|no)", text_lower)
    if fte_match:
        data["fte_recommendation"] = fte_match.group(1).capitalize()

    return data