# OTEKH Application Fonts

## Required families

### Bai Jamjuree

Use for the OTEKH identity, product names, page titles, and major headings.

Download: https://fonts.google.com/specimen/Bai+Jamjuree

Recommended bundled weights: 500, 600, 700.

### IBM Plex Sans Condensed

Use for navigation, labels, controls, tables, panel headings, help text, and general application copy.

Download: https://fonts.google.com/specimen/IBM+Plex+Sans+Condensed

Recommended bundled weights: 400, 500, 600.

### IBM Plex Mono

Use for timestamps, measurements, sensor values, file paths, logs, model names, version numbers, and code.

Download: https://fonts.google.com/specimen/IBM+Plex+Mono

Recommended bundled weights: 400, 500.

## Packaging

Desktop and offline applications must bundle the font files they use, subject to the included font licences. Web applications may self-host WOFF2 files. Do not rely on Google Fonts at runtime when offline operation is part of the product requirement.

Keep the corresponding licence files with distributed fonts. Subset only when the resulting files retain every required Latin Extended character and all orthographic marks used by supported Indigenous languages.

## Fallbacks

```css
--font-display: "Bai Jamjuree", "Avenir Next", "Segoe UI", sans-serif;
--font-ui: "IBM Plex Sans Condensed", "Arial Narrow", "Roboto Condensed", sans-serif;
--font-mono: "IBM Plex Mono", "SFMono-Regular", Consolas, monospace;
```

