# AI-Powered Transition Generation Proposal

## Executive Summary

This proposal outlines a robust, abstract solution for generating transition descriptions between itinerary events using the Gemini API, replacing the current hardcoded pattern-matching approach with dynamic AI-generated transitions.

## Current State Analysis

### Existing Implementation (Post-PR)
The current system uses a `TransitionRegistry` with hardcoded pattern matching:
- 20+ explicit if/elif branches for NZ-specific transitions
- Wildcard patterns (`*`) for flexible matching
- Generic fallback for location-based transitions
- Registry architecture separates trip-specific logic from core pipeline

**Strengths:**
- ✅ Predictable, deterministic output
- ✅ Fast execution (no API calls)
- ✅ Works offline
- ✅ Zero cost

**Weaknesses:**
- ❌ Requires manual coding for each transition pattern
- ❌ Not adaptable to new trip types without code changes
- ❌ Limited contextual awareness
- ❌ Repetitive, mechanical descriptions
- ❌ Doesn't learn from venue descriptions or narratives

## Proposed Solution: AI-Powered Transition Hydrator

### Architecture Overview

Replace the hardcoded `TransitionRegistry` with a `GeminiTransitionHydrator` that dynamically generates transition descriptions using the Gemini API with carefully crafted prompts.

```python
# src/itingen/hydrators/ai/transitions.py

from typing import List, Optional
from itingen.core.base import BaseHydrator
from itingen.core.domain.events import Event
from itingen.integrations.ai.gemini import GeminiClient
from itingen.hydrators.ai.cache import AiCache

class GeminiTransitionHydrator(BaseHydrator[Event]):
    """Hydrator that generates AI-powered transition descriptions between events.
    
    Uses Gemini to create contextually rich, engaging transition narratives
    that consider event types, locations, timing, and trip-specific context.
    """
    
    def __init__(
        self, 
        client: GeminiClient,
        cache: Optional[AiCache] = None,
        style_template: Optional[str] = None,
        prompt_template: Optional[str] = None,
        fallback_strategy: str = "generic"  # "generic", "skip", or "error"
    ):
        self.client = client
        self.cache = cache
        self.style_template = style_template or TRANSITION_STYLE_TEMPLATE
        self.prompt_template = prompt_template or TRANSITION_PROMPT_TEMPLATE
        self.fallback_strategy = fallback_strategy
    
    def hydrate(self, items: List[Event], context=None) -> List[Event]:
        """Add AI-generated transition descriptions to events."""
        if not items:
            return []
        
        new_items = []
        prev_ev: Optional[Event] = None
        
        for ev in items:
            updates = {}
            if prev_ev is not None:
                # Skip if already set (from source data)
                if not ev.transition_from_prev:
                    transition = self._generate_transition(prev_ev, ev)
                    if transition:
                        updates["transition_from_prev"] = transition
            
            new_ev = ev.model_copy(update=updates) if updates else ev
            new_items.append(new_ev)
            prev_ev = new_ev
        
        return new_items
    
    def _generate_transition(self, prev_ev: Event, curr_ev: Event) -> Optional[str]:
        """Generate transition using Gemini API with caching."""
        # Create cache key from event attributes
        payload = {
            "task": "transition",
            "prev_kind": prev_ev.kind,
            "prev_location": prev_ev.location,
            "prev_travel_to": prev_ev.travel_to,
            "prev_travel_mode": getattr(prev_ev, "travel_mode", None),
            "curr_kind": curr_ev.kind,
            "curr_location": curr_ev.location,
            "curr_travel_from": curr_ev.travel_from,
            "curr_travel_mode": getattr(curr_ev, "travel_mode", None),
            "curr_driver": getattr(curr_ev, "driver", None),
            "curr_parking": getattr(curr_ev, "parking", None),
            "prompt_template": self.prompt_template
        }
        
        # Check cache first
        cached_transition = None
        if self.cache:
            cached_transition = self.cache.get_text(payload)
        
        if cached_transition:
            return cached_transition
        
        # Generate with Gemini
        try:
            prompt = self._build_prompt(prev_ev, curr_ev)
            transition = self.client.generate_text(prompt)
            
            # Clean up response (remove quotes, extra whitespace)
            transition = transition.strip().strip('"\'')
            
            # Cache the result
            if self.cache:
                self.cache.set_text(payload, transition)
            
            return transition
            
        except Exception as e:
            print(f"Warning: Failed to generate transition with Gemini: {e}")
            return self._apply_fallback(prev_ev, curr_ev)
    
    def _build_prompt(self, prev_ev: Event, curr_ev: Event) -> str:
        """Build the Gemini prompt for transition generation."""
        return self.prompt_template.format(
            style_guidance=self.style_template,
            prev_kind=prev_ev.kind or "N/A",
            prev_location=prev_ev.location or "N/A",
            prev_travel_to=prev_ev.travel_to or "N/A",
            prev_travel_mode=getattr(prev_ev, "travel_mode", "N/A"),
            curr_kind=curr_ev.kind or "N/A",
            curr_location=curr_ev.location or "N/A",
            curr_travel_from=curr_ev.travel_from or "N/A",
            curr_travel_to=curr_ev.travel_to or "N/A",
            curr_travel_mode=getattr(curr_ev, "travel_mode", "N/A"),
            curr_driver=getattr(curr_ev, "driver", "N/A"),
            curr_parking=getattr(curr_ev, "parking", "N/A")
        )
    
    def _apply_fallback(self, prev_ev: Event, curr_ev: Event) -> Optional[str]:
        """Apply fallback strategy when Gemini fails."""
        if self.fallback_strategy == "skip":
            return None
        elif self.fallback_strategy == "error":
            raise ValueError(f"Failed to generate transition for {prev_ev.kind} -> {curr_ev.kind}")
        else:  # generic
            prev_loc = (prev_ev.location or prev_ev.travel_to or "").strip()
            curr_loc = (curr_ev.location or curr_ev.travel_from or curr_ev.travel_to or "").strip()
            if prev_loc and curr_loc:
                return f"Move from {prev_loc} to {curr_loc}."
            return None
```

### Prompt Engineering

The quality of transitions depends heavily on well-crafted prompts:

```python
# src/itingen/integrations/ai/transition_prompts.py

TRANSITION_STYLE_TEMPLATE = (
    "You are an expert travel guide writing logistics instructions for travelers. "
    "Your tone is clear, practical, and helpful. Focus on concrete actions and logistics. "
    "Keep it concise (1-3 sentences). Be specific about what travelers should do and where they should go."
)

TRANSITION_PROMPT_TEMPLATE = """
{style_guidance}

Generate a clear, actionable transition description for moving between two events in a travel itinerary.

PREVIOUS EVENT:
- Kind: {prev_kind}
- Location: {prev_location}
- Travel destination: {prev_travel_to}
- Travel mode: {prev_travel_mode}

CURRENT EVENT:
- Kind: {curr_kind}
- Location: {curr_location}
- Travel origin: {curr_travel_from}
- Travel destination: {curr_travel_to}
- Travel mode: {curr_travel_mode}
- Driver: {curr_driver}
- Parking instructions: {curr_parking}

Write a 1-3 sentence transition that:
1. Explains how to move from the previous event to the current event
2. Mentions specific locations when relevant
3. Includes practical logistics (parking, driver, timing considerations)
4. Uses action-oriented language ("walk to", "drive to", "board the ferry")
5. Maintains continuity with the previous activity

Output ONLY the transition description text, no preface, no quotes, no labels.
"""

# Trip-specific style overrides (optional)
NZ_TRANSITION_STYLE_TEMPLATE = (
    "You are an expert New Zealand travel guide writing logistics instructions for travelers. "
    "Your tone is clear, practical, and friendly. New Zealand has unique transport like ferries "
    "between islands, scenic drives, and small regional airports. Focus on concrete actions and "
    "logistics specific to NZ travel. Keep it concise (1-3 sentences)."
)
```

### Integration with Existing System

The AI-powered hydrator can coexist with or replace the current registry-based system:

#### Option 1: Hybrid Approach (Recommended for Migration)
```python
class HybridTransitionHydrator(BaseHydrator[Event]):
    """Uses registry first, falls back to Gemini for unknown patterns."""
    
    def __init__(self, registry: TransitionRegistry, gemini_hydrator: GeminiTransitionHydrator):
        self.registry = registry
        self.gemini_hydrator = gemini_hydrator
    
    def _generate_transition(self, prev_ev: Event, curr_ev: Event) -> Optional[str]:
        # Try registry first (fast, predictable)
        description = self.registry.describe(prev_ev, curr_ev)
        if description:
            return description
        
        # Fall back to Gemini for unknown patterns
        return self.gemini_hydrator._generate_transition(prev_ev, curr_ev)
```

#### Option 2: Pure AI Approach
Replace `TransitionHydrator` entirely with `GeminiTransitionHydrator` in the CLI:

```python
# In src/itingen/cli.py

def _handle_generate(args: argparse.Namespace) -> int:
    # ... existing code ...
    
    # Initialize Gemini client if available
    gemini_client = None
    try:
        gemini_client = GeminiClient()
    except ValueError:
        print("Warning: GEMINI_API_KEY not found. Using generic transitions.")
    
    # Choose transition hydrator based on availability
    if gemini_client and args.ai_transitions:
        cache = AiCache(trip_path / ".cache")
        transition_hydrator = GeminiTransitionHydrator(
            client=gemini_client,
            cache=cache,
            style_template=NZ_TRANSITION_STYLE_TEMPLATE,  # Trip-specific style
            fallback_strategy="generic"
        )
    else:
        # Legacy registry-based approach
        registry = create_nz_transition_registry()
        transition_hydrator = TransitionHydrator(registry)
    
    # ... rest of orchestrator setup ...
```

## Benefits of AI-Powered Approach

### 1. **Adaptability**
- Works for ANY trip type without coding new patterns
- Automatically handles novel event combinations
- Learns from provided context (driver, parking, etc.)

### 2. **Contextual Richness**
- Considers full event context (kind, location, mode, timing)
- Can incorporate trip-specific knowledge via style templates
- More natural, varied language than hardcoded patterns

### 3. **Maintainability**
- No need to update code for new trip types
- Single prompt template instead of 20+ if/elif branches
- Easier to adjust tone/style by editing prompts

### 4. **Consistency with Other Hydrators**
- Matches architecture of `NarrativeHydrator` and `BannerImageHydrator`
- Uses same caching strategy
- Familiar patterns for developers

### 5. **Graceful Degradation**
- Falls back to generic transitions if API unavailable
- Caching minimizes API calls (1 call per unique transition pattern)
- Works offline after initial cache warm-up

## Cost & Performance Considerations

### API Costs
- **Gemini 2.0 Flash** (default model): Free tier (1500 RPD limit)
- **Caching**: Dramatically reduces costs after initial generation
- **Typical trip**: ~50-100 events → ~50-100 unique transitions
- **Cost**: Negligible for free tier, <$0.10 per trip for paid tier

### Performance
- **Cold start**: ~1-2 seconds per transition (50-100s total for first run)
- **Cached**: Instant (same as current registry approach)
- **Optimization**: Batch API calls (10-20 transitions in parallel)

### Cache Strategy
```python
# Cache key structure ensures proper reuse
{
    "task": "transition",
    "prev_kind": "ferry",
    "prev_location": "Auckland Ferry Terminal",
    "curr_kind": "drive",
    "curr_location": "Matamata",
    "curr_driver": "John",
    "curr_parking": "on-street near venue"
}
```

Similar transitions across trips reuse cached results.

## Migration Path

### Phase 1: Add AI Hydrator (Parallel)
1. ✅ Implement `GeminiTransitionHydrator` alongside existing registry
2. ✅ Add `--ai-transitions` flag to CLI
3. ✅ Test with NZ trip data
4. ✅ Validate quality and performance

### Phase 2: Hybrid Mode (Default)
1. ✅ Make `HybridTransitionHydrator` the default
2. ✅ Use registry for known patterns, Gemini for unknowns
3. ✅ Gather user feedback

### Phase 3: Full Migration (Optional)
1. ⚠️ Deprecate `TransitionRegistry` and `nz_transitions.py`
2. ⚠️ Make `GeminiTransitionHydrator` the default
3. ⚠️ Keep registry as fallback for offline mode

### Rollback Plan
If AI approach doesn't meet quality standards:
- Registry-based system remains functional
- Simple flag toggle to disable AI transitions
- No breaking changes to core architecture

## Testing Strategy

### Unit Tests
```python
def test_gemini_transition_hydrator_generates_transition():
    """Test that Gemini generates a valid transition."""
    client = GeminiClient()
    hydrator = GeminiTransitionHydrator(client=client, cache=None)
    
    prev_event = Event(kind="ferry", location="Auckland Ferry Terminal", ...)
    curr_event = Event(kind="drive", location="Matamata", driver="John", ...)
    
    result = hydrator._generate_transition(prev_event, curr_event)
    
    assert result is not None
    assert len(result) > 10  # Non-trivial description
    assert "ferry" in result.lower() or "matamata" in result.lower()

def test_gemini_transition_hydrator_uses_cache():
    """Test that cache is used to avoid redundant API calls."""
    client = GeminiClient()
    cache = AiCache(Path("/tmp/test_cache"))
    hydrator = GeminiTransitionHydrator(client=client, cache=cache)
    
    prev_event = Event(kind="ferry", location="Auckland Ferry Terminal", ...)
    curr_event = Event(kind="drive", location="Matamata", ...)
    
    # First call - should hit API
    result1 = hydrator._generate_transition(prev_event, curr_event)
    
    # Second call - should use cache
    result2 = hydrator._generate_transition(prev_event, curr_event)
    
    assert result1 == result2  # Same result from cache

def test_gemini_transition_hydrator_fallback():
    """Test fallback when Gemini API fails."""
    # Mock client that raises exception
    client = Mock(spec=GeminiClient)
    client.generate_text.side_effect = Exception("API error")
    
    hydrator = GeminiTransitionHydrator(
        client=client, 
        fallback_strategy="generic"
    )
    
    prev_event = Event(kind="ferry", location="Auckland", ...)
    curr_event = Event(kind="drive", location="Matamata", ...)
    
    result = hydrator._generate_transition(prev_event, curr_event)
    
    assert result == "Move from Auckland to Matamata."
```

### Integration Tests
```python
def test_nz_trip_with_ai_transitions():
    """Test full NZ trip generation with AI transitions."""
    # Use real API (mark as slow test)
    client = GeminiClient()
    cache = AiCache(Path("trips/nz_2026/.cache"))
    hydrator = GeminiTransitionHydrator(client=client, cache=cache)
    
    # Generate full itinerary
    orchestrator = PipelineOrchestrator(...)
    events = orchestrator.run()
    
    # Validate transitions
    for i, event in enumerate(events[1:], start=1):
        if event.transition_from_prev:
            # Check quality heuristics
            assert len(event.transition_from_prev) > 20
            assert not event.transition_from_prev.startswith("Move from")  # Should be richer
            print(f"Transition {i}: {event.transition_from_prev}")
```

### Quality Validation
Compare AI-generated transitions against human-written examples:
1. Generate transitions for NZ trip with AI
2. Compare to original hardcoded transitions
3. User/stakeholder review for quality, tone, accuracy
4. Iterate on prompts based on feedback

## Prompt Refinement Process

The quality of AI transitions depends on prompt engineering. Iterative refinement:

1. **Baseline Prompt** (v1): Simple instruction to generate transition
2. **Style Guidance** (v2): Add tone, length, and format constraints
3. **Context Enrichment** (v3): Include all relevant event attributes
4. **Trip-Specific Tuning** (v4): Customize for NZ, Europe, Asia, etc.
5. **Few-Shot Examples** (v5): Include 2-3 example transitions in prompt

### Few-Shot Prompt Template (Advanced)
```python
TRANSITION_PROMPT_WITH_EXAMPLES = """
{style_guidance}

Here are examples of high-quality transitions:

Example 1:
Previous: ferry, Auckland Ferry Terminal → Waiheke Island
Current: drive, Waiheke Island → Matiatia Wharf
Output: "Disembark from the ferry, walk with the group to the car pickup area, meet your rental car, load bags, and start the drive across Waiheke Island."

Example 2:
Previous: drive, Matamata
Current: lodging_checkin, Rotorua Hotel, driver: John, parking: on-site
Output: "After the scenic drive, arrive at Rotorua Hotel. John will be driving; plan to park on-site. Unload bags and head to reception for check-in."

Now generate a transition for:
Previous: {prev_kind}, {prev_location}
Current: {curr_kind}, {curr_location}, driver: {curr_driver}, parking: {curr_parking}

Output:
"""
```

## Alternative: Hybrid with Registry Override

For teams that want to keep some hardcoded transitions for critical paths:

```python
class HybridTransitionHydrator(BaseHydrator[Event]):
    """Uses critical-path registry, falls back to AI, then generic."""
    
    def __init__(
        self,
        critical_registry: TransitionRegistry,
        gemini_hydrator: GeminiTransitionHydrator
    ):
        self.critical_registry = critical_registry
        self.gemini_hydrator = gemini_hydrator
    
    def _generate_transition(self, prev_ev: Event, curr_ev: Event) -> Optional[str]:
        # 1. Try critical-path registry (e.g., airport transitions)
        description = self.critical_registry.describe(prev_ev, curr_ev)
        if description:
            return description
        
        # 2. Fall back to Gemini for everything else
        return self.gemini_hydrator._generate_transition(prev_ev, curr_ev)
```

Define only critical transitions in registry (e.g., airport, ferry, border crossings) and let AI handle the rest.

## Conclusion

The AI-powered transition approach offers significant benefits in adaptability, maintainability, and contextual richness while maintaining backward compatibility with the existing registry system. The hybrid approach provides a safe migration path with minimal risk.

**Recommendation**: Implement `GeminiTransitionHydrator` with caching and generic fallback, then test with NZ trip data. If quality meets expectations, transition to hybrid mode as the default.

## Next Steps

1. ✅ Review this proposal with stakeholders
2. ⏭️ Implement `GeminiTransitionHydrator` (est. 2-3 hours)
3. ⏭️ Add transition prompt templates (est. 1 hour)
4. ⏭️ Write unit and integration tests (est. 2 hours)
5. ⏭️ Generate NZ trip with AI transitions and validate quality (est. 1 hour)
6. ⏭️ Gather feedback and iterate on prompts (est. 1-2 hours)
7. ⏭️ Update documentation and CLI flags (est. 1 hour)

**Total estimated effort**: 8-11 hours of development time.

---

**Author**: Claude (Copilot)  
**Date**: 2026-01-14  
**Related Issue**: itingen-08j (TransitionRegistry implementation)  
**Status**: Proposal (awaiting review)
