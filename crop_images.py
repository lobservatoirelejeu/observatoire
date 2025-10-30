import os
import cv2
import numpy as np
from pathlib import Path

def find_non_blank_bounds(image):
    """Find the bounding box of non-transparent/non-blank content in an image"""
    # Check if image has alpha channel (transparency)
    if image.shape[2] == 4:
        # PNG with alpha channel - use alpha to find content
        alpha = image[:, :, 3]
        # Find non-transparent pixels (alpha > 0)
        non_transparent = alpha > 0
        
        # Find the bounding box of non-transparent pixels
        rows = np.any(non_transparent, axis=1)
        cols = np.any(non_transparent, axis=0)
        
        if not np.any(rows) or not np.any(cols):
            # If no non-transparent pixels, return full image bounds
            return 0, 0, image.shape[1], image.shape[0]
        
        min_y, max_y = np.where(rows)[0][[0, -1]]
        min_x, max_x = np.where(cols)[0][[0, -1]]
        
        return min_x, min_y, max_x + 1, max_y + 1
    
    else:
        # No alpha channel - use color-based detection
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Find non-white pixels (assuming white background)
        # You can adjust the threshold (240) if needed
        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours to get bounding box
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            # If no contours found, return full image bounds
            return 0, 0, image.shape[1], image.shape[0]
        
        # Get bounding box of all contours combined
        x_coords = []
        y_coords = []
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            x_coords.extend([x, x + w])
            y_coords.extend([y, y + h])
        
        min_x = max(0, min(x_coords))
        min_y = max(0, min(y_coords))
        max_x = min(image.shape[1], max(x_coords))
        max_y = min(image.shape[0], max(y_coords))
        
        return min_x, min_y, max_x, max_y

def analyze_all_images(input_folder):
    """Analyze all images to find the biggest aspect ratio"""
    print("Analyzing all images to find biggest aspect ratio...")
    
    # Track actual content dimensions and aspect ratios
    content_dimensions = []
    aspect_ratios = []
    
    image_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.png')]
    
    for filename in image_files:
        filepath = os.path.join(input_folder, filename)
        image = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)  # Preserve alpha channel
        
        if image is None:
            print(f"Warning: Could not read {filename}")
            continue
        
        # Apply bottom trimming before analysis
        if image.shape[0] > 160:
            image_trimmed = image[:-160, :]
        else:
            image_trimmed = image
        
        min_x, min_y, max_x, max_y = find_non_blank_bounds(image_trimmed)
        
        # Calculate content dimensions
        content_width = max_x - min_x
        content_height = max_y - min_y
        
        if content_height > 0:  # Avoid division by zero
            aspect_ratio = content_width / content_height
            content_dimensions.append((content_width, content_height))
            aspect_ratios.append(aspect_ratio)
            
            print(f"{filename}: content size {content_width}x{content_height}, aspect ratio {aspect_ratio:.2f}")
    
    if not content_dimensions:
        print("No valid images found!")
        return None
    
    # Find the biggest aspect ratio (widest image relative to height)
    max_aspect_ratio = max(aspect_ratios)
    max_aspect_index = aspect_ratios.index(max_aspect_ratio)
    target_width, target_height = content_dimensions[max_aspect_index]
    
    print(f"\nBiggest aspect ratio: {max_aspect_ratio:.2f} (width/height)")
    print(f"Target dimensions from biggest aspect ratio: {target_width}x{target_height}")
    print(f"All images will be sized to this dimension with content centered")
    
    return target_width, target_height

def crop_to_uniform_size(image, target_width, target_height):
    """Crop image to uniform size using target dimensions, after removing bottom 160 pixels"""
    # First, cut off the bottom 160 pixels
    if image.shape[0] > 160:
        image_trimmed = image[:-160, :]
    else:
        image_trimmed = image
    
    # Find the content bounds on the trimmed image
    min_x, min_y, max_x, max_y = find_non_blank_bounds(image_trimmed)
    
    # Extract just the content at original resolution
    content = image_trimmed[min_y:max_y, min_x:max_x]
    
    if content.size == 0:
        # If no content found, create empty canvas
        if len(image.shape) == 3 and image.shape[2] == 4:  # RGBA
            return np.zeros((target_height, target_width, 4), dtype=np.uint8)
        else:  # RGB
            return np.ones((target_height, target_width, 3), dtype=np.uint8) * 255
    
    # Create a canvas with target dimensions
    if len(image.shape) == 3:
        if image.shape[2] == 4:  # RGBA
            result = np.zeros((target_height, target_width, 4), dtype=np.uint8)
        else:  # RGB
            result = np.ones((target_height, target_width, 3), dtype=np.uint8) * 255  # White background
    else:  # Grayscale
        result = np.ones((target_height, target_width), dtype=np.uint8) * 255
    
    # Get content dimensions
    content_height, content_width = content.shape[:2]
    
    # If content is larger than target, resize it to fit
    if content_width > target_width or content_height > target_height:
        # Calculate scale factor to fit content in target dimensions
        scale_w = target_width / content_width
        scale_h = target_height / content_height
        scale = min(scale_w, scale_h)  # Use the smaller scale to ensure it fits
        
        new_width = int(content_width * scale)
        new_height = int(content_height * scale)
        
        # Resize content to fit
        content = cv2.resize(content, (new_width, new_height), interpolation=cv2.INTER_AREA)
        content_height, content_width = content.shape[:2]
    
    # Center the content in the canvas
    y_offset = (target_height - content_height) // 2
    x_offset = (target_width - content_width) // 2
    
    # Place the content in the center
    result[y_offset:y_offset + content_height, x_offset:x_offset + content_width] = content
    
    return result

def process_images(input_folder, output_folder, target_dimensions):
    """Process all images to uniform size using largest content bounds"""
    if target_dimensions is None:
        print("No target dimensions determined. Exiting.")
        return
    
    target_width, target_height = target_dimensions
    
    # Create output folder
    os.makedirs(output_folder, exist_ok=True)
    
    image_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.png')]
    processed_count = 0
    
    print(f"\nProcessing {len(image_files)} images...")
    print(f"Creating uniform {target_width}x{target_height} images with centered content...")
    
    for filename in image_files:
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        
        image = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)  # Preserve alpha channel
        if image is None:
            print(f"Warning: Could not read {filename}")
            continue
        
        # Create uniform size image with centered content
        uniform_image = crop_to_uniform_size(image, target_width, target_height)
        
        # Save with lossless compression
        if filename.lower().endswith('.png'):
            cv2.imwrite(output_path, uniform_image, [cv2.IMWRITE_PNG_COMPRESSION, 1])
        else:
            cv2.imwrite(output_path, uniform_image)
        processed_count += 1
        
        if processed_count % 10 == 0:
            print(f"Processed {processed_count}/{len(image_files)} images...")
    
    print(f"\nCompleted! Processed {processed_count} images.")
    print(f"Uniform images saved to: {output_folder}")
    print(f"All images are now {target_width}x{target_height} with centered bird content")

def main():
    # Configuration
    input_folder = "images_uncropped"  # Folder containing original images
    output_folder = "images_cropped"  # Output folder for cropped images
    
    print("Bird Image Cropping Tool")
    print("=" * 50)
    
    # Check if input folder exists
    if not os.path.exists(input_folder):
        print(f"Error: Input folder '{input_folder}' not found!")
        print("Please make sure the 'birds' folder exists with your images.")
        return
    
    # Analyze all images to find minimum dimensions
    target_dimensions = analyze_all_images(input_folder)
    
    if target_dimensions:
        # Ask for confirmation
        target_width, target_height = target_dimensions
        print(f"\nProceed with creating uniform {target_width}x{target_height} images? (y/n): ", end="")
        response = input().strip().lower()
        
        if response == 'y' or response == 'yes':
            process_images(input_folder, output_folder, target_dimensions)
        else:
            print("Processing cancelled.")

    
    
if __name__ == "__main__":
    main()