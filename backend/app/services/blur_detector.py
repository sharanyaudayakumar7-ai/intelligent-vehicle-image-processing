import cv2
import numpy as np
def analyze_blur(image: np.ndarray, threshold: float) -> dict:
    score=float(cv2.Laplacian(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY),cv2.CV_64F).var()); blurry=score<threshold
    return {"score":round(score,2),"is_blurry":blurry,"threshold":threshold,"message":"Image may be blurry based on edge detail" if blurry else "Image appears sufficiently sharp based on edge detail"}
