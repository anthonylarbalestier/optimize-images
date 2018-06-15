#!/usr/bin/env python3
# encoding: utf-8
"""
A little CLI utility written in Python to apply some compression to images
using PIL

© 2018 Victor Domingos (MIT License)
"""
import os
import contextlib
import io 

from pathlib import Path
from argparse import ArgumentParser
from PIL import Image


SUPPORTED_FORMATS = ['png', 'jpg', 'jpeg', 'gif']


parser = ArgumentParser(description="Optimize images")

parser.add_argument('path',
    nargs="?", 
    type=str,
    help='The path to the image file or to the folder containing the images to be optimized.')

parser.add_argument('-nr', "--no-recursion",
    action='store_true',
    help="Don't recurse through subdirectories")


def search_images(dirpath, recursive=True):
    if recursive:
        for root, dirs, files in os.walk(dirpath):
            for f in files:
                if not os.path.isfile(os.path.join(root, f)):
                    continue
                extension = os.path.splitext(f)[1][1:]
                if extension.lower() in SUPPORTED_FORMATS:
                    yield os.path.join(root, f)
    else:
        with os.scandir(dirpath) as directory:
            for f in directory:
                if not os.path.isfile(os.path.normpath(f)):
                    continue
                extension = os.path.splitext(f)[1][1:]
                if extension.lower() in SUPPORTED_FORMATS:
                    yield os.path.normpath(f)


def do_optimization(image_file):
    img = Image.open(image_file)
    img_format = img.format
    
    # Remove EXIF data
    data = list(img.getdata())
    no_exif_img = Image.new(img.mode, img.size)
    no_exif_img.putdata(data)
    
    saved_bytes = 0

    while True:
        with io.BytesIO() as file_bytes:
            no_exif_img.save(file_bytes, progressive=True, optimize=True, quality=80, format=img_format)
            
            saved_bytes = os.path.getsize(image_file) - file_bytes.tell()
            if saved_bytes > 100:
                start_size = os.path.getsize(image_file) / 1024
                end_size = file_bytes.tell() / 1024
                saved = saved_bytes / 1024
                percent = saved / start_size * 100
                print(f'✅ {image_file} -> {end_size:.1f}kB [{saved:.1f}kB/{percent:.1f}%]')
                file_bytes.seek(0, 0)
                with open(image_file, 'wb') as f_output:
                    f_output.write(file_bytes.read())
            else:
                print(f'🔴 [SKIPPED] {image_file}')
                saved_bytes = 0
            break
    return saved_bytes


def main(*args):
    args = parser.parse_args(*args)
    recursive = not args.no_recursion
    found_files = 0
    total_optimized = 0
    total_bytes_saved = 0


    # if single file, do_optimization()
    # else search_images and loop through them with do_optimization()
    if not args.path :
        parser.exit(status=0, message="\nPlease specifiy the path of the image or folder to process.\n\n")

    if os.path.isdir(args.path):
        if recursive:
            recursion_txt = ""

        print(f"\nSearching and optimizing image files in {args.path}\n")

        images = (i for i in search_images(args.path, recursive=recursive))
        for image in images:
            found_files += 1
            bytes_saved = int(do_optimization(image))
            if bytes_saved:
                total_optimized += 1
                total_bytes_saved += bytes_saved

    elif os.path.isfile(args.path):
        found_files = 1
        total_optimized = 0
        total_bytes_saved = 0
        do_optimization(args.path)
    else:
        print("No image files were found. Please enter a valid path to the image file or")
        print("the folder containing any images to be processed.")




    

    if found_files:
        total_saved = total_bytes_saved / 1024
        average = total_bytes_saved / found_files /1024
        print(f"{40*'-'}\n")
        print(f"   FILES FOUND: {found_files}")
        print(f"   Total files optimized: {total_optimized}")    
        print(f"   Total space saved: {total_saved:.1f}kB (avg: {average:.1f}kB)\n")  
    else:
        print("No image files were found in the specified directory.\n")
    

if __name__ == "__main__":
    main()

