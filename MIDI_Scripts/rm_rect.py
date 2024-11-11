import cv2
import ast # Assist with different file formats
import os

def remove_rectangles(image_path, rectangles_file, output_path, save = 0):
    
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    
    if __name__ == '__main__':
        # Read matches log file
        with open(rectangles_file, 'r') as file:
            content = file.read()
            rectangles = ast.literal_eval(content)  # Evaluating the string as a list of tuples
    else:
        rectangles = rectangles_file  # if used as module, read the array directly
    
    # Paint whie the area of the matches found 
    for (x_initial, y_initial, x_final, y_final) in rectangles:
        image[y_initial:y_final, x_initial:x_final] = (255, 255, 255)

    # Save simplified image
    if save:
        output_path = os.path.join(output_path, 'rmrect.png')
        cv2.imwrite(output_path, image)
        
    return image


if __name__ == '__main__':    
    input_image_path = '/Users/gabrielmiyazawa/Desktop/Cods/algs/try_pngs/try_on/page_17.png'
    output_image_path = '/Users/gabrielmiyazawa/Desktop/Cods/algs/lose/img_out/'
    rectangles = '/Users/gabrielmiyazawa/Desktop/Cods/algs/lose/matches.txt'
    
    remove_rectangles(input_image_path, rectangles, output_image_path, save = 1)
