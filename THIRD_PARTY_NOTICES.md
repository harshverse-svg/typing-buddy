# Third-Party Notices and Licenses

Typing Buddy relies on third-party open-source libraries and datasets.
This document lists the verified licenses, notices, and attribution details for each component.

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

### 5a. harper-py (Python Bindings)
- **Package Name:** `harper-py`
- **Pinned Version:** `0.2.0`
- **Author:** Maksim Burtsev (GitHub: Maksim-Burtsev)
- **License:** Apache License, Version 2.0
- **PyPI Page:** https://pypi.org/project/harper-py/0.2.0/
- **Source Repository:** https://github.com/Maksim-Burtsev/harper-py
- **Documentation:** https://github.com/Maksim-Burtsev/harper-py/blob/main/docs/guide.md
- **Summary:** Python bindings for Harper, the fast offline English grammar checker written in Rust.

### 5b. Harper Grammar Engine (Upstream Project)
- **Project Name:** Harper (The Grammar Checker for Developers)
- **Created by:** Elijah Potter and Automattic Inc.
- **License:** Apache License, Version 2.0
- **Upstream Source Repository:** https://github.com/Automattic/harper
- **Upstream Website:** https://writewithharper.com/
- **Notice:** `harper-py` packages precompiled native binaries of the Harper core engine under Apache License 2.0.

---

## Word Lists and Lexical Datasets

### 1. SCOWL (Spell Checking Oriented Word Lists)
- **Author & Copyright:** Copyright 2000-2018 by Kevin Atkinson and other contributors.
- **Project Website:** http://wordlist.aspell.net/
- **Source Repository:** https://github.com/en-wl/wordlist
- **License:** Permissive BSD/MIT-style licenses and Public Domain (ENABLE, 109537, 12Dicts 2of12).
- **Notice Requirement:** The full, unabridged SCOWL copyright notice is reproduced in [wordpacks/NOTICE.md](wordpacks/NOTICE.md) as required by the SCOWL project.

### 2. Hermit Dave FrequencyWords (`wordpacks/en-basic`, `wordpacks/en-large`)
- **Author & Copyright:** Copyright (c) 2016 Hermit Dave
- **Source Repository:** https://github.com/hermitdave/FrequencyWords
- **Repository License:** MIT License (https://github.com/hermitdave/FrequencyWords/blob/master/LICENSE)
- **Corpus Origin:** Word frequencies derived from OpenSubtitles movie and television subtitles (http://www.opensubtitles.org/).
- **Reuse Terms & Provenance Note:**
  - Hermit Dave's code and parsing tools are released under MIT. However, the raw frequency data was extracted from community-uploaded OpenSubtitles subtitle files.
  - The reuse terms of OpenSubtitles corpora for commercial distribution contain legal ambiguities because subtitles are user-contributed transcriptions of copyrighted film and television dialogue.
  - While raw word frequency statistics are widely considered uncopyrightable factual data under US and international copyright law, the exact redistribution rights for subtitle-derived datasets remain formally unverified.

#### Optional Provenance Alternative: Local Generation
To eliminate any ambiguity regarding subtitle frequency data, we propose an alternative option:
- Rather than committing the pre-built 150,000-word dataset into git, provide `tools/build_wordlist.py` to generate `wordpacks/en-large/words.txt` locally on demand from clean public-domain and permissively licensed sources (e.g., SCOWL headwords and Project Gutenberg word frequencies).
  - **Pros:** 100% verified copyright provenance; reduces repository download size by ~2 MB.
  - **Cons:** Requires a local build/download step before using the optional `en-large` pack.
*(Per project policy, the committed `en-large` dataset remains bundled until a maintainer decision is finalized).*

### 3. Hinglish Wordlist (`wordpacks/hinglish`)
- **Author:** Typing Buddy Contributors
- **License:** Distributed under the MIT License / CC0 1.0 Universal Public Domain Dedication.
- **Description:** Curated and normalized vocabulary of common Roman-script Hindi words and conversational expressions.

---

## LGPL Dynamic Linking Compliance Note for Redistributors

This repository is distributed as pure Python source code and standard Python package wheels. Dependencies are resolved through standard Python package management (`pip install .`) and imported dynamically from `site-packages` at runtime.

If you choose to redistribute Typing Buddy packaged as a standalone binary executable (such as via PyInstaller, cx_Freeze, or Nuitka):
1. The LGPL-3.0 license requirements apply to the bundled `pynput` and `pystray` components.
2. In particular, LGPL-3.0 Section 4 requires that users have the mechanism to relink or replace the LGPL library with a modified version (e.g. by distributing object/source files or using directory-mode builds with unbundled shared libraries).
3. The official Typing Buddy project intentionally distributes standard Python packages, batch runners, and shell shortcuts rather than monolithic executables to preserve modularity, avoid antivirus false positives, and ensure full license compliance.
