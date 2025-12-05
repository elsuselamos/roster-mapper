# BACKLOG – Roster Mapper
**Features và improvements cho các Phase sau**

---

## Phase 2 - Web UI & Auth

| ID | Feature | Priority | Effort | Notes |
|----|---------|----------|--------|-------|
| P2-01 | Web UI với Jinja2 + Tailwind | P0 | L | Xem UI_SPEC.md |
| P2-02 | User authentication | P0 | M | API Key hoặc simple login |
| P2-03 | Admin dashboard | P1 | M | Stats, recent uploads |
| P2-04 | Upload history per user | P1 | S | List files đã upload |
| P2-05 | Drag & drop upload | P1 | S | |
| P2-06 | Progress bar for large files | P2 | S | |

---

## Phase 3 - Enhancements

| ID | Feature | Priority | Effort | Notes |
|----|---------|----------|--------|-------|
| P3-01 | Batch processing | P1 | M | Upload nhiều files cùng lúc |
| P3-02 | Scheduled jobs | P2 | L | Auto-process từ folder |
| P3-03 | Email notifications | P2 | M | Gửi file sau khi process |
| P3-04 | Export to PDF | P3 | M | |
| P3-05 | Mapping suggestions (AI) | P3 | L | Gợi ý mapping từ context |

---

## Phase 4 - Integration

| ID | Feature | Priority | Effort | Notes |
|----|---------|----------|--------|-------|
| P4-01 | AMOS integration | P1 | XL | Sync với Aircraft Maintenance System |
| P4-02 | SSO / LDAP | P2 | L | Vietjet internal auth |
| P4-03 | Cloud storage (GCS) | P3 | M | Backup files |
| P4-04 | Webhook notifications | P3 | S | |

---

## Technical Debt

| ID | Item | Priority | Notes |
|----|------|----------|-------|
| TD-01 | Add comprehensive error handling | P1 | |
| TD-02 | Increase test coverage to 90% | P1 | |
| TD-03 | Add integration tests | P2 | |
| TD-04 | Performance optimization for large files | P2 | |
| TD-05 | Add request validation middleware | P2 | |
| TD-06 | Implement proper logging rotation | P3 | |

---

## Ideas / Parking Lot

| Idea | Source | Notes |
|------|--------|-------|
| Mobile app | - | Có thể cần cho field staff |
| Voice input | - | "Map file SGN tháng 12" |
| Chatbot interface | - | Telegram/Slack bot |
| Multi-language | - | English version |
| Dark mode | - | User preference |

---

## Prioritization Legend

| Priority | Meaning |
|----------|---------|
| P0 | Must have |
| P1 | Should have |
| P2 | Nice to have |
| P3 | Future consideration |

| Effort | Meaning |
|--------|---------|
| S | Small (< 1 day) |
| M | Medium (1-3 days) |
| L | Large (1 week) |
| XL | Extra Large (2+ weeks) |

