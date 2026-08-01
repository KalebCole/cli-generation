# Résumé inputs

## Recommended project entry

**CLI Generation v2** | Python, Go, browser automation, HAR, API reverse engineering

- Rebuilt an agentic CLI pipeline around a clean reconnaissance-to-generation boundary, turning undocumented web workflows into validated Printing Press API specs with resumable evidence manifests.
- Automated browser traffic capture, endpoint normalization, auth and transport classification, and human checkpoints limited to flow approval, login, and sensitive actions.
- Added semantic quality gates that caught a malformed Algolia request-body model accepted by generator dry-run validation; proved the success path by generating, testing, security-scanning, compiling, and executing a live Open-Meteo CLI.

## Short version

- Built a website-to-CLI reconnaissance pipeline that converts browser workflows into validated API specs, rejects syntactically valid but unusable models, and hands clean contracts to a Go CLI generator.

## Skills supported by the evidence

`Python` · `Go` · `API reverse engineering` · `Browser automation` · `HAR analysis` · `CLI design` · `Test-driven development` · `Security validation` · `Agentic workflows`

## Interview proof points

1. **Boundary decision:** Removed a weaker duplicate generator and made Printing Press the generation engine. The project now owns the missing intake layer.
2. **Failure caught:** A real HN Algolia capture passed schema validation but encoded whole JSON documents as argument names. Added a regression test and semantic gate before generation.
3. **End-to-end proof:** Captured Open-Meteo requests in a browser, produced a one-endpoint spec, generated Go, passed the suite, cleared reachable vulnerabilities after an upstream dependency update, and returned live Seattle weather data.
