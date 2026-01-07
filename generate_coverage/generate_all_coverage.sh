#!/bin/bash

# Directory dei font e dello script
FONT_DIR=~/Library/Fonts
SCRIPT="python generate_font_coverage.py"

# Array con i nomi dei file (senza estensione)
fonts=(
    "PragmataPro_Mono_B_0903"
    "PragmataPro_Mono_B_liga_0903"
    "PragmataPro_Mono_I_0903"
    "PragmataPro_Mono_I_liga_0903"
    "PragmataPro_Mono_R_0903"
    "PragmataPro_Mono_R_liga_0903"
    "PragmataPro_Mono_Z_0903"
    "PragmataPro_Mono_Z_liga_0903"
    "PragmataProB_0903"
    "PragmataProB_liga_0903"
    "PragmataProI_0903"
    "PragmataProI_liga_0903"
    "PragmataProMonoVF_0903"
    "PragmataProMonoVF_Italic_0903"
    "PragmataProMonoVF_Italic_liga_0903"
    "PragmataProMonoVF_Liga_0903"
    "PragmataProR_0903"
    "PragmataProR_liga_0903"
    "PragmataProVF_0903"
    "PragmataProVF_Italic_0903"
    "PragmataProVF_Italic_liga_0903"
    "PragmataProVF_Liga_0903"
    "PragmataProZ_0903"
    "PragmataProZ_liga_0903"
)

# Genera coverage per ogni font
for font in "${fonts[@]}"; do
    echo "Processing $font..."
    $SCRIPT "$FONT_DIR/${font}.ttf" > "${font}.txt"
done

echo "Completato!"