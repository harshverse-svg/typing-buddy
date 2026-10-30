# Typing Buddy Recording & Screenshot Guide

This guide describes how to capture the remaining visual assets on your Windows desktop for GitHub.

---

## Status of Visual Assets

| Asset | Target File | Status | Notes |
|---|---|---|---|
| **Live Demo GIF** | `assets/demo.gif` | ⏳ **Needs User Capture** | Target under 5 MB, ~800 px wide |
| **Word Suggestions Screenshot** | `assets/screenshot-word.png` | ⏳ **Needs User Capture** | Notepad window showing word completion pill |
| **Grammar Suggestions Screenshot** | `assets/screenshot-grammar.png` | ⏳ **Needs User Capture** | Notepad window showing grammar fix pill |
| **System Tray Menu Screenshot** | `assets/screenshot-tray.png` | ✅ **Captured & Integrated** | Windows 11 tray context menu with word packs |

---

## Tool & Recording Specifications

- **Recommended Free Tool:** [ScreenToGif](https://www.screentogif.com/) (free, open source) or OBS Studio.
- **Resolution:** ~800 px wide (crop to the active window area rather than full 4K/1080p desktop).
- **Target File Size:** Under 5 MB for `demo.gif` to ensure fast loading on mobile and desktop GitHub viewports.

---

## 1. Demo GIF (`assets/demo.gif`)

**Exact Scenario to Record (approx. 8–10 seconds total):**
1. Open a clean **Notepad** window.
2. Type: `diff`  
   $\rightarrow$ Wait 1 second as suggestion pill shows `different`, `difficult`. Press `F2` to complete.
3. Type: `recie ` (with space)  
   $\rightarrow$ Notice fuzzy correction `receive` appears. Press `Tab` to accept.
4. Type: `she go`  
   $\rightarrow$ Notice `✎ goes` grammar suggestion pill appears with `Subject-verb agreement` subtitle. Press `Tab` or `F2` to accept.
5. In ScreenToGif, trim the start and end, apply slight compression, and save as `assets/demo.gif`.

### How to Enable in `README.md`:
Once you place `assets/demo.gif` in the repository, open `README.md` and replace the `<!-- DEMO GIF PLACEHOLDER ... -->` block with this exact line:

```markdown
<p align="center"><img src="assets/demo.gif" alt="Typing Buddy Live Demo" width="800"></p>
```

---

## 2. Word Suggestions Screenshot (`assets/screenshot-word.png`)

1. Open **Notepad**.
2. Type `diff` so that the floating overlay appears right at the text cursor displaying:
   `[1] different  [2] difficult  [3] difference`
3. Take a clean window crop screenshot (`Win + Shift + S`).
4. Save as `assets/screenshot-word.png`.

---

## 3. Grammar Suggestion Screenshot (`assets/screenshot-grammar.png`)

1. Open **Notepad**.
2. Type `she go` so that the grammar replacement pill appears:
   `[1] ✎ goes` with subtitle `Subject-verb agreement`.
3. Take a clean window crop screenshot (`Win + Shift + S`).
4. Save as `assets/screenshot-grammar.png`.

---

## 4. System Tray Screenshot (`assets/screenshot-tray.png`)

✅ Already captured from your live Windows 11 desktop and embedded in `README.md`.
