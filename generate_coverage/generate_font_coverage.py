#!/usr/bin/env python3
"""
Generate a Unicode coverage file for OpenType fonts.

This script analyzes one or more font files and produces a formatted text
document showing Unicode character coverage organized by Unicode blocks.

The script:
1. Loads one or more font files (different weights can be merged)
2. Extracts all available codepoints from the font's cmap table
3. Retrieves glyph metrics (advance width, left side bearing, xMax)
4. Groups characters by Unicode blocks
5. Calculates appropriate spacing for narrow/wide characters
6. Generates formatted output showing character coverage

Features:
- Supports multiple font weights (Regular, Bold, Italic, etc.)
- Spacing based on glyph metrics
- Special handling for combining characters and diacritics
- Automatic detection of wide character blocks

When multiple font files are provided, the script merges their coverage and
uses glyphs from the first font where each character is found. Warnings are
printed to stderr for glyphs found only in non-Regular weights.

Output is written to stdout and should be redirected to a file.
"""

import argparse
import math
import sys
import unicodedata
from pathlib import Path
from fontTools.ttLib import TTFont

POSITION_HEADER_NARROW = "Position 0 1 2 3 4 5 6 7 8 9 A B C D E F"
POSITION_HEADER_WIDE = (
    "Position 0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F"
)
PREFIX_SPACE = " "  # "_"
SUFFIX_SPACE = " "  # "."


def eprintf(*args, **kwargs):
    """Print to stderr."""
    print(*args, file=sys.stderr, **kwargs)


def write(s):
    """Write to stdout without newline."""
    sys.stdout.write(s)


def is_combining(cp):
    """Check if a codepoint is a combining character."""
    # Mn = Nonspacing Mark, Mc = Spacing Mark, Me = Enclosing Mark
    return unicodedata.category(chr(cp)) in ("Mn", "Mc", "Me")


def is_printable(cp):
    """Check if a codepoint is printable (not a control or format character)."""
    return (
        # Exclude invisible formatting characters range (U+2060-U+206F)
        (not (0x2060 <= cp <= 0x206F))
        # Exclude Cc (Control), Cf (Format), Zs (Space Separator) categories
        and not (unicodedata.category(chr(cp)) in ("Cc", "Cf", "Zs"))
    )


UNICODE_BLOCKS = [
    (0x0000, 0x007F, "Basic Latin"),
    (0x0080, 0x00FF, "Latin-1 Supplement"),
    (0x0100, 0x017F, "Latin Extended-A"),
    (0x0180, 0x024F, "Latin Extended-B"),
    (0x0250, 0x02AF, "IPA Extensions"),
    (0x02B0, 0x02FF, "Spacing Modifier Letters"),
    (0x0300, 0x036F, "Combining Diacritical Marks"),
    (0x0370, 0x03FF, "Greek and Coptic"),
    (0x0400, 0x04FF, "Cyrillic"),
    (0x0500, 0x052F, "Cyrillic Supplement"),
    (0x0530, 0x058F, "Armenian"),
    (0x0590, 0x05FF, "Hebrew"),
    (0x0600, 0x06FF, "Arabic"),
    (0x0700, 0x074F, "Syriac"),
    (0x0750, 0x077F, "Arabic Supplement"),
    (0x0780, 0x07BF, "Thaana"),
    (0x0900, 0x097F, "Devanagari"),
    (0x0980, 0x09FF, "Bengali"),
    (0x1680, 0x169F, "Ogham"),
    (0x16A0, 0x16FF, "Runic"),
    (0x1700, 0x171F, "Tagalog"),
    (0x1AB0, 0x1AFF, "Combining Diacritical Marks Extended"),
    (0x1B00, 0x1B7F, "Balinese"),
    (0x1D00, 0x1D7F, "Phonetic Extensions"),
    (0x1D80, 0x1DBF, "Phonetic Extensions Supplement"),
    (0x1DC0, 0x1DFF, "Combining Diacritical Marks Supplement"),
    (0x1E00, 0x1EFF, "Latin Extended Additional"),
    (0x1F00, 0x1FFF, "Greek Extended"),
    (0x2000, 0x206F, "General Punctuation"),
    (0x2070, 0x209F, "Superscripts and Subscripts"),
    (0x20A0, 0x20CF, "Currency Symbols"),
    (0x20D0, 0x20FF, "Combining Diacritical Marks for Symbols"),
    (0x2100, 0x214F, "Letterlike Symbols"),
    (0x2150, 0x218F, "Number Forms"),
    (0x2190, 0x21FF, "Arrows"),
    (0x2200, 0x22FF, "Mathematical Operators"),
    (0x2300, 0x23FF, "Miscellaneous Technical"),
    (0x2400, 0x243F, "Control Pictures"),
    (0x2440, 0x245F, "Optical Character Recognition"),
    (0x2460, 0x24FF, "Enclosed Alphanumerics"),
    (0x2500, 0x257F, "Box Drawing"),
    (0x2580, 0x259F, "Block Elements"),
    (0x25A0, 0x25FF, "Geometric Shapes"),
    (0x2600, 0x26FF, "Miscellaneous Symbols"),
    (0x2700, 0x27BF, "Dingbats"),
    (0x27C0, 0x27EF, "Miscellaneous Mathematical Symbols-A"),
    (0x27F0, 0x27FF, "Supplemental Arrows-A"),
    (0x2800, 0x28FF, "Braille Patterns"),
    (0x2900, 0x297F, "Supplemental Arrows-B"),
    (0x2980, 0x29FF, "Miscellaneous Mathematical Symbols-B"),
    (0x2A00, 0x2AFF, "Supplemental Mathematical Operators"),
    (0x2B00, 0x2BFF, "Miscellaneous Symbols and Arrows"),
    (0x2C00, 0x2C5F, "Glagolitic"),
    (0x2C60, 0x2C7F, "Latin Extended-C"),
    (0x2C80, 0x2CFF, "Coptic"),
    (0x2D00, 0x2D2F, "Georgian Supplement"),
    (0x2D30, 0x2D7F, "Tifinagh"),
    (0x2D80, 0x2DDF, "Ethiopic Extended"),
    (0x2DE0, 0x2DFF, "Cyrillic Extended-A"),
    (0x2E00, 0x2E7F, "Supplemental Punctuation"),
    (0xE000, 0xE00A, "Nerd Fonts - Pomicons"),
    (0xE00B, 0xE09F, "Private Use Area"),
    (0xE0A0, 0xE0A3, "Nerd Fonts - Powerline"),
    (0xE0A4, 0xE0AF, "Private Use Area"),
    (0xE0B0, 0xE0D7, "Nerd Fonts - Powerline"),
    (0xE200, 0xE2A9, "Nerd Fonts - Font Awesome Extension"),
    (0xE2AA, 0xE2FF, "Private Use Area"),
    (0xE300, 0xE3E3, "Nerd Fonts - Weather Icons"),
    (0xE5FA, 0xE6B8, "Nerd Fonts - Seti-UI + Custom"),
    (0xE700, 0xE8EF, "Nerd Fonts - Devicons"),
    (0xEA60, 0xEC1E, "Nerd Fonts - Codicons"),
    (0xED00, 0xEDFF, "Nerd Fonts - Font Awesome"),
    (0xEE00, 0xEE0B, "Nerd Fonts - Progress Indicators"),
    (0xEE0C, 0xF2FF, "Nerd Fonts - Font Awesome"),
    (0xF300, 0xF381, "Nerd Fonts - Font Logos"),
    (0xF400, 0xF533, "Nerd Fonts - Octicons"),
    (0xF500, 0xF7FF, "Nerd Fonts - Material Design"),
    (0xF800, 0xF8EF, "Private Use Area"),
    (0xF8F0, 0xFADF, "Nerd Fonts - Material Design (v2 range)"),
    (0xFB00, 0xFB4F, "Alphabetic Presentation Forms"),
    (0xFB50, 0xFDFF, "Arabic Presentation Forms-A"),
    (0xFE00, 0xFE0F, "Variation Selectors"),
    (0xFE10, 0xFE1F, "Vertical Forms"),
    (0xFE20, 0xFE2F, "Combining Half Marks"),
    (0xFE30, 0xFE4F, "CJK Compatibility Forms"),
    (0xFE50, 0xFE6F, "Small Form Variants"),
    (0xFE70, 0xFEFF, "Arabic Presentation Forms-B"),
    (0xFF00, 0xFFEF, "Halfwidth and Fullwidth Forms"),
    (0xFFF0, 0xFFFF, "Specials"),
    (0x10000, 0x1007F, "Linear B Syllabary"),
    (0x10080, 0x100FF, "Linear B Ideograms"),
    (0x10100, 0x1013F, "Aegean Numbers"),
    (0x10140, 0x1018F, "Ancient Greek Numbers"),
    (0x10190, 0x101CF, "Ancient Symbols"),
    (0x101D0, 0x101FF, "Phaistos Disc"),
    (0x10280, 0x1029F, "Lycian"),
    (0x102A0, 0x102DF, "Carian"),
    (0x10300, 0x1032F, "Old Italic"),
    (0x10330, 0x1034F, "Gothic"),
    (0x10380, 0x1039F, "Ugaritic"),
    (0x103A0, 0x103DF, "Old Persian"),
    (0x10400, 0x1044F, "Deseret"),
    (0x10450, 0x1047F, "Shavian"),
    (0x10480, 0x104AF, "Osmanya"),
    (0x10800, 0x1083F, "Cypriot Syllabary"),
    (0x1D400, 0x1D7FF, "Mathematical Alphanumeric Symbols"),
    (0x1F000, 0x1F02F, "Mahjong Tiles"),
    (0x1F030, 0x1F09F, "Domino Tiles"),
    (0x1F0A0, 0x1F0FF, "Playing Cards"),
    (0x1F100, 0x1F1FF, "Enclosed Alphanumeric Supplement"),
    (0x1F200, 0x1F2FF, "Enclosed Ideographic Supplement"),
    (0x1F300, 0x1F5FF, "Miscellaneous Symbols and Pictographs"),
    (0x1F600, 0x1F64F, "Emoticons"),
    (0x1F650, 0x1F67F, "Ornamental Dingbats"),
    (0x1F680, 0x1F6FF, "Transport and Map Symbols"),
    (0x1F700, 0x1F77F, "Alchemical Symbols"),
    (0x1F780, 0x1F7FF, "Geometric Shapes Extended"),
    (0x1F800, 0x1F8FF, "Supplemental Arrows-C"),
    (0x1F900, 0x1F9FF, "Supplemental Symbols and Pictographs"),
    (0x1FA00, 0x1FA6F, "Chess Symbols"),
    (0x1FA70, 0x1FAFF, "Symbols and Pictographs Extended-A"),
    (0x1FB00, 0x1FBFF, "Symbols for Legacy Computing"),
    (0xF0000, 0xF1AF0, "Nerd Fonts - Material Design"),
    (0xF1AF1, 0xFFFFF, "Private Use Area"),
    (0x100000, 0x10FFFF, "Supplementary Private Use Area-B"),
]


def _make_block_finder():
    last_idx = 0

    def find_block_name(cp):
        """Find the Unicode block name for a codepoint."""
        nonlocal last_idx
        num_blocks = len(UNICODE_BLOCKS)
        for offset in range(num_blocks):
            idx = (last_idx + offset) % num_blocks
            start, end, name = UNICODE_BLOCKS[idx]
            if start <= cp <= end:
                last_idx = idx
                return name

    return find_block_name


find_block_name = _make_block_finder()


def calc_wide_blocks(codepoints):
    """Calculate which Unicode blocks should use double-width spacing."""
    wide_blocks = []

    for start, end, name in UNICODE_BLOCKS:
        count_wide = 0

        for cp in codepoints:
            if start <= cp <= end:
                # Special case for ᾖ, ᾗ, 􀄄, 􀄅, 􀄆, 􀄇 which seem to be incorrectly wide
                if 0x1F96 <= cp <= 0x1F97 or 0x100104 <= cp <= 0x100107:
                    continue

                advance, lsb, xmax = codepoints[cp]
                width = max(advance, xmax - lsb)

                if width >= 1536:
                    count_wide += 1

        if count_wide > 2:
            wide_blocks.append((start, end))

    return wide_blocks


def in_wide_block(wide_blocks, start, end):
    """Determine if a line should use double-width spacing."""
    for cp in range(start, end):
        for block_start, block_end in wide_blocks:
            if block_start <= cp <= block_end:
                return True
    return False


def calc_prefix_spaces(codepoints, cp):
    """Calculate number of spaces to add before a char."""
    # If the glyph extends significantly left of the origin, add enough
    # spaces (1024 units each) to avoid overprinting to the left.
    # Threshold of 512 units (0.5 spaces) excludes small extensions.
    lsb = codepoints[cp][1]
    if lsb < -512:
        return math.ceil(-lsb / 1024)
    return 0


def calc_suffix_spaces(
    combining_base, codepoints, is_wide, cp, prefix_spaces
):
    """Calculate number of spaces to add after a char."""
    # If the glyph advances less than expected, add spaces to preserve
    # vertical alignment.

    advance = codepoints[cp][0]
    # For combining marks: use the wider of the mark's advance or base's advance.
    # To calculate this correctly would require using a text shaping engine.
    if is_combining(cp):
        advance = max(advance, codepoints[ord(combining_base)][0])

    expected_width = 2048 if is_wide else 1024
    shortfall = max(0, expected_width - advance)
    nspaces = math.ceil(shortfall / 1024)

    # If a char extends to the left and has been prefixed, then the suffix
    # should be reduced.
    nspaces -= prefix_spaces

    return nspaces


def write_codepoint(combining_base, codepoints, is_wide, cp):
    """Write a codepoint."""
    char = chr(cp)
    prefix_spaces = 0

    if is_combining(cp):
        write(combining_base)

    # Special case for U+1F96 (ᾖ) and U+1F97 (ᾗ)
    # The ypogegrammeni render to the left instead of under the stem of the η (font bug?)
    # Avoid calculation below which would prefix a space
    elif cp == 0x1F96 or cp == 0x1F97:
        pass

    else:
        # Calculate extra spacing for glyphs that extend left
        prefix_spaces = calc_prefix_spaces(codepoints, cp)
        write(PREFIX_SPACE * prefix_spaces)

    write(char)

    # Calculate extra spacing for glyphs that extend right
    suffix_spaces = calc_suffix_spaces(
        combining_base, codepoints, is_wide, cp, prefix_spaces
    )

    # # Special cases for U+27C2 (⟂) and U+2918 (⤘)
    # # They have narrow advance but wide visual width (font bug?)
    # if cp == 0x27C2 or cp == 0x2918:
    #     suffix_spaces = 1

    write(SUFFIX_SPACE * suffix_spaces)


def gen_coverage_section(
    combining_base,
    show_gaps,
    show_position_headers,
    codepoints,
    wide_blocks,
):
    """Generate a single coverage section."""
    last_line = None
    last_printed_block = None
    last_width_mode = None

    # Group codepoints by their 16-char line
    lines_with_codepoints = {}
    for cp in codepoints:
        line = (cp // 16) * 16
        if line not in lines_with_codepoints:
            lines_with_codepoints[line] = []
        lines_with_codepoints[line].append(cp)

    for line, line_codepoints in sorted(lines_with_codepoints.items()):
        gap_here = last_line is not None and line != last_line + 16
        if show_gaps and gap_here:
            write("\n")

        # Detect all block changes within this 16-char line
        segments = []  # List of (start_offset, end_offset, block_name)

        def append(start, end, name):
            # Filter segments to only include those with at least one glyph
            if any(line + i in codepoints for i in range(start, end)):
                segments.append((start, end, name))

        current_segment_start = 0
        current_block_name = None
        for offset in range(16):
            cp_check = line + offset
            block_name = find_block_name(cp_check)
            if block_name != current_block_name:
                if current_block_name is not None:
                    append(current_segment_start, offset, current_block_name)
                current_segment_start = offset
                current_block_name = block_name

        # Close final segment
        if current_block_name is not None:
            append(current_segment_start, 16, current_block_name)

        # Skip this line entirely if no segments have glyphs
        if not segments:
            continue

        # Determine spacing based on number of hex digits (maintains constant width)
        hex_len = len(f"{line:X}")
        width = max(4, hex_len)
        prefix = " U+" if hex_len <= 4 else "U+"
        hex_format = f"{line:0{width}X}"
        suffix = "  " if hex_len <= 5 else " "

        # Write segments with headers
        for seg_start, seg_end, seg_block in segments:
            # Determine if this segment uses double-width spacing
            is_wide = in_wide_block(
                wide_blocks, line + seg_start, line + seg_end
            )

            # Write position header only when transitioning between width modes
            if show_position_headers and last_width_mode != is_wide:
                if is_wide:
                    write(f"\n{POSITION_HEADER_WIDE}\n\n")
                else:
                    write(f"\n{POSITION_HEADER_NARROW}\n\n")

            # Update width mode tracking
            last_width_mode = is_wide

            # Write header if this is a new Unicode block
            if seg_block != last_printed_block:
                write(f"      ▾  {seg_block}\n")
                last_printed_block = seg_block

            # Write line prefix
            write(f"{prefix}{hex_format}{suffix}")

            # Add padding for segments not starting at offset 0
            write(" " * (seg_start * (3 if is_wide else 2)))

            # Write characters for this segment
            for offset in range(seg_start, seg_end):
                cp = line + offset
                if cp in codepoints:
                    write_codepoint(combining_base, codepoints, is_wide, cp)

                    # Write inter-column space
                    if offset < 15:
                        # Skip inter-column separator for very wide characters
                        advance = codepoints[cp][0]
                        expected_advance = 2048 if is_wide else 1024
                        overhang = max(0, advance - expected_advance)
                        remaining = max(0, 1024 - overhang)
                        write(" " * math.ceil(remaining / 1024))
                else:
                    # Write spaces for missing chars
                    write("  " if is_wide else " ")

                    # Write inter-column separator
                    if offset < 15:
                        write(" ")

            write("\n")

        last_line = line

    # Return final width mode for footer
    return last_width_mode


def gen_coverage_file(
    combining_base,
    show_gaps,
    show_position_headers,
    font_name,
    codepoints,
):
    """Generate the coverage file."""
    eprintf(f"\nGenerating coverage...")
    eprintf(f"  Show gaps: {show_gaps}")
    eprintf(f"  Combining base: '{combining_base}'")

    wide_blocks = calc_wide_blocks(codepoints)

    write(f"\n\n{font_name} coverage\n\n\n")

    last_block_wide = gen_coverage_section(
        combining_base,
        show_gaps,
        show_position_headers,
        codepoints,
        wide_blocks,
    )

    if last_block_wide:
        write(f"\n\n{POSITION_HEADER_WIDE}\n")
    else:
        write(f"\n\n{POSITION_HEADER_NARROW}\n")


def get_metrics(font, cp):
    glyf_table = font["glyf"]
    for table in font["cmap"].tables:
        cmap = table.cmap
        if cp not in cmap:
            continue
        glyph_name = cmap[cp]
        advance, lsb = font["hmtx"].metrics[glyph_name]
        if glyph_name in glyf_table:
            glyph = glyf_table[glyph_name]
            xmax = getattr(glyph, "xMax", advance)
            return (advance, lsb, xmax)


def build_codepoints_table(fonts, merged_codepoints):
    codepoints = {}
    first_weight = next(iter(fonts))

    for cp in merged_codepoints:
        if not is_printable(cp):
            continue
        for weight, font in fonts.items():
            metrics = get_metrics(font, cp)
            if metrics:
                if weight != first_weight:
                    eprintf(
                        f"U+{cp:X} ({chr(cp)}) found in {weight.title()} but not {first_weight.title()}"
                    )
                codepoints[cp] = metrics
                break
        if cp not in codepoints:
            eprintf(f"U+{cp:X} ({chr(cp)}) no metrics")
    return codepoints


def extract_and_merge_codepoints(fonts):
    """Extract codepoints from all font weights."""
    weight_codepoints = {}
    first_weight = next(iter(fonts))
    if first_weight != "regular":
        eprintf(
            f"WARNING: First font weight is {first_weight.title()}, expected Regular"
        )

    # Extract codepoints from all weights
    for weight in fonts.keys():
        weight_name = weight.replace("_", "-").title()
        eprintf(f"Extracting {weight_name} weight codepoints...")
        weight_codepoints[weight] = {
            cp for table in fonts[weight]["cmap"].tables for cp in table.cmap
        }
        eprintf(f"  {weight_name}: {len(weight_codepoints[weight])} glyphs")

    # Merge all weights for the main list
    eprintf(f"\nMerging all weights...")
    merged_codepoints = weight_codepoints[first_weight].copy()
    for weight in weight_codepoints.keys():
        if weight != first_weight:
            merged_codepoints.update(weight_codepoints[weight])
    eprintf(f"  Total merged glyphs: {len(merged_codepoints)}")

    return merged_codepoints


def get_font_family(font):
    """Extract the font family name from a TTFont object."""
    for record in font["name"].names:
        # Name ID 1 is font family name
        if record.nameID == 1:
            return record.toUnicode()
    return None


def get_font_style(font):
    """Get the font style from a TTFont object."""
    # Name ID 2 is subfamily name
    for record in font["name"].names:
        if record.nameID == 2:
            return record.toUnicode().lower()
    return None


def get_font_version(font):
    """Extract the font version from a TTFont object."""
    # Name ID 5 is Version string
    for record in font["name"].names:
        if record.nameID == 5:
            version_str = record.toUnicode()
            # Clean up version string (often contains "Version " prefix)
            version_str = version_str.replace("Version ", "").strip()
            return version_str
    return "Unknown"


def get_font_format(font):
    """Determine if font is OTF or TTF based on outline format."""
    # Check for glyf table (TrueType outlines)
    if "glyf" in font:
        return "TTF"
    # Check for CFF table (OpenType with PostScript outlines)
    elif "CFF " in font or "CFF2" in font:
        return "OTF"
    else:
        return "Unknown"


def load_and_validate_fonts(font_paths):
    """Load and validate font files, returning weights dict, font objects, and family name."""
    weights = {}
    fonts = {}
    font_name = None
    font_version = None
    font_format = None

    for font_path in font_paths:
        path = Path(font_path)
        if not path.exists():
            eprintf(f"Error: Font file not found: {font_path}")
            sys.exit(1)

        # Load font
        try:
            font = TTFont(path)
        except Exception as e:
            eprintf(f"Error: Failed to load font file: {font_path}")
            eprintf(f"  {e}")
            sys.exit(1)

        # Extract name and style
        name = f"{get_font_family(font)} ({get_font_version(font)}, {get_font_format(font)})"
        style = get_font_style(font)

        # Validate family consistency
        if font_name is None:
            font_name = name
        elif font_name != name:
            eprintf(f"Warning: Multiple font names.")
            eprintf(f"  Expected: {font_name}")
            eprintf(f"  Found:    {name} in {font_path}")

        # Store font path and object by style
        if style in weights:
            eprintf(
                f"Warning: Multiple {style} fonts specified, using first one"
            )
        else:
            weights[style] = path
            fonts[style] = font

    eprintf(f"Font name: {font_name}")
    eprintf(f"Fonts loaded:")
    for style, path in weights.items():
        if path:
            eprintf(f"  {style.replace('_', '-').title()}: {path}")

    return font_name, fonts


def main():
    parser = argparse.ArgumentParser(
        description="Generate Unicode coverage file for a font"
    )
    parser.add_argument(
        "font_paths",
        nargs="+",
        help="Font file paths; they will be searched in order for codepoints",
    )
    parser.add_argument(
        "--combining-base",
        default="◌",
        help="Base character for combining characters (default: ◌)",
    )
    parser.add_argument(
        "--show-gaps",
        action="store_true",
        help="Show blank lines between coverage gaps (default: off)",
    )
    parser.add_argument(
        "--show-position-headers",
        action="store_true",
        help="Show Position headers when transitioning between narrow/wide blocks (default: off)",
    )
    args = parser.parse_args()

    font_name, fonts = load_and_validate_fonts(args.font_paths)

    codepoints = extract_and_merge_codepoints(fonts)

    if ord(args.combining_base) not in codepoints:
        eprintf(f"Combining base ({args.combining_base}) not found in font.")
        sys.exit(1)

    codepoints = build_codepoints_table(fonts, codepoints)

    gen_coverage_file(
        args.combining_base,
        args.show_gaps,
        args.show_position_headers,
        font_name,
        codepoints,
    )


if __name__ == "__main__":
    main()
