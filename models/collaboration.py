"""
Collaboration models for multi-user trip planning
"""
from sqlalchemy import Column, String, Text, ForeignKey, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel


class SharePermission(str, enum.Enum):
    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"
    ADMIN = "admin"


class TripShare(BaseModel):
    """Model for sharing trips with other users"""
    __tablename__ = "trip_shares"

    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False)
    shared_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    shared_with_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    permission = Column(Enum(SharePermission), default=SharePermission.VIEW, nullable=False)

    # Relationships
    trip = relationship("Trip", backref="shares")
    shared_by = relationship("User", foreign_keys=[shared_by_user_id])
    shared_with = relationship("User", foreign_keys=[shared_with_user_id])

    def __repr__(self):
        return f"<TripShare(trip_id={self.trip_id}, shared_with={self.shared_with_user_id}, permission={self.permission})>"


class TripComment(BaseModel):
    """Model for comments on trips"""
    __tablename__ = "trip_comments"

    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # What the comment is about (optional)
    item_type = Column(String, nullable=True)  # "flight", "accommodation", "activity"
    item_id = Column(String, nullable=True)

    content = Column(Text, nullable=False)

    # Thread support
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("trip_comments.id"), nullable=True)

    # Relationships
    trip = relationship("Trip", backref="comments")
    user = relationship("User", backref="comments")
    replies = relationship("TripComment", backref="parent", remote_side="TripComment.id")

    def __repr__(self):
        return f"<TripComment(id={self.id}, trip_id={self.trip_id}, user_id={self.user_id})>"


class TripVote(BaseModel):
    """Model for voting on alternative options"""
    __tablename__ = "trip_votes"

    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # What is being voted on
    item_type = Column(String, nullable=False)  # "flight", "accommodation", "activity"
    item_id = Column(String, nullable=False)

    # Vote: 1 for upvote, -1 for downvote, 0 for neutral
    vote = Column(Integer, nullable=False, default=0)

    # Optional comment with vote
    comment = Column(Text, nullable=True)

    # Relationships
    trip = relationship("Trip", backref="votes")
    user = relationship("User", backref="votes")

    def __repr__(self):
        return f"<TripVote(id={self.id}, item_type={self.item_type}, item_id={self.item_id}, vote={self.vote})>"
