"""
Visual design system and theme styles for ForenX.
Palette:
- Primary purple: #6D3FC0
- Deep purple: #43206F
- Lavender: #F2ECFA
- Pale lavender: #FAF7FE
- Rose pink: #D96A9B
- Soft pink: #FCEAF2
- Muted mauve: #A77AA6
- Main background: #FCFAFD
- Primary text: #282235
- Secondary text: #746B80
- Border: #E8E0EF
- Success: #287D60
- Warning: #A66B13
- Error: #B83D5B
"""

FORENX_CSS = """
<style>
:root {
  --primary-purple: #6D3FC0;
  --deep-purple: #43206F;
  --lavender: #F2ECFA;
  --pale-lavender: #FAF7FE;
  --rose-pink: #D96A9B;
  --soft-pink: #FCEAF2;
  --muted-mauve: #A77AA6;
  --main-bg: #FCFAFD;
  --primary-text: #282235;
  --secondary-text: #746B80;
  --border: #E8E0EF;
  --success: #287D60;
  --warning: #A66B13;
  --error: #B83D5B;
}

body, .stApp {
  background-color: var(--main-bg);
  color: var(--primary-text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

[data-testid="stSidebar"] {
  background-color: #F8F3FC;
  border-right: 1px solid var(--border);
}

.stMetric {
  background-color: white;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 1px 2px rgba(67, 32, 111, 0.04);
}

.forenx-card {
  background: white;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 18px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(67, 32, 111, 0.03);
}

.forenx-header {
  border-bottom: 1px solid var(--border);
  padding-bottom: 12px;
  margin-bottom: 20px;
}

.forenx-title {
  color: var(--deep-purple);
  font-size: 26px;
  font-weight: 700;
  margin: 0;
}

.forenx-subtitle {
  color: var(--secondary-text);
  font-size: 14px;
  margin-top: 4px;
}

.forenx-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

.badge-verified { background: #e3f7ed; color: var(--success); }
.badge-failed { background: #fbebee; color: var(--error); }
.badge-warning { background: #fef4e5; color: var(--warning); }
.badge-subtle { background: var(--lavender); color: var(--deep-purple); }

.notice-academic {
  background-color: var(--pale-lavender);
  border-left: 4px solid var(--primary-purple);
  padding: 12px 16px;
  border-radius: 4px;
  font-size: 12px;
  color: var(--deep-purple);
  margin-bottom: 20px;
}
</style>
"""
