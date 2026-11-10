# PokeLua: automatic upstream synchronization and releases

Mirror of [Real96/PokeLua](https://github.com/Real96/PokeLua), upstream `main` branch.

## How it works

- Every four hours: GitHub Actions cron `13 */4 * * *` (UTC; GitHub schedules can be delayed).
- Also runs once when `.github/workflows/sync-upstream.yml` is first added or changed.
- Compares the upstream Git commit and merges new commits into mirror `main`, without force-pushing. Real source conflicts fail closed.
- Local `.github/workflows` are preserved when synchronizing to avoid GitHub App workflow-file permission errors.
- Publishes one GitHub prerelease named `sync-<upstream-commit-short-SHA>` per new upstream commit, with no duplicate packages.
- First-time setup also publishes a baseline package for the current upstream commit if no release exists yet.
- Release assets: `PokeLua-sync-<SHA>-scripts.zip` and `SHA256SUMS.txt`.
- The ZIP contains tracked Lua scripts, LICENSE, and README; it excludes the mirror's GitHub Actions files.
- No compilation is needed: scripts are consumed directly by supported emulators.
- GitHub Actions `contents: write` is used; no custom token or external secrets are required.

Manual retry: Actions > **Sync upstream and publish** > **Run workflow**. A run skips publication when the snapshot already exists.

See [Actions](https://github.com/969981/PokeLua/actions/workflows/sync-upstream.yml) and [Releases](https://github.com/969981/PokeLua/releases).
