"""Channel-naming helpers, matching the namespace convention documented in the
TransPM realtime architecture proposal (Section 4): org / project / user / doc.
"""


def org_channel(org_id) -> str:
    return f"org:#{org_id}"


def project_channel(project_id) -> str:
    return f"project:#{project_id}"


def user_channel(user_id) -> str:
    return f"user:#{user_id}"


def doc_channel(document_id) -> str:
    return f"doc:#{document_id}"
