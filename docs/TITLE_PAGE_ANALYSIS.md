# Title Page Support Analysis

## Current State

Looking at `hw/solutions.txt`:
- Line 1: `=== Software Engineering Mathematics ===` (currently rendered as `\section*{Software Engineering Mathematics}`)
- Lines 3-6: TEXT blocks containing:
  - "October 2025" (date)
  - "Dr. Andrew Simpson" (author)
  - "University of Oxford" (institution)
  - "Software Engineering Progamme" (program/subtitle)

These are currently rendered as regular TEXT blocks with manual spacing, appearing after the table of contents.

## LaTeX Title Page Options

### Option 1: Standard `\maketitle` (Recommended)
LaTeX's built-in title page mechanism:
```latex
\title{Title}
\author{Author}
\date{Date}
\maketitle
```

**Pros:**
- Standard LaTeX approach
- Automatic formatting
- Works with `article` class
- Can be customized with packages like `titling`

**Cons:**
- Less control over exact layout
- Title page appears before TOC (may need adjustment)

### Option 2: Custom Title Page
Manual formatting with custom LaTeX:
```latex
\begin{titlepage}
\centering
\vspace*{2cm}
{\Huge Title}\\[1cm]
{\Large Subtitle}\\[0.5cm]
{\large Author}\\[0.5cm]
Date
\end{titlepage}
```

**Pros:**
- Full control over layout
- Can place anywhere (before/after TOC)

**Cons:**
- More complex
- Requires `titlepage` environment (works with `article`)

### Option 3: Title Block Syntax
Treat title metadata as a special block type (like sections):
```txt
TITLE: Software Engineering Mathematics
SUBTITLE: Software Engineering Programme
AUTHOR: Dr. Andrew Simpson
DATE: October 2025
INSTITUTION: University of Oxford
```

**Pros:**
- Clear, explicit syntax
- Easy to parse
- Flexible (can add more fields)

**Cons:**
- New syntax to learn
- More parser complexity

## Recommended Approach

### Syntax Design

I recommend **Option 3** with a special block syntax at the top of the document:

```txt
TITLE: Software Engineering Mathematics
SUBTITLE: Software Engineering Programme
AUTHOR: Dr. Andrew Simpson
DATE: October 2025
INSTITUTION: University of Oxford
```

**Rationale:**
- Clear and explicit
- Easy to parse (similar to existing TEXT: syntax)
- Flexible - can add more fields as needed
- Doesn't interfere with existing content structure

### Implementation Plan

1. **Parser Changes**:
   - Add new token types: `TITLE`, `SUBTITLE`, `AUTHOR`, `DATE`, `INSTITUTION`
   - Parse these as a `TitleBlock` AST node (or individual metadata fields)
   - Store metadata in Document AST node

2. **Generator Changes**:
   - Generate `\title{...}`, `\author{...}`, `\date{...}` in preamble
   - Generate `\maketitle` after `\begin{document}` but before `\tableofcontents`
   - Optionally generate custom formatting for subtitle/institution

3. **LaTeX Output**:
   ```latex
   \documentclass[...]{article}
   ...
   \title{Software Engineering Mathematics}
   \author{Dr. Andrew Simpson}
   \date{October 2025}
   \begin{document}
   \maketitle
   \tableofcontents
   ...
   ```

### Alternative: Simpler Syntax

If the user prefers, we could use a single block:
```txt
TITLEPAGE:
Title: Software Engineering Mathematics
Subtitle: Software Engineering Programme
Author: Dr. Andrew Simpson
Date: October 2025
Institution: University of Oxford
```

This is more compact but requires parsing key-value pairs.

## Questions for User

1. **Syntax preference**: Separate lines (`TITLE: ...`) or single block (`TITLEPAGE: ...`)?
2. **Placement**: Title page before or after table of contents?
3. **Fields needed**: Title, subtitle, author, date, institution - any others?
4. **Formatting**: Use standard `\maketitle` or custom formatting?
5. **Current section**: Should `=== Software Engineering Mathematics ===` become the title, or stay as a section?

## Visual Impact

**Current**: Title appears as unnumbered section after TOC, followed by TEXT blocks with metadata.

**Proposed**: 
- Professional title page at the beginning
- Title, author, date prominently displayed
- Table of contents follows title page
- Cleaner document structure

## Implementation Complexity

- **Parser**: Medium (new token types, new AST node)
- **Generator**: Low (just add commands to preamble and after `\begin{document}`)
- **Tests**: Medium (need tests for parsing and generation)
- **Backward compatibility**: High (existing documents without title metadata still work)

