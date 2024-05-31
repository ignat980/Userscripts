from material_color_utilities_python.utils.string_utils import argbFromHex, hexFromArgb
from material_color_utilities_python.hct.hct import Hct
from material_color_utilities_python.palettes.tonal_palette import TonalPalette

# Given hex code
initial_hex_code = "00E084"

# Convert the initial hex code to an ARGB integer
initial_argb = argbFromHex(initial_hex_code)

# Convert the ARGB integer to an Hct object to get initial HCT values
initial_hct = Hct.fromInt(initial_argb)

# Print the initial HCT values
print(f"Initial HCT values: Hue={initial_hct.hue}, Chroma={initial_hct.chroma}, Tone={initial_hct.tone}")

# Use the initial hue and chroma to create a TonalPalette
tonal_palette = TonalPalette.fromHueAndChroma(initial_hct.hue, initial_hct.chroma)

# The tones we want to generate hex codes for
tones = [5,15,25,35]

# Generate the hex codes for each tone
hex_codes = {}

for t in tones:
    argb = tonal_palette.tone(t)
    hex_code = hexFromArgb(argb)
    hex_codes[t] = hex_code

# Print the results
for t, hex_code in hex_codes.items():
    print(f"Tone {t}: {hex_code}")
