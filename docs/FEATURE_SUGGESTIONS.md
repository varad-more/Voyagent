# Voyagent Feature Suggestions (Post-MVP)

This is a prioritized backlog of high-impact features beyond the current core planner.

## Recommended next 5 for Voyagent specifically
1. Live replan for weather and closures
2. Group preference conflict resolution with voting
3. Confidence score per day plan with warning surfacing
4. Budget guardrails with automatic substitutions
5. Offline itinerary pack with shareable exports

## P0 (High Impact, Near-term)

1. **Live Replan Button**
   - One-click “Replan this day” based on weather, closures, or delays.
   - Re-optimizes only affected blocks, not full trip.

2. **Hard Constraint Layer**
   - Explicit constraints: wheelchair access, kid-friendly, low walking, vegetarian-only, no alcohol, etc.
   - Planner must treat these as non-negotiable.

3. **Trip Confidence Score**
   - Score itinerary feasibility (time realism, venue confidence, transit slack).
   - Show warnings where confidence is low.

4. **Duplicate and Closure Detection**
   - Detect duplicate recommendations across days.
   - Mark potential closure risk with confidence tags.

5. **Export Quality Upgrades**
   - ICS + printable PDF + map snapshot per day.

---

## P1 (Growth + Retention)

6. **Group Decision Engine**
   - Each traveler sets preferences.
   - System computes compromise itinerary + conflict explanation.

7. **Budget Guardrails**
   - Daily and trip-level spend caps.
   - Auto substitutions when over budget.

8. **Saved Templates / Modes**
   - “Weekend sprint”, “Slow travel”, “Food-first”, “Family mode”, “Workation”.

9. **Trip Version History**
   - Full diff view between itinerary versions.
   - Rollback to prior plan.

10. **Offline Itinerary Pack**
   - Cached maps + stops + notes for low/no connectivity scenarios.

---

## P2 (Differentiation)

11. **Inbox Import**
   - Parse flight/hotel confirmations from forwarded email.
   - Auto-populate trip timeline.

12. **Safety Layer**
   - Neighborhood safety context and late-night caution alerts.

13. **Visa + Entry Assistant**
   - Passport-based entry checklist and lead-time reminders.

14. **Packing Assistant**
   - Dynamic packing list from weather, activities, and duration.

15. **Local Gems Mode**
   - Reduce tourist-heavy results; prioritize local and niche spots.

---

## AI/Platform Enhancements

16. **Provider Abstraction + Routing**
   - Route requests by task type (cheap model for extraction, stronger model for planning).

17. **Prompt/Policy Versioning**
   - Track prompt versions and compare quality per version.

18. **Evaluation Harness**
   - Offline benchmark set for itinerary quality and consistency.

19. **A/B Prompt Experiments**
   - Controlled experiments to improve itinerary quality.

20. **Cost-Aware Planner**
   - Auto-adjust depth/detail based on token budget and user tier.

---

## Suggested Priority Order

- Start with: **1, 2, 3, 6, 7**
- Then: **9, 10, 11**
- Then differentiation: **12, 13, 14, 15**

This sequence gives the best mix of user trust, retention, and product moat.
