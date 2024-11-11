import cv2
import numpy as np
import os


verb = False

def center(box):
    x, y, w, h = box
    return x + w/2, y + h/2

def distance(c1, c2):
    return np.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)


# Standardize rectangles sizes
def std_rects(rectangles):
    if not rectangles:
        return ()
    else:
        # Calculate total width and height
        total_width = total_height = 0
        for ((x_initial, y_initial), (x_final, y_final), _, _) in rectangles:
            total_width += x_final - x_initial
            total_height += y_final - y_initial
    
        # Calculate average width and height
        avg_width = total_width / len(rectangles)
        avg_height = total_height / len(rectangles)
    
        standardized_rectangles = []
        for ((x_initial, y_initial), (x_final, y_final), score, name) in rectangles:
            # Calculate center of rectangle
            center_x = (x_initial + x_final) / 2
            center_y = (y_initial + y_final) / 2
    
            # Calculate new corners based on center and average dimensions
            new_x_initial = round(center_x - avg_width / 2)
            new_x_final = round(center_x + avg_width / 2)
            new_y_initial = round(center_y - avg_height / 2)
            new_y_final = round(center_y + avg_height / 2)
    
            standardized_rectangles.append(((new_x_initial, new_y_initial), (new_x_final, new_y_final), score, name))
    
        return standardized_rectangles
    
    
def contained_match(rectangles):
    formated_rect = [tup[0] + tup[1] for tup in rectangles]
    for (x_initial, y_initial, x_final, y_final) in formated_rect:
        """
        if (x_initial[i] <= x_initial[k] and x_final[k] <= x_final[i] and \
            y_initial[i] <= y_initial[k] and y_final[k] <= y_final[i]):
            
            delete rectangle[k]
        
        """

def multi_template_match(main_image_path, templates_dir, output_directory,\
                         threshold = 0.8, min_distance=15, skip_templates = None):
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)
        
    if __name__ == '__main__' or isinstance(main_image_path, str):
        main_image = cv2.imread(main_image_path)
    else:
        # No need to reprocess for subsequent uses
        main_image = main_image_path

    # print(main_image_path);
        
    main_image_gray = cv2.cvtColor(main_image, cv2.COLOR_BGR2GRAY)
    
    # Switch to the templates directory when executing as a module to simplify path references
    templates_directory = os.path.join(os.path.dirname(__file__), 'templates')

    # Construct the full path if it's not already
    if not os.path.isabs(templates_dir):
        templates_dir = os.path.join(templates_directory, templates_dir)
    

    templates = [f for f in os.listdir(templates_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
    all_matches = []  # List to keep track of all matches

    # Initialize template usage dictionary with all templates set to zero
    template_usage = {template_name: 0 for template_name in templates}

    # Preliminary template matching
    if skip_templates is None:
        skip_templates = []
    skip_templates_names = [os.path.basename(path) for path in skip_templates]

    for template_name in templates:
        template_pathname = os.path.basename(template_name)
        if template_pathname in skip_templates_names:
            continue
        
        template_path = os.path.join(templates_dir, template_name)
        template = cv2.imread(template_path, 0)
        w, h = template.shape[::-1]

        # res = cv2.matchTemplate(main_image_gray, template, cv2.TM_CCOEFF_NORMED)
        if main_image_gray.shape[0] >= template.shape[0] and main_image_gray.shape[1] >= template.shape[1]:
            res = cv2.matchTemplate(main_image_gray, template, cv2.TM_CCOEFF_NORMED)
        else:
            res = 0

        loc = np.where(res >= threshold)
        
        # Format matches log
        for pt in zip(*loc[::-1]):
            confidence = res[pt[1], pt[0]]  # Get match quality score
            all_matches.append((pt, (pt[0] + w, pt[1] + h), confidence, template_name))

    # Sort matches by confidence
    all_matches.sort(key=lambda x: x[2], reverse=True)

    # Filter matches by proximity to similar mathces to avoid repeated 
    final_matches = []
    for match in all_matches:
        match_center = center((match[0][0], match[0][1], match[1][0] - match[0][0],\
                               match[1][1] - match[0][1]))
        if not any(distance(center(\
                (final_match[0][0], final_match[0][1],\
                 final_match[1][0] - final_match[0][0],\
                 final_match[1][1] - final_match[0][1])),\
                    match_center) < min_distance for final_match in final_matches):
            final_matches.append(match)
            # Update template counter 
            template_name = match[3]  # Template name at index 3
            template_usage[template_name] += 1

    # Standardize sizes
    resized_matches = std_rects(final_matches)
    
    # Draw rectangles of the final matches
    # for match in resized_matches:
        # cv2.rectangle(main_image, match[0], match[1], (0, 255, 0), 2)
    for ((x_initial, y_initial), (x_final, y_final), score, name) in resized_matches:
        # Ensure the coordinates are integers
        x_initial, y_initial, x_final, y_final = map(int, [x_initial, y_initial, x_final, y_final])
        
        if verb: color = color_gradient_score(score, min_score = threshold)
        else: color = (0, 255, 0)
        cv2.rectangle(main_image, (x_initial, y_initial), (x_final, y_final), color, 2)
    
    if __name__ == '__main__':
        # Save the result
        result_path = os.path.join(output_directory, 'template_matches.png')
        cv2.imwrite(result_path, main_image)
        # print(f"Result saved to {result_path}")
        
        return resized_matches, template_usage, result_path
    else:
        return resized_matches, template_usage, main_image


def color_gradient_score(score, min_score = 0.5, max_score = 0.95):
    if score <= min_score:
        return (0, 0, 255)  # Red
    elif score >= max_score:
        return (0, 255, 0)  # Green
    # else:
    #     # Calculate intermediate colors
    #     red_component = int(255 * (1 - (score - 0.5) / 0.4))
    #     green_component = int(255 * ((score - 0.5) / 0.4))
    #     return (0, green_component, red_component)
    else:
        # Calculate intermediate color between Blue and Green
        blue_component = int(255 * (1 - (score - 0.5) / 0.4))
        green_component = int(255 * ((score - 0.5) / 0.4))
        return (blue_component, green_component, 0)



if __name__ == '__main__':
    main_image_path = '/Users/gabrielmiyazawa/Desktop/Cods/algs/teston.png'
    templates_dir = 'Notes_Full/'
    output_directory = '/Users/gabrielmiyazawa/Desktop/Cods/algs/lose/img_out/'
    
    matches, template_count, matched_image_path = \
        multi_template_match(main_image_path, templates_dir, output_directory, threshold = 0.7)
    
    # save_matches = [tup[0] + tup[1] for tup in matches]
    # print(save_matches)








