"""
Lease Reviewer agents.

Architecture
------------
root_agent (orchestrator / LlmAgent)
└── checklist_agent (sub-agent / LlmAgent)
    defined in sub_agents/checklist_agent/agent.py

Flow
----
1. User uploads a PDF lease and says "please review this lease".
2. root_agent calls `convert_pdf_to_markdown` to convert the PDF via Docling.
3. root_agent transfers to checklist_agent.
4. checklist_agent reads `lease_markdown` from session state, produces a
   human-readable review, and appends the extracted data as a JSON code block.

Note: ADK ends the agent turn after the sub-agent responds, so checklist_agent
is responsible for the complete final reply (prose + structured JSON).
The orchestrator's job is only to trigger the pipeline.
"""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from .settings import settings
from .sub_agents.checklist_agent.agent import checklist_agent
from .tools import convert_pdf_to_markdown

# ---------------------------------------------------------------------------
# Shared LiteLLM model instance (Gemini 2.5 Flash via Google AI Studio)
# ---------------------------------------------------------------------------
_model = LiteLlm(model=settings.agent_model)

# ---------------------------------------------------------------------------
# Orchestrator / root agent
# ---------------------------------------------------------------------------
root_agent = LlmAgent(
    name="lease_reviewer_orchestrator",
    model=_model,
    description="Orchestrates the lease review pipeline end-to-end.",
    instruction="""You are a friendly tenancy advisor helping users review their
residential lease agreement.

## Workflow

1. **Greet the user** and ask them to upload their lease PDF if they have
   not already done so.

2. **When the user provides a file path**, call `convert_pdf_to_markdown` with
   that path. The file path will look like `/uploads/<uuid>/<filename>.pdf`.

3. **After successful conversion**, transfer to `checklist_agent`. It will
   produce the complete review reply for the user — do not add any further
   text yourself after the transfer.

## Important notes
- If the conversion fails, explain the error and ask the user to try again.
- For follow-up questions after a review, answer them directly without
  re-converting the PDF (the Markdown is already in session state).""",
    sub_agents=[checklist_agent],
    tools=[convert_pdf_to_markdown],
)
