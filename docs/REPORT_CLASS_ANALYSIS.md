# Analysis: Converting from Article to Report with Sections/Subsections

## Current Structure

### Document Class
- **Current**: `\documentclass[a4paper,10pt,fleqn]{article}`
- **Location**: `src/txt2tex/latex_gen.py:231`

### Current Question/Subquestion Handling

1. **Questions** (`** Question N **`):
   - **Parser**: Parsed as `Solution` AST node (`src/txt2tex/parser.py:526-555`)
   - **Generator**: `_generate_solution()` (`src/txt2tex/latex_gen.py:1286-1300`)
   - **Current LaTeX Output**:
     ```latex
     \bigskip
     \noindent
     \textbf{Question N}
     
     \medskip
     ```
   - **Visual**: Bold text with manual spacing, no numbering, no table of contents entry

2. **Subquestions** (`(a)`, `(b)`, `(c)`):
   - **Parser**: Parsed as `Part` AST node (`src/txt2tex/parser.py:557-577`)
   - **Generator**: `_generate_part()` (`src/txt2tex/latex_gen.py:1302-1370`)
   - **Current LaTeX Output** (varies by content):
     - Single paragraph: `(a) text` with hanging indent
     - Single expression: `(a) $expr$` with hanging indent
     - Traditional: `(a)\par\vspace{11pt}`
   - **Visual**: Inline labels with manual spacing, no numbering, no table of contents entry

3. **Sections** (`=== Title ===`):
   - **Parser**: Parsed as `Section` AST node (`src/txt2tex/parser.py:497-524`)
   - **Generator**: `_generate_section()` (`src/txt2tex/latex_gen.py:1274-1284`)
   - **Current LaTeX Output**: `\section*{Title}` (unnumbered)
   - **Visual**: Unnumbered section heading

## Proposed Structure

### Document Class Change
- **Proposed**: `\documentclass[a4paper,10pt,fleqn]{report}`
- **Impact**: Enables chapters, changes section numbering behavior

### Proposed Question/Subquestion Handling

1. **Questions** (`** Question N **`):
   - **Proposed LaTeX Output**: `\section{Question N}` (numbered)
   - **Visual Changes**:
     - Numbered sections (e.g., "1 Question 1", "2 Question 2")
     - Automatic spacing (LaTeX default section spacing)
     - Appears in table of contents (if enabled)
     - Larger, bold heading with automatic spacing above/below
     - Section numbers in page headers/footers (if enabled)

2. **Subquestions** (`(a)`, `(b)`, `(c)`):
   - **Proposed LaTeX Output**: `\subsection{(a)}` or `\subsection*{(a)}`
   - **Visual Changes**:
     - Numbered subsections (e.g., "1.1 (a)", "1.2 (b)") if numbered
     - Or unnumbered with `\subsection*` (just "(a)", "(b)") if unnumbered preferred
     - Automatic spacing (LaTeX default subsection spacing)
     - Appears in table of contents (if numbered and TOC enabled)
     - Medium-sized, bold heading
     - Proper hierarchical structure

3. **Sections** (`=== Title ===`):
   - **Options**:
     - **Option A**: Keep as `\section*{Title}` (unnumbered section)
     - **Option B**: Change to `\chapter{Title}` (numbered chapter, starts new page)
   - **Recommendation**: Option A (keep as unnumbered section) unless user wants chapters

## Required Code Changes

### 1. Document Class Change
**File**: `src/txt2tex/latex_gen.py`
**Location**: Line 231
**Change**:
```python
# Current:
lines.append(r"\documentclass[a4paper,10pt,fleqn]{article}")

# Proposed:
lines.append(r"\documentclass[a4paper,10pt,fleqn]{report}")
```

**Impact**: Minimal - just changes document class. All existing packages work with `report`.

### 2. Solution → Section Conversion
**File**: `src/txt2tex/latex_gen.py`
**Location**: `_generate_solution()` method (lines 1286-1300)
**Change**:
```python
# Current:
def _generate_solution(self, node: Solution) -> list[str]:
    """Generate LaTeX for solution."""
    lines: list[str] = []
    lines.append(r"\bigskip")
    lines.append(r"\noindent")
    lines.append(r"\textbf{" + node.number + "}")
    lines.append("")
    lines.append(r"\medskip")  # Add vertical space before content
    lines.append("")
    
    for item in node.items:
        item_lines = self.generate_document_item(item)
        lines.extend(item_lines)
    
    return lines

# Proposed:
def _generate_solution(self, node: Solution) -> list[str]:
    """Generate LaTeX for solution as section."""
    lines: list[str] = []
    lines.append(r"\section{" + node.number + "}")
    lines.append("")
    
    for item in node.items:
        item_lines = self.generate_document_item(item)
        lines.extend(item_lines)
    
    return lines
```

**Impact**: 
- Removes manual spacing (`\bigskip`, `\medskip`)
- Uses LaTeX's automatic section spacing
- Adds section numbering
- Simpler code (removes `\noindent`, `\textbf`)

### 3. Part → Subsection Conversion
**File**: `src/txt2tex/latex_gen.py`
**Location**: `_generate_part()` method (lines 1302-1370)
**Change**: More complex - need to decide on numbered vs unnumbered

**Option 1: Numbered Subsections**
```python
# Proposed:
def _generate_part(self, node: Part) -> list[str]:
    """Generate LaTeX for part label as subsection."""
    lines: list[str] = []
    
    # Use subsection with label
    lines.append(r"\subsection{(" + node.label + ")}")
    lines.append("")
    
    # Generate content
    for item in node.items:
        item_lines = self.generate_document_item(item)
        lines.extend(item_lines)
    
    return lines
```

**Option 2: Unnumbered Subsections** (recommended - preserves current visual style)
```python
# Proposed:
def _generate_part(self, node: Part) -> list[str]:
    """Generate LaTeX for part label as unnumbered subsection."""
    lines: list[str] = []
    
    # Use unnumbered subsection with label
    lines.append(r"\subsection*{(" + node.label + ")}")
    lines.append("")
    
    # Generate content
    for item in node.items:
        item_lines = self.generate_document_item(item)
        lines.extend(item_lines)
    
    return lines
```

**Impact**: 
- Removes all the complex inline formatting logic (hanging indent, etc.)
- Uses LaTeX's automatic subsection spacing
- Simpler code (removes ~70 lines of conditional formatting)
- **Important**: Need to decide if subsections should be numbered or unnumbered

### 4. Section Handling (Optional)
**File**: `src/txt2tex/latex_gen.py`
**Location**: `_generate_section()` method (lines 1274-1284)
**Change**: None required (already uses `\section*`)

**Optional Enhancement**: Could change to `\chapter` if user wants chapters:
```python
# Optional:
lines.append(r"\chapter{" + node.title + "}")
```

## Visual Impact Analysis

### Current Visual Appearance

**Questions**:
- Bold text: "Question 1"
- Manual spacing above/below
- No numbering
- No table of contents entry
- Same font size as body text (just bold)

**Subquestions**:
- Inline labels: "(a) text" or "(a)" on separate line
- Manual spacing (`\vspace{11pt}` or `\medskip`)
- No numbering
- No table of contents entry
- Same font size as body text

### Proposed Visual Appearance

**Questions** (as `\section`):
- Large, bold heading: "1 Question 1"
- Automatic LaTeX section spacing (larger than current `\bigskip`)
- Numbered sequentially (1, 2, 3, ...)
- Appears in table of contents (if `\tableofcontents` is added)
- Larger font size (LaTeX default section size)
- More prominent visual hierarchy

**Subquestions** (as `\subsection` or `\subsection*`):

**If Numbered** (`\subsection`):
- Medium, bold heading: "1.1 (a)", "1.2 (b)", etc.
- Automatic LaTeX subsection spacing
- Numbered within section
- Appears in table of contents
- Medium font size (between section and body)

**If Unnumbered** (`\subsection*`):
- Medium, bold heading: "(a)", "(b)", etc.
- Automatic LaTeX subsection spacing
- No numbering
- Does NOT appear in table of contents
- Medium font size (between section and body)
- **Closest to current appearance** (just better spacing)

### Spacing Comparison

**Current**:
- Question: `\bigskip` (12pt) + `\medskip` (6pt) = ~18pt total
- Subquestion: `\vspace{11pt}` or `\medskip` (6pt)

**Proposed** (LaTeX defaults):
- Section: `\topskip` + `\baselineskip` + section spacing (~20-30pt)
- Subsection: `\baselineskip` + subsection spacing (~12-18pt)

**Result**: Similar or slightly more spacing, but more consistent and professional.

## Test Impact

### Files That Need Updates

1. **Test Files**:
   - `tests/test_01_propositional_logic/test_truth_tables.py` - Tests solution generation
   - `tests/test_coverage/test_latex_gen_coverage.py` - Tests solution marker
   - Any tests that check for `\bigskip`, `\medskip`, `\textbf{Solution` patterns

2. **Expected Test Changes**:
   - Update assertions from `\textbf{Question N}` to `\section{Question N}`
   - Update assertions from `(a)\par\vspace{11pt}` to `\subsection{(a)}` or `\subsection*{(a)}`
   - Remove checks for manual spacing commands

### Backward Compatibility

**Breaking Changes**:
- Document class change: `article` → `report`
- Question formatting: Manual → Section
- Subquestion formatting: Manual → Subsection

**Migration Path**:
- Existing `.txt` files will work without changes (parser unchanged)
- Generated `.tex` files will have different structure
- Generated PDFs will have different visual appearance

## Implementation Complexity

### Low Complexity (Easy)
1. ✅ Document class change (1 line)
2. ✅ Solution → Section conversion (~10 lines to change)

### Medium Complexity
3. ⚠️ Part → Subsection conversion (~70 lines to simplify)
   - Need to remove all inline formatting logic
   - Need to decide: numbered vs unnumbered
   - Need to update all test assertions

### High Complexity
4. ⚠️ Test updates
   - Multiple test files need updates
   - Need to verify visual output matches expectations

## Recommendations

1. **Use `\subsection*` (unnumbered)** for parts to preserve current visual style while gaining better spacing
2. **Keep `\section*`** for `=== Title ===` sections (don't change to chapters unless requested)
3. **Add option** to generate table of contents if user wants it
4. **Test thoroughly** with actual PDF output to verify spacing looks good

## Questions for User

1. **Subsections**: Numbered (`\subsection`) or unnumbered (`\subsection*`)?
   - Numbered: "1.1 (a)", "1.2 (b)" - more formal, appears in TOC
   - Unnumbered: "(a)", "(b)" - closer to current style, cleaner

2. **Sections** (`=== Title ===`): Keep as `\section*` or change to `\chapter`?
   - `\section*`: Unnumbered section, stays on same page
   - `\chapter`: Numbered chapter, starts new page (more formal)

3. **Table of Contents**: Should we add `\tableofcontents` command?
   - Yes: Adds TOC page at beginning
   - No: No TOC (current behavior)

4. **Spacing**: Are you happy with LaTeX's automatic section spacing, or do you want custom spacing?

