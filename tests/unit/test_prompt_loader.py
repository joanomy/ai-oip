"""Tests for the prompt loader.

Happy paths run against committed fixtures under tests/fixtures/prompts;
malformed-template cases build throwaway prompts in tmp_path rather than
committing deliberately broken files.
"""

from pathlib import Path

import pytest

from ai_oip.core.exceptions import PromptError, PromptNotFoundError, PromptRenderError
from ai_oip.prompts import PromptLoader, PromptTemplate

FIXTURES = Path(__file__).parent.parent / "fixtures" / "prompts"


@pytest.fixture
def loader() -> PromptLoader:
    return PromptLoader(base_path=FIXTURES)


def _write_prompt(base: Path, name: str, filename: str, content: str) -> Path:
    prompt_dir = base / name
    prompt_dir.mkdir(parents=True, exist_ok=True)
    path = prompt_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


VALID_BODY = "Hello {{ person_name }}."


def _frontmatter(name: str = "tmp_prompt", version: int = 1, extra: str = "") -> str:
    return (
        "---\n"
        f"name: {name}\n"
        f"version: {version}\n"
        "outcome: test\n"
        "role: test\n"
        "objective: test\n"
        "input_schema: In\n"
        "output_schema: Out\n"
        "validation_rules:\n"
        "  - test\n"
        f"{extra}"
        "---\n"
    )


class TestLoading:
    def test_load_latest_resolves_highest_version(self, loader: PromptLoader) -> None:
        prompt = loader.load("demo_greeting")

        assert prompt.metadata.version == 2

    def test_load_specific_version(self, loader: PromptLoader) -> None:
        prompt = loader.load("demo_greeting", version=1)

        assert prompt.metadata.version == 1
        assert "tone" not in prompt.variables

    def test_metadata_carries_all_required_fields(self, loader: PromptLoader) -> None:
        meta = loader.load("demo_greeting").metadata

        assert meta.name == "demo_greeting"
        assert meta.outcome
        assert meta.role
        assert meta.objective
        assert meta.input_schema == "DemoGreetingInput"
        assert meta.output_schema == "DemoGreetingOutput"
        assert meta.validation_rules

    def test_variables_extracted_from_body(self, loader: PromptLoader) -> None:
        prompt = loader.load("demo_greeting", version=2)

        assert prompt.variables == {"person_name", "tone"}

    def test_unknown_prompt_name_raises(self, loader: PromptLoader) -> None:
        with pytest.raises(PromptNotFoundError, match="No prompt named"):
            loader.load("does_not_exist")

    def test_unknown_version_raises(self, loader: PromptLoader) -> None:
        with pytest.raises(PromptNotFoundError, match="no version 99"):
            loader.load("demo_greeting", version=99)

    def test_prompt_dir_without_version_files_raises(self, tmp_path: Path) -> None:
        (tmp_path / "empty_prompt").mkdir()

        with pytest.raises(PromptNotFoundError, match="no version files"):
            PromptLoader(base_path=tmp_path).load("empty_prompt")


class TestRendering:
    def test_render_substitutes_variables_and_preserves_json_braces(
        self, loader: PromptLoader
    ) -> None:
        prompt = loader.load("demo_greeting", version=2)

        rendered = prompt.render(person_name="Ada", tone="warm")

        assert "Greet Ada in exactly one line, using a warm tone." in rendered
        assert '{"greeting": "<your greeting>"}' in rendered

    def test_render_with_missing_variable_raises(self, loader: PromptLoader) -> None:
        prompt = loader.load("demo_greeting", version=2)

        with pytest.raises(PromptRenderError, match=r"missing variables \['tone'\]"):
            prompt.render(person_name="Ada")

    def test_render_with_unexpected_variable_raises(self, loader: PromptLoader) -> None:
        prompt = loader.load("demo_greeting", version=1)

        with pytest.raises(PromptRenderError, match=r"unexpected variables \['tone'\]"):
            prompt.render(person_name="Ada", tone="warm")


class TestValidation:
    def test_missing_frontmatter_raises(self, tmp_path: Path) -> None:
        _write_prompt(tmp_path, "tmp_prompt", "v1.md", "no frontmatter here")

        with pytest.raises(PromptError, match="no YAML frontmatter"):
            PromptLoader(base_path=tmp_path).load("tmp_prompt")

    def test_non_mapping_frontmatter_raises(self, tmp_path: Path) -> None:
        _write_prompt(tmp_path, "tmp_prompt", "v1.md", "---\n- just\n- a list\n---\nbody")

        with pytest.raises(PromptError, match="must be a YAML mapping"):
            PromptLoader(base_path=tmp_path).load("tmp_prompt")

    def test_invalid_yaml_frontmatter_raises(self, tmp_path: Path) -> None:
        _write_prompt(tmp_path, "tmp_prompt", "v1.md", "---\nname: [unclosed\n---\nbody")

        with pytest.raises(PromptError, match="not valid YAML"):
            PromptLoader(base_path=tmp_path).load("tmp_prompt")

    def test_missing_required_field_raises(self, tmp_path: Path) -> None:
        content = "---\nname: tmp_prompt\nversion: 1\n---\n" + VALID_BODY
        _write_prompt(tmp_path, "tmp_prompt", "v1.md", content)

        with pytest.raises(PromptError, match="frontmatter is invalid"):
            PromptLoader(base_path=tmp_path).load("tmp_prompt")

    def test_name_mismatch_between_frontmatter_and_directory_raises(self, tmp_path: Path) -> None:
        content = _frontmatter(name="other_name") + VALID_BODY
        _write_prompt(tmp_path, "tmp_prompt", "v1.md", content)

        with pytest.raises(PromptError, match="must agree"):
            PromptLoader(base_path=tmp_path).load("tmp_prompt")

    def test_version_mismatch_between_frontmatter_and_filename_raises(self, tmp_path: Path) -> None:
        content = _frontmatter(version=7) + VALID_BODY
        _write_prompt(tmp_path, "tmp_prompt", "v1.md", content)

        with pytest.raises(PromptError, match="must agree"):
            PromptLoader(base_path=tmp_path).load("tmp_prompt")

    def test_invalid_template_body_raises(self, tmp_path: Path) -> None:
        content = _frontmatter() + "Hello {% invalid"
        _write_prompt(tmp_path, "tmp_prompt", "v1.md", content)

        with pytest.raises(PromptError, match="not a valid template"):
            PromptLoader(base_path=tmp_path).load("tmp_prompt")


class TestEvalCases:
    def test_eval_cases_load_and_parse(self, loader: PromptLoader) -> None:
        cases = loader.load_eval_cases("demo_greeting")

        assert [case.id for case in cases] == ["basic_greeting", "formal_tone"]
        assert all(case.expected for case in cases)

    def test_eval_case_variables_render_against_latest_version(self, loader: PromptLoader) -> None:
        # The M4 guarantee: fixtures aren't just parseable, they're
        # actually consumable by the template they belong to.
        prompt: PromptTemplate = loader.load("demo_greeting")

        for case in loader.load_eval_cases("demo_greeting"):
            rendered = prompt.render(**case.variables)
            assert rendered

    def test_missing_eval_fixtures_raise_not_empty_list(self, tmp_path: Path) -> None:
        _write_prompt(tmp_path, "tmp_prompt", "v1.md", _frontmatter() + VALID_BODY)

        with pytest.raises(PromptNotFoundError, match="must ship with eval cases"):
            PromptLoader(base_path=tmp_path).load_eval_cases("tmp_prompt")

    def test_empty_eval_fixtures_raise(self, tmp_path: Path) -> None:
        _write_prompt(tmp_path, "tmp_prompt", "v1.md", _frontmatter() + VALID_BODY)
        evals_dir = tmp_path / "tmp_prompt" / "evals"
        evals_dir.mkdir()
        (evals_dir / "cases.yaml").write_text("[]", encoding="utf-8")

        with pytest.raises(PromptError, match="non-empty list"):
            PromptLoader(base_path=tmp_path).load_eval_cases("tmp_prompt")

    def test_malformed_eval_case_raises(self, tmp_path: Path) -> None:
        _write_prompt(tmp_path, "tmp_prompt", "v1.md", _frontmatter() + VALID_BODY)
        evals_dir = tmp_path / "tmp_prompt" / "evals"
        evals_dir.mkdir()
        (evals_dir / "cases.yaml").write_text("- id: x\n  unknown_field: true\n", encoding="utf-8")

        with pytest.raises(PromptError, match="malformed"):
            PromptLoader(base_path=tmp_path).load_eval_cases("tmp_prompt")

    def test_invalid_yaml_eval_fixtures_raise(self, tmp_path: Path) -> None:
        _write_prompt(tmp_path, "tmp_prompt", "v1.md", _frontmatter() + VALID_BODY)
        evals_dir = tmp_path / "tmp_prompt" / "evals"
        evals_dir.mkdir()
        (evals_dir / "cases.yaml").write_text("- [unclosed", encoding="utf-8")

        with pytest.raises(PromptError, match="not valid YAML"):
            PromptLoader(base_path=tmp_path).load_eval_cases("tmp_prompt")
