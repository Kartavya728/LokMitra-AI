import os

def load_text_from_file(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_multiple_files(paths: list[str]) -> dict:
    """
    Returns {source_name: text}
    """
    texts = {}
    for path in paths:
        name = os.path.splitext(os.path.basename(path))[0]
        texts[name] = load_text_from_file(path)
    return texts
