# Supported Artifacts & Browser Schemas

## 1. Chromium Family (Google Chrome, Microsoft Edge, Brave)
- **Primary File:** SQLite database `History`
- **Extracted Tables:**
  - `urls`: `url`, `title`, `visit_count`, `typed_count`, `last_visit_time`
  - `visits`: `visit_time`, `from_visit`, `transition`
  - `downloads`: `target_path` / `current_path`, `start_time`, `total_bytes`, `state`, `tab_url`
- **Timestamp Format:** Microseconds elapsed since January 1, 1601 00:00:00 UTC (WebKit Epoch).

## 2. Mozilla Firefox
- **Primary File:** SQLite database `places.sqlite`
- **Extracted Tables:**
  - `moz_places`: `url`, `title`, `visit_count`, `frecency`, `last_visit_date`
  - `moz_historyvisits`: `visit_date`, `visit_type`, `from_visit`
  - `moz_bookmarks`: `title`, `dateAdded`, `lastModified`
- **Timestamp Format:** Microseconds elapsed since January 1, 1970 00:00:00 UTC (PRTime Epoch).

## 3. Explicitly Excluded Artifacts
- Passwords & Saved Credentials (`Login Data`)
- HTTP Cookies (`Cookies`)
- Session Tokens & Local Storage
- Autofill Secrets
