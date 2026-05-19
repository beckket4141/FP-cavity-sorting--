#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps


DEFAULT_SOURCE_ROOT = Path(r"D:\自制软件\thesis\数据内容\l_lock图")
DEFAULT_OUTPUT_DIR = Path(r"D:\自制软件\1.thesis\My_nju_thesis-master\thesis\_tmp_preview")


def build_default_cells() -> list[Path]:
    return [Path(f"l_lock={idx}") / f"l{idx}.png" for idx in range(10)]


def parse_cells(raw: str | None) -> list[Path]:
    if not raw:
        return build_default_cells()
    return [Path(part.strip()) for part in raw.split(",") if part.strip()]


def crop_to_aspect(image: Image.Image, target_ratio: float) -> Image.Image:
    width, height = image.size
    src_ratio = width / height
    if abs(src_ratio - target_ratio) < 1e-6:
        return image
    if src_ratio > target_ratio:
        new_width = int(round(height * target_ratio))
        left = max(0, (width - new_width) // 2)
        return image.crop((left, 0, left + new_width, height))
    new_height = int(round(width / target_ratio))
    top = max(0, (height - new_height) // 2)
    return image.crop((0, top, width, top + new_height))


def compose_grid(
    image_paths: list[Path],
    rows: int,
    cols: int,
    canvas_width: int,
    canvas_height: int,
    margin_x: int,
    margin_y: int,
    gap_x: int,
    gap_y: int,
) -> Image.Image:
    if len(image_paths) != rows * cols:
        raise ValueError(f"Need exactly {rows * cols} images, got {len(image_paths)}.")

    tile_width = (canvas_width - 2 * margin_x - (cols - 1) * gap_x) // cols
    tile_height = (canvas_height - 2 * margin_y - (rows - 1) * gap_y) // rows
    if tile_width <= 0 or tile_height <= 0:
        raise ValueError("Canvas is too small for the requested grid.")

    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
    target_ratio = tile_width / tile_height

    for idx, image_path in enumerate(image_paths):
        row = idx // cols
        col = idx % cols
        tile = Image.open(image_path).convert("RGB")
        tile = ImageOps.autocontrast(tile)
        tile = crop_to_aspect(tile, target_ratio).resize((tile_width, tile_height), Image.Resampling.LANCZOS)
        x = margin_x + col * (tile_width + gap_x)
        y = margin_y + row * (tile_height + gap_y)
        canvas.paste(tile, (x, y))

    return canvas


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compose a CCD image grid from raw l_lock PNG files.",
    )
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--basename", default="fp_ccd_grid_regen")
    parser.add_argument("--rows", type=int, default=2)
    parser.add_argument("--cols", type=int, default=5)
    parser.add_argument("--width", type=int, default=1128)
    parser.add_argument("--height", type=int, default=306)
    parser.add_argument("--margin-x", type=int, default=8)
    parser.add_argument("--margin-y", type=int, default=8)
    parser.add_argument("--gap-x", type=int, default=8)
    parser.add_argument("--gap-y", type=int, default=8)
    parser.add_argument(
        "--cells",
        help=(
            "Comma-separated paths relative to --source-root, "
            "for example: l_lock=0/l0.png,l_lock=1/l1.png"
        ),
    )
    parser.add_argument("--png-only", action="store_true")
    args = parser.parse_args()

    cells = parse_cells(args.cells)
    source_paths = [args.source_root / rel_path for rel_path in cells]
    missing = [str(path) for path in source_paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing source images:\n" + "\n".join(missing))

    canvas = compose_grid(
        image_paths=source_paths,
        rows=args.rows,
        cols=args.cols,
        canvas_width=args.width,
        canvas_height=args.height,
        margin_x=args.margin_x,
        margin_y=args.margin_y,
        gap_x=args.gap_x,
        gap_y=args.gap_y,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    png_path = args.output_dir / f"{args.basename}.png"
    canvas.save(png_path)
    print(f"Saved PNG: {png_path}")

    if not args.png_only:
        pdf_path = args.output_dir / f"{args.basename}.pdf"
        canvas.save(pdf_path, resolution=300.0)
        print(f"Saved PDF: {pdf_path}")


if __name__ == "__main__":
    main()
