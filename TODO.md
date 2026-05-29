# TODO — pyrateyourmusic

## Gaps

- [ ] No CI workflows — `.github/workflows/` is intentionally absent. Add the
  standard `OpenVoiceOS/gh-automations` reusable workflows (build-tests,
  coverage, license-check, release_workflow, publish_stable), referenced at
  `@dev`.
- [ ] Release-detail validation — the `_parse.parse_release_page` selectors
  (`.album_title`, `table.album_info`, `#tracks`) are validated against a
  synthetic fixture only; release detail pages 503 from datacenter IPs. Confirm
  against live markup once a residential exit is available, and capture a real
  fixture to replace `tests/fixtures/release.html`.
- [ ] Chart pagination — `get_chart` fetches a single page; add multi-page
  walking over RYM's `/N/` chart URL suffixes.
- [ ] Descriptor coverage — descriptors render on detail pages and some chart
  variants only; confirm which chart paths expose the descriptor line.
- [ ] No lint/typecheck config — add ruff/mypy (the code is fully type-hinted).

## Code TODOs

None found.
