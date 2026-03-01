# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "ollama",
#     "tqdm",
# ]
# ///
import argparse
import sys
from pathlib import Path
from tqdm import tqdm
import ollama

def translate_word(word: str, source_lang: str, target_lang: str, model_name: str) -> str:
    prompt = f"Translate the following word from {source_lang} to {target_lang}. Please provide ONLY the translated word(s). If there are multiple common meanings, separate them with a comma (','). Do not include any explanations, surrounding quotes, or additional text. \n\nWord: {word}"
    
    try:
        response = ollama.chat(
            model=model_name,
            messages=[{
                'role': 'user', 
                'content': prompt
            }],
            options={
                'temperature': 0.1, # Low temp for deterministic and strictly literal translation
            }
        )
        translated_text = response['message']['content'].strip()
        # Ensure no semicolons in the output translation (replace them with commas)
        return translated_text.replace(';', ',')
    except Exception as e:
        print(f"\nError translating word '{word}': {e}", file=sys.stderr)
        return ""

def run_translation(input_file: str | Path, source_lang: str, target_lang: str, model: str = "translategemma:12b-it-q4_K_M", output_file: str | Path | None = None) -> Path:
    input_path = Path(input_file)
    if not input_path.exists() or not input_path.is_file():
        raise FileNotFoundError(f"Input file '{input_file}' does not exist.")

    if output_file:
        output_path = Path(output_file)
    else:
        output_path = input_path.with_name(f"{input_path.stem}_{target_lang.lower()}{input_path.suffix}")

    print(f"Loading '{model}'...")
    
    # Check if we can reach Ollama server (will throw on failure)
    try:
        models = ollama.list()
        model_names = [m.get('name') or m.get('model') for m in models.get('models', [])]
        
        # Simple check, we don't strictly enforce it just in case someone passes a tag format difference.
        if not any(model in name for name in model_names):
            print(f"Warning: Model '{model}' might not be pulled locally. Trying to use it anyway...", file=sys.stderr)
            print(f"Tip: If it fails, run `ollama run {model}` first.", file=sys.stderr)
    except Exception as e:
        raise RuntimeError(f"Error connecting to Ollama: {e}\nIs Ollama running?")

    # Read words & remove duplicates while keeping the original order
    words = []
    seen = set()
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            # The input file might contain previously semi-colon separated data or trailing semicolons.
            # We only want the first word (the source word) to translate.
            w = line.strip().rstrip(';').split(';')[0].strip()
            if w and w not in seen:
                seen.add(w)
                words.append(w)

    print(f"Found {len(words)} unique words to translate.")

    # Translate and write directly to output
    with open(output_path, "w", encoding="utf-8") as out_f:
        # Use tqdm for a simple progress bar
        for word in tqdm(words, desc="Translating", unit="word"):
            translated = translate_word(word, source_lang, target_lang, model)
            out_f.write(f"{word};{translated}\n")
            out_f.flush() # Force write to file periodically so no progress is lost if interrupted

    print(f"\nTranslation completed. Output saved to '{output_path}'.")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Translate a list of words from a file using an Ollama model.")
    parser.add_argument("file", type=str, help="Path to the input file (one word per line).")
    parser.add_argument("source_lang", type=str, help="Source language (e.g., 'English').")
    parser.add_argument("target_lang", type=str, help="Target language (e.g., 'Polish').")
    parser.add_argument("--model", type=str, default="translategemma:12b-it-q4_K_M", help="Ollama model to use (default: translategemma:12b-it-q4_K_M).")
    parser.add_argument("--output", "-o", type=str, help="Output file path. Defaults to input_file_<target_lang>.txt")

    args = parser.parse_args()

    try:
        run_translation(args.file, args.source_lang, args.target_lang, args.model, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
