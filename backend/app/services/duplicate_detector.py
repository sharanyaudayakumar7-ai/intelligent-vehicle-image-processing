import imagehash
import numpy as np
from PIL import Image
from sqlalchemy.orm import Session
from app.database.models import AnalysisResult
def compute_hash(path:str)->str:
    with Image.open(path) as image: return str(imagehash.phash(image))
def analyze_duplicate(path:str,db:Session,distance_threshold:int)->tuple[str,dict]:
    current=compute_hash(path); match=None; best=None
    for result in db.query(AnalysisResult).all():
        distance=imagehash.hex_to_hash(current)-imagehash.hex_to_hash(result.perceptual_hash)
        if best is None or distance<best: best,match=distance,result.job_id
    # imagehash comparisons may yield NumPy scalars depending on their inputs.
    # Keep this detector's public result explicitly native even before the
    # persistence-boundary normalisation in image_processor.
    duplicate=bool(best is not None and best<=distance_threshold)
    return current,{"is_duplicate":duplicate,"matched_job_id":str(match) if duplicate else None,"hash_distance":int(best) if best is not None else None,"threshold":int(distance_threshold),"message":"Potential duplicate identified by perceptual similarity" if duplicate else "No close perceptual match found"}
