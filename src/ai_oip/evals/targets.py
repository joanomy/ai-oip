"""Standard eval targets.

`prompt_completion_target` is the canonical way to evaluate a prompt's
golden cases: render the template with each case's variables, send the
result through a provider, hand the text back to the runner. In CI the
provider is a fake (verifying harness plumbing); against a live
provider the same target evaluates the actual model behavior.
"""

from ai_oip.evals.runner import EvalTarget
from ai_oip.prompts import PromptTemplate
from ai_oip.providers import CompletionRequest, LLMProvider


def prompt_completion_target(prompt: PromptTemplate, provider: LLMProvider) -> EvalTarget:
    """Build an EvalTarget that completes `prompt` through `provider`."""

    async def target(variables: dict[str, object]) -> str:
        rendered = prompt.render(**variables)
        response = await provider.complete(
            CompletionRequest(prompt=rendered, system=prompt.metadata.role)
        )
        return response.text

    return target
