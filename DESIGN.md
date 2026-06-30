# SystemEver Proactive SRM Design System

## 1. Atmosphere & Identity

The mockup feels like a dense ERP command surface: practical, tabular, and presentation-ready, with the SRM agent appearing as a focused operational assistant rather than a marketing layer. The signature is the contrast between a conservative ERP chrome and a green SRM decision panel that makes company-specific routing feel like a natural workflow, not a debug report.

## 2. Color

### Palette

| Role | Token | Light | Dark | Usage |
|------|-------|-------|------|-------|
| Surface/browser | --browser-black | #050505 | #050505 | Browser frame background |
| Surface/tab | --browser-tab | #2d2d2d | #2d2d2d | Browser tab strip |
| Surface/chrome | --chrome | #303030 | #303030 | Top application chrome |
| Surface/panel | --panel | #ffffff | #ffffff | Main ERP and SRM panels |
| Surface/grid-head | --grid-head | #e9edf0 | #e9edf0 | Table header rows |
| Surface/grid-info | --grid-blue | #dceef8 | #dceef8 | Informational grid highlight |
| Text/primary | --ink | #222222 | #222222 | Main text |
| Text/secondary | --muted | #59646b | #59646b | Secondary labels and metadata |
| Border/default | --line | #cfd6da | #cfd6da | Grid and panel dividers |
| Border/strong | --line-dark | #9ea9ae | #9ea9ae | Active table borders |
| Accent/navigation | --left-blue | #075ec3 | #075ec3 | ERP left navigation |
| Accent/navigation-hover | --left-blue-2 | #0052b1 | #0052b1 | Navigation hover and active tones |
| Accent/deep | --left-navy | #12167d | #12167d | Secondary navigation depth |
| Accent/srm | --srm | #2f8b45 | #2f8b45 | SRM agent actions and success states |
| Accent/srm-soft | --srm-soft | #dff2df | #dff2df | SRM result backgrounds |
| Status/warning | --warning | #ffb020 | #ffb020 | Warning chips and validation notices |
| Status/error | --red | #e64444 | #e64444 | Critical validation signals |

### Rules

- Use the existing ERP blues for shell navigation only.
- Use the SRM green only for the assistant panel, validation success, and route result emphasis.
- Validation/risk UI must use status tokens, not decorative colors.

## 3. Typography

### Scale

| Level | Size | Weight | Line Height | Tracking | Usage |
|-------|------|--------|-------------|----------|-------|
| H1 | 22px | 700 | 1.25 | 0 | Major screen titles |
| H2 | 18px | 700 | 1.3 | 0 | Dialog and SRM panel titles |
| H3 | 15px | 700 | 1.4 | 0 | Compact section headers |
| Body | 13px | 400 | 1.45 | 0 | Default ERP body text |
| Body/sm | 12px | 400 | 1.4 | 0 | Grid cells and metadata |
| Caption | 11px | 600 | 1.35 | 0 | Chips, labels, and compact controls |

### Font Stack

- Primary: system UI fonts already used by the static HTML.
- Mono: browser default monospace only for technical identifiers when needed.

### Rules

- Keep ERP grid text compact and scannable.
- Do not introduce hero-scale typography inside operational panels.

## 4. Spacing & Layout

### Base Unit

All spacing derives from a base of 4px.

| Token | Value | Usage |
|-------|-------|-------|
| --space-1 | 4px | Tight icon and label gaps |
| --space-2 | 8px | Compact rows and chips |
| --space-3 | 12px | Toolbar and panel internal gaps |
| --space-4 | 16px | Standard panel padding |
| --space-5 | 20px | Larger panel separation |
| --space-6 | 24px | Major horizontal groups |

### Grid

- Max content width: full viewport inside the browser mock frame.
- Column system: fixed ERP side navigation with flexible work area.
- Breakpoints: the mockup is optimized for desktop demo use, with panels allowed to stack only where existing CSS already supports it.

### Rules

- Preserve fixed-format ERP grids and toolbars.
- New SRM result rows should use compact spacing so they do not push important approval content below the fold.

## 5. Components

### SRM Panel

- Structure: fixed assistant panel with header, step rail, result body, and footer actions.
- Variants: idle, loading, loaded, error.
- Spacing: compact `--space-2` and `--space-3` rows inside the panel.
- States: loading text, error text, and route-specific fourth-step content.
- Accessibility: text labels must remain visible without color as the only signal.
- Motion: reuse existing panel transition timing.

### Login Context Dock

- Structure: existing SystemEver login screen plus a compact company context dock.
- Variants: A/B/C company account selected.
- Spacing: compact `--space-3` rows so the original login composition remains dominant.
- States: selected account, hover-ready account row, login button.
- Accessibility: company ID and role are visible text, not color-only state.
- Motion: no additional animation beyond the existing login-to-ERP transition.

### ERP Grid

- Structure: dense table with header row, body rows, and active cell emphasis.
- Variants: normal row, selected row, highlighted validation row.
- Spacing: existing cell padding only.
- States: selected and status-highlighted.
- Accessibility: avoid adding text that overlaps cells.
- Motion: no layout animation.

## 6. Motion & Interaction

### Timing

| Type | Duration | Easing | Usage |
|------|----------|--------|-------|
| Micro | 100-150ms | ease-out | Button press |
| Standard | 200-300ms | ease-in-out | SRM panel updates |
| Emphasis | 400ms | cubic-bezier(0.16, 1, 0.3, 1) | Existing assistant entrance |

### Rules

- Preserve the existing SRM open/close motion.
- API result loading should update content, not resize the whole page shell.
- Respect compact ERP interactions over decorative animation.

## 7. Depth & Surface

### Strategy

mixed

| Level | Value | Usage |
|-------|-------|-------|
| Default border | 1px solid var(--line) | ERP grids and panel boundaries |
| Strong border | 1px solid var(--line-dark) | Active grid and result emphasis |
| Panel shadow | 0 10px 28px rgba(0,0,0,0.18) | SRM assistant panel |

The ERP area uses borders and tonal shifts; the SRM assistant can use a focused shadow because it floats above the application chrome.
