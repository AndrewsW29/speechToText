# Design Notes

Derived from `UX/UI /angular.html`, `UX/UI /android.html`, `UX/UI /ios.html` (the folder name has a trailing space).

## Screens (all three platforms)

| View | Content |
| :--- | :--- |
| Idle | Title "Ask"; clearable context chip ("Spring · Java"); "Try asking" with 4 suggestion cards; helper text; text input + mic button |
| Listening | "Listening…" status, waveform, "I heard" live caption, auto-stop countdown ring, Cancel and Done |
| Answer | User bubble (Edit), answer card with numbered steps and code blocks (Copy), sources, Helpful / Not helpful, Save / Share / Read aloud, follow-up chips |

## Platform differences

| Aspect | Angular | Android | iOS |
| :--- | :--- | :--- | :--- |
| Navigation | Left rail (Ask, History, Saved, Settings) | Material 3 bottom bar with pill indicator | Tab bar |
| Layout | Rail + history column + main + sources column | Single column, top app bar | Single column, 34pt large title |
| Listening | Inline overlay card | Modal bottom sheet with scrim (28dp radius) | Sheet with grabber (20pt radius) |
| Radii | 12px cards, pills | 16dp cards, 18dp mic, 16/4dp bubble | 12px cards |

## Tokens

| Token | Light | Dark |
| :--- | :--- | :--- |
| bg | #F5F6F7 | #0A0A0A |
| surface | #FFFFFF | #1A1A1A |
| ink / ink2 | #0A0A0A / #333333 | #F5F6F7 / #D1D5DB |
| muted | #5C6B80 (**deviation**) | #9CA3AF |
| primary | #205FFF | #205FFF |
| link | #205FFF | #8CAAFF |
| accent | #AA55FF | #C58BFF |
| tint | rgba(32,95,255,.10) | rgba(140,170,255,.16) |

Fonts: Heebo (300/400/700/800), JetBrains Mono for code. Touch targets ≥ 44px; focus ring 3px accent;
waveform animation disabled under `prefers-reduced-motion`.

## Deviations from the design files

- **muted (light)**: the design uses #64748B, which is 4.4:1 on the #F5F6F7 background and fails WCAG 2.2 AA
  (4.5:1). Implemented as #5C6B80 (5.0:1). Confirm with the designer.
