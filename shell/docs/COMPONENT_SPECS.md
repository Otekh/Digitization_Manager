# OTEKH Component Specifications

## Application chrome

Use `surface.chrome` with light text. Product identity sits at the left. Current project/context follows. Global status and user controls sit at the right. A selected top-level tab uses a gold underline or gold label, not a raised glossy tab.

## Buttons

### Primary

- gold background, charcoal label,
- 40 px default height,
- 12 px horizontal padding minimum,
- one primary button per decision group.

### Secondary

- transparent or panel background,
- 1 px strong border,
- charcoal label.

### Destructive

- error colour is reserved for the final destructive action,
- label the action specifically: Delete file, Remove member.

### Icon buttons

- require tooltip and accessible name,
- 32 x 32 px compact; 40 x 40 px default,
- use 1.5-2 px icon strokes or equivalent filled weight.

## Fields

Every field has a persistent label. Placeholder text is an example, never the only label. Default fields are 40 px high with 8 px inner padding and a 1 px border. Focus uses a 2 px charcoal or gold outline with adequate contrast and no layout shift.

## Tables

- sticky headers for long datasets,
- 40 px minimum row height,
- mono font for timestamps, numeric readings, IDs, and paths,
- left-align text; right-align comparable numbers,
- preserve units in a separate column or visible label,
- selected rows use a restrained gold surface with charcoal text,
- zebra striping is optional and very subtle,
- provide sorting state in text/ARIA, not only arrow direction.

## Navigation trees

Use indentation in 16 px increments. Current item receives a gold label and/or a 3 px gold edge marker. Expand/collapse controls must be separate from the destination when both behaviours exist.

## Panels and inspectors

Panels use a 1 px border and tonal separation, not drop shadows. Panel headers are 32-40 px high. Inspectors group editable properties into collapsible sections. Put Apply/Save near the affected region when changes are staged.

## Tabs and segmented controls

Use tabs for peer views and segmented controls for display modes. Do not use tabs as buttons. Active tabs use gold text, underline, or fill. Inactive states retain readable contrast.

## Toggles, checkboxes, and radios

Use toggles for immediate on/off settings. Use checkboxes for selection and radios for one choice within a visible set. Always provide adjacent text labels and a visible keyboard focus state.

## Sliders and knobs

Use a slider when the range and relative position matter. Always show the exact numeric value. Use knobs only when they materially support compact continuous control, especially audio or sensor applications. Knobs are flat circles with a simple position marker—no faux metal, highlights, ticks for decoration, or 3D shading.

## Charts

- show units and timeframe,
- provide table access to the same data,
- use no more than four series without an alternate selection mechanism,
- distinguish lines through pattern/weight as well as colour,
- tooltips include timestamp, value, unit, and series name,
- live charts indicate paused versus streaming state.

## Dialogs

Dialogs contain a clear object-specific title, concise consequence, and actions ordered from safe to decisive. Unsaved-change dialogs must identify what will be lost. Avoid stacked dialogs.

## Notifications

- inline validation for field-level issues,
- toast for completed reversible actions,
- persistent banner for offline, permission, storage, or system-wide problems,
- modal only when progress cannot safely continue.

## Empty and loading states

Empty states explain why the area is empty and provide one useful next action. Skeletons may be used for known layouts; indeterminate spinners are for unknown durations. Long operations expose progress, elapsed time, and cancellation when safe.

## File and media interactions

Drag-and-drop regions must also provide a standard file picker. Show file name, type, size, destination, validation state, and progress. Never start destructive ingest, rename, or migration work without confirming the destination and resulting structure.

## Keyboard baseline

- Tab / Shift+Tab: move focus
- Enter or Space: activate
- Escape: close transient layer or cancel current mode
- Arrow keys: move within menus, tabs, radios, and data grids
- Command on macOS / Control on Linux and web for documented shortcuts

