# Publication-Quality Visualization Design System

This document describes the design system and principles used in The Mind LLM Coordination Research visualization dashboard.

## Design Philosophy

The visualization dashboard is designed to meet the standards of top-tier academic publications (NeurIPS, ICML, ICLR). Key principles:

1. **Scientific Rigor**: Clear data presentation without decorative elements
2. **Professional Aesthetic**: Modern, clean interface that conveys academic authority
3. **Data Clarity**: Typography and color choices optimized for readability
4. **Publication Ready**: Print-friendly styles included for paper figures

## Color Palette

### Primary Colors
- **Deep Indigo**: `#3730a3` - Primary brand color, used for key UI elements
- **Primary Light**: `#4f46e5` - Interactive elements, highlights
- **Primary Dark**: `#1e1b4b` - Headers, emphasis

### Accent Colors
- **Warm Amber**: `#f59e0b` - Success indicators, highlights
- **Accent Light**: `#fbbf24` - Hover states
- **Accent Dark**: `#d97706` - Active states

### Semantic Colors
- **Success**: `#059669` (emerald green) - Successful outcomes
- **Error**: `#dc2626` (crimson) - Failed outcomes, errors
- **Info**: `#3b82f6` (blue) - Informational elements

### Neutral Palette
- **Background Primary**: `#f8fafc` (cool gray 50)
- **Background Secondary**: `#f1f5f9` (cool gray 100)
- **Card Background**: `#ffffff` (white)
- **Text Primary**: `#0f172a` (slate 900)
- **Text Secondary**: `#475569` (slate 600)
- **Border**: `#cbd5e1` (slate 300)

### Data Visualization Colors
Distinctive palette avoiding common tech/AI blues:
- Purple: `#8b5cf6`
- Blue: `#3b82f6`
- Teal: `#14b8a6`
- Green: `#22c55e`
- Orange: `#f97316`
- Pink: `#ec4899`

## Typography

### Fonts
- **Primary**: Inter (Google Fonts) - Clean, modern sans-serif
- **Monospace**: JetBrains Mono - Technical data, metrics
- **Weights**: 400 (regular), 500 (medium), 600 (semibold), 700 (bold), 800 (extrabold)

### Type Scale
- **Display (h1)**: 2.75rem / 44px (800 weight)
- **Heading 2**: 2rem / 32px (800 weight)
- **Heading 3**: 1.5rem / 24px (700 weight)
- **Body**: 1rem / 16px (400 weight)
- **Small**: 0.875rem / 14px (500 weight)

### Letter Spacing
- Display/Headings: `-0.03em` (tighter for readability at large sizes)
- Body: `-0.01em` (slight tightening for modern feel)
- Labels/Caps: `0.05em` (tracking for uppercase text)

## Layout

### Spacing Scale
Based on 8px grid system:
- XS: 0.5rem / 8px
- SM: 0.75rem / 12px
- MD: 1rem / 16px
- LG: 1.5rem / 24px
- XL: 2rem / 32px
- 2XL: 3rem / 48px

### Containers
- **Max Width**: 1600px (accommodates wide data tables and charts)
- **Padding**: 3rem (desktop), 2rem (tablet), 1rem (mobile)
- **Cards**: 16px border-radius, generous padding

### Grid Systems
- **Charts Grid**: Auto-fit with minimum 450px columns
- **Stats Grid**: Auto-fit with minimum 240px columns
- **Responsive**: Single column on mobile (<768px)

## Components

### Cards
- **Border Radius**: 16px (modern, friendly)
- **Shadow**: Subtle layered shadows for depth
- **Borders**: 1px solid borders for definition
- **Hover**: Subtle lift animation (translateY(-2px))

### Buttons
- **Primary**: Gradient background (indigo)
- **Secondary**: Gradient background (amber)
- **Border Radius**: 8px
- **Padding**: 0.875rem × 1.75rem
- **Transition**: Transform and shadow on hover

### Charts
- **Grid Lines**: Light gray (`#e2e8f0`)
- **Text**: Slate 600 (`#475569`)
- **Tooltips**: White background, rounded, shadowed
- **Bars/Lines**: 3px stroke width for visibility
- **Dots**: 5px radius, 7px on hover

### Tabs
- **Active Indicator**: 3px amber bottom border
- **Background**: Card background with subtle hover
- **Border Radius**: 8px top corners
- **Padding**: 0.875rem × 1.75rem

## Animations

### Timing Functions
- **Standard**: `cubic-bezier(0.4, 0, 0.2, 1)` - Smooth, natural
- **Easing In**: `cubic-bezier(0.4, 0, 1, 1)`
- **Easing Out**: `cubic-bezier(0, 0, 0.2, 1)`

### Durations
- **Fast**: 150ms - Immediate feedback
- **Standard**: 200ms - Default transitions
- **Slow**: 300ms - Complex animations
- **Very Slow**: 400ms - Page transitions

### Key Animations
- **Fade In**: Opacity + translateY(10px)
- **Hover Lift**: translateY(-2px) + shadow
- **Pulse Error**: Box-shadow pulse for error states
- **Slide In**: Transform translateX for reasoning cards

## Accessibility

### Contrast Ratios
All text meets WCAG AA standards:
- Primary text: 4.5:1 minimum
- Large text: 3:1 minimum
- Interactive elements: Clear focus states

### Focus States
- **Outline**: Primary color with 3px ring
- **Visible**: All interactive elements
- **Keyboard Navigation**: Full support

## Responsive Design

### Breakpoints
- **Desktop**: >1200px (full layout)
- **Tablet**: 768px - 1199px (condensed grid)
- **Mobile**: <768px (single column)
- **Small Mobile**: <480px (compact spacing)

### Mobile Optimizations
- Single column layouts
- Touch-friendly targets (44px minimum)
- Reduced spacing and font sizes
- Horizontal scrolling for tables

## Print Styles

For publication in academic papers:
- Hide navigation and controls
- Black borders for charts
- White background
- Page break controls
- High contrast for grayscale printing

## Component-Specific Guidelines

### Experiment Overview
- Gradient stat cards with layered backgrounds
- 3-column grid for aggregate statistics
- Auto-fit chart grid
- Responsive table with horizontal scroll

### Model Comparison
- Radar chart for multi-dimensional analysis
- Scatter plot for performance vs. speed
- Color-coded model indicators
- Scrollable statistics list

### Game Visualizer
- D3.js custom timeline visualization
- Responsive SVG with proper margins
- Interactive tooltips on hover
- Card sequence display with badges

### Game Animator
- Real-time playback controls
- Omniscient mode toggle
- Monospace time display
- Error highlighting with pulse animation

### LLM Reasoning Panel
- Timeline-based card layout
- Color-coded player badges
- Metric grid with monospace values
- Error explanations with context

## Future Enhancements

Potential improvements for publication:
- Dark mode support (for presentations)
- Export to SVG/PNG for figures
- Interactive filtering and sorting
- Statistical significance indicators
- Citation-ready figure captions
