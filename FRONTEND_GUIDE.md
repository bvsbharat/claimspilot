# Frontend Implementation Guide

## Overview

The frontend is a **React + TypeScript + Vite** application with **Tailwind CSS** for styling.

## Architecture

### Components

1. **ClaimCard** - Individual claim display with status, scores, and fraud flags
2. **ClaimsQueue** - Grid of all claims with modal for detailed view
3. **AdjusterPanel** - Shows all adjusters with workload and capacity
4. **MetricsPanel** - Dashboard metrics (total claims, assigned, completed, avg time)
5. **FraudAlerts** - Lists all claims with fraud flags
6. **UploadClaim** - Drag-and-drop file upload component
7. **LiveFeed** - Real-time event stream using Server-Sent Events

### Hooks

- **useSSE** - Custom hook for Server-Sent Events connection

### Types

Complete TypeScript interfaces for:
- Claim
- ExtractedData
- FraudFlag
- RoutingDecision
- Adjuster
- Metrics

## Features

### 1. Claims Queue Tab
- Grid layout of all claims
- Color-coded status badges
- Priority indicators
- Fraud flag warnings
- Click to view detailed modal with:
  - Full extracted data
  - Fraud flags with evidence
  - Routing decision and investigation checklist

### 2. Adjusters Tab
- Adjuster cards with:
  - Name, email, specializations
  - Experience level and years
  - Max claim amount
  - Current workload with progress bar
  - Color-coded capacity (green < 50%, yellow < 70%, orange < 90%, red >= 90%)

### 3. Fraud Alerts Tab
- All claims with fraud indicators
- Detailed evidence for each flag
- Confidence scores
- Severity levels

### 4. Live Feed
- Real-time updates via SSE
- Shows last 10 events
- Connection status indicator
- Event icons based on type

### 5. Upload Section
- Drag-and-drop file upload
- Supports PDF, JPG, PNG
- Progress feedback
- Success/error messages

## Installation

```bash
cd frontend
npm install
```

## Development

```bash
npm run dev
```

Runs on `http://localhost:3030`

## Build

```bash
npm run build
```

## API Integration

All API calls go to `http://localhost:8080`:

- `GET /api/claims/list` - Fetch all claims
- `GET /api/adjusters/list` - Fetch all adjusters
- `GET /api/analytics/fraud-flags` - Fetch fraud flags
- `GET /api/analytics/metrics` - Fetch metrics
- `POST /api/claims/upload` - Upload claim document
- `GET /api/events/stream` - SSE stream for real-time updates

## Proxy Configuration

Vite is configured to proxy `/api` requests to the backend (see `vite.config.ts`):

```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8080',
    changeOrigin: true,
  }
}
```

## Styling

Uses **Tailwind CSS** with custom color scheme:
- Blue for primary actions
- Red for fraud/errors
- Green for success/availability
- Orange/Yellow for warnings
- Gray for neutral elements

## Auto-refresh

- Claims: Every 5 seconds
- Adjusters: Every 10 seconds
- Metrics: Every 10 seconds
- Fraud Flags: Every 10 seconds
- Live Feed: Real-time via SSE

## Component Structure

```
src/
├── components/
│   ├── ClaimCard.tsx        # Individual claim display
│   ├── ClaimsQueue.tsx      # Main claims grid
│   ├── AdjusterPanel.tsx    # Adjusters overview
│   ├── MetricsPanel.tsx     # Dashboard metrics
│   ├── FraudAlerts.tsx      # Fraud indicators
│   ├── UploadClaim.tsx      # File upload
│   └── LiveFeed.tsx         # Real-time events
├── hooks/
│   └── useSSE.ts            # SSE hook
├── types/
│   └── index.ts             # TypeScript types
├── App.tsx                  # Main app component
├── App.css                  # Styles
└── main.tsx                 # Entry point
```

## Key Features

### Responsive Design
- Mobile-first approach
- Grid layouts adapt to screen size
- Hamburger menu for mobile (future enhancement)

### Real-time Updates
- SSE connection for live events
- Auto-refresh for data
- Connection status indicator

### Interactive Elements
- Click claims to view details
- Tab navigation between views
- Drag-and-drop upload
- Modal overlays

## Future Enhancements

- [ ] Search and filter claims
- [ ] Sort by severity/complexity
- [ ] Adjuster reassignment
- [ ] Bulk claim operations
- [ ] Charts and visualizations
- [ ] Export to CSV/PDF
- [ ] Dark mode toggle
- [ ] Mobile-optimized layout
