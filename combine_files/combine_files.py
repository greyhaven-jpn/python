import os
from datetime import datetime

# =========================
# 🔧 HARD CODE PARAMETERS
# =========================
SOURCE_DIR = '/Users/user/Documents/Project/Mac Apps/ImageCompressor/ImageCompressor/ImageCompressor/'

# OUTPUT otomatis sesuai lokasi eksekusi
OUTPUT_DIR = os.getcwd()

# Extensions yang dianggap text-based
ALLOWED_EXTENSIONS = [".swift"]

# =========================
# 🚀 MAIN PROGRAM
# =========================

def combine_files():
    print(f"📂 Current working directory (OUTPUT): {OUTPUT_DIR}")

    if not os.path.exists(SOURCE_DIR):
        print(f"❌ Source directory not found: {SOURCE_DIR}")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 Created output directory: {OUTPUT_DIR}")

    folder_name = os.path.basename(os.path.normpath(SOURCE_DIR))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{folder_name}_{timestamp}.txt"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    print(f"📝 Output file: {output_path}")

    with open(output_path, "w", encoding="utf-8") as outfile:
        for filename in sorted(os.listdir(SOURCE_DIR)):
            file_path = os.path.join(SOURCE_DIR, filename)

            if not os.path.isfile(file_path):
                continue

            _, ext = os.path.splitext(filename)

            if ext.lower() not in ALLOWED_EXTENSIONS:
                print(f"⏭️ Skipped: {filename}")
                continue

            print(f"📄 Processing: {filename}")

            try:
                with open(file_path, "r", encoding="utf-8") as infile:
                    outfile.write(f"\n===== START: {filename} =====\n")
                    outfile.write(infile.read())
                    outfile.write(f"\n===== END: {filename} =====\n\n")
            except Exception as e:
                print(f"⚠️ Error reading {filename}: {e}")

    print("✅ Done combining files!")


if __name__ == "__main__":
    combine_files()