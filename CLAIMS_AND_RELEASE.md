# Environmental claims and release evidence

Reviewed base: `5e3319a4b515c198e7f2356618fb071d7df1e9ac`.

## Claim boundaries (item 25)

| Evidence category | Defensible wording | Evidence required |
|---|---|---|
| Software behaviour | The controller responds to simulated movement and tested sensor faults. | Named tests and recorded outcomes; only claim the cases exercised. |
| Simulated impact | In [scenario], over [duration] seconds, modelled lamp-only energy changed from [baseline] to [adaptive] kWh ([percentage]%). | Same-run impact CSV and metadata. Use N/A for zero baseline and preserve negative savings. |
| Simulated habitat lighting | Modelled artificial illuminance/exposure at configured habitat points was [value and units], for [nighttime/full-run scope]. | Habitat summary and point CSVs. Equal point weighting is not an area survey. |
| Intended benefit | NightWise aims to reduce unnecessary lighting and habitat-side artificial light. | An objective, not a demonstrated environmental outcome. |
| Expected real-world benefit | Lower unnecessary lighting may reduce environmental disturbance; field validation is needed. | Relevant background research. Research does not validate this prototype's numerical outputs. |
| Unsupported outcome | Wildlife recovery, improved pedestrian safety, improved stargazing, measured township savings, or avoided carbon emissions. | Not established by this demo. Do not present these as results. |

Use this slide/video footer: **Simulation estimates: lamp-only energy and artificial illuminance. No field measurements; pedestrian safety, ecological recovery, and night-sky improvement are unvalidated.**

Dashboard and repository documentation were reviewed. Slides, spoken script, and video were not supplied and remain unreviewed. Check their titles, charts, narration, captions, and closing claims against this table. The corridor has no installed lamps but may receive modelled spill. Lux exposure is not a species-specific biological dose.

## Traceability (item 26)

`run_metadata.json` retains scenario routes/windows, environment/measurement points, controller configuration, model version, baseline, interval convention, assumptions, and limitations. It now records UTC generation time, full base commit, worktree status, source/configuration SHA-256 hashes, runtime/dependency versions, actual duration, observed step durations, and CSV hashes.

`time_step_s` retains the configured scalar; `observed_interval_durations_s` separately records the actual interval lengths. Source hashes distinguish local modifications from the base commit. A nonempty worktree status is not a clean release. The metadata excludes its own hash to avoid self-reference.

Release sequence:

1. Apply changes and commit code/configuration. Record that source commit.
2. Run `python -m unittest discover -v` and save the command/output and dependency versions.
3. Run `python export_results.py --scenario all` from that source revision.
4. Check every scenario metadata file and CSV hashes. Preserve the source checkout alongside results if local changes exist.
5. Use only those exports for the results table, slides, and recording. Label the baseline as fixed zone-cap lighting, with identical fixtures/shielding and scheduled daytime off. Do not claim equivalent visibility has been established.
6. Archive the results and test log together. If committing generated outputs afterward, record both the source commit and artifact commit; do not rewrite the source commit field to the later artifact commit.

Energy and exposure conclusions apply only to each exported run. Do not extrapolate a 120-second scenario to annual savings without an explicit usage model. No new real-world environmental result is established by this review.
