"""Prompt loading: versioned Markdown templates with YAML frontmatter.

Layout — one directory per prompt, one file per version, eval fixtures
alongside (required, per ADR-0006's eval discipline):

    templates/
    └── extract_problems/
        ├── v1.md
        ├── v2.md
        └── evals/
            └── cases.yaml

Each template file is YAML frontmatter + a Jinja2 body:

    ---
    name: extract_problems
    version: 2
    outcome: <what this prompt is meant to achieve>
    role: <the role the model assumes>
    objective: <the concrete task>
    input_schema: ProblemExtractionInput
    output_schema: ProblemExtractionOutput
    validation_rules:
      - <rule the output must satisfy>
    ---
    Template body with {{ variables }}.

Design notes:
- `input_schema`/`output_schema` are schema *names*, not imports —
  binding a name to a Pydantic class happens at the agent layer, which
  is allowed to import both `schemas/` and `prompts/`. This module
  depends only on `core` (enforced by import-linter).
- Jinja2 with StrictUndefined, no autoescape (these are text prompts,
  not HTML). Single braces pass through untouched, so JSON examples in
  prompt bodies don't need escaping.
- Templates are trusted, version-controlled repo files; only the
  *variables* are runtime data, so a sandboxed Jinja environment is
  unnecessary.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml
from jinja2 import Environment, StrictUndefined, meta
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ai_oip.core.exceptions import PromptError, PromptNotFoundError, PromptRenderError

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL)
_VERSION_FILE_RE = re.compile(r"\Av(\d+)\.md\Z")

_jinja_env = Environment(undefined=StrictUndefined, autoescape=False)  # noqa: S701 — text, not HTML


class PromptMetadata(BaseModel):
    """The frontmatter every prompt must carry (see CLAUDE.md, Prompt Management)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    version: int = Field(ge=1)
    outcome: str
    role: str
    objective: str
    input_schema: str
    output_schema: str
    validation_rules: list[str]


class PromptEvalCase(BaseModel):
    """One golden eval fixture for a prompt (ADR-0006).

    `expected` is deliberately loose at this milestone: it holds
    expected-property assertions whose semantics the evaluation runner
    (Agent Framework & Evaluation Harness milestone) will define and
    enforce. What M4 guarantees is that fixtures exist, parse, and
    carry variables that actually render against the template.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    variables: dict[str, object]
    expected: dict[str, object]


@dataclass(frozen=True)
class PromptTemplate:
    """A loaded, validated prompt version, ready to render."""

    metadata: PromptMetadata
    body: str
    variables: frozenset[str]

    def render(self, **variables: object) -> str:
        """Render the template with exactly its declared variables.

        Raises:
            PromptRenderError: if any declared variable is missing or
                any unexpected variable is supplied.
        """
        provided = set(variables)
        missing = self.variables - provided
        extra = provided - self.variables
        if missing or extra:
            raise PromptRenderError(
                f"Cannot render prompt {self.metadata.name!r} v{self.metadata.version}: "
                f"missing variables {sorted(missing)}, unexpected variables {sorted(extra)}"
            )
        return _jinja_env.from_string(self.body).render(**variables)


class PromptLoader:
    """Loads versioned prompt templates and their eval fixtures from disk.

    Defaults to the packaged `templates/` directory next to this module;
    tests point it at fixture directories instead.
    """

    def __init__(self, base_path: Path | None = None) -> None:
        default_path = Path(__file__).parent / "templates"
        self._base_path = base_path if base_path is not None else default_path

    def load(self, name: str, version: int | None = None) -> PromptTemplate:
        """Load a prompt by name — a specific version, or the latest.

        Raises:
            PromptNotFoundError: unknown prompt name or version.
            PromptError: malformed frontmatter, or frontmatter that
                disagrees with the directory/file it lives in.
        """
        versions = self._available_versions(name)
        resolved = max(versions) if version is None else version
        if resolved not in versions:
            raise PromptNotFoundError(
                f"Prompt {name!r} has no version {resolved} (available: {sorted(versions)})"
            )
        path = self._base_path / name / f"v{resolved}.md"
        return self._parse(path, expected_name=name, expected_version=resolved)

    def load_eval_cases(self, name: str) -> list[PromptEvalCase]:
        """Load the eval fixtures that every prompt must ship with.

        Raises:
            PromptNotFoundError: the fixtures file doesn't exist — this
                is an error, not an empty list, because "no concrete
                agent ships without an eval suite" is a quality gate
                (ADR-0006), and a silently-empty suite would pass it.
            PromptError: the fixtures file is malformed.
        """
        path = self._base_path / name / "evals" / "cases.yaml"
        if not path.is_file():
            raise PromptNotFoundError(
                f"Prompt {name!r} has no eval fixtures at {path} — every prompt "
                "must ship with eval cases (see ADR-0006)"
            )
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise PromptError(f"Eval fixtures for {name!r} are not valid YAML: {exc}") from exc
        if not isinstance(raw, list) or not raw:
            raise PromptError(f"Eval fixtures for {name!r} must be a non-empty list of cases")
        try:
            return [PromptEvalCase(**case) for case in raw]
        except (ValidationError, TypeError) as exc:
            raise PromptError(f"Eval fixtures for {name!r} are malformed: {exc}") from exc

    def _available_versions(self, name: str) -> set[int]:
        prompt_dir = self._base_path / name
        if not prompt_dir.is_dir():
            raise PromptNotFoundError(f"No prompt named {name!r} under {self._base_path}")
        versions = {
            int(match.group(1))
            for entry in prompt_dir.iterdir()
            if (match := _VERSION_FILE_RE.match(entry.name))
        }
        if not versions:
            raise PromptNotFoundError(f"Prompt {name!r} has no version files (v<N>.md)")
        return versions

    def _parse(self, path: Path, *, expected_name: str, expected_version: int) -> PromptTemplate:
        match = _FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
        if match is None:
            raise PromptError(f"{path} has no YAML frontmatter block (--- ... ---)")
        try:
            raw = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            raise PromptError(f"{path} frontmatter is not valid YAML: {exc}") from exc
        if not isinstance(raw, dict):
            raise PromptError(f"{path} frontmatter must be a YAML mapping")
        try:
            metadata = PromptMetadata(**raw)
        except ValidationError as exc:
            raise PromptError(f"{path} frontmatter is invalid: {exc}") from exc
        if metadata.name != expected_name or metadata.version != expected_version:
            raise PromptError(
                f"{path} frontmatter says name={metadata.name!r} v{metadata.version}, "
                f"but the file lives at {expected_name!r} v{expected_version} — "
                "frontmatter and location must agree"
            )
        body = match.group(2).strip()
        try:
            declared = meta.find_undeclared_variables(_jinja_env.parse(body))
        except Exception as exc:
            raise PromptError(f"{path} body is not a valid template: {exc}") from exc
        return PromptTemplate(metadata=metadata, body=body, variables=frozenset(declared))
