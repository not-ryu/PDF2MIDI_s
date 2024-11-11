import cv2
import numpy as np
import os


def morphologyex(image_path, output_path, ker = (15, 11), save = 0):
    if __name__ == '__main__':
        image = cv2.imread(image_path, 0)
    else:
        image = image_path
        
    # Invert image colors
    image = cv2.bitwise_not(image)
    
    # Threshold the image to get a binary image
    _, binary = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY)
    
    # Define a horizontal kernel for detecting horizontal lines
        # Not used for vertical lines. Mostly for cleaning up.
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    
    # Dilate with a horizontal kernel to enhance horizontal lines
    dilated_horizontal = cv2.dilate(binary, horizontal_kernel, iterations=1)
    
    # Erode to make the lines thinner again, but keep the thick beams
    eroded_horizontal = cv2.erode(dilated_horizontal, horizontal_kernel, iterations=1)
    
    # Opening to further improve resolution of the thicker lines
    opening_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, ker)
    opened_image = cv2.morphologyEx(eroded_horizontal, cv2.MORPH_OPEN, opening_kernel)
    
    # Save morphological map image
    if save:
        result_path = os.path.join(output_path, 'morph.png')
        cv2.imwrite(result_path, opened_image)
    
    return opened_image




if __name__ == '__main__':
    image_path = '/Users/gabrielmiyazawa/Desktop/Cods/algs/try_pngs/try_on/racPre_page_3.png'
    output_path = '/Users/gabrielmiyazawa/Desktop/Cods/algs/lose/img_out/'
    
    # # Setup for staff lines
    # morphologyex(image_path, output_path, ker = (20, 1), save = 1)
    
    morphologyex(image_path, output_path, ker = (1, 7), save = 1)
