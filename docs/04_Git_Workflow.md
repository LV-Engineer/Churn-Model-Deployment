# Git Workflow

Goal: keep the **full history** of the project (many small commits that tell the story of the work), not one big commit at the end. Recruiters can open the commit log and see how the project grew: API, tests, typing, Docker, CI, drift monitoring, README.

## 1. Core principles

- **Commit early, commit often.** One commit = one logical change that can be described in one line.
- **Never rewrite published history.** No `git push --force` on `main`, no squashing everything into one commit. History is part of the portfolio.
- **The repo should work at every commit.** Do not commit a half-broken state to `main`.
- **Commit code, not artifacts.** Data, models and the virtual environment are reproducible from code and seeds (see `.gitignore`).

## 2. Branching

`main` is always in a working state. Each step of `03_Work_Plan.md` gets a short branch named `<type>/<short-name>` (lowercase, words separated by hyphens). The `<type>` is the same set of prefixes as in commit messages (see section 3).

| Plan step | Suggested branch |
| --- | --- |
| 1 Export model and pipeline | `feat/model-export` |
| 2 App skeleton and stubs | `chore/app-skeleton` |
| 3 Docker and PostgreSQL | `feat/docker` |
| 4 Implement the stubs | `feat/api` |
| 5 pytest tests | `test/api-tests` |
| 6 Type hints and mypy | `chore/mypy` |
| 7 GitHub Actions | `chore/ci` |
| 8 Drift monitoring | `feat/drift-monitoring` |
| 9 MLflow, DVC (optional) | `feat/mlflow-dvc` |
| 10 Redis, Grafana (optional) | `feat/cache-dashboard` |
| 11 README | `docs/final-readme` |

Other examples: `fix/schema-validation`, `chore/pin-requirements`, `refactor/split-routers`.

Flow for each step. `main` requires a Pull Request, so the merge happens on GitHub, not locally:

```bash
git switch main
git pull
git switch -c feat/api               # create the step branch
# ... work, several commits ...
git push -u origin feat/api          # push the branch to GitHub
```

Then on GitHub: open a Pull Request from the branch into `main` and merge it with **Create a merge commit**. After that:

```bash
git switch main
git pull                             # get the merge commit
git branch -d feat/api               # optional cleanup
```

Why a merge commit (the `--no-ff` idea): the graph shows "this group of commits was the API step". Squash or rebase merges would remove that structure, so only **Merge** is allowed as the merge method.

A Pull Request also leaves a readable record of the decisions, even for a solo project.

### Protection on GitHub

A ruleset on the default branch (`main`) enables:

- **Restrict deletions** and **Block force pushes**: the history of `main` cannot be rewritten or removed.
- **Require a pull request before merging** (0 required approvals, it is a solo project): nothing reaches `main` by a direct push, including an accidental push from a local branch.

Feature branches are not protected and can be deleted freely after merging.

## 3. Commit messages

English, imperative mood, [Conventional Commits](https://www.conventionalcommits.org/) prefixes:

| Prefix | Use for |
| --- | --- |
| `feat:` | new functionality (an endpoint, a schema, a monitoring script) |
| `fix:` | a bug fix |
| `docs:` | README, brief, experiment log, work plan |
| `refactor:` | code restructuring without behavior change |
| `chore:` | environment, dependencies, `.gitignore`, CI, Docker |
| `test:` | tests |

Examples:

```
feat: add /predict endpoint with Pydantic request schema
fix: return 422 for negative tenure
test: add invalid input cases for /predict
docs: log experiment 2 (latency in Docker)
chore: pin fastapi and scikit-learn versions
```

Keep the first line under about 70 characters. Add a body only when the "why" is not obvious.

## 4. What to commit and when

Commit after each of these moments:

- a new module/script/endpoint works;
- a check or measurement finished: **code and the `02_Experiment_Log.md` row together**, or in two consecutive commits;
- a decision changed (threshold, schema, base image): commit the change plus the docs update;
- a plan step finished: tick it in `03_Work_Plan.md` (`docs: complete step 4`).

Do **not** commit:

- `.venv/`, `data/`, `models/`, `*.pkl`, `*.joblib`, `.env` (already in `.gitignore`);
- large generated reports (keep small ones in `reports/` only if the README needs them);
- secrets, tokens, personal data.

## 5. Review before every commit

```bash
git status          # what changed
git diff            # exactly what changed (unstaged)
git add <files>     # stage deliberately, avoid blind `git add .`
git diff --staged   # what is about to be committed
git commit -m "feat: ..."
```

Staging files selectively lets you split a messy working session into several clean commits (`git add -p` for parts of a file).

## 6. Tags (milestones)

Mark important points so they are easy to find:

```bash
git tag -a v0.1-api -m "API done: /predict and /health"
git tag -a v1.0 -m "Project complete"
git push --tags
```

Suggested tags: `v0.1-api`, `v0.2-docker-ci`, `v0.3-monitoring`, `v1.0`.

## 7. Undoing mistakes safely

| Situation | Command |
| --- | --- |
| Unstage a file | `git restore --staged <file>` |
| Discard local edits in a file | `git restore <file>` (destructive, edits are lost) |
| Fix the last **unpushed** commit message | `git commit --amend` |
| Undo a **pushed** commit | `git revert <hash>` (adds a new commit, history stays) |
| Look at history | `git log --oneline --graph --decorate` |

Rule: `amend`/`rebase` only for commits that are not pushed yet. After a push use `revert`.

## 8. Checklist for a healthy history

- [ ] more than 30 meaningful commits by the end of the project
- [ ] each plan step visible as a branch/merge
- [ ] commit messages follow the convention
- [ ] no data, models or secrets in history
- [ ] tags at the main milestones
- [ ] the experiment log and the work plan are updated in commits alongside the code
