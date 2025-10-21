try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_L
except ImportError:
    print("qrcode library is not installed. Please install it using:")
    print("pip install qrcode[pil]")
    exit(1)

import os
from pathlib import Path

def generate_qr_codes():
    """
    Generate QR codes for all video files in the videos directory.
    Each QR code will link to https://o5x.github.io/duonat/video#{video_id}
    """
    # Base URL for the video links
    base_url = "https://o5x.github.io/duonat/video#"
    
    # Path to the videos directory
    videos_dir = Path("videos")
    
    # Create a directory for QR codes if it doesn't exist
    qr_codes_dir = Path("qr_codes")
    qr_codes_dir.mkdir(exist_ok=True)
    
    # Get all MP4 files in the videos directory
    video_files = list(videos_dir.glob("*.mp4"))
    
    if not video_files:
        print("No video files found in the videos directory.")
        return
    
    print(f"Found {len(video_files)} video files:")
    
    for video_file in video_files:
        # Extract the video ID from the filename (without extension)
        video_id = video_file.stem
        
        # Create the URL for this video
        video_url = f"{base_url}{video_id}"
        
        print(f"Generating QR code for video {video_id}: {video_url}")
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(video_url)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save the QR code image
        qr_code_filename = qr_codes_dir / f"qr_code_{video_id}.png"
        with open(qr_code_filename, 'wb') as f:
            img.save(f, 'PNG')
        
        print(f"QR code saved: {qr_code_filename}")
    
    print(f"\nAll QR codes have been generated and saved in the '{qr_codes_dir}' directory.")

def generate_single_qr_code(video_id):
    """
    Generate a QR code for a specific video ID.
    
    Args:
        video_id (str): The video ID to generate QR code for
    """
    base_url = "https://o5x.github.io/duonat/video#"
    video_url = f"{base_url}{video_id}"
    
    # Create a directory for QR codes if it doesn't exist
    qr_codes_dir = Path("qr_codes")
    qr_codes_dir.mkdir(exist_ok=True)
    
    print(f"Generating QR code for video {video_id}: {video_url}")
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    qr.add_data(video_url)
    qr.make(fit=True)
    
    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save the QR code image
    qr_code_filename = qr_codes_dir / f"qr_code_{video_id}.png"
    with open(qr_code_filename, 'wb') as f:
        img.save(f, 'PNG')
    
    print(f"QR code saved: {qr_code_filename}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Generate QR code for specific video ID provided as command line argument
        video_id = sys.argv[1]
        generate_single_qr_code(video_id)
    else:
        # Generate QR codes for all videos
        generate_qr_codes()