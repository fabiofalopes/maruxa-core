import os
from pathlib import Path
from typing import Optional
from llm.local_llm import LocalLLMWrapper
from llama_index.core.llms import ChatMessage

class MarkdownFilter:
    def __init__(self, base_folder: str, output_folder: str):
        self.base_folder = Path(base_folder)
        self.output_folder = Path(output_folder)
        
        # Load the markdown filter prompt
        prompt_path = Path("src/prompts/markdown-filter-rigid-remove-links.md")
        with open(prompt_path, "r") as f:
            filter_prompt = f.read()
        
        # Initialize LLM with the filter prompt
        self.llm = LocalLLMWrapper.create_markdown_filter_llm(filter_prompt)

    def process_file(self, input_file: Path, output_file: Path):
        """Process a single markdown file"""
        # Read input content
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Process through LLM
        messages = [ChatMessage(role="user", content=content)]
        filtered_content = self.llm.chat(messages)

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write filtered content
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(filtered_content)

    def process_folder(self):
        """Process all markdown files in the base folder structure"""
        print(f"Scanning folder: {self.base_folder}")
        files_found = list(self.base_folder.rglob("*.md"))
        print(f"Found {len(files_found)} markdown files")
        
        for input_path in files_found:
            # Calculate relative path to maintain folder structure
            rel_path = input_path.relative_to(self.base_folder)
            output_path = self.output_folder / rel_path
            
            print(f"Processing: {rel_path}")
            self.process_file(input_path, output_path)

def filter_markdown_folder(input_folder: str, output_folder: Optional[str] = None):
    """Convenience function to filter an entire folder of markdown files"""
    # Clean up the input path - remove quotes and normalize
    input_folder = input_folder.strip('"').strip("'").strip("\\")
    input_path = Path(input_folder).resolve()
    
    # Verify input folder exists
    if not input_path.exists():
        print(f"Error: Input folder '{input_path}' does not exist")
        print(f"Debug - Raw input: {input_folder}")
        print(f"Debug - Resolved path: {input_path}")
        print(f"Debug - Current working directory: {Path.cwd()}")
        return
    
    print(f"Input path: {input_path} (exists: {input_path.exists()})")
    
    # If no output folder specified, create one alongside input folder
    if output_folder is None:
        output_path = input_path.parent / f"{input_path.name}-filtered"
    else:
        output_folder = output_folder.strip('"').strip("'").strip("\\")
        output_path = Path(output_folder)
    
    print(f"Output path will be: {output_path}")
    
    filter = MarkdownFilter(str(input_path), str(output_path))
    filter.process_folder()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Filter markdown files in a folder structure")
    parser.add_argument(
        "input_folder",
        help="Path to folder containing markdown files to filter"
    )
    parser.add_argument(
        "--output-folder",
        help="Optional custom output folder path (default: {input_folder}-filtered)",
        default=None
    )
    
    args = parser.parse_args()
    filter_markdown_folder(args.input_folder, args.output_folder)
