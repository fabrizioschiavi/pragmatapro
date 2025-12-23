# OpenType Font Customization

This directory contains a script to merge OpenType stylistic sets into the `calt` (contextual alternates) feature, which is enabled by default.
This allows the stylistic sets to work in applications which do not support explicit stylistic set activation.
This approach aims to preserve all ligatures while enabling the stylistic sets.

## Setup

### Requirements

- Python 3.7 or later
- FontForge (with Python bindings)
- fonttools Python package

### Installation

#### 1. Install FontForge

**macOS (via Homebrew):**
```bash
brew install fontforge
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install fontforge python3-fontforge
```

**Linux (Fedora):**
```bash
sudo dnf install fontforge python3-fontforge
```

**Other platforms:**
See [FontForge installation guide](https://fontforge.org/en-US/downloads/).

#### 2. Set up Python virtual environment

Navigate to the project directory:
```bash
cd path/to/pragmatapro/merge_stylistic_sets
```

Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Link FontForge Python bindings

The FontForge Python module cannot be installed via pip, so it must be symlinked into your virtual environment.

**macOS (Homebrew):**
```bash
# Find your Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')

# Find FontForge installation
FONTFORGE_PATH=$(brew --prefix fontforge)/lib/python${PYTHON_VERSION}/site-packages

# Create symlink
ln -s ${FONTFORGE_PATH}/fontforge.so venv/lib/python${PYTHON_VERSION}/site-packages/
```

**Linux:**
```bash
# Find your Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')

# Link system fontforge module (adjust path if needed)
ln -s /usr/lib/python3/dist-packages/fontforge.so venv/lib/python${PYTHON_VERSION}/site-packages/
# Or try: /usr/lib/python${PYTHON_VERSION}/site-packages/fontforge.so
```

#### 4. Install Python dependencies

Make sure your virtual environment is still activated, then install the required package:
```bash
pip install fonttools
```

#### 5. Verify installation

Test that everything is set up correctly:
```bash
python -c "import fontforge; import fontTools.ttLib; print('Setup successful!')"
```

If you see "Setup successful!", you're ready to use the script.

### Troubleshooting

**"No module named 'fontforge'"**
- The symlink wasn't created correctly.
  Use `find /usr -name "fontforge.so" 2>/dev/null` (Linux) or `find $(brew --prefix)/Cellar/fontforge -name "fontforge.so"` (macOS) to locate the file, then create the symlink manually.

**"ModuleNotFoundError: No module named 'fontTools'"**
- Make sure your virtual environment is activated and run `pip install fonttools` again.

**Permission errors when opening fonts**
- This is normal for some font files.
  The script automatically handles this by temporarily fixing font permissions.

## Usage

The script merges specified stylistic sets into the `calt` feature of a font.

**Syntax:**
```bash
python merge_stylistic_sets.py -f <features> [-s <suffix>] <input_font> <output_font>
```

**Arguments:**
- `-f, --features` (required): Comma-separated list of stylistic sets to merge (e.g., `ss13,ss15,ss18`)
- `-s, --suffix` (optional): Font family name suffix (default: `Custom`)
- `input_font`: Path to input font file (TTF or OTF format)
- `output_font`: Path to output font file

**Example:** Create a Custom variant with `ss13,ss15,ss18` enabled:
```bash
cd path/to/pragmatapro/merge_stylistic_sets
source venv/bin/activate
for S in R B I Z; do
  python merge_stylistic_sets.py -f ss13,ss15,ss18 -s Custom ~/Library/Fonts/PragmataPro${S}_liga_0903.ttf ~/Library/Fonts/PragmataPro${S}_liga_Custom_0903.ttf
done
cd -
```

**Note:** Font paths shown are for macOS (`~/Library/Fonts`).
On Linux, fonts are typically in `~/.local/share/fonts` or `/usr/share/fonts`.

## Limitations: when `pyftfeatfreeze` is still needed

Another tool for customizing fonts is [`pyftfeatfreeze`](https://github.com/twardoch/fonttools-opentype-feature-freezer).
The motivation for `merge_stylistic_sets` is to address one of the noted limitations: Ligature, Multiple, or Chaining Contextual substitutions.
This limitation means that using `pyftfeatfreeze` to enable e.g. `ss13` breaks other ligatures, and the point of `merge_stylistic_sets` is that it does not.
On the other hand, using `merge_stylistic_sets` to enable e.g. `ss16` produces a font where some applications still display the glyphs as if `ss16` was not enabled.
For these, the approach taken by `pyftfeatfreeze` is needed, though it does break the ligatures that involve letters, such as `[OK]` and `- [v]`.

**Examples using pyftfeatfreeze:**

Create Fraktur variant:
```bash
cd ~/Library/Fonts
pyftfeatfreeze -f 'ss03' -R 'PragmataPro Liga/PragmataPro Liga Fraktur' PragmataProR_liga_0903.ttf PragmataProR_liga_Fraktur_0903.ttf
pyftfeatfreeze -f 'ss04' -R 'PragmataPro Liga/PragmataPro Liga Fraktur' PragmataProB_liga_0903.ttf PragmataProB_liga_Fraktur_0903.ttf
pyftfeatfreeze           -R 'PragmataPro Liga/PragmataPro Liga Fraktur' PragmataProI_liga_0903.ttf PragmataProI_liga_Fraktur_0903.ttf
pyftfeatfreeze           -R 'PragmataPro Liga/PragmataPro Liga Fraktur' PragmataProZ_liga_0903.ttf PragmataProZ_liga_Fraktur_0903.ttf
cd -
```

Create Script variant:
```bash
cd ~/Library/Fonts
pyftfeatfreeze           -R 'PragmataPro Liga/PragmataPro Liga Script' PragmataProR_liga_0903.ttf PragmataProR_liga_Script_0903.ttf
pyftfeatfreeze           -R 'PragmataPro Liga/PragmataPro Liga Script' PragmataProB_liga_0903.ttf PragmataProB_liga_Script_0903.ttf
pyftfeatfreeze -f 'ss06' -R 'PragmataPro Liga/PragmataPro Liga Script' PragmataProI_liga_0903.ttf PragmataProI_liga_Script_0903.ttf
pyftfeatfreeze -f 'ss07' -R 'PragmataPro Liga/PragmataPro Liga Script' PragmataProZ_liga_0903.ttf PragmataProZ_liga_Script_0903.ttf
cd -
```

Create Serif variant:
```bash
cd ~/Library/Fonts
pyftfeatfreeze -f 'ss16' -R 'PragmataPro Liga/PragmataPro Liga Serif' PragmataProR_liga_0903.ttf PragmataProR_liga_Serif_0903.ttf
pyftfeatfreeze -f 'ss08' -R 'PragmataPro Liga/PragmataPro Liga Serif' PragmataProB_liga_0903.ttf PragmataProB_liga_Serif_0903.ttf
pyftfeatfreeze -f 'ss09' -R 'PragmataPro Liga/PragmataPro Liga Serif' PragmataProI_liga_0903.ttf PragmataProI_liga_Serif_0903.ttf
pyftfeatfreeze -f 'ss10' -R 'PragmataPro Liga/PragmataPro Liga Serif' PragmataProZ_liga_0903.ttf PragmataProZ_liga_Serif_0903.ttf
cd -
```
