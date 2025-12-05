# UI FLOW - Roster Mapper Phase 2

---

## 📍 User Journey

```
┌─────────┐     ┌──────────┐     ┌─────────┐     ┌─────────┐
│ UPLOAD  │ --> │ PREVIEW  │ --> │ PROCESS │ --> │ RESULTS │
│         │     │          │     │         │     │         │
│ Select  │     │ Check    │     │ Confirm │     │ Download│
│ Files   │     │ Mapping  │     │ & Run   │     │ Files   │
└─────────┘     └──────────┘     └─────────┘     └─────────┘
```

---

## 🖥️ Page Wireframes

### 1. Upload Page (`/upload`)

```
┌─────────────────────────────────────────────────────────────┐
│  🛫 ROSTER MAPPER                    [Upload][Admin][Dash]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🌍 Station Selection                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Station: [Auto-detect ▼]    ☑ Auto-detect filename  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ SGN✅  HAN✅  DAD✅  CXR✅  HPH✅  VCA✅  VII✅    │   │
│  │  10     74     8      6      5      5      5       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📁 Upload Files                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │         📁 Kéo thả files vào đây                    │   │
│  │            hoặc click để chọn                       │   │
│  │                                                     │   │
│  │         Excel (.xlsx, .xls) - Multi-file           │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                    [Clear All] [➡️ Preview Mapping]         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. Preview Page (`/preview`)

```
┌─────────────────────────────────────────────────────────────┐
│  🛫 ROSTER MAPPER                    [Upload][Admin][Dash]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  👁️ Preview Mapping            [← Quay lại] [✅ Start]     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📄 HAN_ROSTER_DEC2025.xlsx                          │   │
│  │ Sheet: roste lọc | 259 rows    Station: [HAN ▼]    │   │
│  │ ✅ 2101 mapped | ⚠️ 2 unmapped: B19, B3            │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ User ID | Name     | 26/11      | 27/11      | ... │   │
│  │─────────┼──────────┼────────────┼────────────┼─────│   │
│  │ VJC001  │ Nguyen A │ DT→HC      │ BD1_O→BD1  │     │   │
│  │         │          │ (green bg) │ (green bg) │     │   │
│  │ VJC002  │ Tran B   │ B19        │ HC         │     │   │
│  │         │          │ (red bg)   │            │     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                         [✅ Xác nhận & Start Mapping]       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. Results Page (`/results`)

```
┌─────────────────────────────────────────────────────────────┐
│  🛫 ROSTER MAPPER                    [Upload][Admin][Dash]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                          🎉                                 │
│                  Mapping Complete!                          │
│                   3 files processed                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ✅ HAN_ROSTER.xlsx                                  │   │
│  │ Station: HAN | 2101 mapped, 2479 unchanged          │   │
│  │ ┌─────┬─────┬─────┬─────┐                [⬇️ DL]   │   │
│  │ │15860│2101 │2479 │11219│                          │   │
│  │ │Total│Map  │Same │Empty│                          │   │
│  │ └─────┴─────┴─────┴─────┘                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│            [📤 Upload More] [📊 View Dashboard]            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4. Admin Page (`/admin`)

```
┌─────────────────────────────────────────────────────────────┐
│  🛫 ROSTER MAPPER                    [Upload][Admin][Dash]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚙️ Admin - Mapping Management                              │
│                                                             │
│  [SGN][HAN][DAD][CXR][HPH][VCA][VII]  <- Tabs               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ HAN Mappings (74 entries)    [📥 Import] [📤 Export]│   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ Versions: v20241205_150000 (74) | v20241204 (70)    │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ From Code    │ To Code                              │   │
│  │──────────────┼──────────────────────────────────────│   │
│  │ DT           │ HC                                   │   │
│  │ BD1_O        │ BD1                                  │   │
│  │ PQC          │ HC                                   │   │
│  │ ...          │ ...                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📚 Import: CSV (from,to) | JSON | Excel                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5. Dashboard Page (`/dashboard`)

```
┌─────────────────────────────────────────────────────────────┐
│  🛫 ROSTER MAPPER                    [Upload][Admin][Dash]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 Dashboard                                               │
│                                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │  📋     │ │  🌍     │ │  ✈️     │ │  📝     │           │
│  │  124    │ │   5     │ │   7     │ │   15    │           │
│  │ Total   │ │ Active  │ │ Total   │ │ Recent  │           │
│  │Mappings │ │Stations │ │Stations │ │Actions  │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│                                                             │
│  ┌─────────────────────┐ ┌─────────────────────┐           │
│  │ Mappings/Station    │ │ Actions Distribution │           │
│  │ ▓▓▓▓▓▓▓▓ HAN 74    │ │      ╭───╮           │           │
│  │ ▓▓▓ SGN 10         │ │     ╱     ╲          │           │
│  │ ▓▓ DAD 8           │ │    │ ● ●   │         │           │
│  │ ▓ CXR 6            │ │     ╲     ╱          │           │
│  │ ▓ HPH 5            │ │      ╰───╯           │           │
│  └─────────────────────┘ └─────────────────────┘           │
│                                                             │
│  Station Details Table                                      │
│  Recent Activity Log                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 Design System

### Colors (Vietjet Brand)
- Primary: `#E31837` (Vietjet Red)
- Secondary: `#FFD700` (Vietjet Yellow)
- Success: `#10B981`
- Warning: `#F59E0B`
- Error: `#EF4444`

### Highlights
- Mapped cell: `bg-green-50` (light green)
- Unmapped cell: `bg-red-50` (light red)

### Components
- Buttons: `rounded-lg` with hover states
- Cards: `rounded-xl shadow-sm border`
- Tables: Striped, hover highlight

---

## 🔄 API Interactions

| Action | API Call | Response |
|--------|----------|----------|
| Upload files | `POST /upload` (form) | Redirect to `/preview` |
| Update station | `POST /preview/update-station` (HTMX) | HTML snippet |
| Start mapping | `POST /process` | Redirect to `/results` |
| Download file | `GET /api/v1/download/{id}` | Excel file |
| Batch download | `GET /api/v1/batch-download` | ZIP file |

