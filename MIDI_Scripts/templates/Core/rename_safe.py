
import os
import re

def rename(directory, new_base_name):
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
    
    files = os.listdir(directory)
    number_of_files = len(files)
    print('Starting number of files:', number_of_files)
    
    pattern = re.compile(rf"^{new_base_name}_(\d+)\.(\w+)$")
    
    existing_numbers = set()
    changes_made = False  # Track if any renaming was done
    
    for filename in files:
        _, ext = os.path.splitext(filename)
        if ext.lower() not in image_extensions:
            continue
        
        match = pattern.match(filename)
        if match:
            existing_numbers.add(int(match.group(1)))
    
    next_number = 1
    while next_number in existing_numbers:
        next_number += 1
    
    for filename in files:
        _, ext = os.path.splitext(filename)
        if ext.lower() not in image_extensions:
            continue
        
        if pattern.match(filename):
            continue
        
        new_filename = f"{new_base_name}_{next_number}{ext}"
        
        while os.path.exists(os.path.join(directory, new_filename)):
            next_number += 1
            new_filename = f"{new_base_name}_{next_number}{ext}"
        
        os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
        print(f"Renamed: {filename} -> {new_filename}")
        changes_made = True  # Mark that a change was made
        
        next_number += 1
    
    if not changes_made:
        print("No files renamed.")
        
    files = os.listdir(directory)
    number_of_files = len(files)
    print('Ending number of files:', number_of_files)



if __name__ == '__main__':
    directory = ''
    new_base_name = 'cf'
    
    rename(directory, new_base_name)




