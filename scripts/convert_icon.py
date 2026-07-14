import os
import sys
from PIL import Image

def convert_icon(src_path, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    if not os.path.exists(src_path):
        print(f"Error: Source image not found at {src_path}")
        sys.exit(1)
        
    img = Image.open(src_path)
    
    # Resize and save as PNG
    png_path = os.path.join(dest_dir, 'icon.png')
    # Use newer Pillow Resampling if available, fallback to ANTIALIAS for older Pillow
    try:
        resample_filter = Image.Resampling.LANCZOS
    except AttributeError:
        resample_filter = Image.ANTIALIAS
        
    img_resized = img.resize((256, 256), resample_filter)
    img_resized.save(png_path, format='PNG')
    
    # Save as ICO
    ico_path = os.path.join(dest_dir, 'icon.ico')
    img.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Icons saved successfully:\n  - {png_path}\n  - {ico_path}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python convert_icon.py <src_image_path> <dest_dir>")
        sys.exit(1)
    convert_icon(sys.argv[1], sys.argv[2])
