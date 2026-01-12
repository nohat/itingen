# PDF Validation Failure Report

**Date**: 2026-01-12  
**Issue**: itingen-uif  
**Status**: FAILED

## Summary

Validation of PDF output against scaffold POC **failed** due to fundamental architectural mismatch between implementation and specification.

## Root Cause

### Architectural Mismatch
- **Specified**: ReportLab (in `requirements.txt`, `pyproject.toml`, `ARCHITECTURE.md`)
- **Implemented**: FPDF2 (in actual code)
- **Scaffold POC**: ReportLab with Unicode font support

### Immediate Failure
Cannot generate PDF for NZ 2026 trip due to Unicode character rendering errors:
```
Error: Character "→" at index 24 in text is outside the range 
of characters supported by the font used: "helvetica"
```

### Data Source
Trip data files (`trips/nz_2026/events/*.md`) contain Unicode arrows (→) in location fields:
- `Queenstown → Gibbston Valley`
- `Te Anau → Queenstown`
- `AKL → LAX`
- etc.

## Scaffold POC Implementation

The scaffold POC uses ReportLab with proper Unicode support:

**Font Fallback Chain**:
1. SourceSans3 (preferred UI font)
2. NotoSans (fallback)
3. DejaVuSans (second fallback)  
4. Helvetica (last resort)

**Font Management**:
- Downloads fonts from GitHub on first use
- Caches in `scaffold-data/data/cache/pdf_fonts/`
- Registers TTF fonts with ReportLab
- Supports Māori macrons and Unicode characters

**Reference**: `/Users/nohat/scaffold/tools/nz_trip_pdf_render.py`

## Impact

**Cannot validate**:
- Layout quality
- Image placement
- Typography/spacing
- Narrative quality
- Weather boxes
- Overall aesthetic

**Reason**: Cannot generate a PDF to compare against scaffold POC.

## Required Fixes

### Created Issues

1. **itingen-hds** (P1): Replace FPDF2 with ReportLab
   - Migrate entire PDF rendering stack
   - Match scaffold POC architecture
   - Update all PDF components

2. **itingen-q6c** (P2): Implement Unicode font support
   - Download/cache font system
   - Register SourceSans3, NotoSans, DejaVuSans
   - Implement fallback chain
   - Depends on: itingen-hds

### Validation Retry

After completing itingen-hds and itingen-q6c:
1. Re-run: `python -m itingen.cli generate --trip trips/nz_2026 --format pdf`
2. Compare generated PDF with scaffold POC output
3. Document findings in new validation report

## Lessons Learned

1. **Verify architecture alignment early** - Check implementation matches specification before validation
2. **Test with real data** - Unicode characters in production data exposed the mismatch
3. **Don't patch around architectural issues** - Attempted Unicode sanitization was wrong approach
4. **Library choice matters** - FPDF2 vs ReportLab have different capabilities and APIs

## Current State

- Git: Clean, all changes committed
- Tests: Passing (with FPDF2 implementation)
- PDF Generation: **BROKEN** (Unicode errors)
- Validation: **BLOCKED** until architecture fixed
