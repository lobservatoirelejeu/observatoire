import os
import json
from pathlib import Path

try:
    import qrcode
    import qrcode.image.pil
    from PIL import Image
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    print("Error: qrcode library not available. Install with: pip install qrcode[pil]")

def generate_qr_with_logo(url, output_path):
    """Generate a QR code with logo in center, black on white, no borders"""
    if not QR_AVAILABLE:
        return False
    try:
        from PIL import Image, ImageDraw
        import os
        
        # Create QR code with 1 square border and larger size for logo insertion
        qr = qrcode.QRCode(
            version=1, 
            box_size=10, 
            border=1,  # 1 square white margin
            image_factory=qrcode.image.pil.PilImage
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Create QR image - black on white
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to RGBA for better processing
        qr_img = qr_img.convert("RGBA")
        qr_width, qr_height = qr_img.size
        
        # Load and process logo (PNG only)
        logo_path_png = "assets/logo.png"
        
        logo = None
        if os.path.exists(logo_path_png):
            logo = Image.open(logo_path_png)
        
        if logo:
            # Convert logo to RGBA
            logo = logo.convert("RGBA")
            
            # Calculate logo size (about 1/4 of QR code size for more visibility)
            logo_size = min(qr_width, qr_height) // 4
            
            # Resize logo maintaining aspect ratio
            logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Calculate position to center logo on QR code
            logo_w, logo_h = logo.size
            paste_x = (qr_width - logo_w) // 2
            paste_y = (qr_height - logo_h) // 2
            
            # Paste logo directly onto QR code with alpha blending
            qr_img.paste(logo, (paste_x, paste_y), logo)
        
        # Convert to RGB to remove alpha channel (solid white background)
        final_img = Image.new("RGB", qr_img.size, (255, 255, 255))
        final_img.paste(qr_img, mask=qr_img.split()[-1] if qr_img.mode == "RGBA" else None)
        
        # Save as PNG
        final_img.save(output_path, 'PNG')
        return True
    except Exception as e:
        print(f"QR generation error for {output_path}: {e}")
        return False

def generate_transparent_qr(bird_code, qr_folder, bird_name=None):
    """Generate a QR code for a specific bird"""
    url = f"https://lobservatoirelejeu.github.io/observatoire/oiseau#{bird_code}"
    
    # Include bird name in filename, replacing spaces with underscores
    if bird_name:
        # Clean bird name for filename: replace spaces with underscores, remove special chars
        clean_name = bird_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        # Remove other problematic characters
        clean_name = ''.join(c for c in clean_name if c.isalnum() or c in '_-')
        qr_filename = f"{bird_code}_{clean_name}.png"
    else:
        qr_filename = f"{bird_code}.png"
    
    qr_path = os.path.join(qr_folder, qr_filename)
    return generate_qr_with_logo(url, qr_path)

def generate_gallery_qr(qr_folder):
    """Generate a QR code for the gallery page"""
    url = "https://lobservatoirelejeu.github.io/observatoire/galerie"
    qr_filename = "galerie.png"
    qr_path = os.path.join(qr_folder, qr_filename)
    return generate_qr_with_logo(url, qr_path)

def load_birdmap():
    """Load bird data from birdmap.json"""
    try:
        with open('birdmap.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: birdmap.json not found!")
        print("Please run generate.py first to create the birdmap.json file.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in birdmap.json: {e}")
        return None

def generate_all_qrcodes():
    """Generate QR codes for all birds in birdmap.json and gallery"""
    print("QR Code Generator")
    print("=" * 50)
    
    # Check if qrcode library is available
    if not QR_AVAILABLE:
        return
    
    # Load bird data
    birdmap = load_birdmap()
    if not birdmap:
        return
    
    # Create output folder
    qrcodes_folder = "qrcodes"
    Path(qrcodes_folder).mkdir(exist_ok=True)
    
    print(f"Generating QR codes for {len(birdmap)} birds + gallery...")
    print(f"Output folder: {qrcodes_folder}")
    print("QR codes will be black on white with logo in center (1 square border)")
    print()
    
    # Track success/failure
    success_count = 0
    failed_birds = []
    
    # Generate QR code for gallery first
    print("Generating QR for gallery: Galerie des Oiseaux")
    if generate_gallery_qr(qrcodes_folder):
        print("  ✓ gallery.png created")
        success_count += 1
    else:
        print("  ✗ Failed to create gallery.png")
        failed_birds.append("Gallery (Galerie des Oiseaux)")
    
    print()
    
    # Generate QR code for each bird
    for bird_code, bird_data in birdmap.items():
        bird_name = bird_data.get('common', 'Unknown Bird')
        
        print(f"Generating QR for {bird_code}: {bird_name} (hash: {bird_code})")
        
        if generate_transparent_qr(bird_code, qrcodes_folder, bird_name):
            # Clean bird name for display
            clean_name = bird_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            clean_name = ''.join(c for c in clean_name if c.isalnum() or c in '_-')
            print(f"  ✓ {bird_code}_{clean_name}.png created")
            success_count += 1
        else:
            print(f"  ✗ Failed to create QR for {bird_name}")
            failed_birds.append(f"{bird_code} ({bird_name})")
    
    # Summary
    print()
    print("=" * 50)
    print(f"QR Code Generation Complete!")
    print(f"Successfully generated: {success_count}/{len(birdmap) + 1} QR codes")
    
    if failed_birds:
        print(f"Failed to generate QR codes for:")
        for failed in failed_birds:
            print(f"  - {failed}")
    else:
        print("All QR codes generated successfully!")
    
    print(f"\nQR codes saved to: {os.path.abspath(qrcodes_folder)}")
    print("QR codes are black on white PNG images with logo in center and 1 square border.")

def main():
    try:
        generate_all_qrcodes()
    except KeyboardInterrupt:
        print("\nGeneration cancelled by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()