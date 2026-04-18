import os
import shutil
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from models.interaction_model import Interaction, UploadedFile

router = APIRouter()


@router.post("/upload/{interaction_id}")
async def upload_files(
    interaction_id: int,
    file_type: str = Form(..., description="Type of file: 'materials' or 'samples'"),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload files for materials shared or samples distributed
    """
    # Validate file type
    if file_type not in ["materials", "samples"]:
        raise HTTPException(status_code=400, detail="file_type must be 'materials' or 'samples'")

    # Check if interaction exists
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")

    uploaded_files = []

    allowed_mime_types = {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/bmp",
        "image/webp",
        "application/pdf",
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain",
        "application/zip",
        "application/x-zip-compressed",
    }
    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".webp",
        ".pdf",
        ".csv",
        ".xls",
        ".xlsx",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".txt",
        ".zip",
    }

    for file in files:
        # Validate file type
        file_extension = Path(file.filename).suffix.lower()
        if not (file.content_type in allowed_mime_types or file_extension in allowed_extensions):
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} type is not supported. Allowed types: images, PDF, CSV, Excel, Word, PowerPoint, text, zip."
            )

        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        # Create file path
        file_path = Path("uploads") / unique_filename

        # Save file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file {file.filename}: {str(e)}")

        # Create database record
        uploaded_file = UploadedFile(
            interaction_id=interaction_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=str(file_path),
            file_type=file_type,
            mime_type=file.content_type,
            file_size=file_path.stat().st_size
        )

        db.add(uploaded_file)
        uploaded_files.append({
            "id": uploaded_file.id,
            "filename": uploaded_file.filename,
            "original_filename": uploaded_file.original_filename,
            "file_path": uploaded_file.file_path,
            "file_type": uploaded_file.file_type,
            "mime_type": uploaded_file.mime_type,
            "file_size": uploaded_file.file_size
        })

    db.commit()

    return {
        "message": f"Successfully uploaded {len(uploaded_files)} files",
        "files": uploaded_files
    }


@router.get("/files/{interaction_id}")
def get_uploaded_files(interaction_id: int, db: Session = Depends(get_db)):
    """
    Get all uploaded files for an interaction
    """
    files = db.query(UploadedFile).filter(UploadedFile.interaction_id == interaction_id).all()

    return {
        "interaction_id": interaction_id,
        "files": [
            {
                "id": file.id,
                "filename": file.filename,
                "original_filename": file.original_filename,
                "file_path": file.file_path,
                "file_type": file.file_type,
                "mime_type": file.mime_type,
                "file_size": file.file_size,
                "uploaded_at": file.uploaded_at,
                "url": f"/uploads/{file.filename}"
            }
            for file in files
        ]
    }


@router.delete("/files/{file_id}")
def delete_uploaded_file(file_id: int, db: Session = Depends(get_db)):
    """
    Delete an uploaded file
    """
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete physical file
    try:
        os.remove(file_record.file_path)
    except OSError:
        pass  # File might already be deleted

    # Delete database record
    db.delete(file_record)
    db.commit()

    return {"message": "File deleted successfully"}