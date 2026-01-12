# PDF Generation Gaps - Comparison to POC

**Date**: 2026-01-11
**Status**: Image generation fixed, PDF rendering needs work

---

## Executive Summary

Image generation is now working correctly (Gemini thumbnails + Imagen banners), but the PDF rendering pipeline needs significant work to match the scaffold POC quality. This document outlines the gaps and tracks the work needed.

---

## ✅ What's Working (Validated)

### Image Generation
- ✅ **Gemini Thumbnails (1:1)**: Working with gemini-2.5-flash-image
- ✅ **Imagen Banners (16:9)**: Working with imagen-4.0-ultra-generate-001
- ✅ **Ligne Claire Style**: Prompt templates ported from POC
- ✅ **Image Caching**: Fingerprint-based caching working
- ✅ **API Integration**: All 13 integration tests passing

### Pipeline
- ✅ **Event Parsing**: YAML/JSON ingestion working
- ✅ **Core Hydrators**: Maps, Weather, Narratives, Images all implemented
- ✅ **Markdown Output**: Basic markdown generation working

---

## ❌ Critical Gaps (P1)

### 1. PDF Renderer Implementation
**Issue**: [itingen-4ds](https://github.com/anthropics/itingen/issues/4ds)
**Status**: ✅ Completed
**Description**: Current markdown renderer is basic. Need proper PDF generation with:
- Day banner images as headers (16:9 panoramic)
- Event thumbnail images inline (1:1 square)
- Proper typography and spacing matching POC
- Page breaks and layout optimization
- Professional PDF aesthetic

**Blocked By**: None
**Blocking**: Weather boxes (itingen-w5k), Final validation (itingen-uif)

### 2. Day Banner Generation Pipeline
**Issue**: [itingen-26y](https://github.com/anthropics/itingen/issues/26y)
**Status**: Not started
**Description**: Need day-level hydrator/aggregation:
- Aggregate events by day
- Identify 2-5 "hero" visual elements per day
- Generate 16:9 Imagen banner with Wimmelbilderbuch style
- Include weather context and mood
- Filter out mundane events (generic meals, etc.)

**Blocked By**: None
**Blocking**: Banner validation (itingen-c28)

---

## 🔍 Validation Tasks (P1)

### 3. Thumbnail Image Validation
**Issue**: [itingen-3vy](https://github.com/anthropics/itingen/issues/3vy)
**Status**: Ready for human review
**What to Validate**:
- ✓ 1:1 square aspect ratio
- ✓ Ligne Claire style (bold outlines, flat colors, isometric)
- ✓ Event-appropriate content
- ✓ No text/typography visible
- ✓ Subject fills 70-85% of frame
- ✓ Vibrant, cheerful, saturated colors

**Sample Images**: `output/sample_images/thumbnail_*.png`

### 4. Banner Image Validation
**Issue**: [itingen-c28](https://github.com/anthropics/itingen/issues/c28)
**Status**: Blocked by banner generation (itingen-26y)
**What to Validate**:
- ✓ 16:9 panoramic aspect ratio
- ✓ Wimmelbilderbuch style (detailed, busy composition)
- ✓ Hero elements visible and recognizable
- ✓ Cohesive unified scene
- ✓ Aerial/isometric view
- ✓ No text/typography

**Sample Images**: `output/sample_images/banner_*.png`

### 5. Final PDF Comparison
**Issue**: [itingen-uif](https://github.com/anthropics/itingen/issues/uif)
**Status**: Blocked by PDF renderer (itingen-4ds)
**What to Validate**: Side-by-side comparison with scaffold POC PDF:
- Layout quality and spacing
- Image placement and sizing
- Typography and readability
- Narrative quality and tone
- Weather boxes presentation
- Overall aesthetic match

---

## 🔧 Enhancement Tasks (P2)

### 6. Weather Summary Boxes
**Issue**: [itingen-w5k](https://github.com/anthropics/itingen/issues/w5k)
**Status**: Blocked by PDF renderer (itingen-4ds)
**Description**: Add weather summary box to each day header:
- Typical high/low temperatures
- Weather conditions (sunny, cloudy, rainy)
- Visual weather icon
- Integrated into day banner header

### 7. Narrative Prompt Improvements
**Issue**: [itingen-nb2](https://github.com/anthropics/itingen/issues/nb2)
**Status**: Ready to start
**Description**: Review and port narrative prompt templates from scaffold:
- Tone guidance (casual, engaging, "picture this...")
- Context integration (weather, mood, logistics)
- Validate narrative quality matches POC

### 8. Image Post-Processing
**Issue**: [itingen-25j](https://github.com/anthropics/itingen/issues/25j)
**Status**: Ready to start
**Description**: Add image post-processing pipeline:
- Auto-detect and crop borders/padding (max 22% trim)
- Resample to target aspect ratio (LANCZOS interpolation)
- Format optimization (PNG preferred, JPEG fallback)
- Full-bleed aesthetic (no margins/borders)

### 9. Markdown Image References
**Issue**: [itingen-rld](https://github.com/anthropics/itingen/issues/rld)
**Status**: Ready to start
**Description**: Enhance markdown renderer:
- Include image paths in markdown output
- Add markdown image embedding syntax
- Useful for preview before PDF generation

---

## 🚀 Advanced Features (P3)

### 10. Visual Brief Generation
**Issue**: [itingen-lqe](https://github.com/anthropics/itingen/issues/lqe)
**Status**: Not started
**Description**: Use Gemini + Google Search grounding:
- Generate 4-line visual brief: SUBJECT, MUST_INCLUDE, AVOID, SOURCES
- Cache research results
- Improves image generation quality

### 11. Venue Research
**Issue**: [itingen-a99](https://github.com/anthropics/itingen/issues/a99)
**Status**: Not started
**Description**: Generate detailed venue visual descriptions:
- Canonical venue name
- Multi-paragraph visual description
- Primary/secondary visual cues
- Camera angle suggestions
- Enriches thumbnail prompts

### 12. Prompt Synthesis
**Issue**: [itingen-66s](https://github.com/anthropics/itingen/issues/66s)
**Status**: Not started
**Description**: Gemini synthesizes final image prompts:
- Combines event context + venue research + visual brief
- More intelligent than template-based approach
- Higher quality, more contextual images

---

## 📊 Priority Roadmap

### Phase 1: Critical Path (P1)
1. **Thumbnail Validation** (itingen-3vy) - Human review sample images ← **START HERE**
2. **PDF Renderer** (itingen-4ds) - Implement proper PDF generation
3. **Day Banner Generation** (itingen-26y) - Aggregate events → Imagen banners
4. **Banner Validation** (itingen-c28) - Human review banner images
5. **Final PDF Validation** (itingen-uif) - Compare to scaffold POC

### Phase 2: Polish (P2)
6. Weather boxes (itingen-w5k)
7. Narrative improvements (itingen-nb2)
8. Image post-processing (itingen-25j)
9. Markdown enhancements (itingen-rld)

### Phase 3: Advanced (P3)
10. Visual brief generation (itingen-lqe)
11. Venue research (itingen-a99)
12. Prompt synthesis (itingen-66s)

---

## 🎯 Current Status

### Completed
- ✅ Image generation API integration (Gemini + Imagen)
- ✅ Prompt template porting (Ligne Claire + Wimmelbilderbuch)
- ✅ Basic thumbnail generation working
- ✅ Integration test suite (13/13 passing)
- ✅ Sample images generated for validation

### In Progress
- 🔄 None (awaiting priority selection)

### Next Actions
1. **Human validation of sample images** (itingen-3vy)
   - Review `output/sample_images/`
   - Open `view_samples.html` in browser
   - Document findings

2. **Decide on PDF rendering approach**
   - Choose PDF library (reportlab, weasyprint, etc.)
   - Plan layout architecture
   - Design component system

---

## 📁 Key Files

### Sample Images (For Validation)
- `output/sample_images/thumbnail_ferry_waiheke.png` - Gemini 1:1
- `output/sample_images/thumbnail_wine_tasting.png` - Gemini 1:1
- `output/sample_images/banner_auckland_day.png` - Imagen 16:9
- `output/sample_images/view_samples.html` - Browser viewer

### Implementation Files
- `src/itingen/integrations/ai/gemini.py` - Image generation client
- `src/itingen/integrations/ai/image_prompts.py` - Prompt templates
- `src/itingen/hydrators/ai/images.py` - Thumbnail hydrator
- `tests/integration/test_real_api_integrations.py` - Integration tests

### Documentation
- `docs/INTEGRATION_VALIDATION.md` - Full integration test results
- `docs/POC_VALIDATION.md` - POC feature comparison
- `docs/PDF_GAPS.md` - This document

---

## 💡 Notes

### Why Thumbnails Work But Banners Need Work
- **Thumbnails**: Event-level, simple pipeline, working correctly
- **Banners**: Day-level aggregation needed, more complex prompt synthesis

### Cost Considerations
- **Gemini images**: ~$0.01 per image (fast, cheap for thumbnails)
- **Imagen images**: ~$0.05 per image (higher quality for banners)
- Caching is critical to avoid regeneration costs

### Quality Bar
All output must match or exceed the scaffold POC in:
- Visual aesthetic (style, colors, composition)
- Information density (right level of detail)
- Professional presentation (layout, typography)
- User experience (readability, navigation)

---

**Last Updated**: 2026-01-11
**Created Issues**: 12 tasks across 3 priority levels
**Ready to Start**: 10 issues with no blockers
