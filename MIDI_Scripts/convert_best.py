import fitz  # PyMuPDF
import os
import sys
import time

import multiprocessing

def convert_page(pdf_path, page_num, name, resolution, outpath):
    doc = fitz.open(pdf_path)  # Open the PDF here to ensure it's local to the process
    zoom = resolution / 72
    mat = fitz.Matrix(zoom, zoom)
    page = doc.load_page(page_num)  # Load the page
    pix = page.get_pixmap(matrix=mat)  # Render the page
    output_image_path = os.path.join(outpath, f'{name}_p_{page_num}.png')
    pix.save(output_image_path)
    doc.close()  # Close the document to free up the resource
    # print(f'Converted page {page_num}')

def convert_pdf_to_png(pdf_path, pages_arg, resolution=300, outpath=None):
    name = os.path.splitext(os.path.basename(pdf_path))[0]
    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    doc.close()

    pages_to_convert = determine_pages(pages_arg, num_pages)

    if not pages_to_convert:
        print('Invalid page range.')
        return
    
    out_path = outpath or os.path.dirname(pdf_path)
    start_time = time.time()
    
    # Determine the number of cores to use
    num_cores = max(1, multiprocessing.cpu_count() // 2)  # Using half of available cores

    # Set up multiprocessing with limited cores
    with multiprocessing.Pool(processes=num_cores) as pool:
        args = [(pdf_path, page_num, name, resolution, out_path) for page_num in pages_to_convert]
        pool.starmap(convert_page, args)

    end_time = time.time()
    print(f"Converted {len(pages_to_convert)} pages to images at {resolution} DPI")
    print(f"Execution time: {end_time - start_time} seconds")

def determine_pages(pages_arg, num_pages):
    if pages_arg.isdigit():
        page = int(pages_arg)
        return [page] if page < num_pages else []
    elif ':' in pages_arg:
        start, end = map(int, pages_arg.split(':'))
        return list(range(start, min(end + 1, num_pages)))
    elif ',' in pages_arg:
        return [int(num) for num in pages_arg.split(',')]
    else:
        return list(range(num_pages))



# def convert_pdf_to_png(pdf_path, pages_arg, resolution=300, outpath = None):
#     doc = fitz.open(pdf_path)
#     num_pages = len(doc)
#     name = os.path.splitext(os.path.basename(pdf_path))[0]
    
#     if pages_arg.isdigit():
#         page = int(pages_arg)

#         if page < num_pages:
#             pages_to_convert = [page]
#         else:
#             print('Invalid page range.')
#             return 
#     elif pages_arg:
#         if ':' in pages_arg:
#             start, end = map(int, pages_arg.split(':'))
#             pages_to_convert = list(range(start, min(end + 1, num_pages)))
#         elif ',' in pages_arg:
#             pages_to_convert = [int(num) for num in pages_arg.split(',')]
#     else:
#         pages_to_convert = range(num_pages)

    
#     os.chdir(os.path.dirname(pdf_path))
#     out_path = os.path.dirname(pdf_path)

#     # Start the timer
#     start_time = time.time()


#     for page_num in pages_to_convert:
#         if page_num < num_pages:
#             page = doc.load_page(page_num)
#             # Specify the zoom factor for the resolution.
#             zoom = resolution / 72
#             mat = fitz.Matrix(zoom, zoom)
#             pix = page.get_pixmap(matrix=mat)  # Render page to an image at the specified resolution
#             if outpath:
#                 output_image_path = os.path.join(outpath, f'{name}_p_{page_num}.png')
#             else:
#                 output_image_path = os.path.join(out_path, f'{name}_p_{page_num}.png')
#             pix.save(output_image_path)
#         print(f'Converted page {page_num}')

#     # End the timer and print the execution time
#     end_time = time.time()
#     print(f"Converted {len(pages_to_convert)} pages to images at {resolution} DPI in {output_image_path}")
#     print(f"Execution time: {end_time - start_time} seconds")

if __name__ == '__main__':
    if len(sys.argv) > 3:
        pdf_path = sys.argv[1]
        pages_arg = sys.argv[2]
        outpath = sys.argv[3]
        convert_pdf_to_png(pdf_path, pages_arg, outpath=outpath)
        
    elif sys.argv == ['']:
        pdf_paths = ['/Users/gabrielmiyazawa/Desktop/Cods/algs/try_pngs/IMSLP15870-Sibelius_-_4_Pieces_for_Violin_or_Cello_and_Piano,_Op.78_Nos.1-3.pdf']
        pages_arg = ''
        custom_out = '/Users/gabrielmiyazawa/Desktop/Cods/algs/try_pngs/sib_violin/'
        for pdf_path in pdf_paths:
            convert_pdf_to_png(pdf_path, pages_arg, 400, outpath=custom_out)
    else:
        print("Usage: python script.py <pdf_path> <pages (x,y ; x:y ; blank for all)> <output_path>")






