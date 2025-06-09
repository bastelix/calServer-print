import os


def test_open_devtools_wrapped():
    here = os.path.dirname(__file__)
    js_path = os.path.join(here, '..', 'electron', 'main.js')
    with open(js_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    idx = None
    for i, line in enumerate(lines):
        if 'openDevTools' in line:
            idx = i
            break
    assert idx is not None, "openDevTools call not found"

    # Find the nearest previous non-empty line
    j = idx - 1
    while j >= 0 and lines[j].strip() == '':
        j -= 1
    assert j >= 0, "No preceding line found"

    assert 'if (isDev' in lines[j], "openDevTools should be inside dev check"
