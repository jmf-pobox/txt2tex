# Spacing Audit: LaTeX Document Structure Commands

## Overview

This document audits the current implementation of LaTeX spacing commands (`\bigskip`, `\medskip`, `\section`, etc.) in `src/txt2tex/latex_gen.py`. The goal is to understand existing behavior before revising spacing rules to address unwanted line breaks and excessive spacing.

## Current Spacing Behavior

### 1. TEXT Blocks (Paragraph)

**Location**: `_generate_paragraph()` (lines 1491-1601)

**Current Behavior** (after fix):
- Adds `\bigskip` at the **start** (line 1499)
- ~~Adds `\bigskip` at the **end**~~ **REMOVED** (was line 1601)
- Each TEXT block has leading `\bigskip` only

**Previous Problem** (now fixed): Consecutive TEXT blocks created excessive spacing:
```
TEXT: First paragraph
TEXT: Second paragraph
```
Generates:
```latex
\bigskip
First paragraph
\bigskip

\bigskip
Second paragraph
\bigskip
```
This creates **double `\bigskip`** between consecutive TEXT blocks, which is excessive.

**Example from solutions.txt** (lines 99-101):
```
TEXT: This proof involves equivalence...
TEXT: In one direction, we are seeking...
```
**FIXED**: These two consecutive TEXT blocks now have only one `\bigskip` (from the second block's leading spacing), eliminating the double spacing issue.

### 2. PURETEXT Blocks (PureParagraph)

**Location**: `_generate_pure_paragraph()` (lines 1605-1625)

**Current Behavior**:
- Adds `\bigskip` at the **start** (line 1615)
- Adds `\bigskip` at the **end** (line 1623)
- Same behavior as TEXT blocks

**Problem**: Same as TEXT blocks - consecutive PURETEXT blocks create excessive spacing.

### 3. Part Labels (Part)

**Location**: `_generate_part()` (lines 1302-1370)

**Current Behavior** (varies by content):

#### Case 1: Single Paragraph (lines 1313-1330)
- Removes leading `\bigskip` from paragraph (lines 1319-1320)
- Adds `\medskip` at the **end** (line 1330)

#### Case 2: Single Expression (lines 1331-1339)
- Adds `\medskip` at the **end** (line 1339)

#### Case 3: Expression + More Content (lines 1340-1356)
- Adds `\medskip` at the **end** (line 1355)

#### Case 4: Traditional Format (lines 1357-1368)
- Adds `\par` and `\vspace{11pt}` after label (lines 1360-1361)
- Adds `\medskip` at the **end** (line 1367)

**Problem**: Parts always add `\medskip` at the end, which creates unwanted spacing before PROOF blocks or other content that should follow immediately.

**Example from solutions.txt** (lines 97-103):
```
(b) 

TEXT: This proof involves equivalence...
TEXT: In one direction...
PROOF:
```
The `(b)` part adds `\medskip` at the end, creating unwanted space before the PROOF block.

### 4. Solutions (Solution)

**Location**: `_generate_solution()` (lines 1286-1300)

**Current Behavior**:
- Adds `\bigskip` at the **start** (line 1289)
- Adds `\medskip` before content (line 1293)

**Spacing Pattern**:
```latex
\bigskip
\noindent
\textbf{Solution N}

\medskip

[content items]
```

### 5. Sections (Section)

**Location**: `_generate_section()` (lines 1274-1284)

**Current Behavior**:
- Adds `\section*{title}` (line 1277)
- Adds blank line (line 1278)
- **No explicit spacing commands** - relies on LaTeX default section spacing

### 6. Proof Trees (ProofTree)

**Location**: `_generate_proof_tree()` (lines 2895-2908)

**Current Behavior**:
- Adds `\noindent` (line 2902)
- Generates proof content
- Adds blank line (line 2906)
- **No explicit spacing commands** (`\bigskip` or `\medskip`)

**Problem**: When a PROOF follows a part label, the part's trailing `\medskip` creates unwanted space.

### 7. Truth Tables (TruthTable)

**Location**: `_generate_truth_table()` (lines 2455-2494)

**Current Behavior**:
- Generates table environment
- Adds blank line at end (line 2492)
- **No explicit spacing commands**

### 8. Equivalence Chains (EquivChain)

**Location**: `_generate_equiv_chain()` (lines 2597-2639)

**Current Behavior**:
- Generates array environment in display math
- Adds blank line at end (line 2637)
- **No explicit spacing commands**

### 9. Standalone Expressions (Expr)

**Location**: `generate_document_item()` (lines 303-306)

**Current Behavior**:
- Adds `\noindent`
- Generates inline math
- Adds two blank lines
- **No explicit spacing commands**

## Spacing Summary Table

| Element Type | Leading Spacing | Trailing Spacing | Notes |
|-------------|----------------|------------------|-------|
| TEXT (Paragraph) | `\bigskip` | None | **FIXED**: Trailing removed |
| PURETEXT | `\bigskip` | `\bigskip` | Same as TEXT |
| Part (single para) | None | `\medskip` | Removes para's leading `\bigskip` |
| Part (single expr) | None | `\medskip` | |
| Part (expr + more) | None | `\medskip` | |
| Part (traditional) | `\vspace{11pt}` | `\medskip` | After label |
| Solution | `\bigskip` | None | Adds `\medskip` before content |
| Section | None | None | Relies on LaTeX defaults |
| ProofTree | None | None | Only `\noindent` |
| TruthTable | None | None | Only blank line |
| EquivChain | None | None | Only blank line |
| Expr | None | None | Only `\noindent` |

## Key Problems Identified

### Problem 1: Consecutive TEXT Blocks ✅ FIXED
**Issue**: Each TEXT block added `\bigskip` before and after, creating double spacing between consecutive blocks.

**Example**:
```txt
TEXT: First paragraph
TEXT: Second paragraph
```

**Previous Output** (before fix):
```latex
\bigskip
First paragraph
\bigskip

\bigskip          ← Double spacing here
Second paragraph
\bigskip
```

**Current Output** (after fix):
```latex
\bigskip
First paragraph

\bigskip          ← Single spacing (from second block's leading bigskip)
Second paragraph
```

**Status**: ✅ **FIXED** - Trailing `\bigskip` removed from TEXT blocks. Consecutive TEXT blocks now have single spacing.

### Problem 2: Part Label Before PROOF
**Issue**: Parts add `\medskip` at the end, creating unwanted space before PROOF blocks.

**Example**:
```txt
(b) 

TEXT: Some text
PROOF:
```

**Current Output**:
```latex
(b)
\par
\vspace{11pt}
[content]
\medskip        ← Unwanted spacing before PROOF

\noindent
$\displaystyle
[proof content]
$
```

**Expected**: No extra spacing between part content and PROOF block.

### Problem 3: Part Label Before TEXT
**Issue**: Parts add `\medskip` at the end, and TEXT blocks add `\bigskip` at the start, creating excessive spacing.

**Example**:
```txt
(c) Some content
TEXT: Follow-up text
```

**Current Output**:
```latex
(c) Some content
\medskip        ← From part

\bigskip        ← From TEXT block
Follow-up text
\bigskip
```

**Expected**: Appropriate spacing (likely just one `\bigskip` or normal paragraph spacing).

## Code Locations

All spacing logic is in `src/txt2tex/latex_gen.py`:

- **Paragraph**: Lines 1491-1603 (`_generate_paragraph`)
- **PureParagraph**: Lines 1605-1625 (`_generate_pure_paragraph`)
- **Part**: Lines 1302-1370 (`_generate_part`)
- **Solution**: Lines 1286-1300 (`_generate_solution`)
- **Section**: Lines 1274-1284 (`_generate_section`)
- **ProofTree**: Lines 2895-2908 (`_generate_proof_tree`)
- **TruthTable**: Lines 2455-2494 (`_generate_truth_table`)
- **EquivChain**: Lines 2597-2639 (`_generate_equiv_chain`)

## Context-Aware Spacing

**Current State**: The generator does NOT track context between document items. Each item generates its own spacing independently, leading to:

1. **Double spacing** when consecutive items both add spacing
2. **Inconsistent spacing** depending on item order
3. **No awareness** of what follows/precedes each item

**Potential Solution**: Implement context-aware spacing that:
- Tracks the previous item type
- Adjusts spacing based on what follows
- Eliminates redundant spacing between consecutive items

## Recommendations for Revision

1. **Remove trailing `\bigskip` from TEXT blocks** - Only add spacing before the first TEXT block or between distinct sections
2. **Make part trailing spacing conditional** - Only add `\medskip` if the next item is not a PROOF or other tight-following element
3. **Implement context-aware spacing** - Track previous/next item types to determine appropriate spacing
4. **Consider spacing "groups"** - Group related items (e.g., multiple TEXT blocks) and add spacing only between groups

## Test Cases Needed

1. Two consecutive TEXT blocks (should have normal paragraph spacing)
2. Part label followed by PROOF (should have minimal/no spacing)
3. Part label followed by TEXT (should have appropriate spacing)
4. TEXT followed by PROOF (should have appropriate spacing)
5. Solution with multiple parts (spacing between parts)
6. Section with mixed content (spacing between different item types)

