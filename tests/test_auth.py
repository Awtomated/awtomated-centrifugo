import time

import jwt
import pytest

from centrifugo_toolkit.auth import decode_token, issue_connection_token, issue_subscription_token

# 32+ bytes so PyJWT doesn't emit InsecureKeyLengthWarning for HS256 in these tests.
SECRET = "s3cret-test-signing-key-32-bytes-long!!"
OTHER_SECRET = "a-completely-different-test-signing-key"


class TestIssueConnectionToken:
    def test_token_decodes_with_expected_claims(self):
        token = issue_connection_token("user-123", hmac_secret=SECRET, ttl_seconds=60)
        claims = decode_token(token, SECRET)

        assert claims["sub"] == "user-123"
        assert claims["exp"] > claims["iat"]
        assert claims["exp"] - claims["iat"] == 60
        assert "jti" in claims

    def test_token_rejected_with_wrong_secret(self):
        token = issue_connection_token("user-123", hmac_secret=SECRET)
        with pytest.raises(jwt.PyJWTError):
            decode_token(token, OTHER_SECRET)

    def test_expired_token_rejected(self):
        token = issue_connection_token("user-123", hmac_secret=SECRET, ttl_seconds=-1)
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_token(token, SECRET)

    def test_extra_claims_are_included(self):
        token = issue_connection_token(
            "user-123", hmac_secret=SECRET, extra_claims={"org_id": "org-1"},
        )
        claims = decode_token(token, SECRET)
        assert claims["org_id"] == "org-1"


class TestIssueSubscriptionToken:
    def test_token_carries_channel_claim(self):
        token = issue_subscription_token("user-123", "project:#42", hmac_secret=SECRET)
        claims = decode_token(token, SECRET)
        assert claims["channel"] == "project:#42"
        assert claims["sub"] == "user-123"
