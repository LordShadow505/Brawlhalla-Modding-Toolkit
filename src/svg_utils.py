"""
SVG Rendering Utilities for Brawlhalla Modding Toolkit
======================================================
Provides a unified interface for rendering SVG files to PIL Images,
supporting multiple backends (resvg, cairosvg, svglib) with graceful fallbacks.
"""

from src.utils import get_project_root
import io
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Union
from PIL import Image, ImageDraw

# Cache for rendered icons to avoid redundant processing
_svg_cache = {}

# ── Backend Detection ────────────────────────────────────────────────

# 1. RESVG (Preferred: Modern, fast, self-contained wheels available)
HAS_RESVG = False
try:
    import resvg_py
    HAS_RESVG = True
except ImportError:
    try:
        import resvg
        HAS_RESVG = True
    except ImportError:
        resvg = None

# 2. CAIROSVG (Legacy: Good but requires system Cairo DLLs on Windows)
HAS_CAIROSVG = False
try:
    import cairosvg
    HAS_CAIROSVG = True
except (ImportError, OSError):
    cairosvg = None

# 3. SVGLIB (Fallback: Pure Python but limited SVG support)
HAS_SVGLIB = False
try:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM
    HAS_SVGLIB = True
except ImportError:
    pass


def render_svg(
    source: Union[str, Path, bytes],
    size: Tuple[int, int],
    bg_color: Optional[Tuple[int, int, int, int]] = (0, 0, 0, 0)
) -> Optional[Image.Image]:
    """
    Renders an SVG to a PIL Image using the best available backend.
    
    Args:
        source: Path to .svg file, or SVG string/bytes.
        size: Target (width, height) in pixels.
        bg_color: Optional background color (RGBA).
        
    Returns:
        PIL.Image in RGBA mode, or None on failure.
    """
    w, h = size
    
    # Identify source type
    svg_path = None
    svg_data = None
    
    if isinstance(source, (str, Path)) and os.path.exists(str(source)):
        svg_path = str(source)
    else:
        svg_data = source if isinstance(source, bytes) else str(source).encode("utf-8")

    # --- Method 1: resvg (Modern Rust-based renderer, very portable) ---
    if HAS_RESVG:
        try:
            # Attempt to use resvg_py (most common pip package with wheels)
            try:
                import resvg_py
                if svg_path:
                    png_data = resvg_py.svg_to_bytes(svg_path=svg_path, width=w, height=h)
                else:
                    png_data = resvg_py.svg_to_bytes(svg_string=svg_data.decode("utf-8"), width=w, height=h)
                return Image.open(io.BytesIO(png_data)).convert("RGBA")
            except (ImportError, AttributeError):
                # Fallback to alternative resvg binding
                import resvg
                if hasattr(resvg, 'render'):
                    text = svg_data.decode("utf-8") if svg_data else Path(svg_path).read_text(encoding="utf-8")
                    png_data = resvg.render(text, width=w, height=h)
                    return Image.open(io.BytesIO(png_data)).convert("RGBA")
        except Exception as e:
            print(f"[SVG] resvg backend failed: {e}")

    # --- Method 2: cairosvg ---
    if HAS_CAIROSVG:
        try:
            if svg_path:
                png_data = cairosvg.svg2png(url=svg_path, output_width=w, output_height=h)
            else:
                png_data = cairosvg.svg2png(bytestring=svg_data, output_width=w, output_height=h)
            return Image.open(io.BytesIO(png_data)).convert("RGBA")
        except Exception as e:
            print(f"[SVG] cairosvg failed: {e}")

    # --- Method 3: resvg via subprocess (If binary is bundled in Lib/bin) ---
    # Look for resvg.exe in project root or Lib
    possible_bins = [
        Path(sys.argv[0]).parent / "Lib" / "bin" / "resvg.exe",
        (get_project_root() / "src") / "Lib" / "bin" / "resvg.exe",
        Path("C:/Program Files/resvg/resvg.exe")
    ]
    for bin_path in possible_bins:
        if bin_path.exists():
            try:
                # We need a temp file if we have data instead of path
                temp_svg = None
                input_file = svg_path
                if not input_file:
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tf:
                        tf.write(svg_data)
                        temp_svg = tf.name
                        input_file = temp_svg
                
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
                    output_png = tf.name
                
                subprocess.run([
                    str(bin_path), input_file, output_png,
                    "--width", str(w), "--height", str(h)
                ], check=True, capture_output=True)
                
                img = Image.open(output_png).convert("RGBA")
                
                # Cleanup
                if temp_svg: os.unlink(temp_svg)
                os.unlink(output_png)
                return img
            except Exception as e:
                print(f"[SVG] resvg subprocess failed: {e}")

    # --- Method 4: svglib (Last resort pure python) ---
    if HAS_SVGLIB:
        try:
            if svg_path:
                drawing = svg2rlg(svg_path)
            else:
                drawing = svg2rlg(io.BytesIO(svg_data))
                
            # Scaling
            scale_x = w / drawing.width
            scale_y = h / drawing.height
            drawing.scale(scale_x, scale_y)
            drawing.width, drawing.height = w, h
            
            png_io = io.BytesIO()
            renderPM.drawToFile(drawing, png_io, fmt="PNG")
            return Image.open(png_io).convert("RGBA")
        except Exception as e:
            print(f"[SVG] svglib failed: {e}")

    return None


def get_svg_icon(
    path: Path,
    size: Tuple[int, int],
    cache: bool = True
) -> Optional[Image.Image]:
    """Gets a rendered SVG icon, using cache if enabled."""
    key = (str(path), size)
    if cache and key in _svg_cache:
        return _svg_cache[key]
    
    img = render_svg(path, (size[0]*2, size[1]*2)) # Render at 2x for High DPI
    if img and cache:
        _svg_cache[key] = img
    return img


def create_svg_fallback(size: Tuple[int, int], color: Tuple[int, int, int, int] = (200, 200, 200, 160)) -> Image.Image:
    """Creates a basic box fallback when all SVG renderers fail."""
    w, h = size[0]*2, size[1]*2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, w-3, h-3], outline=color)
    return img
