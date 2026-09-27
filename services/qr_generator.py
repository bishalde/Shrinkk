import io

import qrcode
from qrcode.constants import ERROR_CORRECT_M
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer

DEFAULT_FG = "#101010"
DEFAULT_BG = "#FFFFFF"
BORDER = 2


def _rgb(hex_color):
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))


def _matrix(data):
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, border=BORDER)
    qr.add_data(data)
    qr.make(fit=True)
    return qr


def generate_png(data, fg=DEFAULT_FG, bg=DEFAULT_BG, box_size=16):
    qr = _matrix(data)
    qr.box_size = box_size
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=SolidFillColorMask(back_color=_rgb(bg), front_color=_rgb(fg)),
    )
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def generate_svg(data, fg=DEFAULT_FG, bg=DEFAULT_BG):
    matrix = _matrix(data).get_matrix()  # includes the border
    size = len(matrix)
    cells = "".join(
        f"M{x},{y}h1v1h-1z"
        for y, row in enumerate(matrix)
        for x, on in enumerate(row)
        if on
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'shape-rendering="crispEdges"><rect width="100%" height="100%" fill="{bg}"/>'
        f'<path d="{cells}" fill="{fg}"/></svg>'
    )
    return io.BytesIO(svg.encode("utf-8"))
