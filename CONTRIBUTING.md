# Contributing to Kurogane K-7

Thanks for helping. A few rules keep a hardware repo sane.

## Before you start

- Open an issue first for anything bigger than a typo, so work isn't duplicated.
- New DeckBus modules: use the *Module proposal* issue template and follow `docs/deckbus_v1.md`.

## Hardware changes

- KiCad 8 or newer. One logical change per pull request.
- KiCad files don't merge: say in the issue which board you're editing so two people don't edit it at once.
- Run ERC and DRC before opening the PR and paste the summary into the PR description.
- Changing a connector, pinout or board outline? Update `docs/`, `enclosure/kurogane_k7.scad` and `bom/BOM.csv` in the same PR.
- Don't commit Gerbers or STLs; they go in GitHub Releases.

## Software changes

- Python 3.11+, standard library where possible. Keep services small and documented.

## Commit messages

`area: short summary`, for example `mainboard: move DSI FPC 2 mm left` or `deckbus: add GNSS module`.

## Releases

Tag hardware revisions `k7-revA`, `k7-revB`, ... and attach Gerbers, BOM, pick-and-place and STLs to the Release.
