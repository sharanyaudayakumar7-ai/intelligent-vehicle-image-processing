import cv2
import numpy as np
def analyze_brightness(image: np.ndarray, threshold: float) -> dict:
    score=float(cv2.cvtColor(image,cv2.COLOR_BGR2GRAY).mean()); low=score<threshold
    return {"score":round(score,2),"is_low_light":low,"threshold":threshold,"message":"Image may have low brightness" if low else "Image brightness is above the configured low-light threshold"}
