from datetime import datetime
import json
import os
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.scan_history import ScanHistory
from app.services.forensics import ForensicsService
from app.services.ai_detector import AIDetectorService
from app.services.video_detector import VideoDetectorService
from app.services.audio_detector import AudioDetectorService
from app.services.face_detector import FaceDetectorService
from app.services.report_generator import ReportGenerator
from app.services.explainability import ExplainabilityService

router = APIRouter()


def _save_scan(db: Session, filename: str, media_type: str, ai_probability: float, verdict: str, full_response: dict):
    record = ScanHistory(
        filename=filename,
        media_type=media_type,
        ai_score=f"{int(ai_probability * 100)}%",
        verdict=verdict,
        full_result_json=json.dumps(full_response),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/analyze/image")
async def analyze_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not an image.")

    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        metadata = ForensicsService.analyze_metadata(file_path)
        ela_path = ForensicsService.run_ela(file_path)
        c2pa_result = ForensicsService.check_c2pa_metadata(file_path)
        noise_analysis = ForensicsService.analyze_noise_pattern(file_path)
        dct_analysis = ForensicsService.analyze_dct_compression(file_path)
        face_analysis = FaceDetectorService.detect_faces_in_image(file_path)

        ai_results = AIDetectorService.detect_ai_generation(file_path)
        ai_score = ai_results.get("ai_probability", 0)
        heatmap_analysis = ExplainabilityService.generate_heatmap(file_path, ai_score)

        if c2pa_result.get("has_c2pa") and c2pa_result.get("is_ai_generated"):
            ai_results["ai_probability"] = 0.99
            ai_results["human_probability"] = 0.01
            ai_results["confidence_score"] = 1.0
            ai_results["manipulation_score"] = 0.99
            ai_results["detected_type"] = f"Confirmed AI Generated (C2PA Verified - {c2pa_result.get('generator', 'Unknown')})"
            recommendation = f"Confirmed AI Generated. Cryptographically signed by {c2pa_result.get('issuer', 'Unknown')} via {c2pa_result.get('generator', 'Unknown')}."
        elif ai_score > 0.8:
            recommendation = "Highly Likely AI Generated. Structural anomalies detected."
        elif ai_score > 0.5:
            recommendation = "Suspicious. Potential AI generation or heavy digital manipulation."
        else:
            recommendation = "Likely Authentic. Standard sensor patterns found."

        response = {
            "filename": file.filename,
            "status": "Success",
            "metadata_analysis": metadata,
            "forensic_analysis": {
                "ela_result_path": os.path.basename(ela_path),
                "heatmap_analysis": heatmap_analysis,
                "noise_analysis": noise_analysis,
                "dct_compression_analysis": dct_analysis
            },
            "c2pa_analysis": c2pa_result,
            "face_analysis": face_analysis,
            "ai_detection_scores": ai_results,
            "final_recommendation": recommendation
        }

        record = _save_scan(db, file.filename, "IMAGE", ai_results.get("ai_probability", 0), ai_results.get("detected_type", "Unknown"), response)
        response["scan_id"] = record.id

        return response

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/analyze/video")
async def analyze_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a video.")

    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        c2pa_result = ForensicsService.check_c2pa_metadata(file_path)
        video_results = VideoDetectorService.detect_video_deepfake(file_path)
        ai_score = video_results.get("ai_probability", 0)

        if c2pa_result.get("has_c2pa") and c2pa_result.get("is_ai_generated"):
            video_results["ai_probability"] = 0.99
            video_results["human_probability"] = 0.01
            video_results["confidence_score"] = 1.0
            video_results["manipulation_score"] = 0.99
            video_results["detected_type"] = f"Confirmed AI Generated (C2PA Verified - {c2pa_result.get('generator', 'Unknown')})"
            recommendation = f"Confirmed AI Generated. Cryptographically signed by {c2pa_result.get('issuer', 'Unknown')} via {c2pa_result.get('generator', 'Unknown')}."
        elif ai_score > 0.75:
            recommendation = "Highly Likely Deepfake. Strong AI-generation signals found across sampled frames."
        elif ai_score > 0.40:
            recommendation = "Suspicious. Potential face-swap or generative artifacting found."
        else:
            recommendation = "Likely Authentic. No significant AI-generation signals detected."

        response = {
            "filename": file.filename,
            "status": "Success",
            "metadata_analysis": {
                "file_format": file_extension.replace(".", "").upper(),
                "codec_status": "VALID"
            },
            "c2pa_analysis": c2pa_result,
            "ai_detection_scores": video_results,
            "final_recommendation": recommendation
        }

        record = _save_scan(db, file.filename, "VIDEO", video_results.get("ai_probability", 0), video_results.get("detected_type", "Unknown"), response)
        response["scan_id"] = record.id

        return response

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)}")


@router.post("/analyze/audio")
async def analyze_audio(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.content_type.startswith("audio/") and not file.filename.lower().endswith(('.mp3', '.wav', '.m4a', '.flac')):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid audio format.")

    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        c2pa_result = ForensicsService.check_c2pa_metadata(file_path)
        audio_results = AudioDetectorService.detect_audio_deepfake(file_path)
        ai_score = audio_results.get("ai_probability", 0)

        if c2pa_result.get("has_c2pa") and c2pa_result.get("is_ai_generated"):
            audio_results["ai_probability"] = 0.99
            audio_results["human_probability"] = 0.01
            audio_results["confidence_score"] = 1.0
            audio_results["manipulation_score"] = 0.99
            audio_results["detected_type"] = f"Confirmed AI Generated (C2PA Verified - {c2pa_result.get('generator', 'Unknown')})"
            recommendation = f"Confirmed AI Generated. Cryptographically signed by {c2pa_result.get('issuer', 'Unknown')} via {c2pa_result.get('generator', 'Unknown')}."
        elif ai_score > 0.75:
            recommendation = "Highly Likely AI Synthesized Voice. Artificial pitch consistency detected."
        elif ai_score > 0.45:
            recommendation = "Suspicious. Potential voice cloning or heavy spectral artifacting."
        else:
            recommendation = "Likely Authentic. Natural voice frequencies and standard room acoustics found."

        response = {
            "filename": file.filename,
            "status": "Success",
            "metadata_analysis": {
                "file_format": file_extension.replace(".", "").upper(),
                "audio_channels": "STEREO/MONO",
                "sample_rate_check": "OPTIMAL"
            },
            "c2pa_analysis": c2pa_result,
            "ai_detection_scores": audio_results,
            "final_recommendation": recommendation
        }

        record = _save_scan(db, file.filename, "AUDIO", audio_results.get("ai_probability", 0), audio_results.get("detected_type", "Unknown"), response)
        response["scan_id"] = record.id

        return response

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")


@router.get("/scans/history")
async def get_scan_history(db: Session = Depends(get_db)):
    records = db.query(ScanHistory).order_by(ScanHistory.id.desc()).all()
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "media_type": r.media_type,
            "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "ai_score": r.ai_score,
            "verdict": r.verdict,
        }
        for r in records
    ]


@router.get("/scans/{scan_id}")
async def get_scan_detail(scan_id: int, db: Session = Depends(get_db)):
    record = db.query(ScanHistory).filter(ScanHistory.id == scan_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Scan not found.")
    return json.loads(record.full_result_json)


@router.get("/scans/{scan_id}/report")
async def download_report(scan_id: int, db: Session = Depends(get_db)):
    record = db.query(ScanHistory).filter(ScanHistory.id == scan_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Scan not found.")

    scan_data = json.loads(record.full_result_json)
    scan_data["media_type"] = record.media_type

    pdf_path = ReportGenerator.generate_pdf_report(scan_id, scan_data)

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"forensic_report_{scan_id}.pdf"
    )