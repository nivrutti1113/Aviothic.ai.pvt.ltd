import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from bson import ObjectId

from ..models.user import UserInDB
from ..middleware.auth import get_current_user, require_doctor, require_admin
from ..db import db

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/user/history", 
            summary="Get user's prediction history",
            description="""Fetch all predictions made by the current user.
            
            Returns complete history with images, GradCAM, reports, and doctor status.
            """)
async def get_user_history(current_user: UserInDB = Depends(get_current_user)):
    """Get current user's prediction history.
    
    Args:
        current_user: Authenticated user (from dependency)
        
    Returns:
        List of user's predictions with all relevant information
    """
    try:
        logger.info(f"Fetching prediction history for user: {current_user.email}")
        
        # Query predictions by user_id
        user_predictions = []
        records = await db.get_recent_inferences(limit=100)  # Get recent records
        
        # Filter for current user
        for record in records:
            if record.get("user_id") == current_user.id:
                # Clean up the record for response
                cleaned_record = {
                    "id": record.get("_id"),
                    "case_id": record.get("case_id"),
                    "prediction": record.get("prediction"),
                    "confidence": record.get("confidence"),
                    "risk_score": record.get("risk_score"),
                    "explanation": record.get("explanation"),
                    "image_url": record.get("image_url"),
                    "gradcam_url": record.get("gradcam_path"),
                    "report_url": record.get("report_path"),
                    "doctor_status": record.get("doctor_status"),
                    "doctor_note": record.get("doctor_note"),
                    "created_at": record.get("timestamp")
                }
                user_predictions.append(cleaned_record)
        
        logger.info(f"Returning {len(user_predictions)} records for user: {current_user.email}")
        return user_predictions
        
    except Exception as e:
        logger.error(f"Error fetching user history for {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user history"
        )


@router.get("/doctor/cases",
            summary="Get pending cases for doctors",
            description="""Fetch all pending cases requiring doctor review.
            
            Returns cases that need confirmation/rejection with images and AI predictions.
            """)
async def get_pending_cases(current_user: UserInDB = Depends(require_doctor)):
    """Get pending cases for doctor review.
    
    Args:
        current_user: Authenticated doctor/admin user (from dependency)
        
    Returns:
        List of pending cases for review
    """
    try:
        logger.info(f"Fetching pending cases for doctor: {current_user.email}")
        
        # Query all predictions that need doctor review
        all_records = await db.get_recent_inferences(limit=1000)  # Get all records
        
        pending_cases = []
        for record in all_records:
            # Include cases that don't have a doctor status or need review
            if record.get("doctor_status") is None or record.get("doctor_status") == "":
                # Clean up the record for response
                cleaned_record = {
                    "id": record.get("_id"),
                    "case_id": record.get("case_id"),
                    "user_id": record.get("user_id"),
                    "prediction": record.get("prediction"),
                    "confidence": record.get("confidence"),
                    "risk_score": record.get("risk_score"),
                    "explanation": record.get("explanation"),
                    "image_url": record.get("image_url"),
                    "gradcam_url": record.get("gradcam_path"),
                    "report_url": record.get("report_path"),
                    "created_at": record.get("timestamp")
                }
                pending_cases.append(cleaned_record)
        
        logger.info(f"Returning {len(pending_cases)} pending cases for doctor: {current_user.email}")
        return pending_cases
        
    except Exception as e:
        logger.error(f"Error fetching pending cases for doctor {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch pending cases"
        )


@router.post("/doctor/add-note",
             summary="Add doctor note to case",
             description="""Add a note to a specific case and update its status.
             
             Allows doctors to add notes and set confirmation status.
             """)
async def add_doctor_note(case_data: dict, current_user: UserInDB = Depends(require_doctor)):
    """Add doctor note to a case.
    
    Args:
        case_data: Contains case_id, note, and status
        current_user: Authenticated doctor/admin user (from dependency)
        
    Returns:
        Success message
    """
    try:
        case_id = case_data.get("case_id")
        note = case_data.get("note")
        status_update = case_data.get("status")  # "confirmed", "rejected", or None
        
        if not case_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Case ID is required"
            )
        
        # Validate status if provided
        if status_update and status_update not in ["confirmed", "rejected", None, ""]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status must be 'confirmed', 'rejected', or empty"
            )
        
        logger.info(f"Adding doctor note for case {case_id} by doctor: {current_user.email}")
        
        # Update the case in database
        update_data = {
            "doctor_note": note,
            "doctor_status": status_update,
            "reviewed_by": current_user.id,
            "reviewed_at": case_data.get("reviewed_at")  # Use provided timestamp or server will set it
        }
        
        result = await db.db.inferences.update_one(
            {"case_id": case_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )
        
        logger.info(f"Doctor note added successfully for case {case_id}")
        return {"message": "Doctor note added successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding doctor note for case {case_data.get('case_id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add doctor note"
        )


@router.post("/doctor/confirm",
             summary="Confirm doctor review of case",
             description="""Confirm or reject a case prediction.
             
             Sets the doctor status to confirmed or rejected.
             """)
async def confirm_case(case_data: dict, current_user: UserInDB = Depends(require_doctor)):
    """Confirm or reject a case prediction.
    
    Args:
        case_data: Contains case_id and confirmation status
        current_user: Authenticated doctor/admin user (from dependency)
        
    Returns:
        Success message
    """
    try:
        case_id = case_data.get("case_id")
        status_update = case_data.get("status")  # "confirmed" or "rejected"
        
        if not case_id or not status_update:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Case ID and status are required"
            )
        
        # Validate status
        if status_update not in ["confirmed", "rejected"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status must be 'confirmed' or 'rejected'"
            )
        
        logger.info(f"Confirming case {case_id} as {status_update} by doctor: {current_user.email}")
        
        # Update the case in database
        update_data = {
            "doctor_status": status_update,
            "reviewed_by": current_user.id,
            "reviewed_at": case_data.get("reviewed_at") or None  # Use provided timestamp or server will set it
        }
        
        result = await db.db.inferences.update_one(
            {"case_id": case_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )
        
        logger.info(f"Case {case_id} confirmed as {status_update} successfully")
        return {"message": f"Case confirmed as {status_update}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming case {case_data.get('case_id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm case"
        )


@router.get("/admin/predictions",
            summary="Get all predictions for admin",
            description="""Fetch all predictions for administrative oversight.
            
            Allows admins to view all predictions across all users.
            """)
async def get_all_predictions(current_user: UserInDB = Depends(require_admin)):
    """Get all predictions for admin oversight.
    
    Args:
        current_user: Authenticated admin user (from dependency)
        
    Returns:
        List of all predictions
    """
    try:
        logger.info(f"Fetching all predictions for admin: {current_user.email}")
        
        # Get all records
        all_records = await db.get_recent_inferences(limit=1000)
        
        # Format the records
        formatted_records = []
        for record in all_records:
            cleaned_record = {
                "id": record.get("_id"),
                "case_id": record.get("case_id"),
                "user_id": record.get("user_id"),
                "prediction": record.get("prediction"),
                "confidence": record.get("confidence"),
                "risk_score": record.get("risk_score"),
                "explanation": record.get("explanation"),
                "image_url": record.get("image_url"),
                "gradcam_url": record.get("gradcam_path"),
                "report_url": record.get("report_path"),
                "doctor_status": record.get("doctor_status"),
                "doctor_note": record.get("doctor_note"),
                "admin_status": record.get("admin_status"),
                "created_at": record.get("timestamp")
            }
            formatted_records.append(cleaned_record)
        
        logger.info(f"Returning {len(formatted_records)} records for admin: {current_user.email}")
        return formatted_records
        
    except Exception as e:
        logger.error(f"Error fetching all predictions for admin {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch predictions"
        )


@router.post("/admin/approve",
             summary="Approve admin action on prediction",
             description="""Approve or set admin status on a prediction.
             
             Allows admins to approve doctor confirmations or set admin status.
             """)
async def approve_prediction(approval_data: dict, current_user: UserInDB = Depends(require_admin)):
    """Approve admin action on a prediction.
    
    Args:
        approval_data: Contains case_id and admin status
        current_user: Authenticated admin user (from dependency)
        
    Returns:
        Success message
    """
    try:
        case_id = approval_data.get("case_id")
        admin_status = approval_data.get("admin_status")
        
        if not case_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Case ID is required"
            )
        
        logger.info(f"Setting admin status '{admin_status}' for case {case_id} by admin: {current_user.email}")
        
        # Update the case in database
        update_data = {
            "admin_status": admin_status
        }
        
        result = await db.db.inferences.update_one(
            {"case_id": case_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )
        
        logger.info(f"Admin status set successfully for case {case_id}")
        return {"message": "Admin status updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting admin status for case {approval_data.get('case_id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set admin status"
        )


@router.get("/admin/users",
            summary="Get all users for admin",
            description="""Fetch all registered users for administrative oversight.
            
            Allows admins to view all registered users.
            """)
async def get_all_users(current_user: UserInDB = Depends(require_admin)):
    """Get all registered users for admin oversight.
    
    Args:
        current_user: Authenticated admin user (from dependency)
        
    Returns:
        List of all users
    """
    try:
        logger.info(f"Fetching all users for admin: {current_user.email}")
        
        # Get all users from database
        users_cursor = db.db.users.find({})
        users = []
        
        async for user_doc in users_cursor:
            user_doc["id"] = str(user_doc.pop("_id"))
            # Remove sensitive information
            user_doc.pop("hashed_password", None)
            user_doc.pop("refresh_tokens", None)
            user_doc.pop("forgot_password_token", None)
            user_doc.pop("forgot_password_expires", None)
            users.append(user_doc)
        
        logger.info(f"Returning {len(users)} users for admin: {current_user.email}")
        return users
        
    except Exception as e:
        logger.error(f"Error fetching all users for admin {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )


@router.delete("/admin/user/{user_id}",
               summary="Delete user account",
               description="""Delete a user account.
               
               Allows admins to delete user accounts.
               """)
async def delete_user(user_id: str, current_user: UserInDB = Depends(require_admin)):
    """Delete a user account.
    
    Args:
        user_id: ID of user to delete
        current_user: Authenticated admin user (from dependency)
        
    Returns:
        Success message
    """
    try:
        logger.info(f"Deleting user {user_id} by admin: {current_user.email}")
        
        # Delete the user
        result = await db.db.users.delete_one({"_id": ObjectId(user_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User {user_id} deleted successfully by admin: {current_user.email}")
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id} by admin {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


__all__ = ["router"]