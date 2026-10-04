# Contributing to VLP Studio

VLP Studio is research software maintained by a single author. Contributions, bug reports
and questions are welcome, and this document explains how to make them useful. It also
states the project's scope boundaries honestly, so that nobody spends effort on a change
that will not be merged.

Everything happens in one place: <https://github.com/najera-maldonado/vlp-studio>.

## Getting help

| You want to | Do this |
|-------------|---------|
| Ask how to install or use something | Open a [GitHub issue](https://github.com/najera-maldonado/vlp-studio/issues) with the `question` label, after checking [`docs/installation.md`](docs/installation.md) and [`docs/usage.md`](docs/usage.md) |
| Report a bug | Open an issue following the template below |
| Suggest a feature | Open an issue describing the scientific use case |
| Understand what actually works | Read [`ESTADO.md`](ESTADO.md) — it is the authoritative map, and it is blunt |

There is no mailing list and no chat. Issues are the only support channel, which keeps the
record public and searchable.

## Reporting a bug

Please include:

1. **What you ran**, as the exact command or API call.
2. **What you expected and what happened**, with the full error message, not a paraphrase.
3. **The output of the health endpoint**, which identifies your installation in one line:
   ```bash
   curl -s http://localhost:5000/api/health
   ```
   Most reports about gate 1 or gate 4 turn out to be a missing engine, and this shows that
   immediately.
4. **How you installed it** — Docker or a local pip install — and your Python version.
5. **The structure involved**, if the bug depends on a particular capsid, enzyme or SMILES
   string. If the structure is not in the shipped library, say where it came from.

Before reporting a scientific discrepancy, please check whether the output you are looking
at is flagged `"illustrative": true`. Gates 3 and 4 are placeholders by design, and
illustrative output disagreeing with reality is expected, not a bug. See
[`docs/usage.md`](docs/usage.md#telling-real-output-from-illustrative-output).

## Contributing code

1. **Open an issue first** for anything beyond a typo or an obvious fix. It is worth
   agreeing on the approach before you write it, especially for anything touching the
   science.
2. **Fork and branch.** Work on a branch named for the change.
3. **Keep the change small and reversible.** The project follows a deliberate
   "strangler" pattern: each commit extracts or changes one piece and leaves the Studio
   working. There is no big-rewrite commit, and pull requests that restructure several
   subsystems at once will be asked to split.
4. **Run the checks locally** before opening the pull request:
   ```bash
   cd nanocapsule-mvp
   ruff check src tests          # lint
   ruff format --check src tests # formatting
   python -m pytest -q           # 22 tests
   ```
   Continuous integration runs exactly these, plus a `compileall` pass over the other three
   engines. A pull request that fails them will not be reviewed until it passes.
5. **Add a test when you change behaviour.** Smoke tests belong in `tests/test_smoke.py` and
   should stay fast and engine-free. If your change alters a scientific number, the right
   place is `tests/test_golden_science.py`, and changing a golden value needs a written
   justification in the pull request: that is the whole point of freezing it.
6. **Describe the change in terms of the funnel.** Which gate does it affect, and does it
   change a real measurement or an illustrative placeholder?

### Code conventions

- Python 3.12. Formatting and linting are handled by `ruff`, configured in
  `nanocapsule-mvp/pyproject.toml` (line length 100, double quotes, import sorting). Do not
  hand-format against it.
- Keep the layering: `src/web/app.py` is a thin HTTP adapter and contains no science;
  orchestration goes in `src/services/<gate>.py`; domain logic in `src/core/`. Adding a gate
  means adding a service module and re-exporting it from the facade.
- Never hard-code a scientific parameter. Everything tunable lives in
  `config/default.yaml`.
- Use `src/core/paths.py` for filesystem locations rather than relative paths.
- Mark placeholder output with `"illustrative": true` in the response, and give real
  measurements a `source` field naming the engine. This convention is what lets users trust
  the output at all, so it is not optional.
- New documentation is written in English. The internal working documents (`ESTADO.md`,
  `PENDIENTES.md`, `BITACORA.md`) stay in Spanish; they are the author's decision log, not
  user-facing docs.

### What the test suite does and does not cover

Worth knowing before you trust a green CI run. The tests validate **wiring and shape**: that
the application boots, that every route responds, that service functions return the expected
structure, and that a handful of frozen numerical results have not moved. They deliberately
**do not** exercise the slow binary engines — HOLE, PyMOL, Vina, Packmol — which means CI
passing does not prove that a change to engine invocation still works. Changes in that area
need to be exercised by hand, and the pull request should say how you did it.

## Scope boundaries

These are firm, and knowing them in advance saves everyone time.

**Third-party engines are called, never forked.** HOLE, AutoDock Vina, idock, AMBER,
GROMACS, Open Babel and the SIRAH force field are invoked as external processes. The project
will not vendor, patch or reimplement them. This is both a licensing position and a
maintenance one.

**Non-redistributable engines stay user-supplied.** HOLE and NetMHCIIpan carry academic
licences that forbid redistribution, so they will not be bundled into the Docker image or
the repository, however convenient that would be.

**Open scientific decisions are the author's to make.** Three issues are recorded as
deliberately unresolved in [`ESTADO.md`](ESTADO.md) §4b, and pull requests that resolve them
unilaterally will not be merged, because each needs a simulation to be run before a choice is
defensible:

- `CIENCIA-1` — the sign of the ±1 Å internal-radius safety margin.
- `CIENCIA-2` — coarse-grained versus all-atom resolution of the substrate system.
- `CIENCIA-3` — PackMan's heating protocol.

Reporting them more clearly, or adding a test that pins current behaviour, is welcome.

**No molecular dynamics result is validated yet.** Gate 4's simulation has never been run.
Please do not add documentation, figures or claims that imply otherwise.

**Deferred by design, not forgotten:** cloud deployment, multi-user support, a job queue and
security hardening. They become relevant when someone other than the author runs a shared
instance. The Studio is a single-user local server today and is documented as such.

## Licensing of contributions

The project's own code is licensed under the **GNU AGPLv3 or later**. By contributing you
agree that your contribution is licensed on the same terms. If you add a dependency, record
it in [`THIRD_PARTY.md`](THIRD_PARTY.md) with its licence, and check that the licence is
compatible with AGPLv3.

## Code of conduct

Be straightforward and civil. Critique the code, the data and the reasoning, not the person.
Scientific disagreement is welcome and expected; personal hostility is not, and will be
moderated by the maintainer.
