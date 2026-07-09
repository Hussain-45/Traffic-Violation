import os
import unittest
import datetime
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.services.password_service import password_service
from backend.app.services.jwt_service import jwt_service
from backend.app.services.rbac_service import rbac_service, require_permission
from backend.app.services.auth_service import auth_service
from backend.app.models import User, SessionModel, Role, Permission
from backend.app.services.password_policy import password_policy_service
from backend.app.services.token_blacklist import token_blacklist_service
from backend.app.services.identity_adapters import OAuth2GoogleAdapter, LDAPAdapter
from backend.app.services.security_context import get_security_context, SecurityContext


class TestAuthAndRBACServices(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock(spec=Session)

    # 1. Password Service Tests
    def test_password_service_hashing_and_verification(self):
        plain = "super_secure_password"
        hashed = password_service.hash_password(plain)
        self.assertNotEqual(plain, hashed)
        self.assertTrue(password_service.verify_password(plain, hashed))
        self.assertFalse(password_service.verify_password("wrong_pass", hashed))

    # 2. JWT Service Tests
    def test_jwt_service_token_operations(self):
        data = {"sub": "john_doe", "role": "officer"}
        access_token = jwt_service.create_access_token(data)
        refresh_token = jwt_service.create_refresh_token(data)

        # Verify access token
        decoded_access = jwt_service.decode_token(access_token)
        self.assertEqual(decoded_access["sub"], "john_doe")
        self.assertEqual(decoded_access["role"], "officer")
        self.assertEqual(decoded_access["type"], "access")

        # Verify refresh token
        decoded_refresh = jwt_service.decode_token(refresh_token)
        self.assertEqual(decoded_refresh["sub"], "john_doe")
        self.assertEqual(decoded_refresh["type"], "refresh")

        # Invalid token yields None
        self.assertIsNone(jwt_service.decode_token("invalid.token.signature"))

    # 3. RBAC Service Tests
    def test_rbac_service_permissions_fallback(self):
        user = User(username="officer_bob", role="officer", status="active", roles_rel=[])
        perms = rbac_service.get_user_permissions(user)
        self.assertIn("dashboard", perms)
        self.assertIn("violation_review", perms)
        self.assertNotIn("settings", perms)

        # Test has_permission
        self.assertTrue(rbac_service.has_permission(user, "dashboard"))
        self.assertFalse(rbac_service.has_permission(user, "settings"))

    def test_rbac_service_roles_rel(self):
        # Setup relationship mocks
        mock_perm = Permission(name="settings")
        mock_role = Role(name="admin", permissions=[mock_perm])
        user = User(username="admin_alice", role="officer", status="active", roles_rel=[mock_role])

        self.assertTrue(rbac_service.has_permission(user, "settings"))
        self.assertTrue(rbac_service.has_role(user, "admin"))

    # 4. Auth Service Tests
    def test_authenticate_user_success(self):
        hashed = password_service.hash_password("mypassword")
        user = User(id=1, username="test_user", password_hash=hashed, status="active", failed_login_attempts=0, locked_until=None)
        self.db.query().filter().first.return_value = user

        auth_user = auth_service.authenticate_user(self.db, "test_user", "mypassword")
        self.assertEqual(auth_user.id, user.id)
        self.assertEqual(user.failed_login_attempts, 0)

    def test_authenticate_user_wrong_password(self):
        hashed = password_service.hash_password("mypassword")
        user = User(id=1, username="test_user", password_hash=hashed, status="active", failed_login_attempts=0, locked_until=None)
        self.db.query().filter().first.return_value = user

        with self.assertRaises(HTTPException) as ctx:
            auth_service.authenticate_user(self.db, "test_user", "wrongpassword")
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(user.failed_login_attempts, 1)

    def test_authenticate_user_lockout(self):
        hashed = password_service.hash_password("mypassword")
        user = User(id=1, username="test_user", password_hash=hashed, status="active", failed_login_attempts=4, locked_until=None)
        self.db.query().filter().first.return_value = user

        with self.assertRaises(HTTPException) as ctx:
            auth_service.authenticate_user(self.db, "test_user", "wrongpassword")
        self.assertEqual(ctx.exception.status_code, 423) # LOCKED status
        self.assertIsNotNone(user.locked_until)

    def test_authenticate_user_active_lockout(self):
        hashed = password_service.hash_password("mypassword")
        future_locked = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
        user = User(id=1, username="test_user", password_hash=hashed, status="active", failed_login_attempts=5, locked_until=future_locked)
        self.db.query().filter().first.return_value = user

        with self.assertRaises(HTTPException) as ctx:
            auth_service.authenticate_user(self.db, "test_user", "mypassword")
        self.assertEqual(ctx.exception.status_code, 423)

    def test_create_user_session(self):
        user = User(id=1, username="test_user", role="admin")
        session = auth_service.create_user_session(self.db, user, remember_me=True)
        
        self.assertEqual(session.user_id, 1)
        self.assertFalse(session.is_revoked)
        self.db.add.assert_called_once()
        self.db.commit.assert_called()

    def test_refresh_user_session_success(self):
        # Create session mock
        session_rec = SessionModel(id="session-123", user_id=1, is_revoked=False, expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=1))
        user = User(id=1, username="test_user", role="admin", status="active", roles_rel=[])
        self.db.query().filter().first.side_effect = [session_rec, user]

        # Generate refresh token
        payload = {"sub": "test_user", "session_id": "session-123", "type": "refresh"}
        refresh_token = jwt_service.create_refresh_token(payload)

        # Patch rbac_service
        with patch("backend.app.services.auth_service.rbac_service") as mock_rbac:
            mock_rbac.get_user_permissions.return_value = {"dashboard"}
            access_token, new_refresh_token = auth_service.refresh_user_session(self.db, refresh_token)
            
            self.assertIsNotNone(access_token)
            self.assertIsNotNone(new_refresh_token)
            self.assertTrue(session_rec.is_revoked)

    def test_revoke_session(self):
        session_rec = SessionModel(id="session-123", is_revoked=False)
        self.db.query().filter().first.return_value = session_rec

        payload = {"sub": "test_user", "session_id": "session-123", "type": "refresh"}
        token = jwt_service.create_refresh_token(payload)

        success = auth_service.revoke_session(self.db, token)
        self.assertTrue(success)
        self.assertTrue(session_rec.is_revoked)
        self.assertTrue(token_blacklist_service.is_token_blacklisted(token))
        self.db.commit.assert_called()

    def test_change_password_success(self):
        hashed = password_service.hash_password("oldpass")
        user = User(id=1, password_hash=hashed)

        success = auth_service.change_password(self.db, user, "oldpass", "NewPass123!")
        self.assertTrue(success)
        self.assertTrue(password_service.verify_password("NewPass123!", user.password_hash))
        self.db.commit.assert_called()

    # 5. Password Policy Tests
    def test_password_policy_complexities(self):
        # Valid password
        password_policy_service.validate_password("SecurePass1!") # should not raise error

        # Weak password (length)
        with self.assertRaises(ValueError):
            password_policy_service.validate_password("Short1!")

        # Weak password (uppercase)
        with self.assertRaises(ValueError):
            password_policy_service.validate_password("lowercase1!")

        # Weak password (digit)
        with self.assertRaises(ValueError):
            password_policy_service.validate_password("NoDigits!")

        # Weak password (special character)
        with self.assertRaises(ValueError):
            password_policy_service.validate_password("NoSpecial12")

    def test_change_password_complexity_failure(self):
        hashed = password_service.hash_password("oldpass")
        user = User(id=1, password_hash=hashed)

        # Weak new password
        with self.assertRaises(ValueError):
            auth_service.change_password(self.db, user, "oldpass", "weak")

    # 6. Identity Provider Tests
    def test_google_adapter_auth(self):
        adapter = OAuth2GoogleAdapter()
        res = adapter.authenticate({"id_token": "mock-google-token"})
        self.assertIsNotNone(res)
        self.assertEqual(res["username"], "google_user")

        # Invalid token
        res_fail = adapter.authenticate({"id_token": "invalid"})
        self.assertIsNone(res_fail)

    def test_ldap_adapter_auth(self):
        adapter = LDAPAdapter()
        res = adapter.authenticate({"username": "jack@corp.local", "password": "CorpPass123"})
        self.assertIsNotNone(res)
        self.assertEqual(res["username"], "jack")

        # Invalid login
        res_fail = adapter.authenticate({"username": "jack@corp.local", "password": "wrong"})
        self.assertIsNone(res_fail)

    # 7. Security Context Dependency Tests
    def test_security_context_blacklisted_throws(self):
        token_blacklist_service.blacklist_token("blacklisted-token", expires_in_seconds=10.0)
        with self.assertRaises(HTTPException) as ctx:
            get_security_context(authorization="Bearer blacklisted-token", db=self.db)
        self.assertEqual(ctx.exception.status_code, 401)
