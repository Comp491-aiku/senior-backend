"""
Collaboration endpoints for multi-user trip planning
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database.connection import get_db
from models.user import User
from models.trip import Trip
from models.collaboration import TripShare, TripComment, TripVote, SharePermission
from auth.dependencies import get_current_user

router = APIRouter()


# Schemas
class ShareTripRequest(BaseModel):
    """Schema for sharing a trip"""
    trip_id: str
    user_email: EmailStr
    permission: str = "view"  # view, comment, edit, admin


class ShareTripResponse(BaseModel):
    """Schema for share trip response"""
    share_id: str
    trip_id: str
    shared_with: str  # email
    permission: str
    created_at: str

    class Config:
        from_attributes = True


class AddCommentRequest(BaseModel):
    """Schema for adding a comment"""
    trip_id: str
    content: str
    item_type: Optional[str] = None  # flight, accommodation, activity
    item_id: Optional[str] = None
    parent_comment_id: Optional[str] = None


class CommentResponse(BaseModel):
    """Schema for comment response"""
    id: str
    user_name: str
    user_email: str
    content: str
    item_type: Optional[str] = None
    item_id: Optional[str] = None
    created_at: str
    replies: List['CommentResponse'] = []

    class Config:
        from_attributes = True


class VoteRequest(BaseModel):
    """Schema for voting"""
    trip_id: str
    item_type: str  # flight, accommodation, activity
    item_id: str
    vote: int  # 1 (upvote), -1 (downvote), 0 (neutral)
    comment: Optional[str] = None


class VoteResponse(BaseModel):
    """Schema for vote response"""
    id: str
    user_name: str
    item_type: str
    item_id: str
    vote: int
    comment: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


# Endpoints
@router.post("/trips/share", response_model=ShareTripResponse)
async def share_trip(
    request: ShareTripRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Share a trip with another user

    Args:
        request: Share trip request with user email and permission
        current_user: Current authenticated user
        db: Database session

    Returns:
        Share information
    """
    # Verify trip exists and belongs to user
    trip = db.query(Trip).filter(
        Trip.id == request.trip_id,
        Trip.user_id == current_user.id
    ).first()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or you don't have permission"
        )

    # Find user to share with
    shared_with_user = db.query(User).filter(User.email == request.user_email).first()

    if not shared_with_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {request.user_email} not found"
        )

    # Check if already shared
    existing_share = db.query(TripShare).filter(
        TripShare.trip_id == request.trip_id,
        TripShare.shared_with_user_id == shared_with_user.id
    ).first()

    if existing_share:
        # Update permission if already shared
        existing_share.permission = SharePermission(request.permission)
        db.commit()
        db.refresh(existing_share)
        share = existing_share
    else:
        # Create new share
        share = TripShare(
            trip_id=request.trip_id,
            shared_by_user_id=current_user.id,
            shared_with_user_id=shared_with_user.id,
            permission=SharePermission(request.permission)
        )
        db.add(share)
        db.commit()
        db.refresh(share)

    return ShareTripResponse(
        share_id=str(share.id),
        trip_id=str(share.trip_id),
        shared_with=request.user_email,
        permission=share.permission.value,
        created_at=share.created_at.isoformat()
    )


@router.get("/trips/{trip_id}/shares")
async def get_trip_shares(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all shares for a trip

    Args:
        trip_id: Trip ID
        current_user: Current user
        db: Database session

    Returns:
        List of shares
    """
    # Verify access to trip
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.user_id != current_user.id:
        # Check if user has access through sharing
        has_access = db.query(TripShare).filter(
            TripShare.trip_id == trip_id,
            TripShare.shared_with_user_id == current_user.id
        ).first()

        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")

    # Get all shares
    shares = db.query(TripShare).filter(TripShare.trip_id == trip_id).all()

    return {
        "shares": [
            {
                "id": str(share.id),
                "shared_with": share.shared_with.email,
                "permission": share.permission.value,
                "created_at": share.created_at.isoformat()
            }
            for share in shares
        ]
    }


@router.post("/trips/comments", response_model=CommentResponse)
async def add_comment(
    request: AddCommentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a comment to a trip

    Args:
        request: Comment request
        current_user: Current user
        db: Database session

    Returns:
        Created comment
    """
    # Verify access to trip
    trip = db.query(Trip).filter(Trip.id == request.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Check permission (must have at least comment permission)
    if trip.user_id != current_user.id:
        share = db.query(TripShare).filter(
            TripShare.trip_id == request.trip_id,
            TripShare.shared_with_user_id == current_user.id
        ).first()

        if not share or share.permission == SharePermission.VIEW:
            raise HTTPException(status_code=403, detail="You don't have permission to comment")

    # Create comment
    comment = TripComment(
        trip_id=request.trip_id,
        user_id=current_user.id,
        content=request.content,
        item_type=request.item_type,
        item_id=request.item_id,
        parent_comment_id=request.parent_comment_id
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return CommentResponse(
        id=str(comment.id),
        user_name=current_user.name,
        user_email=current_user.email,
        content=comment.content,
        item_type=comment.item_type,
        item_id=comment.item_id,
        created_at=comment.created_at.isoformat(),
        replies=[]
    )


@router.get("/trips/{trip_id}/comments")
async def get_comments(
    trip_id: str,
    item_type: Optional[str] = None,
    item_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comments for a trip

    Args:
        trip_id: Trip ID
        item_type: Optional filter by item type
        item_id: Optional filter by item ID
        current_user: Current user
        db: Database session

    Returns:
        List of comments
    """
    # Verify access
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.user_id != current_user.id:
        has_access = db.query(TripShare).filter(
            TripShare.trip_id == trip_id,
            TripShare.shared_with_user_id == current_user.id
        ).first()
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")

    # Build query
    query = db.query(TripComment).filter(TripComment.trip_id == trip_id)

    if item_type:
        query = query.filter(TripComment.item_type == item_type)
    if item_id:
        query = query.filter(TripComment.item_id == item_id)

    comments = query.all()

    return {
        "comments": [
            CommentResponse(
                id=str(c.id),
                user_name=c.user.name,
                user_email=c.user.email,
                content=c.content,
                item_type=c.item_type,
                item_id=c.item_id,
                created_at=c.created_at.isoformat(),
                replies=[]
            )
            for c in comments
        ]
    }


@router.post("/trips/vote", response_model=VoteResponse)
async def vote_on_item(
    request: VoteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Vote on a trip item (flight, accommodation, activity)

    Args:
        request: Vote request
        current_user: Current user
        db: Database session

    Returns:
        Vote information
    """
    # Verify access
    trip = db.query(Trip).filter(Trip.id == request.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.user_id != current_user.id:
        share = db.query(TripShare).filter(
            TripShare.trip_id == request.trip_id,
            TripShare.shared_with_user_id == current_user.id
        ).first()
        if not share or share.permission == SharePermission.VIEW:
            raise HTTPException(status_code=403, detail="You don't have permission to vote")

    # Check if user already voted
    existing_vote = db.query(TripVote).filter(
        TripVote.trip_id == request.trip_id,
        TripVote.user_id == current_user.id,
        TripVote.item_type == request.item_type,
        TripVote.item_id == request.item_id
    ).first()

    if existing_vote:
        # Update existing vote
        existing_vote.vote = request.vote
        existing_vote.comment = request.comment
        db.commit()
        db.refresh(existing_vote)
        vote = existing_vote
    else:
        # Create new vote
        vote = TripVote(
            trip_id=request.trip_id,
            user_id=current_user.id,
            item_type=request.item_type,
            item_id=request.item_id,
            vote=request.vote,
            comment=request.comment
        )
        db.add(vote)
        db.commit()
        db.refresh(vote)

    return VoteResponse(
        id=str(vote.id),
        user_name=current_user.name,
        item_type=vote.item_type,
        item_id=vote.item_id,
        vote=vote.vote,
        comment=vote.comment,
        created_at=vote.created_at.isoformat()
    )


@router.get("/trips/{trip_id}/votes")
async def get_votes(
    trip_id: str,
    item_type: Optional[str] = None,
    item_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get votes for a trip or specific item

    Args:
        trip_id: Trip ID
        item_type: Optional filter by item type
        item_id: Optional filter by item ID
        current_user: Current user
        db: Database session

    Returns:
        Vote summary
    """
    # Verify access
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Build query
    query = db.query(TripVote).filter(TripVote.trip_id == trip_id)

    if item_type:
        query = query.filter(TripVote.item_type == item_type)
    if item_id:
        query = query.filter(TripVote.item_id == item_id)

    votes = query.all()

    # Calculate vote summary
    upvotes = sum(1 for v in votes if v.vote > 0)
    downvotes = sum(1 for v in votes if v.vote < 0)
    score = sum(v.vote for v in votes)

    return {
        "votes": [
            VoteResponse(
                id=str(v.id),
                user_name=v.user.name,
                item_type=v.item_type,
                item_id=v.item_id,
                vote=v.vote,
                comment=v.comment,
                created_at=v.created_at.isoformat()
            )
            for v in votes
        ],
        "summary": {
            "total_votes": len(votes),
            "upvotes": upvotes,
            "downvotes": downvotes,
            "score": score
        }
    }
