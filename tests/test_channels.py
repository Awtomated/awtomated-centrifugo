import pytest

from centrifugo_toolkit.channels import doc_channel, org_channel, project_channel, user_channel


@pytest.mark.parametrize(
    "fn, entity_id, expected",
    [
        (org_channel, "a1b2c3", "org:#a1b2c3"),
        (project_channel, 42, "project:#42"),
        (user_channel, "user-9", "user:#user-9"),
        (doc_channel, "doc-7", "doc:#doc-7"),
    ],
)
def test_channel_builders(fn, entity_id, expected):
    assert fn(entity_id) == expected
