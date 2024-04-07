The [`box_drawing_extra.json`](./box_drawing_extra.json) file contains the information for how to use the extra box drawing characters programatically (accurate as of 0.830).

The JSON is an array of records. Each record has the following fields, including their meanings:

- `"ch"`: Character text, as a string
- `"cp"`: Codepoint value, as an integer
- `"dot"`: Whether or not it's one of the characters with a dot in the center
- `"mt"`: True if the middle-top of this glyph has an exit
- `"rt"`: True if the right-top of this glyph has an exit
- `"rm"`: True if the right-middle of this glyph has an exit
- `"rb"`: True if the right-bottom of this glyph has an exit
- `"mb"`: True if the middle-bottom of this glyph has an exit
- `"lb"`: True if the left-bottom of this glyph has an exit
- `"lm"`: True if the left-middle of this glyph has an exit
- `"lt"`: True if the left-top of this glyph has an exit
- `"bitmask"`: Bitmask of exits, as an 8-bit integer.

    `"bitmask"` bit meanings (from least significant bit to most significant bit):
    - Bit 0: left-top exit exists if this bit is set
    - Bit 1: left-middle exit exists if this bit is set
    - Bit 2: left-bottom exit exists if this bit is set
    - Bit 3: middle-bottom if this bit is set
    - Bit 4: right-bottom if this bit is set
    - Bit 5: right-middle if this bit is set
    - Bit 6: right-top if this bit is set
    - Bit 7: middle-top if this bit is set

    This is counter-clockwise starting at the top-left corner. This information is redundant with the `"mt"`/`"rt"`/`"rm"`/`"rb"`/`"mb"`/`"lb"`/`"lm"`/`"lt"` fields, so it may be ignored if desired.
- `"count"`: Number of exits (same as number of set bits in the `"bitmask"` field)
