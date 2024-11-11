import os
import time
import argparse
from main import process_sheet_music
from NoteModifiers import process_midi
from Make_MIDI import make_midi
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process sheet music image to MIDI')
    parser.add_argument('base_dir', help='Base directory for input/output')
    
    args = parser.parse_args()
    
    # Directories are already created by the JS code
    input_dir = os.path.join(args.base_dir, 'in')
    output_dir = os.path.join(args.base_dir, 'out')
    final_output_dir = os.path.join(args.base_dir, 'final_output')
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    
    # Get all image files from input directory
    image_files = [f for f in os.listdir(input_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
    if not image_files:
        print("No image files found in input directory")
        exit(1)
    
    # Process each image file
    for image_file in sorted(image_files):  # Sort to maintain page order
        image_path = os.path.join(input_dir, image_file)
        process_sheet_music(image_path, output_dir, templates_dir)
        
        time.sleep(1)

        process_midi(output_dir)

        time.sleep(1)

        make_midi(output_dir, final_output_dir)

        # Clear output directory after processing each image
        for file in os.listdir(output_dir):
            file_path = os.path.join(output_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
