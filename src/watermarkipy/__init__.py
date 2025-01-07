from typing import Literal
from PIL.ImageFilter import GaussianBlur
from PIL.Image import Image, new
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype


def shrink(image: Image, scale: float = 1) -> None:
    """
    Shrinks the image whilst maintaining aspect ratio
    Operation performed in-place - the shrunk image will replace the original image
    :param image: image to be shrunk
    :param scale: multiplier to both the height and width of the original image, must be in range (0, 1]
    :raises:
    """
    if not 0.0 < scale <= 1.0:
        raise "scale must be in range (0, 1]"
    if scale == 1:
        return image
    image.thumbnail((
        round(image.width * scale),
        round(image.height * scale)
    ))


def blur(image: Image, blur_amount: float = 0.1) -> Image:
    """
    Blur an image using Gaussian blur, 0 is no blur, 1 is maximum blur
    :param image: image to be blurred
    :param blur_amount: relative blur amount in the range [0, 1]
    :returns: original image if no blur was applied, or copy of blurred image
    :raises: 
    """
    if not 0.0 <= blur_amount <= 1.0:
        raise "blur_amount must be in range [0, 1]"
    if blur_amount == 0.0:
        return image
    return image.filter(GaussianBlur(min(image.width, image.height) * blur_amount / 10))

ALPHA_MODE = "RGBA"

'''
    watermark_text: str | None = Field(default=None)
    watermark_font_size: int = Field(default=200)
    watermark_angle: int = Field(default=45)
    watermark_color: int = Field(default=0xffffff)
    watermark_opacity: float = Field(default=1.0, ge=0.0, le=1.0)
    watermark_x: int | None = Field(default=None)
    watermark_y: int | None = Field(default=None)
    watermark_repeat: bool = Field(default=True)
'''

_pos_map = {
    "x": {
        "left": {
            "anchor": "l",
            "pos": lambda image: 0
        },
        "middle": {
            "anchor": "m",
            "pos": lambda image: image.width / 2
        },
        "right": {
            "anchor": "r",
            "pos": lambda image: image.width
        },
    },
    "y": {
        "top": {
            "anchor": "a",
            "pos": lambda image: 0
        },
        "middle": {
            "anchor": "m",
            "pos": lambda image: image.height / 2
        },
        "bottom": {
            "anchor": "d",
            "pos": lambda image: image.height
        },
    },
}


def watermark(
    image: Image,
    text: str,
    font: str,
    font_size: float | None = None,
    x: int | Literal["left", "middle", "right"] = "middle",
    y: int | Literal["top", "middle", "bottom"] = "middle",
    anchor: str = '',
    repeat: bool = False,
    repeat_spacing_x: int | None = None,
    repeat_spacing_y: int | None = None,
    color: tuple[int] = (255, 255, 255),
) -> Image:
    """
    Watermarks an image

    :param image: image to be watermarked
    :param text: text to add to image
    :param font: text font
    :param font_size: size of text font
    :param angle: 
    :param x: either absolute x coordinate or relative position
    :param y: either absolute y coordinate or relative position
    :param anchor: text anchor, see https://pillow.readthedocs.io/en/stable/handbook/text-anchors.html
    :param repeat: whether the watermark is repeated to fill the entire image
    :param color: 3/4-tuple of R, G, B, and A (optional) values representing the text's color
    :returns: copy of image containing watermark
    """
    if text == "" or font_size == 0 or len(color) == 4 and color[3] == 0:
        return image
    
    if font_size is None:
        font_size = min(image.width, image.height) / 10
    
    if len(color) not in (3, 4) or not all(0 <= x <= 255 for x in color):
        raise ValueError(f"Invalid color: {color}")
    
    if not anchor:
        def get_anchor(pos, pos_str):
            if not isinstance(x, str):
                return "m"
            try:
                return _pos_map[pos_str][pos]["anchor"]
            except KeyError:
                raise ValueError(f"Invalid relative {pos_str} position: {pos}")
        anchor = f"{get_anchor(x, "x")}{get_anchor(y, "y")}"

    if isinstance(x, str):
        try:
            x = _pos_map["x"][x]["pos"](image)
        except KeyError:
            raise Exception(f"Invalid relative x position: {x}")
        
    if isinstance(y, str):
        try:
            y = _pos_map["y"][y]["pos"](image)
        except KeyError:
            raise Exception(f"Invalid relative y position: {y}")
    
    
    if (old_mode := image.mode) != ALPHA_MODE:
        image = image.convert(ALPHA_MODE)

    watermark = new(ALPHA_MODE, image.size, (0, 0, 0, 0))


    pil_font = truetype(font, size=font_size)

    xys = [(x, y)]

    if repeat:
        def get_default_spacing():
            dx1, dy1, dx2, dy2 = pil_font.getbbox("x")
            return abs(dx1 - dx2), abs(dy1 - dy2)
        default_spacing = get_default_spacing()
        if repeat_spacing_x is None:
            repeat_spacing_x = default_spacing[0]
        if repeat_spacing_y is None:
            repeat_spacing_y = default_spacing[1]
        dx1, dy1, dx2, dy2 = pil_font.getbbox(
            text=text,
            anchor=anchor
        )
        dx, dy = abs(dx1 - dx2), abs(dy1 - dy2)
        repeat_count = int(max(image.width / dx, image.height / dy))
        # x1, y1, x2, y2 = x + dx1, y + dy1, x + dx2, y + dy2
        for i in range(repeat_count):
            for j in range(repeat_count):
                xys.append((x + (dx + repeat_spacing_x) * i, y + (dy + repeat_spacing_y) * j))
                xys.append((x + (dx + repeat_spacing_x) * i, y - (dy + repeat_spacing_y) * j))
                xys.append((x - (dx + repeat_spacing_x) * i, y + (dy + repeat_spacing_y) * j))
                xys.append((x - (dx + repeat_spacing_x) * i, y - (dy + repeat_spacing_y) * j))

    draw = Draw(watermark)
    for xy in xys:
        draw.text(
            xy=xy,
            text=text,
            fill=color,
            font=pil_font,
            anchor=anchor,
        )

    Image.alpha_composite(image, watermark)
    if old_mode != ALPHA_MODE:
        image = image.convert(old_mode)
    return image