# Scripts

Helpers to translate word lists and verify translation files. Format everywhere is `source;translation` (one pair per line, UTF-8).

Scripts: `translate.py` (translate), `verify_translation.py` (verify), `main.py` (pipeline: translate → verify → publish), `remove_duplicates.py` (dedupe CSV).

## Prerequisites

- Python 3.12+
- [Ollama](https://ollama.com) running locally with a translation model, e.g.:
  ```sh
  ollama run translategemma:12b-it-q4_K_M
  ```
- Install deps (from `scripts/`):
  ```sh
  uv sync
  # or: pip install ollama tqdm pydantic
  ```

## Quick use

Run from `scripts/`:

```sh
# 1. Translate a word list (one word per line) English -> Polish
uv run translate.py ../src/en_pl/temp_en.txt English Polish --output ../src/en_pl/temp_en_polish.txt
# Output defaults to <input>_<target-lang>.txt when --output is omitted.

# 2. Verify structure only (fast, no LLM)
uv run verify_translation.py ../src/en_pl/temp_en_polish.txt

# 3. Verify structure + meaning with LLM
uv run verify_translation.py ../src/en_pl/temp_en_polish.txt --llm --source_lang English --target_lang Polish

# 4. Full pipeline (translate -> verify -> rename to common_NNNN.csv + update src/index.json)
#    Edit INPUT_FILE / SOURCE_LANG / TARGET_LANG at the top of main.py first.
uv run main.py
```

With plain Python replace `uv run X.py` with `python X.py`.

## Behavior

- `translate.py` dedupes input (order kept), translates word by word with a progress bar, writes `word;translation` lines incrementally (safe to interrupt), exit 1 on missing file / Ollama down.
- `verify_translation.py` (no `--llm`) removes empty lines and lines without exactly one `;` or with an empty side, rewrites the file in place, and prints `Line N [reason]: content` for each removal. With `--llm` it additionally drops pairs the model rejects. Exit 0 = done (even if lines were removed), exit 1 = file missing / Ollama unreachable.
- `main.py` runs the full pipeline and publishes the result as `src/en_pl/common_NNNN.csv` (next free index) + appends it to `src/index.json`.
