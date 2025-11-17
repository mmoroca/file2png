# --- file2png v3: Simplified & Smart ---
# --- Converts any file to PNG and vice versa. Auto-detects ZIPs. ---
# --- Based on MrTalida's design | Refactor by @mmoroca + Gemini ---
# --- NOV 17, 2025 ---

from PIL import Image
import os
import argparse
import math
import zipfile
import io

# --- Fixed Configuration ---
# Complexity removed: always 8 bits, pure Black & White.
WHITE = 255
BLACK = 0
GRAY_PADDING = 127 
BITS_PER_BYTE = 8

# --- Main Logic ---

def process_file(source_path, dest_path):
    """
    Detects the direction of conversion based on file extensions.
    """
    ext_source = os.path.splitext(source_path)[1].lower()
    
    if ext_source == '.png':
        decode_png(source_path, dest_path)
    else:
        encode_file(source_path, dest_path)

# ----------------------------------------------------------------------
## ENCODING: File -> (ZIP in memory if needed) -> PNG
# ----------------------------------------------------------------------

def encode_file(file_path, png_dest_path):
    ext = os.path.splitext(file_path)[1].lower()
    binary_data = b""

    print(f"📂 Processing: {file_path}")

    try:
        # CASE A: The file is ALREADY a ZIP. Do not re-compress.
        if ext == '.zip':
            print("ℹ️  File is already a ZIP. Reading raw bytes...")
            with open(file_path, 'rb') as f:
                binary_data = f.read()

        # CASE B: Any other file. Compress to ZIP in memory.
        else:
            print("ℹ️  Standard file detected. Compressing to ZIP in memory...")
            buffer_zip = io.BytesIO()
            with zipfile.ZipFile(buffer_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
                clean_name = os.path.basename(file_path)
                zf.write(file_path, arcname=clean_name)
            binary_data = buffer_zip.getvalue()
            print(f"   (Compressed size: {len(binary_data)} bytes)")

        # --- Convert Bytes to Bits (Visualization) ---
        print("🎨 Generating bitmap...")
        image_bits = ""
        
        for byte_val in binary_data:
            # Convert to standard binary (8 bits, zero-padded to the left)
            image_bits += bin(byte_val)[2:].zfill(BITS_PER_BYTE)

        # --- Calculate Square Dimensions ---
        num_bits = len(image_bits)
        side = math.ceil(math.sqrt(num_bits))
        
        img = Image.new('L', (side, side))
        pixels = img.load()

        # --- Draw Pixels ---
        index = 0
        for y in range(side):
            for x in range(side):
                if index < num_bits:
                    bit = image_bits[index]
                    pixels[x, y] = WHITE if bit == '1' else BLACK
                    index += 1
                else:
                    pixels[x, y] = GRAY_PADDING

        # --- Save ---
        if not png_dest_path.lower().endswith('.png'):
            png_dest_path += '.png'
            
        img.save(png_dest_path)
        print(f"✅ Image saved to: {png_dest_path} ({side}x{side} px)")

    except Exception as e:
        print(f"❌ Encoding error: {e}")

# ----------------------------------------------------------------------
## DECODING: PNG -> Bytes -> Extract ZIP
# ----------------------------------------------------------------------

def decode_png(png_path, dest_folder):
    print(f"🔍 Reading image: {png_path}")

    try:
        img = Image.open(png_path).convert('L')
        width, height = img.size
        read_bits = ""

        # 1. Extract bits from image
        for y in range(height):
            for x in range(width):
                val = img.getpixel((x, y))
                if val == BLACK: read_bits += '0'
                elif val == WHITE: read_bits += '1'
                # Gray (padding) is ignored

        if not read_bits:
            print("❌ Error: Image is empty or contains no valid data.")
            return

        # 2. Reconstruct Bytes
        bytes_data = bytearray()
        for i in range(0, len(read_bits), BITS_PER_BYTE):
            block = read_bits[i:i + BITS_PER_BYTE]
            
            # Protection against loose bits (padding errors)
            if len(block) < BITS_PER_BYTE:
                block = block.ljust(BITS_PER_BYTE, '0')
            
            bytes_data.append(int(block, 2))

        # 3. Decompress
        # Since we always store a ZIP structure (native or created),
        # we always attempt to unzip into the destination folder.
        print("📦 Extracting content...")
        
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)

        memory_buffer = io.BytesIO(bytes_data)
        
        try:
            with zipfile.ZipFile(memory_buffer, 'r') as zf:
                zf.extractall(path=dest_folder)
                names = zf.namelist()
                print(f"✅ Files recovered in '{dest_folder}': {names}")
        except zipfile.BadZipFile:
            print("❌ Error: Image data does not form a valid ZIP file.")

    except Exception as e:
        print(f"❌ Decoding error: {e}")

# ----------------------------------------------------------------------
## Entry Point
# ----------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="File <-> PNG Converter (Simplified & Smart)")
    parser.add_argument('source', help="File to convert OR .png image to read")
    parser.add_argument('destination', help="Output PNG filename OR Destination folder for extraction")

    args = parser.parse_args()

    process_file(args.source, args.destination)