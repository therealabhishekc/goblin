"""
API endpoints for managing workflow templates.
Handles CRUD operations for interactive menu templates.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from app.core.database import get_database_session
from app.models.conversation import (
    WorkflowTemplateDB,
    WorkflowTemplateCreate,
    WorkflowTemplateUpdate,
    WorkflowTemplateResponse,
    TemplateType
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/templates", tags=["templates"])

# ==================================================================================
# TEMPLATE CRUD ENDPOINTS
# ==================================================================================

@router.get("/", response_model=List[WorkflowTemplateResponse])
async def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    template_type: Optional[TemplateType] = None,
    db: Session = Depends(get_database_session)
):
    """
    List all workflow templates with optional filtering.
    
    Query Parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    - is_active: Filter by active status
    - template_type: Filter by template type (button, list, text)
    """
    try:
        query = db.query(WorkflowTemplateDB)
        
        if is_active is not None:
            query = query.filter(WorkflowTemplateDB.is_active == is_active)
        
        if template_type:
            query = query.filter(WorkflowTemplateDB.template_type == template_type.value)
        
        templates = query.order_by(WorkflowTemplateDB.created_at.desc()).offset(skip).limit(limit).all()
        
        return [
            WorkflowTemplateResponse(
                id=str(template.id),
                template_name=template.template_name,
                template_type=template.template_type,
                trigger_keywords=template.trigger_keywords or [],
                menu_structure=template.menu_structure or {},
                is_active=template.is_active,
                created_at=template.created_at,
                updated_at=template.updated_at
            )
            for template in templates
        ]
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")


@router.get("/{template_id}", response_model=WorkflowTemplateResponse)
async def get_template(template_id: str, db: Session = Depends(get_database_session)):
    """
    Get a specific template by ID.
    """
    try:
        template = db.query(WorkflowTemplateDB).filter(WorkflowTemplateDB.id == template_id).first()
        
        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
        
        return WorkflowTemplateResponse(
            id=str(template.id),
            template_name=template.template_name,
            template_type=template.template_type,
            trigger_keywords=template.trigger_keywords or [],
            menu_structure=template.menu_structure or {},
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")


@router.get("/name/{template_name}", response_model=WorkflowTemplateResponse)
async def get_template_by_name(template_name: str, db: Session = Depends(get_database_session)):
    """
    Get a specific template by name.
    """
    try:
        template = db.query(WorkflowTemplateDB).filter(
            WorkflowTemplateDB.template_name == template_name
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_name}")
        
        return WorkflowTemplateResponse(
            id=str(template.id),
            template_name=template.template_name,
            template_type=template.template_type,
            trigger_keywords=template.trigger_keywords or [],
            menu_structure=template.menu_structure or {},
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template by name {template_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")


@router.post("/", response_model=WorkflowTemplateResponse, status_code=201)
async def create_template(
    template: WorkflowTemplateCreate,
    db: Session = Depends(get_database_session)
):
    """
    Create a new workflow template.
    """
    try:
        # Check if template with same name already exists
        existing = db.query(WorkflowTemplateDB).filter(
            WorkflowTemplateDB.template_name == template.template_name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Template with name '{template.template_name}' already exists"
            )
        
        # Create new template
        db_template = WorkflowTemplateDB(
            template_name=template.template_name,
            template_type=template.template_type.value,
            trigger_keywords=template.trigger_keywords,
            menu_structure=template.menu_structure,
            is_active=template.is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        
        logger.info(f"✅ Created template: {template.template_name}")
        
        return WorkflowTemplateResponse(
            id=str(db_template.id),
            template_name=db_template.template_name,
            template_type=db_template.template_type,
            trigger_keywords=db_template.trigger_keywords or [],
            menu_structure=db_template.menu_structure or {},
            is_active=db_template.is_active,
            created_at=db_template.created_at,
            updated_at=db_template.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")


@router.put("/{template_id}", response_model=WorkflowTemplateResponse)
async def update_template(
    template_id: str,
    template: WorkflowTemplateUpdate,
    db: Session = Depends(get_database_session)
):
    """
    Update an existing workflow template.
    """
    try:
        db_template = db.query(WorkflowTemplateDB).filter(
            WorkflowTemplateDB.id == template_id
        ).first()
        
        if not db_template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
        
        # Update fields if provided
        update_data = template.dict(exclude_unset=True)
        
        if 'template_type' in update_data and update_data['template_type']:
            update_data['template_type'] = update_data['template_type'].value
        
        for field, value in update_data.items():
            setattr(db_template, field, value)
        
        db_template.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_template)
        
        logger.info(f"✅ Updated template: {db_template.template_name}")
        
        return WorkflowTemplateResponse(
            id=str(db_template.id),
            template_name=db_template.template_name,
            template_type=db_template.template_type,
            trigger_keywords=db_template.trigger_keywords or [],
            menu_structure=db_template.menu_structure or {},
            is_active=db_template.is_active,
            created_at=db_template.created_at,
            updated_at=db_template.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update template: {str(e)}")


@router.delete("/{template_id}")
async def delete_template(template_id: str, db: Session = Depends(get_database_session)):
    """
    Delete a workflow template.
    """
    try:
        db_template = db.query(WorkflowTemplateDB).filter(
            WorkflowTemplateDB.id == template_id
        ).first()
        
        if not db_template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
        
        template_name = db_template.template_name
        
        db.delete(db_template)
        db.commit()
        
        logger.info(f"✅ Deleted template: {template_name}")
        
        return {"message": f"Template '{template_name}' deleted successfully", "id": template_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete template: {str(e)}")


@router.post("/{template_id}/toggle")
async def toggle_template_status(template_id: str, db: Session = Depends(get_database_session)):
    """
    Toggle the active status of a template.
    """
    try:
        db_template = db.query(WorkflowTemplateDB).filter(
            WorkflowTemplateDB.id == template_id
        ).first()
        
        if not db_template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
        
        db_template.is_active = not db_template.is_active
        db_template.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_template)
        
        status = "activated" if db_template.is_active else "deactivated"
        logger.info(f"✅ Template {status}: {db_template.template_name}")
        
        return {
            "message": f"Template '{db_template.template_name}' {status} successfully",
            "is_active": db_template.is_active
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error toggling template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to toggle template: {str(e)}")
