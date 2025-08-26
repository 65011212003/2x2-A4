from PIL import Image

def split_image_to_a4(image_path, output_prefix="page", landscape=True):
    # A4 size in pixels at 300 DPI
    a4_width, a4_height = (3508, 2480) if landscape else (2480, 3508)

    img = Image.open(image_path)
    img_width, img_height = img.size

    # Resize image to fit exactly 2x1 A4 pages (upper and lower)
    new_width = a4_width * 1
    new_height = a4_height * 2
    img = img.resize((new_width, new_height), Image.LANCZOS)

    # Split into 2 parts vertically (upper and lower)
    for i in range(2):
        left = 0
        upper = i * a4_height
        right = a4_width
        lower = upper + a4_height
        crop = img.crop((left, upper, right, lower))
        crop.save(f"{output_prefix}_{i+1}.jpg", "JPEG")

# Example usage
split_image_to_a4("BookFront.png", output_prefix="a4_part", landscape=True)
