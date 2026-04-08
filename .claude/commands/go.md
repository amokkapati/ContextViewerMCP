Call `get_selection` with `wait: false` to read the current state from `~/.context-viewer-state.json`. Then:

1. If `voice_query` is non-empty, treat it as the user's instruction and execute it (e.g. explain the selection, navigate to a line, answer a question).
2. If `voice_query` is empty but there is a selection, describe what the selected code does.
3. If there is no selection and no voice query, say "No selection found — please select text in the viewer first."
