# UX/UI Design Specification: Android, iOS, Angular

Companion to [FEATURE.md](FEATURE.md). Covers the voice-driven developer assistant on three clients that share one product experience but follow each platform's native conventions.

## 1. Design principles

- **Voice first, text always available.** One tap starts listening. Every voice action has a typed equivalent.
- **Show what the system heard.** The transcript is always visible and editable before or after the answer. This builds trust and fixes speech-recognition errors cheaply.
- **Answers are scannable.** Developers want code and steps, not paragraphs. Lead with the result, then the explanation.
- **Cite sources.** Every answer shows where it came from, so users can verify.
- **Honest states.** Listening, thinking, low confidence, and offline each look distinct. Never fake certainty.
- **Native feel over pixel parity.** Same information architecture, tokens, and tone. Platform-specific navigation, controls, and motion.
- **Accessible by default.** WCAG 2.2 AA minimum, full screen-reader support, no voice-only paths.

## 2. Users and key scenarios

| Persona | Context | Primary need |
|---|---|---|
| **Junior dev** | Learning Spring on a laptop | Step-by-step "how do I create X" with code |
| **Senior dev on the move** | Phone, hands busy | Fast spoken lookup, short answers, save for later |
| **Team lead** | Web dashboard | Review what the team asks, see feedback and gaps |

Core scenarios:
1. Ask by voice: "How do I create a controller and a service in Java?" and get a structured answer with code.
2. Refine: "Now add validation" (follow-up in the same conversation).
3. Save a snippet and copy it into an IDE.
4. Give feedback (helpful / not helpful) that improves future answers.
5. Browse history and saved items.

## 3. Information architecture

```
App
├── Onboarding (first run): welcome → mic permission → language/topic prefs
├── Ask (home)            ← primary tab, voice button
│   ├── Conversation thread
│   └── Answer detail (full-screen code view)
├── History               ← past conversations, search
├── Saved                 ← snippets and answers, tags
└── Settings
    ├── Voice: language, auto-send, push-to-talk vs tap-to-toggle
    ├── Answers: detail level, preferred languages/frameworks
    ├── Privacy: audio retention, delete data
    ├── Appearance: theme, text size
    └── Account / Server (self-hosted URL)
```

Navigation:
- **Android:** bottom navigation bar (Ask, History, Saved, Settings), Material 3.
- **iOS:** `TabView` with the same four tabs, SF Symbols.
- **Angular:** left navigation rail on desktop, bottom bar under 600 px, same four destinations.

## 4. Design tokens (shared source of truth)

Maintain tokens in one JSON file (Style Dictionary or Tokens Studio), exported to Compose `Color.kt`/`Theme.kt`, SwiftUI `Color` assets, and Angular CSS custom properties.

### Color (light / dark)

| Token | Light | Dark | Use |
|---|---|---|---|
| `primary` | #3B5BDB | #8FA6FF | Mic button, primary actions, links |
| `onPrimary` | #FFFFFF | #0B1437 | Text/icons on primary |
| `surface` | #FFFFFF | #121418 | Cards, sheets |
| `background` | #F6F7FA | #0C0E12 | App background |
| `surfaceVariant` | #ECEEF4 | #1B1E25 | Input bars, chips |
| `onSurface` | #14161B | #E7E9EF | Primary text |
| `onSurfaceMuted` | #5B6270 | #A3A9B7 | Secondary text, timestamps |
| `success` | #1F9D55 | #4FD18B | Positive feedback, "copied" |
| `warning` | #B7791F | #F0B84A | Low confidence |
| `error` | #D64545 | #FF8A8A | Errors, recording stop |
| `listening` | #E8590C | #FF9A5C | Active recording accent |
| `codeBg` | #0F172A | #0A0D14 | Code blocks (dark in both themes) |

Rules: text contrast at least 4.5:1, UI components at least 3:1. Never use color alone to convey state (pair with icon or text).

### Typography

| Role | Android (Material 3) | iOS | Web |
|---|---|---|---|
| Display / title | Headline Small, 24 | Title 2 | 24 / 32, 600 |
| Body | Body Large, 16 | Body, 17 | 16 / 24, 400 |
| Caption | Label Medium, 12 | Caption 1 | 12 / 16, 500 |
| Code | JetBrains Mono, 14 | SF Mono, 14 | JetBrains Mono, 14 |

- UI font: system font on each platform (Roboto, SF Pro, Inter with system fallback on web).
- Honor system text scaling: Android `sp`, iOS Dynamic Type, web `rem`. Test at 200%.

### Spacing, shape, elevation

- Spacing scale (4-pt grid): 4, 8, 12, 16, 24, 32, 48.
- Corner radius: 8 (chips), 12 (cards, code), 16 (sheets), full (mic button, avatars).
- Elevation: use tonal surfaces and 1px borders instead of heavy shadows; one soft shadow for the floating mic.
- Minimum touch target: 48 x 48 dp (Android), 44 x 44 pt (iOS), 44 x 44 px (web, with 24 px minimum visible size).

### Motion

- Durations: 100 ms (feedback), 200 ms (transitions), 300 ms (sheets).
- Easing: standard decelerate for entering, accelerate for exiting.
- Respect "reduce motion" (Android animator scale, iOS `accessibilityReduceMotion`, CSS `prefers-reduced-motion`): replace pulsing/waveform animation with a static indicator plus text.

## 5. Core screens (wireframes)

### 5.1 Onboarding

```
┌───────────────────────┐
│        (illustration) │
│  Ask your code        │
│  assistant out loud.  │
│                       │
│  Get answers with     │
│  code and sources.    │
│                       │
│  [ Continue ]         │
│  • ○ ○                │
└───────────────────────┘
```
Step 2: permission priming ("We use the microphone only while you hold or tap the button. Audio is processed on your server."), then the OS permission dialog. If denied, show a typed-input fallback and a "Open Settings" link rather than blocking.
Step 3: choose topics (Java, Spring, Kotlin, Angular, ...) to seed filters.

### 5.2 Ask (home), idle state

```
┌─────────────────────────────┐
│ Ask                    ⚙    │
├─────────────────────────────┤
│                             │
│   Try asking:               │
│  ┌───────────────────────┐  │
│  │ "Create a REST        │  │
│  │  controller in Spring"│  │
│  └───────────────────────┘  │
│  ┌───────────────────────┐  │
│  │ "Explain dependency   │  │
│  │  injection"           │  │
│  └───────────────────────┘  │
│                             │
├─────────────────────────────┤
│ [ Type a question…    ] (🎤)│
└─────────────────────────────┘
 Ask  History  Saved  Settings
```
- Suggestion chips fill the empty state and double as examples of good phrasing.
- The input bar holds a text field and a large circular mic button (56 dp / 56 pt).

### 5.3 Listening state

```
┌─────────────────────────────┐
│ Listening…                  │
│                             │
│   ▁▂▅▇▅▂▁▂▅▇▅▂▁  (waveform) │
│                             │
│  "how do I create a         │
│   controller and a serv…"   │  ← live partial transcript
│                             │
│   [ Cancel ]     [ ■ Done ] │
└─────────────────────────────┘
```
- Mic button turns `listening` color with a gentle pulse. Waveform reflects input level.
- Haptic tick on start and stop. Optional earcon, off by default.
- Modes: **tap to toggle** (default) and **hold to talk** (setting). Auto-stop after about 1.5 s of silence (voice activity detection), with a visible countdown ring.
- Live partial transcript requires a streaming path (WebSocket). If not streaming, show "Listening…" with the waveform only.

### 5.4 Transcript confirmation (processing)

```
┌─────────────────────────────┐
│ You asked                   │
│ ┌─────────────────────────┐ │
│ │ How do I create a       │ │
│ │ controller and a service│ │
│ │ in Java?            ✎   │ │
│ └─────────────────────────┘ │
│ ◔ Finding answers…          │
└─────────────────────────────┘
```
- The transcript bubble is editable (✎). Editing re-runs the query.
- If STT confidence is low, highlight uncertain words with a dotted underline and offer alternatives on tap.
- Progress copy changes by stage: "Transcribing…", "Searching knowledge…", "Writing answer…". Use skeleton placeholders, not a spinner alone.

### 5.5 Answer

```
┌─────────────────────────────┐
│ ✓ Create controller + service│
│   (Spring · Java)           │
├─────────────────────────────┤
│ 1. Create the service       │
│ ┌─────────────────────────┐ │
│ │ @Service                │ │
│ │ public class …          │ │
│ │              [Copy] [⤢] │ │
│ └─────────────────────────┘ │
│ 2. Create the controller    │
│ ┌─────────────────────────┐ │
│ │ @RestController …       │ │
│ └─────────────────────────┘ │
│                             │
│ Sources: Spring Docs · …    │
│ 👍 Helpful   👎 Not helpful │
│ [Save] [Share] [🔊 Read]    │
├─────────────────────────────┤
│ Follow-ups: [Add validation]│
│ [ Type or tap mic…    ] (🎤)│
└─────────────────────────────┘
```
- Answer structure: headline (intent + detected language/framework), numbered steps, code blocks, short explanation, sources, feedback, follow-up chips.
- Code blocks: syntax highlighting, language label, Copy button (shows "Copied" for 2 s, announced to screen readers), expand to full screen, horizontal scroll rather than wrapping.
- Optional **Read aloud** (TTS). Read prose, announce "code block, Java", and skip reading code line by line by default.
- Confidence: if low, show a banner "I'm not fully sure. Here are the closest matches." and list the top sources first.
- Feedback: 👍/👎. On 👎 open a small sheet with reasons (wrong language, outdated, incomplete, didn't understand me) plus optional text. These reasons feed the retraining loop.

### 5.6 History

- Grouped by day (Today, Yesterday, Earlier), each row shows the question, intent chip, and a thumbs state.
- Search bar with filter chips (language, saved, helpful).
- Swipe actions: delete (left), save (right). Provide a long-press menu alternative for accessibility.

### 5.7 Saved

- Cards with title, code preview (3 lines), tags. Tags editable.
- Multi-select mode for bulk delete and export (Markdown, copy all).

### 5.8 Settings

- Grouped lists as in the IA. A **Privacy** group shows what is stored and offers "Delete all my audio and history".
- Server URL field (for self-hosting) with a "Test connection" button.

### 5.9 Error, empty, and offline states

| State | Message | Action |
|---|---|---|
| No mic permission | "Microphone is off. You can still type." | Open Settings, Type instead |
| Nothing heard | "I didn't catch that." | Try again |
| Server unreachable | "Can't reach the server." | Retry, Check server URL |
| Offline | Banner "You're offline. History and saved items are available." | Queue question (optional) |
| No results | "No matching docs found for that." | Rephrase, Show closest |
| Slow response (>8 s) | "Still working… " | Cancel |

Tone: plain, short, no blame, no jargon, always one clear next step.

## 6. Components inventory

Build once per platform from the same spec; name them identically.

| Component | Variants / states |
|---|---|
| `MicButton` | idle, listening (pulse), processing (ring), disabled, error |
| `Waveform` | live level, static (reduced motion) |
| `TranscriptBubble` | partial (italic, muted), final, editable, low-confidence words |
| `AnswerCard` | loading skeleton, complete, low-confidence, error |
| `CodeBlock` | collapsed, expanded, copied |
| `SourceChip` | web/doc/repo icon, opens link |
| `FeedbackBar` | none, helpful, not helpful (with reason sheet) |
| `SuggestionChip` | default, pressed |
| `ConversationItem` | user, assistant |
| `Banner` | info, warning, error, offline |
| `EmptyState` | illustration + title + action |

## 7. Platform specifics

### 7.1 Android (Kotlin, Jetpack Compose, Material 3)

- **Theme:** Material 3 with dynamic color (Material You) optional. Provide a fixed brand scheme as default and fallback.
- **Navigation:** `NavigationBar` for tabs, Navigation Compose for destinations, predictive back gesture supported.
- **Mic button:** `LargeFloatingActionButton` or custom `IconButton` in a rounded input bar. Place within thumb reach (bottom right area).
- **Listening UI:** `ModalBottomSheet` over the conversation, or inline expansion of the input bar. Waveform drawn with `Canvas`.
- **Permissions:** `rememberLauncherForActivityResult` + rationale dialog. Handle "Don't ask again" by routing to app settings.
- **Haptics:** `HapticFeedback` on start/stop.
- **Foreground behavior:** stop recording when the app goes to background. No background recording.
- **Adaptive layouts:** use window size classes. Compact (phone): single pane. Medium/Expanded (tablet, foldable): two-pane with history list on the left and conversation on the right (`ListDetailPaneScaffold`).
- **Accessibility:** `contentDescription` on icon buttons, `semantics { liveRegion }` for state changes ("Listening", "Answer ready"), TalkBack traversal order tested, minimum 48 dp targets, support font scale and display size.
- **Theming files:** `Color.kt`, `Type.kt`, `Shape.kt` generated from tokens.

### 7.2 iOS (Swift, SwiftUI, Human Interface Guidelines)

- **Navigation:** `TabView` with SF Symbols (`mic.fill`, `clock`, `bookmark`, `gearshape`). `NavigationStack` inside each tab. Large titles on top-level screens.
- **Mic button:** prominent circular button in the input bar. Use `.sensoryFeedback` for haptics and `.symbolEffect(.pulse)` for the listening state.
- **Listening UI:** `.sheet` with `presentationDetents([.medium])`, or inline expansion. Drag indicator visible.
- **Materials:** use system materials (`.regularMaterial`) for floating bars. Respect Dark Mode and increased contrast.
- **Permissions:** microphone usage string in Info.plist written for humans ("Used to turn your spoken question into text."). Pre-prompt screen before the system prompt.
- **Gestures:** swipe actions via `.swipeActions`, pull to refresh in History, interactive dismiss for sheets. Never fight the system back swipe.
- **Adaptive:** iPad uses `NavigationSplitView` (sidebar plus detail). Support Split View and Stage Manager.
- **Accessibility:** VoiceOver labels and hints, `accessibilityAddTraits(.isButton)`, announce state with `AccessibilityNotification.Announcement`, Dynamic Type up to accessibility sizes, Reduce Motion, Bold Text, Voice Control names matching visible labels.
- **Widgets/shortcuts (later):** App Intent "Ask the assistant" and a Lock Screen control for quick voice capture.

### 7.3 Angular (latest stable, standalone components, Signals)

- **UI kit:** Angular Material (M3 theme) plus CDK for overlays, a11y, and virtual scroll. Theme from the shared tokens as CSS custom properties.
- **Layout:** responsive grid with breakpoints.

| Width | Layout |
|---|---|
| < 600 px | Single column, bottom nav, input bar fixed at bottom |
| 600-1023 px | Navigation rail, single content column (max 720 px) |
| >= 1024 px | Rail + history side panel + conversation, optional right "sources" panel |

- **Desktop mic:** large mic button in the input bar plus a keyboard shortcut (for example `Space` when the input is not focused, or `Ctrl/Cmd + Shift + M`), shown in a tooltip. `Esc` cancels.
- **Capture:** `navigator.mediaDevices.getUserMedia` requires HTTPS (or localhost). Handle `NotAllowedError` and `NotFoundError` with the states in section 5.9. Use `AudioWorklet` for the level meter.
- **Structure by feature:** `voice-capture`, `conversation`, `history`, `saved`, `settings`, `shared/ui`.
- **Performance:** lazy-loaded routes, `@defer` for the code highlighter, virtual scroll for long history, `OnPush` and Signals.
- **Web extras:** deep links per conversation, PWA install and offline shell, copy buttons using the Clipboard API with a fallback, print stylesheet for answers.
- **Accessibility:** semantic landmarks (`nav`, `main`), `aria-live="polite"` region for status and answers, visible focus rings, skip link, full keyboard operation, color contrast verified in both themes.
- **Team/admin dashboard (optional):** table of questions with intent, confidence, and feedback, plus charts for top intents and unanswered topics.

## 8. Voice UX details

- **Prompting the user:** show example phrases in the empty state and rotate them. Teach one thing at a time.
- **Latency budget:** acknowledge input in under 100 ms (visual and haptic), show the transcript within about 1 s of stop, first answer content within 3 s where possible (stream tokens).
- **Corrections:** "Edit" on the transcript, and a "Try again" mic next to it.
- **Disambiguation:** if intent confidence is low or the language is missing, ask one short clarifying question with chips: "Which language? [Java] [Kotlin] [TypeScript]".
- **Multi-turn context:** show a small context chip ("Spring · Java") that the user can clear.
- **Privacy cues:** a persistent recording indicator while the mic is open, and never record in the background. Link to "What happens to my audio" from the permission screen.
- **Spoken output:** off by default. When on, keep spoken answers short and summarize rather than reading code.

## 9. Content and microcopy

- Voice and tone: calm, direct, developer-friendly. No exclamation marks, no jokes in error states.
- Button labels are verbs: "Copy", "Save", "Try again".
- Examples: "Listening…", "I heard: ...", "Here's how to do it:", "I'm not fully sure. These are the closest matches."
- Localization: externalize all strings (`strings.xml`, `Localizable.xcstrings`, Angular i18n). Allow 40% text expansion and RTL layouts. Voice language is a separate setting from UI language.

## 10. Accessibility checklist (all platforms)

- [ ] Every control has an accessible name and role
- [ ] Contrast at least 4.5:1 for text, 3:1 for UI components, in light and dark
- [ ] All voice features have a non-voice alternative
- [ ] State changes announced (listening, processing, answer ready, error)
- [ ] Works at 200% text size without clipping or horizontal scroll
- [ ] Reduced motion variants for pulse and waveform
- [ ] Targets at least 44-48 px with adequate spacing
- [ ] No time limits without a way to extend or disable (auto-stop is adjustable)
- [ ] Captions or transcript for any audio output
- [ ] Verified with TalkBack, VoiceOver, and NVDA/VoiceOver on web

## 11. Design workflow and tooling

- **Figma:** one file with a shared token library, component library, and per-platform pages (Material 3 kit, iOS 26 HIG kit, web). Prototype the listening to answer flow.
- **Design tokens:** JSON in the repo (`/design/tokens`), built with Style Dictionary into Kotlin, Swift, and CSS outputs in CI.
- **Component docs:** Storybook (Angular), Compose Preview / Paparazzi screenshot tests (Android), SwiftUI Previews / snapshot tests (iOS).
- **Visual regression:** Chromatic or Playwright screenshots for web, Paparazzi for Android, swift-snapshot-testing for iOS, run in CI alongside the TDD suite from FEATURE.md.
- **Usability testing:** 5 users per round on the core scenario "ask, correct, copy code, give feedback". Track task success, time to first answer, transcript edit rate, and thumbs-down reasons.

## 12. Success metrics for the UX

- Time from tap to first answer content (target under 4 s).
- Transcript edit rate (a proxy for STT quality).
- Helpful rate (👍 / total feedback), and the top 👎 reasons.
- Copy-code rate per answer (a proxy for usefulness).
- Voice vs. typed usage ratio.
- Accessibility defects per release (target zero blockers).

## 13. Design delivery order

1. Tokens and base components (MicButton, TranscriptBubble, CodeBlock, AnswerCard) in Figma and in code on all three platforms.
2. Ask flow screens: idle, listening, processing, answer, error states.
3. Feedback sheet and follow-ups.
4. History and Saved.
5. Settings and Privacy.
6. Tablet/desktop adaptive layouts and the team dashboard.
7. Polish: motion, haptics, TTS, localization, accessibility audit.
