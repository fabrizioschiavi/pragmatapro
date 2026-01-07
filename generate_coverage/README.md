# Font Unicode Coverage Generator

This directory contains a script to generate a visual Unicode coverage file for OpenType fonts.
The script analyzes font files and produces a formatted text document showing which characters are supported, organized by Unicode blocks.

## Setup

### Requirements

- Python 3.7 or later
- fonttools Python package

### Installation

Navigate to the project directory:
```bash
cd path/to/pragmatapro/generate_coverage
```

Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

Install Python dependencies:
```bash
pip install fonttools
```

Verify installation:
```bash
python -c "import fontTools.ttLib; print('Setup successful!')"
```

If you see "Setup successful!", you're ready to use the script.

### Troubleshooting

**"ModuleNotFoundError: No module named 'fontTools'"**
- Make sure your virtual environment is activated and run `pip install fonttools` again.

## Usage

The script generates a Unicode coverage report showing which characters are present in a font.

**Syntax:**
```bash
python generate_font_coverage.py [options] <font_file> [<font_file> ...] > output.txt
```

**Arguments:**
- `font_paths`: One or more font file paths (TTF or OTF format); fonts are searched in order for codepoints
- `--combining-base <char>` (optional): Base character for displaying combining characters (default: `◌`)
- `--show-gaps` (optional): Show blank lines between coverage gaps
- `--show-position-headers` (optional): Show position headers when transitioning between narrow/wide character blocks

**Output:**
The script outputs to stdout a formatted text file showing:
- Font family name, version, and format
- Characters organized by Unicode block
- Visual representation of character coverage with proper spacing
- Special handling for combining characters and wide glyphs

**Note:** When multiple font files are provided, the script merges their coverage and uses glyphs from the first font where each character is found.
Warnings are printed to stderr for glyphs found only in non-Regular weights.

**Batch generation:**
To generate all files with a single click, run the `generate_all_coverage.sh` shell script. 
All generated files will be saved in the `generate_coverage` folder.

## Examples

**Example:** Generate coverage for a single font weight:
```bash
cd path/to/pragmatapro/generate_coverage
source venv/bin/activate
python generate_font_coverage.py ~/Library/Fonts/PragmataProR_liga_0903.ttf > coverage.txt
```

**Example:** Generate coverage for multiple weights (Regular, Bold, Italic, Bold-Italic):
```bash
cd path/to/pragmatapro/generate_coverage
source venv/bin/activate
python generate_font_coverage.py ~/Library/Fonts/PragmataPro{R,I,B,Z}_liga_0903.ttf > coverage.txt
```

**Note:** Font paths shown are for macOS (`~/Library/Fonts`).
On Linux, fonts are typically in `~/.local/share/fonts` or `/usr/share/fonts`.
