# OTEKH Accessibility Standard

Target WCAG 2.2 AA for web applications and equivalent native accessibility APIs for desktop applications.

## Required

- 4.5:1 contrast for normal text.
- 3:1 contrast for large text, graphical objects, and control boundaries.
- Visible focus on every interactive element.
- Full keyboard access without traps.
- Minimum 24 x 24 px pointer target; prefer 40 x 40 px in application UI and 44 x 44 px where touch is expected.
- Labels and instructions remain visible after entry.
- Status is never communicated through colour alone.
- Zoom to 200% without loss of function; reflow where applicable.
- Reduced motion is respected.
- Meaningful images have alt text; decorative images are ignored by assistive technology.
- Tables expose header relationships, sort state, selection, and row/column position.

## OTEKH palette cautions

Harvest gold on white is not suitable for normal text. Use it as a fill with dark charcoal text, an indicator, a large graphic, or a border. Olive on the warm canvas may be too low-contrast at small sizes; use charcoal for body text.

## Charts

Provide a text summary and accessible data table. Use line styles, markers, labels, or direct annotation in addition to colour.

## Language and cultural access

Support correct Unicode and diacritics. Do not normalize or strip Indigenous-language orthography. Allow screen readers to encounter the original text and, where useful, optional pronunciation or language metadata. Access restrictions and cultural protocols must be described in language users can understand.

## Test matrix

- keyboard only,
- VoiceOver on macOS and iOS where applicable,
- Orca on supported Linux environments,
- browser zoom at 200% and 400%,
- reduced motion,
- high contrast / increased contrast,
- colour-vision simulation,
- offline and degraded network,
- long names, translated labels, and Kanien'kéha diacritics.

