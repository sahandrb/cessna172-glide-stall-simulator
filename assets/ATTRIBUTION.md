# Asset attribution

Code in this repository is MIT. The aircraft drawing is not.

## Aircraft sprite

- File: `assets/aircraft/2004_cessna_172s.png`
- Source: Wikimedia Commons, "2004 Cessna 172S"
- Page: https://commons.wikimedia.org/wiki/File:2004_Cessna_172S.svg
- Author: Er-Jin Jang
- License: CC BY-SA 4.0
- The owner supplied this transparent PNG. It is used directly. There is no SVG conversion and cairosvg is not a dependency.
- The propeller and spinner drawn on the nose are masked out. The only propeller in the simulator is drawn procedurally by the program.
- Preparation: the image is flipped horizontally so the nose points right. `sprite_level_correction_deg` is 0. A fit through the dark cabin windows, after that flip, is within about one degree of horizontal and is biased by the raked windshield, so no extra rotation is applied. The fuselage reference used for pitch is the image x-axis.

## Background

Clouds, the ground, and the sky gradient are procedural. No third-party background pack is included.
