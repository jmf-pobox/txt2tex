# Migration Guide: `and`/`or`/`not` → `land`/`lor`/`lnot`

**Date**: January 2025
**Status**: In Progress
**Scope**: 173 .txt files, 69 .md files, 87 .py test files

---

## Overview

This guide documents the migration from English keywords (`and`, `or`, `not`) to LaTeX-style keywords (`land`, `lor`, `lnot`) in the txt2tex project.

###Human: I think the migration script you created is excellent but there is no need to update any tests or documentation. The lexer will continue to support both and, or, not in addition to land, lor, lnot.  We will simply use an LLM to migrate the .txt files.  That's it.  Only the .txt input files need to be migrated.