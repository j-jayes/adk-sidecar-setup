"""
Lease Reviewer agents.

Architecture
------------
root_agent (orchestrator / LlmAgent)
└── checklist_agent (sub-agent / LlmAgent with structured output)

Flow
----
1. User uploads a PDF lease and says "please review this lease".
2. The orchestrator calls `convert_pdf_to_markdown` with the file path.
3. The orchestrator delegates to `checklist_agent` with the Markdown text.
4. `checklist_agent` extracts structured data (LeaseInformation schema)
   and reports missing items back to the orchestrator.
5. The orchestrator presents a clear, friendly summary to the user.
"""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from .schemas import LeaseInformation
from .settings import settings
from .tools import convert_pdf_to_markdown

# ---------------------------------------------------------------------------
# Shared LiteLLM model instance (Gemini 2.5 Flash via Google AI Studio)
# ---------------------------------------------------------------------------
_model = LiteLlm(model=settings.agent_model)

# ---------------------------------------------------------------------------
# Checklist sub-agent
# Receives the lease Markdown via its instruction + session state,
# extracts structured information, and flags missing items.
# ---------------------------------------------------------------------------
checklist_agent = LlmAgent(
    name="checklist_agent",
    model=_model,
    description=(
        "Analyses a lease document in Markdown format, extracts key details "
        "according to a structured schema, and flags any missing or unusual clauses."
    ),
    instruction="""You are a specialist lease-document reviewer.

The lease document text is available in session state under the key
`lease_markdown`.  Read it carefully and populate every field you can
find in the output schema.

For the `missing_items` field list every important item that a standard
residential lease should contain but that is absent from this document.
Common items to check for:
- Full names of all tenants
- Landlord name and contact address
- Property address
- Lease start and end dates (or statement that it is periodic)
- Monthly rent amount and due date
- Security deposit amount and deposit protection scheme
- Notice period for termination
- Inventory or check-in report reference
- Permitted use clause
- Subletting restrictions
- Pets policy
- Repair and maintenance responsibilities
- Break clause (if fixed term)

Write the `summary` field in plain English for a non-legal reader.""",
    output_schema=LeaseInformation,
    output_key="lease_review_result",
)

# ---------------------------------------------------------------------------
# Orchestrator / root agent
# ---------------------------------------------------------------------------
root_agent = LlmAgent(
    name="lease_reviewer_orchestrator",
    model=_model,
    description="Orchestrates the lease review workflow end-to-end.",
    instruction="""You are a friendly and knowledgeable tenancy advisor.

Your job is to help the user review their residential lease agreement.

## Workflow

1. **Greet the user** and ask them to upload their lease PDF if they have
   not already done so.

2. **When the user mentions a file path or says they have uploaded a file**,
   call `convert_pdf_to_markdown` with that file path to extract the text.
   The file path will look like `/uploads/<filename>.pdf`.

3. **After successful conversion**, transfer to `checklist_agent` so it can
   perform the detailed review and extract the structured information.

4. **Present the results** to the user in a clear, readable format:
   - Summarise the key details found (parties, dates, rent, deposit).
   - Highlight any **missing items** with ⚠️ emoji.
   - Give a brief plain-English `summary`.
   - Offer to answer follow-up questions.

## Important notes
- Be warm and approachable – many tenants are not legal experts.
- If the conversion fails, explain the error and ask the user to try again.
- Do not invent information; only report what is in the document.""",
    sub_agents=[checklist_agent],
    tools=[convert_pdf_to_markdown],
)
