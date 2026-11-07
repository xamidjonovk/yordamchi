---
name: Yordamchi
description: Uzbek personal assistant with a primary browser dashboard and retained legacy desktop surface.
colors:
  web-ground: "#081519"
  web-surface: "#0d2026"
  web-raised: "#122b32"
  web-rail: "#10262d"
  web-line: "#29434b"
  web-ink: "#edf5f6"
  web-muted: "#abc2c9"
  web-cyan: "#83e6d2"
  web-primary-ink: "#082b26"
  web-primary-hover: "#b0f4e7"
  web-amber: "#f0c68a"
  web-red: "#ffacac"
  web-field: "#081a20"
  web-nav-active: "#24434a"
  workspace: "#f4f6f8"
  surface: "#ffffff"
  ink: "#162b34"
  muted: "#52636d"
  divider: "#dfe6e9"
  navigation: "#142e36"
  navigation-active: "#2a4850"
  primary: "#137c68"
  primary-hover: "#0f6656"
  primary-wash: "#e9f5ef"
  success-ink: "#12634f"
  warning: "#8b5b17"
  warning-wash: "#fff5df"
  error: "#aa3e44"
  error-wash: "#fdedef"
typography:
  web-display:
    fontFamily: "Display, Interface, sans-serif"
    fontSize: "clamp(27px, 2.6vw, 38px)"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.035em"
  web-title:
    fontFamily: "Interface, system-ui, sans-serif"
    fontSize: "19px"
    fontWeight: 550
    lineHeight: 1.4
  web-body:
    fontFamily: "Interface, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.6
  web-label:
    fontFamily: "Interface, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 550
  web-code:
    fontFamily: "Consolas, monospace"
    fontSize: "12px"
    lineHeight: 1.7
  headline:
    fontFamily: "Segoe UI Variable, Segoe UI, sans-serif"
    fontSize: "30px"
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  title:
    fontFamily: "Segoe UI Variable, Segoe UI, sans-serif"
    fontSize: "18px"
    fontWeight: 650
    letterSpacing: "-0.015em"
  body:
    fontFamily: "Segoe UI Variable, Segoe UI, sans-serif"
    fontSize: "14px"
    fontWeight: 400
  label:
    fontFamily: "Segoe UI Variable, Segoe UI, sans-serif"
    fontSize: "12px"
    fontWeight: 550
  log:
    fontFamily: "Consolas, monospace"
    fontSize: "11px"
    lineHeight: 1.9
rounded:
  web-control: "8px"
  web-tag: "6px"
  web-surface: "12px"
  web-conversation: "14px"
  badge: "5px"
  control: "7px"
  navigation: "8px"
  panel: "12px"
  dialog: "14px"
spacing:
  web-gap-small: "8px"
  web-control-gap: "16px"
  web-mobile-gutter: "20px"
  web-panel-inset: "26px"
  web-column-gap: "28px"
  web-page-gutter: "40px"
  xs: "4px"
  sm: "8px"
  md: "12px"
  field: "16px"
  compact-gutter: "18px"
  panel-gutter: "24px"
  page-gutter: "36px"
components:
  web-button-primary:
    backgroundColor: "{colors.web-cyan}"
    textColor: "{colors.web-primary-ink}"
    rounded: "{rounded.web-control}"
    padding: "10px 16px"
  web-button-primary-hover:
    backgroundColor: "{colors.web-primary-hover}"
  web-button-secondary:
    backgroundColor: "{colors.web-raised}"
    textColor: "{colors.web-ink}"
    rounded: "{rounded.web-control}"
    padding: "10px 16px"
  web-button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.web-ink}"
    rounded: "{rounded.web-control}"
    padding: "10px 16px"
  web-input:
    backgroundColor: "{colors.web-field}"
    textColor: "{colors.web-ink}"
    rounded: "{rounded.web-control}"
    padding: "11px 13px"
  web-navigation-active:
    backgroundColor: "{colors.web-nav-active}"
    textColor: "{colors.web-cyan}"
    rounded: "{rounded.web-control}"
    padding: "13px 12px"
  web-surface:
    backgroundColor: "{colors.web-surface}"
    textColor: "{colors.web-ink}"
    rounded: "{rounded.web-surface}"
    padding: "26px"
  web-tag:
    textColor: "{colors.web-cyan}"
    rounded: "{rounded.web-tag}"
    padding: "5px 9px"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    typography: "{typography.label}"
    padding: "9px 14px"
    height: "36px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "9px 14px"
  button-subtle:
    textColor: "{colors.primary}"
    rounded: "{rounded.control}"
    padding: "9px 14px"
  button-danger:
    backgroundColor: "{colors.error}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "9px 14px"
  navigation-active:
    backgroundColor: "{colors.navigation-active}"
    textColor: "{colors.surface}"
    rounded: "{rounded.navigation}"
    padding: "12px 14px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "10px 11px"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
  status-running:
    backgroundColor: "{colors.primary-wash}"
    textColor: "{colors.success-ink}"
    rounded: "{rounded.badge}"
    padding: "5px 7px"
---
# Design System: Yordamchi

## Overview

### Browser — primary surface

**Creative North Star: "Jarvis-like personal dashboard"**

A futuristic Jarvis-like personal dashboard in Operate mode: dark petrol surfaces, cyan action cues, familiar forms and one perspective-projected 3D nucleus. Display typography gives the browser surface its identity while local interface fonts keep daily reading and entry practical.

The browser is the primary surface. The optional legacy desktop retains its earlier pale Personal Control Desk system. Browser tokens are prefixed `web-`; existing unprefixed tokens belong only to the legacy desktop. The two palettes and component scopes must not be mixed. This document records built source, rather than an unimplemented visual proposal.

**Key Characteristics:**
- Dark petrol browser workspace with cyan actions.
- Local interface typography and self-hosted display typography.
- One animated nucleus surrounded by ordinary operational controls.
- Explicit service state, keyboard focus and responsive layouts.

### Legacy desktop — retained reference

**Creative North Star: "Personal Control Desk"**

A quiet personal control desk in Operate mode: a pale workspace, deep teal navigation and restrained sea-green actions. The Windows frame and system typography keep the application familiar while precise rows, clear status labels and generous gutters support repeated daily use.

The user confirmed a modern desktop application and a control-desk composition. This document records the completed implementation, reconciled with that direction; it is not a new visual identity. Runtime truth leads the interface, with activity, empty states and errors expressed using real data.

**Key Characteristics:**
- Quiet, modern operational workspace.
- Clear hierarchy and compact, readable records.
- Restrained action color and explicit status language.
- Familiar Windows typography and controls.

## Colors

### Browser — primary surface

#### Primary

**Luminous Cyan** (`web-cyan`) identifies primary actions, links, focus, selected navigation and the idle nucleus. **Deep Action Ink** (`web-primary-ink`) keeps primary button labels dark; **Pale Cyan Hover** (`web-primary-hover`) marks their hover state.

#### Neutral

**Petrol Ground**, **Petrol Surface**, **Raised Petrol** and **Rail Petrol** (`web-ground`, `web-surface`, `web-raised`, `web-rail`) separate the page, work areas, controls and navigation. **Soft Ice Ink**, **Muted Blue Grey** and **Petrol Divider** (`web-ink`, `web-muted`, `web-line`) carry content and boundaries. Fields and selected navigation use `web-field` and `web-nav-active`.

#### Semantic states

`web-amber` supplies the busy nucleus color; `web-red` is declared in the stylesheet but is not currently the error-notice foreground. Actual notices use separate warm backgrounds and readable text; error notices use a red-brown surface. Preserve those component values instead of assuming every declared token is applied.

**The State Before Decoration Rule.** Service labels report real connection and setup state; the nucleus expresses conversation activity, not service health.

### Legacy desktop — retained reference

The palette combines cool pale neutrals, deep teal navigation and a restrained sea-green primary accent. The frontmatter records the source CSS values; names below describe their use.

#### Primary

- **Sea Green** (`primary`): primary actions, active tabs, focus rings and today markers.
- **Deep Sea Green** (`primary-hover`): primary action hover state.
- **Green Wash** (`primary-wash`): selected runtime symbols and running-state surfaces; `success-ink` provides their readable label color.

#### Neutral

- **Cool Workspace** (`workspace`) and **White Surface** (`surface`): the scrolling workspace and distinct work panels.
- **Deep Ink** (`ink`) and **Slate Text** (`muted`): main text and readable supporting information, including adjacent-month dates.
- **Fine Divider** (`divider`): panel boundaries, tables and section separation.
- **Deep Teal Navigation** (`navigation`) and **Selected Teal** (`navigation-active`): persistent navigation and the active destination.

#### Semantic states

Warning amber and its pale wash identify waiting, starting and recovery notices. Muted red and its pale wash identify failure, missed work and destructive confirmation. Statuses always carry text and may include a dot or icon.

**The State Before Decoration Rule.** Use the accent for actions, selection and confirmed state; show status with words as well as color.

## Typography

### Browser — primary surface

**Display Font:** Space Grotesk, self-hosted at `/assets/display.ttf` under the CSS family alias `Display`; fallback `Interface, sans-serif`. The bundled font license identifies the Space Grotesk project. It appears in page headlines, the welcome heading and wordmark.

**Body Font:** CSS alias `Interface` resolves local Aptos, Segoe UI or Helvetica Neue, then falls back to `system-ui, sans-serif`. **Code Font:** Consolas, monospace, for setup commands only.

#### Hierarchy

- **Display:** `web-display`; page headlines become 28px at mobile widths. The welcome heading is 26px, falling to 24px on mobile.
- **Title:** `web-title`; normal section titles. Smaller status titles and record headings serve denser regions.
- **Body:** `web-body`; conversation messages use 14px and supporting paragraphs vary by context. Paragraph measure is bounded to 70ch.
- **Label:** `web-label`; helper and secondary status text use smaller sizes. Controls inherit the interface font.

**The Two Type Roles Rule.** Keep display typography on the wordmark and selected headings; use local interface typography for controls and reading.

### Legacy desktop — retained reference

**Display and Body Font:** Segoe UI Variable, Segoe UI, sans-serif. Operate mode deliberately uses the native Windows type voice.
**Log Font:** Consolas, monospace.

The hierarchy is compact and practical. Weight and spacing distinguish tasks and headings; long explanatory paragraphs remain bounded to 72ch, while empty-state explanations use 45ch.

#### Hierarchy

- **Headline:** page titles (30px, weight 650, line-height 1.2); compact desktop titles reduce to 26px at 1200px and below.
- **Title:** section headings (18px, weight 650), with smaller record headings at 14-15px.
- **Body:** inherited interface base (14px); explanatory copy and form values use 12-13px with paragraph line-height 1.65.
- **Label:** actions and field labels (12px, weight 550); secondary metadata uses 10-11px at readable contrast.
- **Logs:** actual service output (11px, line-height 1.9), wrapping long content rather than widening the application.

**The Familiar Type Rule.** Use the Windows system sans for interface text; reserve monospace for actual logs and code.

## Layout

### Browser — primary surface

A fixed left rail is 232px wide; the workspace offsets by the same amount. The topbar has a 74px minimum height. Main content is capped at 1660px with 40px padding. Distinct work areas use bordered surfaces and records use ruled rows.

At 1150px and below, the rail becomes 200px and main padding 28px. At 940px and below, the rail becomes a 76px icon column, while knowledge panels stack. At 700px and below, navigation moves above the workspace with visible labels; main padding becomes 25px by 20px, the chat layout stacks, and profile fields become one column. At 1600px and above, the chat context column and message region grow.

The conversation-first composition and exact page regions are recorded in `.impeccable/web-surface.md`. Browser delivery evidence covers 390px, 768px and 1440px; those are verification widths, not CSS breakpoints.

### Legacy desktop — retained reference

A full-height application shell contains a fixed-width navigation column and flexible workspace. The workspace has a fixed topbar (66px), then one vertical scroll surface. The default sidebar is 218px; the page uses 36px horizontal gutters and 34px top padding. Main work plus context columns use a flexible primary column and 310px context column, separated by 24px.

At 1200px and below, the sidebar narrows to 186px, horizontal content gutters become 24px, and the context column becomes 270px. At 1020px and below, navigation becomes a 76px icon rail with accessible destination names; content gutters become 22px and the context column is 272px. At 1600px and above, horizontal gutters become 52px and the context column 350px. The native window minimum is 900px; the validated delivery widths are 960px and 1440px. Mobile is outside this desktop surface.

Controls form tight local groups; panels use roughly 18-24px internal space and 18-24px separation. Tables use fine row rules and horizontal overflow containment when needed. Form pairs use two columns; the details workspace retains a secondary editing column. Calendar dates use a seven-column grid with a separate selected-day agenda.

## Elevation & Depth

### Browser — primary surface

Most depth comes from dark tonal layers and thin borders, without card shadows. A protected dialog uses `0 20px 70px #0006` over a `#061014bb` backdrop. The nucleus supplies actual perspective through transformed XYZ points rendered into a 2D canvas; it is not a flat image or a WebGL dependency.

**The Bounded Depth Rule.** Keep animated spatial depth inside the nucleus; ordinary forms, navigation and records remain stable.

### Legacy desktop — retained reference

The workspace is flat by default. White panels, pale supporting surfaces and fine borders carry most depth. Selected segmented controls have a subtle lift; toasts and protected dialogs use soft, offset shadows. A calendar selection uses a fine inset outline as a state boundary.

#### Shadow Vocabulary

- **Selected control:** `0 1px 3px #18374017`.
- **Toast:** `0 8px 26px #142e3629`.
- **Protected dialog:** `0 16px 48px #142e3626`, over a tinted backdrop.

**The Flat Workspace Rule.** Separate ordinary surfaces with tone and fine borders; reserve soft elevation for overlays and selected controls.

## Shapes

### Browser — primary surface

Buttons and fields use `web-control`; panels use `web-surface`; conversation, nucleus frame and dialog use `web-conversation`. Setup tags use `web-tag`. Thin strokes define boundaries. Inline SVG icons share rounded caps and joins with a 1.6 stroke width. Compact round dots supplement labels. Long message and source text wraps within its container.

### Legacy desktop — retained reference

Controls use gently curved corners (7px), navigation items (8px), status labels (5px), panels and runtime containers (12px), and dialogs (14px). Thin neutral borders define normal containers. Rounded status dots remain compact; they supplement words. Icons share a consistent thin-stroke inline SVG language, normally 15-20px. Avoid clipping long user content; use wrapping or a bounded scroll area.

## Components

### Browser — primary surface

#### Buttons

Primary cyan buttons have dark labels, 600 weight, 10px by 16px padding and a 44px base minimum height. Secondary buttons use the raised surface; quiet controls are transparent. Hover changes background and border. Focus uses a cyan 2px outline with 4px offset. Disabled buttons use half opacity and a waiting cursor. Mobile heading and motion controls have explicit smaller minimum heights; do not assume every button shares 44px.

#### Inputs / Fields

Dark fields use a 1px `#3a5660` border, control corners and 11px by 13px padding. The shared focus outline and cyan caret remain visible. Labels sit above fields and helper text follows. The chat composer is a special transparent, bottom-bordered textarea; it must not inherit a full field outline at rest.

#### Navigation

Four native buttons change the visible section. The selected destination carries `aria-current="page"`, cyan text and a lighter petrol background. The 940px icon rail retains its text in the DOM; mobile restores visible labels above the content. Navigation icons are inline SVG.

#### Panels, records and tags

Work panels use surface tone, a fine border, 12px corners and 26px padding, reducing to 20px on mobile. Search results and source records are ruled rows with wrapped source identifiers. Setup tags are compact bordered labels. Empty states explain the absence of records in text.

#### Nucleus and motion

A field of 420 XYZ points is rotated, depth-sorted and perspective-projected, with three elliptical orbital lines. Idle points are cyan; a pending chat request changes them to amber and increases angular speed; microphone activity uses a lighter cyan. Adjacent words describe activity. `prefers-reduced-motion` starts the nucleus still and removes CSS transitions and smooth scrolling. A labeled button toggles motion; a resize observer redraws the still canvas. Rotation does not advance while the page is hidden or a different section is selected.

#### Feedback

Inline status notices provide recovery messages. The conversation is a polite live log and exposes busy state. Browser speech availability changes the microphone control and helper text. Source exclusion opens a native dialog; cancellation is distinct from confirmation. Standard button background and border transitions last 160ms.

### Legacy desktop — retained reference

#### Buttons

Compact, clearly actionable controls use a 36px minimum height, 9px by 14px padding and weight 550. Primary buttons use Sea Green with white text; secondary buttons use white with a fine border; subtle buttons carry colored text without a resting border; destructive actions use muted red. Small secondary actions reduce to a 29px minimum height. Hover changes tone and borders; keyboard focus uses a 2px accent outline with 3px offset. Disabled buttons reduce opacity and show a non-actionable cursor.

#### Inputs / Fields

White fields use a fine neutral stroke, 7px corners, 10px by 11px padding and 39px minimum height. Labels sit 7px above the control; help text follows below. Textareas grow vertically. Hover strengthens the border; focus uses the shared outline. Placeholders remain readable. Switches use a compact pill track with a white thumb and an accent checked state.

#### Navigation

Deep teal navigation uses light, hue-related foregrounds. Active destinations gain a lighter teal surface and a green-tinted SVG icon; hover strengthens both surface and text. The compact icon rail preserves destination names through labels/tooltips. The current destination is explicitly marked.

#### Status labels

Small rectangular pills use 5px corners, 5px by 7px padding and 11px weight-550 labels. Green means running or completed, amber means starting or waiting, red means failed or missed, and slate means inactive. A dot reinforces the state without replacing the text.

#### Panels and records

Panels group distinct work areas on white surfaces with 12px corners and fine borders. Headers use 22px by 24px padding at the normal width; bodies retain a 24px inset. Rows and tables are the default for repeated records. Empty states explain the absence of records and expose a relevant next action.

#### Runtime controls

Local and VPS runtime containers share a clear title, platform description, state label, primary lifecycle control and supporting readiness text. Selected environment gains a restrained green border. Unreachable, stopped, starting and ready remain distinct states. Operations show backend-confirmed progress. Polling preserves keyboard focus and active forms.

#### Calendar

The full month uses seven equal columns, readable adjacent-month labels and fine grid rules. Today gets a solid accent date marker; the selected day uses a pale green surface and fine outline. Dates remain real buttons. The compact version removes grid rules while retaining selection and today cues.

#### Feedback and motion

Inline notices explain recovery; temporary toasts confirm completed actions. Protected dialogs are reserved for destructive memory operations. Button state transitions use 160ms ease-out; toast opacity and translation use 200ms. Switches use 160ms. Reduced-motion preference removes transitions, animation and smooth scrolling. Text selection, caret and scrollbars are themed from the same palette.

## Do's and Don'ts

### Browser — primary surface

#### Do:

- **Do** keep conversation and everyday controls readable around the nucleus.
- **Do** use the web-prefixed tokens for browser additions and preserve the legacy desktop scope.
- **Do** pair service state with text derived from the backend.
- **Do** preserve visible keyboard focus, source evidence and entered form values during polling.
- **Do** honor reduced motion and retain a manual animation control.

#### Don't:

- **Don't** use the decorative nucleus as evidence of service health.
- **Don't** invent operational charts, percentages or progress values.
- **Don't** carry the legacy desktop mobile exclusion or pale palette into the browser.
- **Don't** load remote display fonts when the bundled font is available.

### Legacy desktop — retained reference

#### Do:
- **Do** keep the Uzbek interface direct, with action verbs and explicit recovery text.
- **Do** preserve visible keyboard focus and entered form values during status polling.
- **Do** use native buttons and links for interactive records and calendar dates.
- **Do** pair real status labels with restrained semantic colors.
- **Do** keep the desktop composition usable at 960px and 1440px with vertical scrolling.

#### Don't:
- **Don't** invent charts, progress values or operational metrics to fill empty space.
- **Don't** turn every record into a separate decorative card.
- **Don't** replace the consistent inline SVG icon language with emoji or Unicode symbols.
- **Don't** add ornamental gradients or large display typography to this operational workspace.
