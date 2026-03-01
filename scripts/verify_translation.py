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

# Add current directory to path so we can import modules if needed
sys.path.append(str(Path(__file__).parent))

def is_valid_translation(line: str) -> bool:
    """
    Checks if a line has a proper translation format.
    A valid line should have exactly one semicolon separating two non-empty strings.
    """
    parts = line.split(';')
    
    # Needs exactly one semicolon separating source and translation
    if len(parts) != 2:
        return False
    
    source = parts[0].strip()
    translation = parts[1].strip()
    
    # Both source and translation must contain text
    if not source or not translation:
        return False
        
    return True

def llm_verify_translation(source: str, translation: str, src_lang: str, tgt_lang: str, model_name: str) -> bool:
    """
    Uses an LLM to semantically verify if the translation is accurate.
    """
    prompt = f"Translate the following word from {src_lang} to {tgt_lang}. Please provide ONLY the translated word(s). If there are multiple common meanings, separate them with a comma (','). Do not include any explanations, surrounding quotes, or additional text. \n\nWord: {source}"
    
    try:
        response = ollama.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.1}
        )
        expected = response['message']['content'].strip()
        
        # Simple string matching to handle synonyms or slight formatting differences
        t_lower = translation.lower()
        e_lower = expected.lower()
        
        # Check if the generated translation exists in the provided translation or vice versa
        # Also split by commas for robust checking of multiple meanings
        valid = False
        for e_part in e_lower.split(','):
            e_part = e_part.strip()
            if not e_part: continue
            if e_part in t_lower:
                valid = True
                break
        
        for t_part in t_lower.split(','):
            t_part = t_part.strip()
            if not t_part: continue
            if t_part in e_lower:
                valid = True
                break
                
        return valid
    except Exception as e:
        # If Ollama fails (e.g., service down), we should probably fail fast,
        # but for the script's sake, we might just print an error and assume it's invalid
        # or exit the program. Let's exit the program as it indicates an infrastructure failure.
        print(f"\nError connecting to Ollama during verification: {e}", file=sys.stderr)
        sys.exit(1)

def run_verification(file_path: str | Path, llm: bool = False, source_lang: str = "English", target_lang: str = "Polish", model: str = "translategemma:12b-it-q4_K_M") -> None:
    file_path = Path(file_path)
    
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"File '{file_path}' does not exist.")
        
    if llm:
        print(f"LLM Verification Enabled. Model: '{model}' | Source: '{source_lang}' | Target: '{target_lang}'")
        try:
            # Check model availability
            ollama.list()
        except Exception as e:
            raise RuntimeError(f"Error connecting to Ollama: {e}\nIs Ollama running?")
            
    valid_lines = []
    removed_lines = []
    
    # Read the file
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    print(f"Found {len(lines)} lines to verify.")
    
    iterator = enumerate(lines)
    if llm:
        iterator = tqdm(iterator, total=len(lines), desc="Verifying", unit="line")
        
    for idx, line in iterator:
        stripped_line = line.rstrip('\n')
        
        # Remove empty lines silently
        if not stripped_line:
            continue
            
        # 1. Structural Validation
        if not is_valid_translation(stripped_line):
            removed_lines.append((idx + 1, stripped_line, "Malformed structure"))
            continue
            
        # 2. Semantic Validation (if enabled)
        if llm:
            parts = stripped_line.split(';')
            source = parts[0].strip()
            translation = parts[1].strip()
            
            is_valid = llm_verify_translation(source, translation, source_lang, target_lang, model)
            if not is_valid:
                removed_lines.append((idx + 1, stripped_line, "Rejected by LLM"))
                continue
                
        # Passed all checks
        valid_lines.append(line) # keep original line with newline
                
    # Overwrite the file with valid lines only
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(valid_lines)
        
    # State logging removed since main.py handles pipeline tracking and index.json
    # Print the removed lines to console along with line numbers and reasons
    if removed_lines:
        print(f"\nFound and removed {len(removed_lines)} invalid lines:")
        for line_num, content, reason in removed_lines:
            print(f"  Line {line_num} [{reason}]: {content}")
    else:
        print("\nAll lines are correctly formatted translations. No lines were removed.")
        
    print(f"\nVerification complete! The file was saved with {len(valid_lines)} valid lines.")

def main():
    parser = argparse.ArgumentParser(description="Verify translation file format and optionally use an LLM for semantic verification.")
    parser.add_argument("file", type=str, help="Path to the target translation file.")
    
    # Optional LLM args
    parser.add_argument("--llm", action="store_true", help="Enable semantic verification using an LLM.")
    parser.add_argument("--source_lang", type=str, default="English", help="Source language (needed if --llm is used).")
    parser.add_argument("--target_lang", type=str, default="Polish", help="Target language (needed if --llm is used).")
    parser.add_argument("--model", type=str, default="translategemma:12b-it-q4_K_M", help="Ollama model to use (default: translategemma:12b-it-q4_K_M).")
    
    args = parser.parse_args()
    
    try:
        run_verification(args.file, args.llm, args.source_lang, args.target_lang, args.model)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
