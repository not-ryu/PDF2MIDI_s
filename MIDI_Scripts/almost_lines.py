import cv2
import numpy as np
import os
import ast
# from sklearn.cluster import DBSCAN



def filter_lines_by_angle(lines, min_angle, max_angle):
    filtered_lines = []
    for line in lines:
        for x1, y1, x2, y2 in line:
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            if min_angle <= angle <= max_angle:
                filtered_lines.append(line)
    return filtered_lines



def join_stacked_lines(lines, max_gap=10, angle_similarity=7):
    """
    Joins lines that are stacked to form a single long line per occurrence.

    :param lines: List of line segments, where each line is represented as [x1, y1, x2, y2].
    :param max_gap: Maximum allowed gap between lines to consider them as continuous (in pixels).
    :param angle_similarity: Maximum allowed difference in angle to consider lines as having similar direction (in degrees).
    :return: List of joined lines.
    """

    # Convert angle similarity to radians
    angle_similarity = np.deg2rad(angle_similarity)

    # Sort the lines by the average of their y-coordinates (for horizontal lines)
    lines = sorted(lines, key=lambda line: (line[0][1] + line[0][3]) / 2)

    joined_lines = []
    current_line = None

    for line in lines:
        if current_line is None:
            current_line = line
            continue

        # Calculate the angle and midpoint of the current line
        cx1, cy1, cx2, cy2 = current_line[0]
        current_midpoint = ((cx1 + cx2) / 2, (cy1 + cy2) / 2)
        current_angle = np.arctan2(cy2 - cy1, cx2 - cx1)

        # Calculate the angle and midpoint of the next line
        nx1, ny1, nx2, ny2 = line[0]
        next_midpoint = ((nx1 + nx2) / 2, (ny1 + ny2) / 2)
        next_angle = np.arctan2(ny2 - ny1, nx2 - nx1)

        # Calculate the distance and angle difference between the lines
        distance = np.sqrt((next_midpoint[0] - current_midpoint[0])**2 + (next_midpoint[1] - current_midpoint[1])**2)
        angle_diff = np.abs(current_angle - next_angle)

        # Join lines if they are close in proximity and have similar angle
        if distance <= max_gap and angle_diff <= angle_similarity:
            # Extend the current line to include the next line
            joined_x1 = min(cx1, nx1)
            joined_y1 = min(cy1, ny1)
            joined_x2 = max(cx2, nx2)
            joined_y2 = max(cy2, ny2)
            current_line = [[joined_x1, joined_y1, joined_x2, joined_y2]]
        else:
            # Add the current line to the list of joined lines
            joined_lines.append(current_line)
            # Start a new current line
            current_line = line

    # Add the last line to the list of joined lines
    if current_line is not None:
        joined_lines.append(current_line)

    return joined_lines



def detect_staff_lines(image_path, out_path, segment_lenght = 300):
    # if __name__ == '__main__':    
    #     binary = cv2.imread(image_path, 0)
    # else:
    #     binary = cv2.cvtColor(image_path, cv2.COLOR_BGR2GRAY)
    
    if isinstance(image_path, str):  # Check if image_input is a file path
        binary = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)  # Read image from file path
    else:
        binary = cv2.cvtColor(image_path, cv2.COLOR_BGR2GRAY)  # Convert image array to grayscale


    # Initial Line Detection
    initial_lines = cv2.HoughLinesP(binary, 1, np.pi / 180, 100, minLineLength=150, maxLineGap=50)
    initial_lines = filter_lines_by_angle(initial_lines, min_angle=-5, max_angle=5)
    
    # Create a Line Mask
    line_mask = np.zeros_like(binary)
    if initial_lines is not None:
        for line in initial_lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(line_mask, (x1, y1), (x2, y2), 255, 2)

    # Reapply Hough Transform on the Line Mask
    refined_lines = cv2.HoughLinesP(line_mask, 1, np.pi / 180, 50, minLineLength=50, maxLineGap=40)

    # Filter Long Lines
    long_lines = []
    if refined_lines is not None:
        for line in refined_lines:
            x1, y1, x2, y2 = line[0]
            length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            if length > segment_lenght:
                long_lines.append(line)
    
    # Join stacked lines
    single_lines = join_stacked_lines(long_lines, max_gap=10, angle_similarity=2)
    
    return binary, single_lines


def is_within_ranges(y, ranges, tolerance = 10):
    for y_start, y_end in ranges:
        if (y_start - tolerance) <= y <= (y_end + tolerance):
            return True
    return False


def std_staff(image_path, out_path):
    binary, staff_lines = detect_staff_lines(image_path, out_path)
    color_image = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    
    # Create empty images
    contour_image = np.zeros_like(color_image)
    contour_image_rgb = cv2.cvtColor(contour_image, cv2.COLOR_BGR2RGB)
    contour_image_rgb_2 = cv2.cvtColor(contour_image, cv2.COLOR_BGR2RGB)
    contour_image_rgb_3 = cv2.cvtColor(contour_image, cv2.COLOR_BGR2RGB)
    # Draw the long, refined lines on binary image
    for line in staff_lines:
        x1, y1, x2, y2 = line[0]
        cv2.line(contour_image_rgb, (x1, y1), (x2, y2), (0, 255, 0), 1)
        cv2.line(color_image, (x1, y1), (x2, y2), (0, 255, 0), 1)

    result_path = os.path.join(out_path, 'staff_alone.png')
    cv2.imwrite(result_path, contour_image_rgb)

    result_path = os.path.join(out_path, 'staff_binary.png')
    cv2.imwrite(result_path, color_image)
    
    
    # Get contour of filtered staff alone
    gray_image = cv2.cvtColor(contour_image_rgb, cv2.COLOR_BGR2GRAY)
    contours, _ = cv2.findContours(gray_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    line_coords = []
    for cnt in contours:
        x, y, width, height = cv2.boundingRect(cnt)
        leftmost = x
        rightmost = x + width
        midpoint_y = y + height // 2
        
        line_coords.append(((leftmost, midpoint_y), (rightmost, midpoint_y)))

    for coords in line_coords:
        cv2.line(contour_image_rgb_2, coords[0], coords[1], (0, 0, 255), 1)
    output_path = os.path.join(out_path, 'loc_staff.png')
    cv2.imwrite(output_path, contour_image_rgb_2)



    """
    correct up to here. then forgot to account for angle when drawing and saving coordinates.
    Maybe this fixes staff_lines.py
    """
    
    
    matches_path = os.path.join(out_path, 'matches_cleffs.txt')
    with open(matches_path, 'r') as file:
        data = file.read().strip()
        rect_list = sorted(ast.literal_eval(data), key=lambda x: x[0][1])
    clavs_range = [(rect[0][1], rect[1][1]) for rect in rect_list]
    
    # Standardize sizes of staff based on longest width span
    min_x = min(x1 for (x1, _), (_, _) in line_coords)
    max_x = max(x2 for (_, _), (x2, _) in line_coords)
    span_x = max_x - min_x
    
    adjusted_line_coords = []
    for (x1, y1), (x2, y2) in line_coords:
        if is_within_ranges(y1, clavs_range) or is_within_ranges(y2, clavs_range):

            midpoint_x = (x1 + x2) // 2
            new_x1 = midpoint_x - span_x // 2
            new_x2 = midpoint_x + span_x // 2
            if new_x1 < min_x:
                new_x1 = min_x
                new_x2 = min_x + span_x
            elif new_x2 > max_x:
                new_x1 = max_x - span_x
                new_x2 = max_x
                
            adjusted_line_coords.append(((new_x1, y1), (new_x2, y2)))
    
    for coords in adjusted_line_coords:
        cv2.line(contour_image_rgb_3, coords[0], coords[1], (0, 0, 255), 1)
    output_path = os.path.join(out_path, 'loc_std_staff.png')
    
    print("\nDEBUG - Saving loc_std_staff.png:")
    print("DEBUG - Full output path:", output_path)
    print("DEBUG - Directory exists:", os.path.exists(os.path.dirname(output_path)))
    print("DEBUG - Directory is writable:", os.access(os.path.dirname(output_path), os.W_OK))
    
    # Before saving, verify the image data
    print("\nDEBUG - Image verification:")
    print("DEBUG - Image shape:", contour_image_rgb_3.shape)
    print("DEBUG - Image dtype:", contour_image_rgb_3.dtype)
    print("DEBUG - Image min/max values:", np.min(contour_image_rgb_3), np.max(contour_image_rgb_3))
    
    # Ensure the output directory exists
    os.makedirs(out_path, exist_ok=True)
    
    # Try saving with error handling
    try:
        success = cv2.imwrite(output_path, contour_image_rgb_3)
        if not success:
            print("DEBUG - cv2.imwrite returned False")
    except Exception as e:
        print("DEBUG - Error saving image:", str(e))
    
    print("DEBUG - File was written:", os.path.exists(output_path))
    if os.path.exists(output_path):
        print("DEBUG - File size:", os.path.getsize(output_path))

    print("got here")
    print(output_path)
    
    txt_outpath = os.path.join(out_path, 'staves.txt')
    stded_staff = sorted(adjusted_line_coords, key=lambda x: x[0][1])
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(txt_outpath), exist_ok=True)
    
    with open(txt_outpath, 'w') as file:
        file.write(str(stded_staff))
        print('Standardized staffs saved at:', output_path)


    txt_outpath = os.path.join(out_path, 'raw_staff.txt')
    line_coords = sorted(line_coords, key=lambda x: x[0][1])
    with open(txt_outpath, 'w') as file:
        file.write(str(stded_staff))
        print('Standardized staffs saved at:', output_path)

    return stded_staff



if __name__ == '__main__':
    
    out_path = '/Users/gabrielmiyazawa/Desktop/Cods/algs/lose/img_out/set_5/'
    image_path = '/Users/gabrielmiyazawa/Desktop/Cods/algs/lose/img_out/set_5/morph_staff.png'
        
    os.chdir(out_path)
    
    stave = std_staff(image_path, out_path)
    

    
    # flattened_data = [item.flatten().tolist() if isinstance(item, np.ndarray) else [subitem for sublist in item for subitem in sublist] for item in raw_seg]
    # line_segments = [((x1, y1), (x2, y2)) for x1, y1, x2, y2 in flattened_data]
    
    # matches_outpath = os.path.join(out_path, 'line_segments.txt')
    # with open(matches_outpath, 'w') as file:
    #     file.write(str(line_segments))



    # with open('matches_cleffs.txt', 'r') as file:
    #     data = file.read().strip()
    #     rect_list = sorted(ast.literal_eval(data), key=lambda x: x[0][1])
    # clavs_range = [(rect[0][1], rect[1][1]) for rect in rect_list]




    
    
    
    
    
    
    
    
    
    
    