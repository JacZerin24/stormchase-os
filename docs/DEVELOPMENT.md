# Development, CI and Deployment

## Workspace

`web/` is the independently buildable v0.1 application. Future `api/`, `pipelines/`, `research/` and cross-cutting `tests/` should be added only when functional work exists. Avoid empty placeholder modules.

Node.js 22+, npm. In `web/`: `npm install`, `npm run dev`, `npm run typecheck`, `npm test`, `npm run build`.

## Branch/review process

- Create a short-lived `feat/*` or `fix/*` branch.
- Commit a narrow reviewable change and open a PR to `main`.
- Confirm `Web CI` completes on the PR. Review diff and coverage.
- Merge only after checks and human review. Main triggers `Deploy Pages`.
- Inspect workflow logs and live URL; document browser smoke test separately.
- Enable branch protection/rulesets on `main` once checks are created.

## Enable GitHub Pages (repository owner)

1. Navigate to **Settings → Pages**.
2. Under **Build and deployment**, choose **Source: GitHub Actions**.
3. In **Settings → Actions → General**, permit actions required by the repository if not already permitted.
4. Merge a passing PR to `main`; watch **Actions → Deploy Pages** and the `github-pages` environment.
5. Visit https://jaczerin24.github.io/stormchase-os/ and check navigation, mobile layout, live SPC/NWS overlays, timestamps, layer toggles, and unavailable states.
6. Configure default branch protection/ruleset requiring the `Web CI / check` status after it has run, if available to your repository plan.

GitHub Pages requires base path `/stormchase-os/` for this project repository; the Vite build sets that in CI using `GITHUB_PAGES=true`.

## Data-source QA

At least once per release inspect provider data and dates, API rate/CORS behavior, malformed response behavior, polygon CRS, warning null geometries, correct UTC labels, and source links. Browser request headers cannot spoof User-Agent. Use the official NWS site for safety-critical alerts.

## GitHub Pages caveats

Pages is static hosting: no authoritative alert delivery, no server-side cron/reliable workers. Public repository code must not contain API keys. Use the repository's Secrets/Variables UI for future secret backend jobs.

## Dependency reproducibility and known installer issue

Initial PR CI failed at npm installation under npm 10 with `Cannot read properties of null (reading 'edgesOut')`; a documented optional-peer resolver defect affects recent Vitest packages. `web/.npmrc` temporarily sets `legacy-peer-deps=true`; GitHub Actions CI run #2 subsequently passed typecheck, all 7 tests and production build. This is a workaround, not evidence that all dependency security or peer-compatibility issues are resolved. Generate and commit `web/package-lock.json`, move workflows to `npm ci`, and reassess the workaround after dependency pinning. See issue #2.
