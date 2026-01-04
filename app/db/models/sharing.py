"""
Sharing Database Model

Handles conversation sharing in Supabase.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import secrets

from app.db.supabase import get_supabase_admin_client


class ShareService:
    """
    Service for managing conversation shares in Supabase.

    Tables required:
    - conversation_shares: id, conversation_id, owner_id, shared_with_id,
      shared_with_email, permission, share_token, token_expires_at,
      accepted_at, created_at, updated_at
    """

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = get_supabase_admin_client()
        return self._client

    async def create_share(
        self,
        conversation_id: str,
        owner_id: str,
        permission: str = "view",
        shared_with_email: Optional[str] = None,
        create_link: bool = False,
        expires_in_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a new share for a conversation.

        Args:
            conversation_id: The conversation to share
            owner_id: The owner creating the share
            permission: 'view', 'comment', or 'edit'
            shared_with_email: Email to invite (optional)
            create_link: Whether to create a shareable link
            expires_in_days: Link expiration in days (optional)

        Returns:
            The created share record
        """
        share_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        data = {
            "id": share_id,
            "conversation_id": conversation_id,
            "owner_id": owner_id,
            "permission": permission,
            "created_at": now,
            "updated_at": now,
        }

        if shared_with_email:
            data["shared_with_email"] = shared_with_email.lower()
            # Check if user already exists and auto-link
            user = await self._find_user_by_email(shared_with_email)
            if user:
                data["shared_with_id"] = user["id"]

        if create_link:
            data["share_token"] = secrets.token_urlsafe(32)
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
                data["token_expires_at"] = expires_at.isoformat()

        result = self.client.table("conversation_shares").insert(data).execute()

        if result.data:
            return result.data[0]
        return data

    async def get_shares(
        self,
        conversation_id: str,
        owner_id: str,
    ) -> List[Dict[str, Any]]:
        """Get all shares for a conversation (owner only)."""
        result = (
            self.client.table("conversation_shares")
            .select("*")
            .eq("conversation_id", conversation_id)
            .eq("owner_id", owner_id)
            .order("created_at", desc=True)
            .execute()
        )

        shares = result.data or []

        # Enrich with user info for accepted shares
        for share in shares:
            if share.get("shared_with_id"):
                user = await self._get_user_info(share["shared_with_id"])
                if user:
                    share["shared_user"] = user

        return shares

    async def get_share(
        self,
        share_id: str,
        owner_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a specific share by ID."""
        result = (
            self.client.table("conversation_shares")
            .select("*")
            .eq("id", share_id)
            .eq("owner_id", owner_id)
            .maybe_single()
            .execute()
        )

        return result.data if result.data else None

    async def update_share(
        self,
        share_id: str,
        owner_id: str,
        permission: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update a share's permission level."""
        update_data = {"updated_at": datetime.utcnow().isoformat()}

        if permission:
            update_data["permission"] = permission

        result = (
            self.client.table("conversation_shares")
            .update(update_data)
            .eq("id", share_id)
            .eq("owner_id", owner_id)
            .execute()
        )

        return result.data[0] if result.data else None

    async def revoke_share(
        self,
        share_id: str,
        owner_id: str,
    ) -> bool:
        """Revoke a share (delete it)."""
        result = (
            self.client.table("conversation_shares")
            .delete()
            .eq("id", share_id)
            .eq("owner_id", owner_id)
            .execute()
        )

        return bool(result.data)

    async def get_shared_with_me(
        self,
        user_id: str,
        user_email: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all conversations shared with the user."""
        shares = []

        # Query 1: Accepted shares by user_id
        accepted_result = (
            self.client.table("conversation_shares")
            .select("*, conversations(*)")
            .eq("shared_with_id", user_id)
            .not_.is_("accepted_at", "null")
            .order("created_at", desc=True)
            .execute()
        )
        if accepted_result.data:
            shares.extend(accepted_result.data)

        # Query 2: Pending invites by user_id (user was auto-linked but hasn't accepted)
        pending_by_id_result = (
            self.client.table("conversation_shares")
            .select("*, conversations(*)")
            .eq("shared_with_id", user_id)
            .is_("accepted_at", "null")
            .order("created_at", desc=True)
            .execute()
        )
        if pending_by_id_result.data:
            shares.extend(pending_by_id_result.data)

        # Query 3: Pending email invites (user not yet linked)
        if user_email:
            email_result = (
                self.client.table("conversation_shares")
                .select("*, conversations(*)")
                .eq("shared_with_email", user_email.lower())
                .is_("shared_with_id", "null")
                .execute()
            )
            if email_result.data:
                shares.extend(email_result.data)

        # Enrich with owner info
        for share in shares:
            owner = await self._get_user_info(share["owner_id"])
            if owner:
                share["owner"] = owner

        return shares

    async def get_pending_invitations(
        self,
        user_email: str,
    ) -> List[Dict[str, Any]]:
        """Get pending invitations for a user by email."""
        result = (
            self.client.table("conversation_shares")
            .select("*, conversations(*)")
            .eq("shared_with_email", user_email.lower())
            .is_("accepted_at", "null")
            .order("created_at", desc=True)
            .execute()
        )

        shares = result.data or []

        for share in shares:
            owner = await self._get_user_info(share["owner_id"])
            if owner:
                share["owner"] = owner

        return shares

    async def accept_invitation(
        self,
        share_id: str,
        user_id: str,
        user_email: str,
    ) -> Optional[Dict[str, Any]]:
        """Accept a share invitation."""
        # Verify the share exists and is for this user
        result = (
            self.client.table("conversation_shares")
            .select("*")
            .eq("id", share_id)
            .execute()
        )

        if not result.data:
            return None

        share = result.data[0]

        # Check if invitation is for this user
        if (
            share.get("shared_with_id") != user_id
            and share.get("shared_with_email", "").lower() != user_email.lower()
        ):
            return None

        # Already accepted
        if share.get("accepted_at"):
            return share

        # Accept the invitation
        now = datetime.utcnow().isoformat()
        update_result = (
            self.client.table("conversation_shares")
            .update({
                "shared_with_id": user_id,
                "accepted_at": now,
                "updated_at": now,
            })
            .eq("id", share_id)
            .execute()
        )

        return update_result.data[0] if update_result.data else None

    async def validate_share_token(
        self,
        token: str,
    ) -> Optional[Dict[str, Any]]:
        """Validate a share token and return the share if valid."""
        result = (
            self.client.table("conversation_shares")
            .select("*, conversations(*)")
            .eq("share_token", token)
            .maybe_single()
            .execute()
        )

        if not result.data:
            return None

        share = result.data

        # Check expiration
        if share.get("token_expires_at"):
            expires_at = datetime.fromisoformat(
                share["token_expires_at"].replace("Z", "+00:00")
            )
            if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
                return None

        return share

    async def get_user_permission(
        self,
        conversation_id: str,
        user_id: str,
    ) -> Optional[str]:
        """Get user's permission level for a conversation."""
        # Check if user is owner
        conv_result = (
            self.client.table("conversations")
            .select("user_id")
            .eq("id", conversation_id)
            .maybe_single()
            .execute()
        )

        if conv_result.data and conv_result.data["user_id"] == user_id:
            return "owner"

        # Check shares
        share_result = (
            self.client.table("conversation_shares")
            .select("permission")
            .eq("conversation_id", conversation_id)
            .eq("shared_with_id", user_id)
            .not_.is_("accepted_at", "null")
            .maybe_single()
            .execute()
        )

        if share_result.data:
            return share_result.data["permission"]

        return None

    async def _find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find a user by email in auth.users."""
        try:
            # Use admin client to query auth.users
            result = self.client.auth.admin.list_users()
            for user in result:
                if user.email and user.email.lower() == email.lower():
                    return {"id": user.id, "email": user.email}
        except Exception:
            pass
        return None

    async def _get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user info from auth.users."""
        try:
            user = self.client.auth.admin.get_user_by_id(user_id)
            if user:
                return {
                    "id": user.user.id,
                    "email": user.user.email,
                    "name": user.user.user_metadata.get("full_name")
                    or user.user.user_metadata.get("name"),
                    "avatar_url": user.user.user_metadata.get("avatar_url"),
                }
        except Exception:
            pass
        return None


# Singleton instance
_share_service: Optional[ShareService] = None


def get_share_service() -> ShareService:
    """Get the share service singleton."""
    global _share_service
    if _share_service is None:
        _share_service = ShareService()
    return _share_service
