# Third-Party Notices and Licenses

Typing Buddy relies on third-party open-source libraries and datasets.
This document lists the licenses, notices, and attribution details for each component.

---

## Python Libraries

### 1. pynput
- **License:** GNU Lesser General Public License v3.0 (LGPL-3.0)
- **Copyright:** Moses Palmér
- **Source:** https://github.com/moses-palmer/pynput
- **Notice:** Typing Buddy links to `pynput` dynamically via Python standard module imports (`import pynput`). Under the LGPL v3.0, end users are permitted to modify or replace the installed `pynput` distribution in their Python environment.

### 2. pystray
- **License:** GNU Lesser General Public License v3.0 (LGPL-3.0)
- **Copyright:** Moses Palmér
- **Source:** https://github.com/moses-palmer/pystray
- **Notice:** Typing Buddy links to `pystray` dynamically via Python standard module imports (`import pystray`). Under the LGPL v3.0, end users are permitted to modify or replace the installed `pystray` distribution in their Python environment.

### 3. Pillow (PIL Fork)
- **License:** Historical Permission Notice and Disclaimer (HPND)
- **Copyright:** (c) 1997-2011 by Secret Labs AB, 1995-2011 by Fredrik Lundh, 2010-present by Jeffrey A. Clark (Alex) and contributors.
- **Source:** https://github.com/python-pillow/Pillow

### 4. comtypes
- **License:** MIT License
- **Copyright:** (c) Thomas Heller and contributors.
- **Source:** https://github.com/enthought/comtypes

### 5. harper-py (Optional Grammar Engine)
- **License:** Apache License, Version 2.0
- **Copyright:** Elijah Potter and Harper contributors.
- **Source:** https://github.com/automata/harper / https://github.com/Automata-Systems/harper-py

---

## Word Lists and Lexical Datasets

### 1. English Word Frequencies (`wordpacks/en-basic`, `wordpacks/en-large`)
- Sourced from Hermit Dave's OpenSubtitles frequency corpora and Kevin Atkinson's SCOWL (Spell Checking Oriented Word Lists).
- **Licenses:**
  - Hermit Dave frequency list: MIT License.
  - SCOWL wordlists: Copyright 2000-2014 by Kevin Atkinson, licensed under permissive BSD/MIT-style licenses and Public Domain notices.

### 2. Hinglish Wordlist (`wordpacks/hinglish`)
- Curated and normalized vocabulary of common Roman-script Hindi terms, loanwords, and conversational expressions.
- **License:** Distributed under the MIT License / CC0 1.0 Universal Public Domain Dedication.

---

## LGPL Dynamic Linking Compliance Note for Redistributors

This repository is distributed as pure Python source code and standard Python package wheels. Dependencies are resolved through standard Python package management (`pip install .`) and imported dynamically from `site-packages` at runtime.

If you choose to redistribute Typing Buddy packaged as a standalone binary executable (such as via PyInstaller, cx_Freeze, or Nuitka):
1. The LGPL-3.0 license requirements apply to the bundled `pynput` and `pystray` components.
2. In particular, LGPL-3.0 Section 4 requires that users have the mechanism to relink or replace the LGPL library with a modified version (e.g. by distributing object/source files or using directory-mode builds with unbundled shared libraries).
3. The official Typing Buddy project intentionally distributes standard Python packages, batch runners, and shell shortcuts rather than monolithic executables to preserve modularity, avoid antivirus false positives, and ensure full license compliance.
