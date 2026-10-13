LABELS = ["billing", "bug", "account", "feature_request", "other"]

PROMPT_TEMPLATE = """Classify this support ticket for Tidepool, a note-taking app.
Choose one label: billing, bug, account, feature_request, other.

Ticket:
{ticket}

Answer with the label."""


def build_prompt(ticket: str) -> str:
    return PROMPT_TEMPLATE.format(ticket=ticket.strip())
