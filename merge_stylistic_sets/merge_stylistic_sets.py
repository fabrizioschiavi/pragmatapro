#!/usr/bin/env python3
"""
Merge OpenType stylistic sets into calt feature.

This script merges the specified stylistic sets into the contextual
alternates (calt) feature, which is enabled by default in most
applications. This allows the stylistic sets to work in applications that
don't support explicit stylistic set activation, while preserving existing
ligatures.

The script works by:
1. Testing if the font can be opened with FontForge (supports both TTF and
   OTF formats)
2. If the font has restricted permissions:
   - Creates a temporary file in the system temp directory
   - Fixes the permissions using fontTools (changes `fsType` from Restricted
     0x0002 to Editable 0x0008)
   - Preserves the "No subsetting" flag (bit 8: 0x0100) if present
   - Uses the fixed version for processing
   - Cleans up the temporary file when done
3. Finding lookups associated with the specified stylistic sets
4. Adding the `calt` feature to those lookups using `lookupSetFeatureList()`
5. Preserving the original feature associations
6. Updating font metadata to indicate customization
7. Generating the output font in the same format as input

This approach preserves all ligatures by adding features rather than
remapping glyphs.
"""

import argparse
import os
import sys
import tempfile

import fontforge
from fontTools.ttLib import TTFont


def merge_stylistic_sets_to_calt(
    input_font, output_font, stylistic_sets, suffix="Custom"
):
    """Merge specified stylistic sets into the calt feature."""
    print(f"Opening font: {input_font}")
    font = fontforge.open(input_font)

    # Track which lookups we've processed
    merged_count = 0

    # Get all GSUB lookups
    try:
        all_lookups = font.gsub_lookups
        print(f"Found {len(all_lookups)} GSUB lookups in font")
    except AttributeError:
        print("Warning: Font has no GSUB lookups")
        all_lookups = []

    # Find lookups associated with our target stylistic sets
    target_lookups = []
    for lookup in all_lookups:
        try:
            info = font.getLookupInfo(lookup)
            # info[2] contains feature script language tuples
            feature_script_langs = info[2] if len(info) > 2 else []

            for fsl in feature_script_langs:
                feature_tag = fsl[0]
                if feature_tag in stylistic_sets:
                    target_lookups.append(
                        (lookup, feature_tag, info[0], info[1])
                    )
                    print(
                        f"Found lookup '{lookup}' for feature '{feature_tag}'"
                    )
                    break
        except Exception as e:
            print(f"Warning: Could not process lookup '{lookup}': {e}")
            continue

    if not target_lookups:
        print(
            f"Warning: No lookups found for stylistic sets {stylistic_sets}"
        )
        print("Available features in font:")
        for lookup in all_lookups[:20]:  # Show first 20 for debugging
            try:
                info = font.getLookupInfo(lookup)
                if len(info) > 2:
                    features = [fsl[0] for fsl in info[2]]
                    print(f"  {lookup}: {features}")
            except Exception:
                pass

    # For each target lookup, add its feature to calt
    for lookup, original_feature, _, _ in target_lookups:
        try:
            # Get the feature-script-lang info for this lookup
            info = font.getLookupInfo(lookup)

            # Add calt feature to this lookup (in addition to its existing feature)
            # We need to preserve the original feature and add calt
            current_features = list(info[2]) if len(info) > 2 else []

            # Check if calt is already there
            has_calt = any(fsl[0] == "calt" for fsl in current_features)

            if not has_calt:
                # Copy script/language associations from the original feature
                original_scripts = next(
                    (
                        fsl[1]
                        for fsl in current_features
                        if fsl[0] == original_feature
                    ),
                    (("latn", ("dflt",)),),  # Fallback to Latin
                )
                current_features.append(("calt", original_scripts))

                # Update the lookup with new features using lookupSetFeatureList
                font.lookupSetFeatureList(lookup, tuple(current_features))

                print(
                    f"Added 'calt' feature to lookup '{lookup}' (originally {original_feature})"
                )
                merged_count += 1
            else:
                print(f"Lookup '{lookup}' already has calt feature")

        except Exception as e:
            print(f"Error processing lookup '{lookup}': {e}")
            continue

    # Update font metadata to indicate customization
    # Extract style (e.g., "Regular", "Bold", etc.) from full name
    style = font.fullname.replace(font.familyname, "").strip()

    # Update family name with suffix
    font.familyname += f" {suffix}"

    # Reconstruct full name: family + suffix + style
    if style:
        font.fullname = font.familyname + " " + style
    else:
        font.fullname = font.familyname

    # Reconstruct PostScript name: remove spaces and add style
    base_fontname = font.familyname.replace(" ", "")
    if style:
        font.fontname = base_fontname + style.replace(" ", "")
    else:
        font.fontname = base_fontname

    # Add a note to the font
    try:
        font.appendSFNTName(
            "English (US)",
            "Descriptor",
            f"Customized with {', '.join(stylistic_sets)} features enabled by default",
        )
    except Exception as e:
        print(f"Warning: Could not add descriptor to font: {e}")

    print(f"\nSuccessfully merged {merged_count} lookups into calt feature")
    print(f"Generating output font: {output_font}")

    # Generate the output font
    print(f"Font family name: {font.familyname}")
    font.generate(output_font)
    font.close()

    print(f"Generated: {output_font}")


def main():
    parser = argparse.ArgumentParser(
        description="Merge OpenType stylistic sets into calt feature.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("input_font", help="Input font file (TTF or OTF)")
    parser.add_argument("output_font", help="Output font file")
    parser.add_argument(
        "-f",
        "--features",
        required=True,
        help="Comma-separated list of stylistic sets to merge (e.g., ss13,ss15,ss18)",
    )
    parser.add_argument(
        "-s",
        "--suffix",
        default="Custom",
        help="Font family name suffix (default: Custom)",
    )

    args = parser.parse_args()

    input_font = args.input_font
    output_font = args.output_font
    stylistic_sets = args.features.split(",")
    suffix = args.suffix

    if not os.path.exists(input_font):
        print(f"Error: Input font not found: {input_font}")
        sys.exit(1)

    print(f"\nMerging stylistic sets: {', '.join(stylistic_sets)}")
    print(f"Input:  {input_font}")
    print(f"Output: {output_font}")
    print()

    font_to_process = input_font
    temp_file = None

    try:
        # Test if FontForge can open the font
        test_font = fontforge.open(input_font)
        test_font.close()
    except Exception:
        # Font has restricted permissions, need to fix them
        print("Font has restricted permissions, fixing...")

        # Create a temporary file in system temp directory
        file_ext = os.path.splitext(input_font)[1]
        temp_fd, temp_file = tempfile.mkstemp(
            suffix=file_ext, prefix="font_fix_"
        )
        os.close(temp_fd)

        # Fix permissions
        try:
            font = TTFont(input_font)
            if "OS/2" in font:
                old_fsType = font["OS/2"].fsType
                # Change from Restricted (0x0002) to Editable (0x0008)
                # Keep bit 8 (No subsetting = 0x0100) if it's set
                new_fsType = (old_fsType & 0x0100) | 0x0008
                font["OS/2"].fsType = new_fsType
                print(
                    f"  Fixed permissions: fsType {old_fsType} -> {new_fsType}"
                )
            font.save(temp_file)
            font.close()
            font_to_process = temp_file
        except Exception as e:
            print(f"  Error fixing permissions: {e}")
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            sys.exit(1)

    try:
        # Process the font (either original or fixed version)
        merge_stylistic_sets_to_calt(
            font_to_process, output_font, stylistic_sets, suffix
        )
    finally:
        # Clean up temporary file if it was created
        if temp_file and os.path.exists(temp_file):
            print(f"Cleaning up temporary file: {temp_file}")
            os.remove(temp_file)


if __name__ == "__main__":
    main()
