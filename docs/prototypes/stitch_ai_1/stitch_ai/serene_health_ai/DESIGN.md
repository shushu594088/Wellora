---
name: Serene Health AI
colors:
  surface: '#f8f9ff'
  surface-dim: '#d0dbed'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e6eeff'
  surface-container-high: '#dee9fc'
  surface-container-highest: '#d9e3f6'
  on-surface: '#121c2a'
  on-surface-variant: '#3f4945'
  inverse-surface: '#27313f'
  inverse-on-surface: '#eaf1ff'
  outline: '#6f7975'
  outline-variant: '#bec9c3'
  surface-tint: '#166a56'
  primary: '#005141'
  on-primary: '#ffffff'
  primary-container: '#176b57'
  on-primary-container: '#9ce9cf'
  inverse-primary: '#89d5bd'
  secondary: '#56615d'
  on-secondary: '#ffffff'
  secondary-container: '#dae5e0'
  on-secondary-container: '#5c6763'
  tertiary: '#42484c'
  on-tertiary: '#ffffff'
  tertiary-container: '#596064'
  on-tertiary-container: '#d4dadf'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#a4f2d8'
  primary-fixed-dim: '#89d5bd'
  on-primary-fixed: '#002018'
  on-primary-fixed-variant: '#005140'
  secondary-fixed: '#dae5e0'
  secondary-fixed-dim: '#bec9c4'
  on-secondary-fixed: '#141d1b'
  on-secondary-fixed-variant: '#3f4946'
  tertiary-fixed: '#dde3e8'
  tertiary-fixed-dim: '#c1c7cc'
  on-tertiary-fixed: '#161c20'
  on-tertiary-fixed-variant: '#41484c'
  background: '#f8f9ff'
  on-background: '#121c2a'
  surface-variant: '#d9e3f6'
typography:
  headline-xl-elder:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-lg-elder:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  title-elder:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 30px
  body-elder:
    fontFamily: Plus Jakarta Sans
    fontSize: 17px
    fontWeight: '400'
    lineHeight: 26px
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '700'
    lineHeight: 28px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 22px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 0.75rem
  margin: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.25rem
---

## Brand & Style

### Brand Personality & Core Mood
This design system embodies the clinical trust of modern medicine paired with the human warmth of a personal caregiver. Grounded in the clean, uncluttered clarity of Apple iOS Human Interface Guidelines, it replaces sterile anxiety with calming order, natural breathing room, and effortless readability. The emotional response aims to convey serenity, reassurance, agency, and zero friction.

### Visual Style
- **Modern Apple iOS Ergonomics:** Heavy emphasis on subtle tinted surfaces, light 1px structural dividing borders, restrained shadows, and natural hierarchy.
- **Dual-Mode Ergonomic Dualism:** 
  1. *Standard Mode*: Structured for working adults and caregivers who need high-density data review, fast verification workflows, medication tracking, and clear AI consultations.
  2. *Elder Mode (长辈模式)*: Voice-first, generous physical hit targets, high contrast, enlarged typography (starting at 17px body and scaling up to 28px page titles), single-column sequential decisions, and zero cognitive overload.
- **Iconography Style:** Strictly uniform 2px stroke line-art geometry, rounded terminal ends, and balanced negative space.

## Colors

### Color Hierarchy & Semantic Application
- **Canvas Base (`#F6F8F5`):** A soft, organic warm-tinted gray that eliminates harsh mobile glare and distinguishes individual cards without heavy shadows.
- **Card Surface (`#FFFFFF`):** Pure elevated white surfaces applied across list modules, AI response boxes, and interactive form cells.
- **Surface Outline (`#E2E8F0`):** Crisp 1px borders providing subtle containment for all standalone cards, action buttons, and segmented pills.
- **Primary Spruce Brand (`#176B57`):** The grounding medical green. Used for solid call-to-actions, active navigation states, verified checkmarks, and focused tab indicators.
- **Soft Accent Green (`#E8F3EE`):** Tinted container background for AI voice hubs, success badges, and secondary affirmative chips.
- **Informational / Pending Slate (`#EDF3F8` / Text `#334E68`):** Gentle cool-slate tint designated strictly for pending items ("待核对", "待完善", guide notes).
- **Critical Alert Red (`#D9383A`):** High-priority indicators for risk alerts, abnormal lab values, and miss-dosage warnings.
- **Typography Neutrals:** Primary headers and values rest on deep Charcoal Slate (`#1F2937`), with secondary metadata and captions balanced at Neutral Cool (`#6B7280`).

## Typography

The typographic hierarchy uses **Plus Jakarta Sans** for clean numerical readability paired with system CJK fallback (`PingFang SC` / `Hiragino Sans GB`).

### Scale Breakdown
- **Standard Mode:**
  - `headline-lg` (22px/28px, Bold): Primary screen headers, conversational greetings.
  - `headline-md` (18px/24px, SemiBold): Card section headings, medical category titles.
  - `body-lg` (16px/22px, Medium): Form values, primary list cell titles, core prompts.
  - `body-md` (14px/20px, Regular): Body paragraphs, description text, metadata.
  - `label-sm` (12px/16px, Medium): Badges, status tags ("待核对", "已确认"), timestamps.
- **Elder Mode (长辈模式):**
  - `headline-xl-elder` (28px/36px, Bold): Main greetings ("下午好，张阿姨"), question banners.
  - `headline-lg-elder` (24px/32px, Bold): Prompt focal points, report step confirmation dates.
  - `title-elder` (22px/30px, SemiBold): Prominent list items, large button texts.
  - `body-elder` (17px/26px, Regular/Medium): Instructions, secondary guidance labels, status descriptions.

## Layout & Spacing

### Ergonomic Rules & Touch Targets
The layout system is built for a 390pt mobile viewport baseline with elastic adaptation:
- **Standard Mode:** Outer screen padding is fixed at 16px (`1rem`). Card vertical rhythm maintains 12px to 16px gaps. Interactive button heights sit at a minimum of 48px to satisfy standard iOS ergonomic compliance.
- **Elder Mode (长辈模式):** Section margins expand to 20px. Vertical gaps between modules increase to 16px–20px. Primary interactive touch targets and action buttons strictly guarantee a minimum height of 60px with prominent full-width footprints.

## Elevation & Depth

This design system avoids heavy drop shadows, opting instead for pure iOS architectural depth:
- **Tier 0 (Canvas):** Underlying natural background (`#F6F8F5`).
- **Tier 1 (Cards & Modules):** Pure `#FFFFFF` surface enclosed by a subtle 1px border (`#E2E8F0`). Flat structure or an extremely soft diffuse shadow: `0 2px 8px rgba(0, 0, 0, 0.03)`.
- **Tier 2 (Modals & Sheets):** Elevated sheet modals at `#FFFFFF` paired with a 16px corner radius and a 20% dark backdrop overlay.
- **Floating Controls (Voice & CTAs):** Bottom sticky button bars sit within a blurred glassmorphic panel (`backdrop-filter: blur(16px); background: rgba(246, 248, 245, 0.9)`), anchored cleanly without harsh dividers.

## Shapes

The geometric framework follows deliberate organic radius tiers:
- **Card Surfaces:** Standard 12px border radius for content cards, data containers, and interactive option tiles.
- **Buttons:** 8px corner radius for standard action buttons and primary action bars; 12px for large Elder Mode buttons.
- **Dialogs & Bottom Sheets:** 16px top corner radius for sliding sheets, inspection panels, and confirmation alerts.
- **Pills & Status Badges:** Fully rounded capsule shape (`9999px`) for tags, filter switchers, and floating icon buttons.

## Components

### Buttons
- **Primary Solid:** Background `#176B57`, text `#FFFFFF`, rounded 8px (12px in Elder Mode). Min-height 48px (Standard) / 60px (Elder).
- **Secondary Outlined:** Background `#FFFFFF`, border 1px `#176B57`, text `#176B57`.
- **Voice Trigger Button (Elder Mode):** Large spherical or pill-shaped container filled with `#E8F3EE` featuring a `#176B57` 2px linear microphone icon and pulse-ring indicator.

### Status Badges & Chips
- **Pending ("待核对" / "待完善"):** Background `#EDF3F8`, text `#334E68`, rounded `9999px`, font size 12px (14px Elder).
- **Verified ("已确认"):** Background `#E8F3EE`, text `#176B57`, rounded `9999px`.
- **Alert / Risk:** Background `#FDE8E8`, text `#D9383A`, rounded `9999px`.

### List Cells & Data Rows
- White card container with 1px `#E2E8F0` border.
- Left-aligned 2px linear icon (in `#176B57` or neutral slate).
- Two-line data hierarchy: primary title on top (`#1F2937`), secondary descriptor below (`#6B7280`).
- Right-aligned chevron indicator (`#9CA3AF`) or contextual status pill.

### Form Inputs & Search Fields
- Enclosed with 1px `#E2E8F0` border, `#FFFFFF` fill, 8px radius, placeholder in `#9CA3AF`. Right-aligned mic trigger icon for voice input.

### Elder Mode Step Progression
- Single-focus cards with bold centered dates/values, audio read-aloud buttons (`听一遍`), and dual "Confirm & Next" vs "Voice Edit" actions.