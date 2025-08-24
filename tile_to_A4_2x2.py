#!/usr/bin/env python3
"""
Split a single image into a 2x2 tiled poster, where EACH tile is exactly A4 size.
Outputs both PNG tiles (with correct DPI) and one PDF per tile at true A4 page size.

Dependencies:
  pip install pillow reportlab

Usage example:
  python tile_to_A4_2x2.py input.jpg --dpi 300 --mode cover --margin-mm 0 --outdir ./tiles

Notes:
- "cover" fills the total 2x2 A4 poster and crops any overflow (no white bars).
- "contain" fits the full image within the poster without cropping (may add white bars).
- DPI controls the pixel dimensions of the PNG exports. PDFs are true A4 regardless of DPI.

Author: ChatGPT
"""
import argparse
import os
from typing import Tuple
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

A4_MM = (210.0, 297.0)  # width, height in mm

def mm_to_inches(mm_value: float) -> float:
    return mm_value / 25.4

def a4_pixels(dpi: int) -> Tuple[int, int]:
    """Return (width_px, height_px) for A4 at given DPI."""
    w_in = mm_to_inches(A4_MM[0])
    h_in = mm_to_inches(A4_MM[1])
    return (int(round(w_in * dpi)), int(round(h_in * dpi)))

def resize_to_poster(img: Image.Image, target_size: Tuple[int, int], mode: str) -> Image.Image:
    """
    Resize/crop or letterbox the source 'img' to exactly target_size.
    mode = 'cover'  -> fill and crop (like CSS background-size: cover)
    mode = 'contain'-> fit inside, add white bars as needed
    """
    tw, th = target_size
    if mode == "cover":
        # scale so the image covers the target area, then crop center
        scale = max(tw / img.width, th / img.height)
        new_w = int(round(img.width * scale))
        new_h = int(round(img.height * scale))
        img_resized = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - tw) // 2
        top = (new_h - th) // 2
        return img_resized.crop((left, top, left + tw, top + th))
    elif mode == "contain":
        # fit entire image and paste onto white background
        scale = min(tw / img.width, th / img.height)
        new_w = int(round(img.width * scale))
        new_h = int(round(img.height * scale))
        img_resized = img.resize((new_w, new_h), Image.LANCZOS)
        bg = Image.new("RGB", (tw, th), (255, 255, 255))
        left = (tw - new_w) // 2
        top = (th - new_h) // 2
        bg.paste(img_resized, (left, top))
        return bg
    else:
        raise ValueError("mode must be 'cover' or 'contain'")

def save_tile_png(tile: Image.Image, path: str, dpi: int):
    # Ensure RGB and set DPI metadata
    if tile.mode != "RGB":
        tile = tile.convert("RGB")
    tile.save(path, format="PNG", dpi=(dpi, dpi))

def save_tile_pdf(tile: Image.Image, path: str, margin_mm: float = 0.0):
    """
    Save one PDF page at true A4 size and draw the tile to fill the page
    with the specified margins (in mm).
    """
    if tile.mode != "RGB":
        tile = tile.convert("RGB")
    c = canvas.Canvas(path, pagesize=A4)
    page_w, page_h = A4  # points
    margin_pt = margin_mm * mm
    draw_x = margin_pt
    draw_y = margin_pt
    draw_w = page_w - 2 * margin_pt
    draw_h = page_h - 2 * margin_pt

    # Maintain aspect ratio; A4 tile should already match aspect but this is safe
    tile_ar = tile.width / tile.height
    page_ar = draw_w / draw_h
    if tile_ar > page_ar:
        # fit by width
        render_w = draw_w
        render_h = draw_w / tile_ar
        render_x = draw_x
        render_y = draw_y + (draw_h - render_h) / 2
    else:
        # fit by height
        render_h = draw_h
        render_w = draw_h * tile_ar
        render_x = draw_x + (draw_w - render_w) / 2
        render_y = draw_y

    img_reader = ImageReader(tile)
    c.drawImage(img_reader, render_x, render_y, width=render_w, height=render_h, preserveAspectRatio=True, mask='auto')
    c.showPage()
    c.save()

def main():
    parser = argparse.ArgumentParser(description="Split an image into 2x2 A4 tiles (PNG + PDF).")
    parser.add_argument("input", help="Path to input image (any format Pillow can read).")
    parser.add_argument("--outdir", default="./tiles", help="Output directory. Default: ./tiles")
    parser.add_argument("--prefix", default="tile", help="Output filename prefix. Default: tile")
    parser.add_argument("--dpi", type=int, default=300, help="DPI for PNG tiles (300 is print-friendly).")
    parser.add_argument("--mode", choices=["cover", "contain"], default="cover",
                        help="How to fit the image into the total 2x2 A4 poster. Default: cover")
    parser.add_argument("--margin-mm", type=float, default=0.0,
                        help="Page margin (for PDFs) in millimeters. Default: 0 (edge-to-edge)")

    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # Compute A4 and full poster sizes in pixels
    a4_w_px, a4_h_px = a4_pixels(args.dpi)
    poster_w_px, poster_h_px = a4_w_px * 2, a4_h_px * 2

    # Load image
    img = Image.open(args.input)
    # Convert to RGB to avoid weird modes (e.g. palette)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    # Prepare poster-sized image (exact pixel size)
    poster = resize_to_poster(img, (poster_w_px, poster_h_px), args.mode)

    # Slice into 2x2 tiles
    tiles = []
    for row in range(2):
        for col in range(2):
            left = col * a4_w_px
            top = row * a4_h_px
            right = left + a4_w_px
            bottom = top + a4_h_px
            tile = poster.crop((left, top, right, bottom))
            tiles.append(((row, col), tile))

    # Save each tile as PNG and PDF
    for (row, col), tile in tiles:
        png_path = os.path.join(args.outdir, f"{args.prefix}_r{row+1}c{col+1}.png")
        pdf_path = os.path.join(args.outdir, f"{args.prefix}_r{row+1}c{col+1}.pdf")
        save_tile_png(tile, png_path, dpi=args.dpi)
        save_tile_pdf(tile, pdf_path, margin_mm=args.margin_mm)

    # Also write a README with quick assembly guidance
    readme_path = os.path.join(args.outdir, "README.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(
            "2x2 A4 tiling complete.\n\n"
            "Files:\n"
            "  - tile_r1c1.*, tile_r1c2.*\n"
            "  - tile_r2c1.*, tile_r2c2.*\n\n"
            "Printing tips:\n"
            "  1) For PNGs: print at 100% scale using the DPI you chose (default 300).\n"
            "  2) For PDFs: print with 'Actual size' (no scaling). Margins set by --margin-mm.\n"
            "  3) Arrange tiles as:\n"
            "       r1c1 | r1c2\n"
            "       -----+-----\n"
            "       r2c1 | r2c2\n"
        )

    print(f"Done. Output written to: {os.path.abspath(args.outdir)}")
    print("Tiles:")
    for (row, col), _ in tiles:
        print(f"  - {args.prefix}_r{row+1}c{col+1}.png / .pdf")

if __name__ == "__main__":
    main()
