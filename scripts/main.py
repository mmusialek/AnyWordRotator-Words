import json
import sys
from pathlib import Path
from pydantic import BaseModel

# Import the refactored functions directly
from translate import run_translation
from verify_translation import run_verification

# ==========================================
# CONFIGURATION PARAMETERS
# ==========================================
# Set these parameters to control the pipeline
INPUT_FILE = "src/en_pl/temp_en.txt"  # Path to the input words file
SOURCE_LANG = "English"                 # Source language
TARGET_LANG = "Polish"                  # Target language

# Optional parameters
OUTPUT_FILE = ""                        # Leave empty to auto-generate based on target language
MODEL = "translategemma:12b-it-q4_K_M"  # Ollama model to use for translation and verification
LLM_VERIFY = True                       # Set to True to enable semantic LLM verification
# ==========================================

def make_production_ready(file_path: Path) -> Path:
    """Renames the verified file to common_[xxxx].csv where xxxx is the next available index."""
    target_dir = file_path.parent
    
    # Find all common_*.csv files in the directory
    existing_files = list(target_dir.glob("common_*.csv"))
    
    max_index = 0
    for f in existing_files:
        name = f.stem
        try:
            # Expecting format like 'common_0001'
            parts = name.split('_')
            if len(parts) == 2 and parts[1].isdigit():
                max_index = max(max_index, int(parts[1]))
        except ValueError:
            pass
            
    next_index = max_index + 1
    new_name = f"common_{next_index:04d}.csv"
    new_path = target_dir / new_name
    
    # Rename the file
    file_path.rename(new_path)
    print(f"Renamed '{file_path.name}' to '{new_name}'")
    
    return new_path

class WordFile(BaseModel):
    fileUrl: str

class IndexData(BaseModel):
    wordFiles: list[WordFile] = []

def update_index_json(file_path: Path):
    """Updates the src/index.json file with the production-ready translated file using Pydantic."""
    # Find project root (assuming main.py is in scripts/)
    proj_root = Path(__file__).resolve().parent.parent
    index_path = proj_root / "src" / "index.json"
    
    if not index_path.exists():
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_data = IndexData()
    else:
        with open(index_path, "r", encoding="utf-8") as f:
            try:
                raw_data = json.load(f)
                index_data = IndexData.model_validate(raw_data)
            except Exception:
                index_data = IndexData()

    # Format the file path to be relative to the project root with forward slashes
    try:
        rel_path = file_path.resolve().relative_to(proj_root).as_posix()
    except ValueError:
        # If the file is not inside the project root, just use its name
        rel_path = file_path.name

    # Check if the exact entry already exists
    if not any(wf.fileUrl == rel_path for wf in index_data.wordFiles):
        index_data.wordFiles.append(WordFile(fileUrl=rel_path))
        
        with open(index_path, "w", encoding="utf-8") as f:
            # model_dump_json serializes it directly to a nicely formatted JSON string
            json_str = index_data.model_dump_json(indent=4)
            f.write(json_str)
        print(f"Updated {index_path.name} with '{rel_path}'.")
    else:
        print(f"File '{rel_path}' is already in {index_path.name}.")

def main():
    print(f"Starting translation pipeline for: {INPUT_FILE}")
    
    # Find paths relative to project root
    proj_root = Path(__file__).resolve().parent.parent
    input_path = proj_root / INPUT_FILE
    
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' does not exist.")
        sys.exit(1)
        
    if OUTPUT_FILE:
        out_path = Path(OUTPUT_FILE)
        if not out_path.is_absolute():
            out_path = proj_root / OUTPUT_FILE
    else:
        out_path = input_path.with_name(f"{input_path.stem}_{TARGET_LANG.lower()}{input_path.suffix}")

    print("\n" + "="*40)
    print(" STEP 1: Translating")
    print("="*40)
    try:
        generated_output_path = run_translation(
            input_file=input_path,
            source_lang=SOURCE_LANG,
            target_lang=TARGET_LANG,
            model=MODEL,
            output_file=out_path
        )
    except Exception as e:
        print(f"\nError during translating: {e}")
        sys.exit(1)

    print("\n" + "="*40)
    print(" STEP 2: Verifying Translation")
    print("="*40)
    try:
        run_verification(
            file_path=generated_output_path,
            llm=LLM_VERIFY,
            source_lang=SOURCE_LANG,
            target_lang=TARGET_LANG,
            model=MODEL
        )
    except Exception as e:
        print(f"\nError during verification: {e}")
        sys.exit(1)

    print("\n" + "="*40)
    print(" STEP 3: Making Production Ready")
    print("="*40)
    prod_path = make_production_ready(generated_output_path)
    update_index_json(prod_path)
    
    print("\n✅ Pipeline completed successfully!")
    print(f"Production ready file is located at: {prod_path}")

if __name__ == "__main__":
    main()
