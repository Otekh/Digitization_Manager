export const otekhTheme = {
  color: {
    brand: { olive: "#646A44", gold: "#CAA133", black: "#000000", silver: "#C0C0C0" },
    surface: {
      chrome: "#282B24",
      darkOlive: "#4E4F37",
      canvas: "#C1C1BD",
      panel: "#C7C7C4",
      recessed: "#ADACA6",
      muted: "#818377",
    },
    border: { default: "#818377", strong: "#606255" },
    text: {
      primary: "#282B24",
      secondary: "#4E4F37",
      inverse: "#F0F0EA",
      inverseMuted: "#C7C7C4",
    },
    action: { primary: "#CFA134", pressed: "#B28926", focus: "#CAA133" },
    status: { good: "#AEC76F", attention: "#CFA134", error: "#A52B32", info: "#5C7880" },
  },
  font: {
    display: '"Bai Jamjuree", "Avenir Next", "Segoe UI", sans-serif',
    ui: '"Inter", "Segoe UI", Arial, sans-serif',
    mono: '"Inter", "SFMono-Regular", Consolas, monospace',
  },
  space: [0, 4, 8, 12, 16, 24, 32, 48, 64],
  control: { compact: 32, default: 40, touch: 44 },
  radius: { control: 2, container: 4 },
  motion: { fast: 100, panel: 180 },
  breakpoint: { compact: 720, wide: 1200 },
} as const;

export type OtekhTheme = typeof otekhTheme;
