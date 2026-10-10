<!-- © 2026 shear559 · fabius · reference depth for skills/fabius-decor/SKILL.md -->

# Geospatial evidence — show where, when and how it is known

Use for maps and spatial dashboards. Decor owns visual meaning; `fabius-disciplina` feed implementation, `fabius-scientia` validity, `fabius-cohors` acting agents. No globe, feed or MCP server is bundled.

## Choose the view from the question

Name region, time window, entity class, decision and precision. Tables compare exact values; 2D maps show geography; globes serve questions where 3D matters. Cinematic framing adds no evidence.

Each layer declares source/attribution, coverage, coordinate system, units, altitude datum, observation/retrieval times, cadence, completeness and age limit. Distinguish observation, delayed playback, interpolation, propagated orbits, simulation and estimated geometry. Missing metadata stays unknown.

## Make temporal truth visible

| State | What the reader must see |
|---|---|
| Fresh observation | Its source time and the declared coverage |
| Delayed or interpolated | The playback time and method; movement is not another measurement |
| Propagated or modeled | Input epoch, model and limitations; never labelled live observation |
| Healthy empty response | No observations within the stated extent/window, with successful feed status |
| Partial or truncated | Coverage or result limit that makes the visible count incomplete |
| Failed or stale feed | Failure or age alongside retained markers; last known positions stay visibly old |

Keep observation/event time, retrieval time and render time separate. A freshly fetched or repainted view does not advance the source observation time; include all three in inspection/export evidence, with unknown times explicit. Track transport health separately from row count. Empty maps cannot prove absence; cached maps cannot prove feed health. Agent answers inherit these qualifications. Smooth animation and current clocks cannot establish freshness. Thermal/night-vision shaders are styling, not measurements.

## Preserve spatial meaning

- Validate latitude/longitude order, degree/radian conversions, speed units and time zones at ingestion. Name whether height is above terrain, mean sea level or an ellipsoid before combining layers. Unknown datum means unresolved placement, not a guessed conversion.
- Project real heading into the current camera view; rotating the camera must not change the entity's reported course. Bound interpolation and extrapolation in time; stop or label prediction beyond that bound.
- Check antimeridian crossings, poles and missing heights. Cluster dense marks with counts and a way to inspect members. Preserve selected entities and distinguish an off-screen target from a removed one.
- Let color encode a stable category or state; use shape/text as well. Keep attribution, units, age and selected-item facts readable at mobile width. Provide keyboard-accessible selection and a textual result view.

## Prove meaning, then polish

Exercise a known coordinate and datum, a dated fixture, healthy-empty and failed feeds, partial coverage, an old cached snapshot and reconnect. Verify disabling a layer cancels or rejects its late response. Assert displayed positions, timestamps, counts and state labels against those fixtures; inspect the rendered mobile view and console. Record any unverified provider separately from local fixture coverage.

A shared URL may restore the view with different data. Preserve view state plus authorized dated snapshots or source identifiers for reproducibility, and attribution in exports. Software licensing does not grant rights to imagery, models, footage or data; inspect their terms separately.

An acting agent reads current scene context, uses bounded typed actions and confirms the resulting scene before announcing success. Keep public spatial analysis scoped to events, infrastructure and assets; never infer a person's identity or intent from a marker. An exploratory map is not a navigation or emergency-response instrument. Chart grammar → [visualization.md](visualization.md).

Informed by **God's Eye View** (Bilawal Sidhu, MIT code; separate data/asset terms), commit `591f299d11f38a612629a274463196d57ae3862e`, inspected 2026-10-10 — temporal state, healthy-empty versus degraded feeds and attribution, re-expressed in Fabius's own workflow; no upstream code, feeds, models or media bundled. See credits/README.md.
