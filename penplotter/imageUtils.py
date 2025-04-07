from PIL import Image
import numpy as np
import cv2

def resize_image(image_path, scale_factor=2):
    img = Image.open(image_path)
    new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
    img_resized = img.resize(new_size, Image.LANCZOS)
    new_image_path = "resized_" + image_path
    img_resized.save(new_image_path)
    return new_image_path

def image_to_contours(img, n=10, canny_threshold1=50, canny_threshold2=150, pen_diameter=2, max_width=2000, multiplier=4.5):    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, canny_threshold1, canny_threshold2)
    
    kernel_size = int(pen_diameter * 2)
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    height, width = img.shape[:2]
    scale =  multiplier*max_width / max(width, height)
    simplified_contours = []

    for contour in contours:
        if cv2.contourArea(contour) < 10:
            continue
        
        epsilon = n * cv2.arcLength(contour, True) / 100
        approx = cv2.approxPolyDP(contour, epsilon, True)
        approx = approx.squeeze()
        if approx.ndim == 1: 
            approx = np.expand_dims(approx, axis=0)

        scaled = [(int(x * scale), multiplier*max_width - int(y * scale)) for (x, y) in approx]
        simplified_contours.append(scaled)

    all_points = [pt for contour in simplified_contours for pt in contour]
    if all_points:
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        center_x = (min(xs) + max(xs)) // 2
        center_y = (min(ys) + max(ys)) // 2

        centered_contours = []
        for contour in simplified_contours:
            centered_contours.append([(x - center_x, y - center_y) for (x, y) in contour])
        simplified_contours = centered_contours
    
    return simplified_contours