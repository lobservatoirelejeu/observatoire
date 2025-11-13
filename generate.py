import os
import subprocess
import glob
import hashlib
import json
import shutil
from pathlib import Path

def load_labels():
    """Load bird labels from labels.txt"""
    labels = {}
    try:
        with open('labels.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and ' ' in line:
                    parts = line.split(' ', 1)
                    bird_id = parts[0]
                    if ',' in parts[1]:
                        common_name, scientific_name = parts[1].split(', ', 1)
                        labels[bird_id] = {
                            "common": common_name.strip(),
                            "scientific": scientific_name.strip()
                        }
    except FileNotFoundError:
        print("labels.txt not found")
    return labels

def process_videos():
    # Load labels from labels.txt
    labels = load_labels()
    
    # Get all videos and images
    video_files = glob.glob("videos/*.mp4")
    image_files = glob.glob("images_cropped/*.png")  # Only PNG files
    
    if not video_files and not image_files:
        print("No video or image files found")
        return
    
    birds_folder = "birds"
    sounds_folder = "sounds"
    images_folder = "images"
    Path(birds_folder).mkdir(exist_ok=True)
    Path(sounds_folder).mkdir(exist_ok=True)
    Path(images_folder).mkdir(exist_ok=True)
    print(f"Processing {len(video_files)} videos and {len(image_files)} images...")
    print(f"Outputs: sounds -> {sounds_folder}/, images -> {images_folder}/")
    
    # Initialize birdmap for hash to bird name mapping
    birdmap = {}
    
    # Group files by bird ID for paired processing
    file_pairs = {}
    
    # Add videos to file pairs
    for video_file in video_files:
        filename = Path(video_file).stem
        # Extract ID from format "L_Observatoire - Chant à déterminer(ID).mp4"
        try:
            if '(' in filename and ')' in filename:
                start_idx = filename.rfind('(') + 1
                end_idx = filename.rfind(')')
                bird_id = filename[start_idx:end_idx]
            else:
                bird_id = filename
        except:
            bird_id = filename
        
        if bird_id not in file_pairs:
            file_pairs[bird_id] = {}
        file_pairs[bird_id]['video'] = {
            'path': video_file,
            'filename': filename
        }
    
    # Add images to file pairs
    for image_file in image_files:
        filename = Path(image_file).stem
        # Extract ID from format "ID.png"
        bird_id = filename
        
        if bird_id not in file_pairs:
            file_pairs[bird_id] = {}
        file_pairs[bird_id]['image'] = {
            'path': image_file,
            'filename': filename
        }
    
    # VALIDATION: Check that every bird has all required components
    print("Validating all birds have complete data...")
    missing_components = []
    
    for bird_id, files in file_pairs.items():
        has_video = 'video' in files
        has_image = 'image' in files
        has_label = bird_id in labels
        
        missing = []
        if not has_video:
            missing.append("video/sound")
        if not has_image:
            missing.append("image")
        if not has_label:
            missing.append("label")
        
        if missing:
            missing_components.append(f"Bird ID {bird_id}: missing {', '.join(missing)}")
    
    # If any bird is missing components, cancel generation
    if missing_components:
        print("\n❌ GENERATION CANCELLED - Missing required components:")
        for missing in missing_components:
            print(f"  {missing}")
        print("\nAll birds must have:")
        print("  - Video file in videos/ folder")
        print("  - PNG image in images/ folder") 
        print("  - Label entry in labels.txt")
        return
    
    print("✅ All birds have complete data (video, image, label)")
    print(f"Proceeding with generation of {len(file_pairs)} birds...\n")
    
    # Process all file pairs
    bird_index = 1  # Start ID from 1
    used_codes = set()  # Track used codes to detect collisions
    
    for bird_id, files in file_pairs.items():

        # Generate unique hash code with collision detection
        attempts = 0
        init = 0
        max_attempts = 1000  # Safety limit
        
        while attempts < max_attempts:
            # Generate 3-digit ID format (001, 002, 003, etc.)
            three_digit_id = f"{bird_index + init + attempts:03d}"
            
            # Generate hash using 3-digit ID (last 4 chars of MD5)
            hash_object = hashlib.md5(three_digit_id.encode())
            bird_code = hash_object.hexdigest()[-4:]
            
            # Check for collision
            if bird_code not in used_codes:
                used_codes.add(bird_code)
                break
            
            init = 200
            attempts += 1
            print(f"  ⚠️ Collision detected for {bird_code}, trying next ID...")
        
        if attempts >= max_attempts:
            print(f"❌ GENERATION FAILED: Could not generate unique code for bird {bird_id}")
            return
        
        # Get bird names from labels and add ID (we know they exist from validation)
        bird_data = labels[bird_id].copy()  # Copy to avoid modifying original
        bird_data['id'] = three_digit_id  # Add 3-digit ID field
        birdmap[bird_code] = bird_data
        
        print(f"Processing bird ID {bird_id} -> {bird_code} (#{three_digit_id}: {bird_data['common']})...")
        
        # Track success of each component
        mp3_success = False
        jpg_success = False
        
        # Process video (sound generation)
        video_path = files['video']['path']
        print(f"  Video: {files['video']['filename']}")
        
        try:
            subprocess.run([
                "ffmpeg", "-i", video_path, "-vn", "-acodec", "libmp3lame",
                "-q:a", "0", "-y", f"{sounds_folder}/{bird_code}.mp3"
            ], capture_output=True, check=True)
            print(f"    ✓ {bird_code}.mp3")
            mp3_success = True
        except Exception as e:
            print(f"    ✗ {bird_code}.mp3 failed: {e}")
        
        # Process image
        image_path = files['image']['path']
        print(f"  Image: {files['image']['filename']}")
        
        try:
            shutil.copy2(image_path, f"{images_folder}/{bird_code}.jpg")
            print(f"    ✓ {bird_code}.jpg copied")
            jpg_success = True
        except Exception as e:
            print(f"    ✗ {bird_code}.jpg copy failed: {e}")
        
        # Check if all components succeeded
        if not (mp3_success and jpg_success):
            print(f"\n❌ GENERATION FAILED for bird {bird_id} ({bird_data['common']})")
            print("Not all components were successfully generated.")
            print("Cleaning up and cancelling generation...")
            
            # Clean up any partial files
            sound_file = f"{sounds_folder}/{bird_code}.mp3"
            image_file = f"{images_folder}/{bird_code}.jpg"
            
            if os.path.exists(sound_file):
                os.remove(sound_file)
                print(f"Removed: {sound_file}")
            if os.path.exists(image_file):
                os.remove(image_file)
                print(f"Removed: {image_file}")
            
            return

        print(f"  → Successfully processed all components for bird {bird_id}")
        bird_index += 1  # Increment for next bird
    
    # Save birdmap.json
    try:
        with open('birdmap.json', 'w', encoding='utf-8') as f:
            json.dump(birdmap, f, indent=2, ensure_ascii=False)
        print(f"✓ birdmap.json created with {len(birdmap)} entries")
    except Exception as e:
        print(f"✗ Failed to create birdmap.json: {e}")
    
    print("Done!")

if __name__ == "__main__":
    process_videos()