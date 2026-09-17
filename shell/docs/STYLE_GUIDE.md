# OTEKH Application Style Guide

Version 1.0 — July 2026

## 1. Purpose

This system governs OTEKH applications across macOS, Linux, and the web. It is intended for research-creation tools, local AI and language applications, archives, media systems, sensor interfaces, project spaces, and public or community-facing tools.

The system should make separately developed applications feel related without forcing them into identical layouts. Shared identity comes from typography, colour roles, spacing, borders, interaction behaviour, icon logic, and information hierarchy.

## 2. Design principles

### Operational clarity

The current task, selected object, system status, unsaved state, and next available action must be visible without hunting.

### Flat, not empty

Use borders, alignment, tonal surfaces, and spacing to establish structure. Do not remove necessary controls in the name of minimalism.

### Dense, not cramped

OTEKH tools may show complex data. Density is acceptable when labels remain legible, groups are clearly bounded, and controls retain adequate target sizes.

### Quiet identity

Olive and harvest gold create recognition. Gold is an accent for state and action, not the default colour of every element.

### Relational systems

Where relevant, interfaces may reveal connections between people, sources, land, media, sensors, processes, and permissions. Avoid generic “AI magic” imagery.

### Local and durable

Design for intermittent connectivity, local storage, long-running processes, and explicit sync state. Never imply that data is safely stored or synchronized when it is not.

## 3. Brand architecture

Use the full OTEKH mark on launch/about surfaces, documentation covers, installers, and product-family pages. Use the wordmark or compact mark in persistent application chrome. Individual app icons use the shared olive/gold/black family and a simple pictogram.

Product naming pattern:

`OTEKH [Product Name]`

Examples:

- OTEKH Media Manager
- OTEKH Archive
- OTEKH Project Space
- OTEKH Pit Fire
- OTEKH Local AI

Do not abbreviate the organization name inside formal branding. Short functional labels may be used in constrained UI only.

## 4. Colour system

### Brand colours

| Role | Token | Hex | Use |
|---|---|---:|---|
| OTEKH Olive | `brand.olive` | `#646A44` | identity, logo, selected family surfaces |
| Harvest Gold | `brand.gold` | `#CAA133` | brand accent, icons, highlights |
| Black | `brand.black` | `#000000` | pictograms and highest-contrast marks |
| Silver | `brand.silver` | `#C0C0C0` | small logo details only |

### Interface colours

| Role | Token | Hex | Use |
|---|---|---:|---|
| Application charcoal | `surface.chrome` | `#282B24` | top/bottom chrome, dark panels |
| Dark olive | `surface.darkOlive` | `#4E4F37` | secondary dark surface |
| Work canvas | `surface.canvas` | `#C1C1BD` | principal light workspace |
| Raised panel | `surface.panel` | `#C7C7C4` | cards, inspectors, grouped regions |
| Recessed surface | `surface.recessed` | `#ADACA6` | selected wells, inactive fields |
| Muted olive-grey | `surface.muted` | `#818377` | secondary navigation and disabled regions |
| Structural border | `border.default` | `#818377` | panel and control borders |
| Strong border | `border.strong` | `#606255` | focused structure and dark-light boundaries |
| Interaction gold | `action.primary` | `#CFA134` | selected tab, primary action, active data |
| Pressed gold | `action.pressed` | `#B28926` | pressed/active interaction state |

### Text colours

| Role | Hex |
|---|---:|
| Text on light | `#282B24` |
| Secondary text on light | `#4E4F37` |
| Text on dark | `#F0F0EA` |
| Secondary text on dark | `#C7C7C4` |
| Disabled text | `#606255` |

### Status colours

Status colours are functional and must always be paired with text, an icon, or both.

| Status | Hex | Meaning |
|---|---:|---|
| Connected / good | `#AEC76F` | online, valid, operational |
| Attention | `#CFA134` | review, pending, changed |
| Error / destructive | `#A52B32` | failed, blocked, destructive |
| Information | `#5C7880` | neutral system information |

### Colour discipline

- The default light workspace uses charcoal text on warm grey.
- Gold indicates selection, emphasis, active data, or the primary action.
- Never use gold for long body text.
- Never communicate state through colour alone.
- Avoid gradients, glow, translucency, glass effects, and decorative shadows.
- Use no more than one primary accent colour in a control group.

## 5. Typography

### Font stack

```css
--font-display: "Bai Jamjuree", "Avenir Next", "Segoe UI", sans-serif;
--font-ui: "IBM Plex Sans Condensed", "Arial Narrow", "Roboto Condensed", sans-serif;
--font-mono: "IBM Plex Mono", "SFMono-Regular", Consolas, monospace;
```

### Roles

| Role | Font | Weight | Size / line |
|---|---|---:|---:|
| Product name | Bai Jamjuree | 600 | 20 / 24 |
| Page title | Bai Jamjuree | 600 | 18 / 24 |
| Panel title | IBM Plex Sans Condensed | 600 | 13 / 16 |
| Navigation | IBM Plex Sans Condensed | 500 | 13 / 16 |
| Button / control | IBM Plex Sans Condensed | 600 | 12 / 16 |
| Body | IBM Plex Sans Condensed | 400 | 14 / 20 |
| Supporting text | IBM Plex Sans Condensed | 400 | 12 / 16 |
| Data / identifier | IBM Plex Mono | 400 or 500 | 12 / 16 |

Use sentence case for commands and field labels. Uppercase is reserved for short navigation groups, status labels, table headings, and compact panel labels. Increase tracking when uppercase is used.

Do not use ultra-light weights. Do not synthesize condensed type by scaling normal text.

## 6. Grid, spacing, and geometry

The base spacing unit is 4 px.

`4, 8, 12, 16, 24, 32, 48, 64`

- Control height: 32 px compact, 40 px default, 44 px touch-capable.
- Top application bar: 64 px desktop.
- Status bar: 40-48 px.
- Sidebar: 240-280 px.
- Inspector: 300-360 px.
- Panel padding: 12 px compact, 16 px default.
- Control gap: 8 px.
- Section gap: 16 or 24 px.
- Border: 1 px.
- Corner radius: 0-2 px for most controls; 4 px maximum for dialogs and app-level containers.

Prefer aligned rectangular regions. Rounded cards should not dominate the interface.

## 7. Layout system

A full technical application may use:

1. top application bar,
2. left navigation,
3. main working canvas,
4. optional right inspector,
5. bottom status bar.

Not every application needs all five regions. Remove a region only when its function is absent.

The central workspace should receive the most area. Sidebars should be resizable when their content varies. At narrow widths, inspectors become drawers and secondary navigation collapses behind a labelled control.

## 8. Components

See `COMPONENT_SPECS.md` for implementation details.

Core component families:

- application bars and tabs,
- navigation trees,
- panels and inspectors,
- buttons and segmented controls,
- inputs, selects, search, and steppers,
- tables and lists,
- charts and live data,
- sliders, toggles, knobs, and meters,
- dialogs, notifications, and unsaved-change prompts,
- empty, loading, offline, error, and permission states.

## 9. Motion

Motion confirms change; it does not decorate.

- Micro-transition: 80-120 ms.
- Panel/drawer transition: 160-200 ms.
- Use linear or restrained ease-out timing.
- Never animate live data in a way that obscures exact values.
- Respect reduced-motion settings.
- Loading indicators must be paired with a label after two seconds.

## 10. Content and language

- Use direct verbs: Save, Export, Connect, Calibrate, Add member.
- Name the object: “Delete recording?” rather than “Are you sure?”
- State consequences before destructive actions.
- Distinguish Save, Sync, Upload, Export, and Publish.
- Use plain language around AI. Identify when output is generated, provisional, local, or externally processed.
- Do not describe community knowledge as “content” when a more precise term is available.
- Surfaces involving cultural material, permissions, protocols, or restricted knowledge must name access conditions explicitly.

## 11. Data, AI, and archive-specific requirements

- Show source, model/tool, processing location, and timestamp where relevant.
- Distinguish generated output from community-verified knowledge.
- Provide review and correction paths.
- Never fabricate language material or imply validation that has not occurred.
- Archive tools must show access level, custody, permissions, provenance, and change history.
- Local-first applications must show whether a process is on-device, on the lab server, or external.
- Destructive actions require confirmation and, where practical, recovery.

## 12. Responsive and platform behaviour

Use native platform conventions for window controls, file pickers, keyboard shortcuts, and accessibility APIs. Preserve the OTEKH visual language through tokens, typography, panels, and state—not by overriding basic operating-system behaviour.

Breakpoints:

- compact: below 720 px,
- medium: 720-1199 px,
- wide: 1200 px and above.

At compact widths, use one principal column, move inspectors to drawers, convert dense tables to labelled rows, and keep primary actions visible.

## 13. Accessibility

See `ACCESSIBILITY.md`. The minimum target is WCAG 2.2 AA for web interfaces and equivalent platform accessibility for desktop applications.

## 14. Governance and versioning

- Design-system versions use semantic versioning.
- Token changes require a changelog entry.
- New icons must be reviewed at 16, 24, 32, 64, 128, and 512 px.
- Product-specific colours may extend the palette but may not replace core semantic roles.
- Exceptions must be documented in the product repository.

