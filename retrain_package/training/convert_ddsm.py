#!/usr/bin/env python3
"""training/convert_ddsm.py
CBIS-DDSM DICOM Parser and converter to PNG format.
"""
import argparse
import os
import glob
import pydicom
from PIL import Image
import numpy as np

def convert_dicom_to_png(dicom_path, output_path, normalize=True):
    """Convert DICOM file to PNG format."""
    # Read DICOM file
    ds = pydicom.dcmread(dicom_path)
    
    # Extract pixel array
    pixel_array = ds.pixel_array
    
    # Normalize pixel values to 0-255 range
    if normalize:
        pixel_array = pixel_array.astype(float)
        pixel_array = (pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min())
        pixel_array = (pixel_array * 255).astype(np.uint8)
    
    # Convert to PIL Image
    img = Image.fromarray(pixel_array)
    
    # Save as PNG
    img.save(output_path, 'PNG')
    return img

def process_cbis_ddsm(input_dir, output_dir, class_mapping=None):
    """Process CBIS-DDSM dataset."""
    if class_mapping is None:
        # Default mapping for CBIS-DDSM
        class_mapping = {
            'Calc-Test': 'malignant',
            'Calc-Training': 'malignant',
            'Mass-Test': 'malignant',
            'Mass-Training': 'malignant',
            'Normal': 'benign'
        }
    
    # Create output directories
    for class_name in set(class_mapping.values()):
        os.makedirs(os.path.join(output_dir, class_name), exist_ok=True)
    
    # Process each subdirectory
    for subdir in os.listdir(input_dir):
        subdir_path = os.path.join(input_dir, subdir)
        if not os.path.isdir(subdir_path):
            continue
            
        # Determine class based on subdirectory name
        class_name = None
        for key, value in class_mapping.items():
            if key in subdir:
                class_name = value
                break
        
        if class_name is None:
            print(f"Warning: Could not determine class for {subdir}")
            continue
        
        # Process DICOM files in subdirectory
        dicom_files = glob.glob(os.path.join(subdir_path, "*.dcm"))
        print(f"Processing {len(dicom_files)} DICOM files in {subdir} -> {class_name}")
        
        for i, dicom_file in enumerate(dicom_files):
            try:
                # Generate output filename
                basename = os.path.splitext(os.path.basename(dicom_file))[0]
                output_filename = f"{basename}.png"
                output_path = os.path.join(output_dir, class_name, output_filename)
                
                # Convert DICOM to PNG
                convert_dicom_to_png(dicom_file, output_path)
                print(f"Converted {dicom_file} -> {output_path}")
            except Exception as e:
                print(f"Error converting {dicom_file}: {e}")

def main(args):
    print(f"Converting CBIS-DDSM dataset from {args.input_dir} to {args.output_dir}")
    
    # Parse class mapping if provided
    class_mapping = None
    if args.class_mapping:
        class_mapping = {}
        for mapping in args.class_mapping:
            key, value = mapping.split(':')
            class_mapping[key] = value
    
    # Process dataset
    process_cbis_ddsm(args.input_dir, args.output_dir, class_mapping)
    print("Conversion completed!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert CBIS-DDSM DICOM files to PNG")
    parser.add_argument("--input_dir", required=True, help="Input directory containing CBIS-DDSM DICOM files")
    parser.add_argument("--output_dir", required=True, help="Output directory for PNG files")
    parser.add_argument("--class_mapping", nargs='+', help="Class mapping (e.g., 'Calc-Test:malignant')")
    
    args = parser.parse_args()
    main(args)