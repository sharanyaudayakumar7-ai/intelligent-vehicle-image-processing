def analyze_dimensions(width:int,height:int,min_width:int,min_height:int)->dict:
    valid=width>=min_width and height>=min_height
    return {"width":width,"height":height,"resolution":width*height,"valid":valid,"minimum_width":min_width,"minimum_height":min_height,"message":"Image meets the configured minimum dimensions" if valid else "Image is below the configured minimum dimensions"}
