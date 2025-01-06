from typing import Literal
from PIL.ImageFilter import GaussianBlur
from PIL.Image import Image, new
from PIL import ImageDraw, ImageFont


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

_pos_anchor_map = {
    "x": {
        "left": "l",
        "middle": "m",
        "right": "r",
    },
    "y": {
        "top": "a",
        "middle": "m",
        "bottom": "d"
    }
}


def watermark(
    image: Image,
    text: str,
    font: str,
    font_size: float | None = None,
    angle: float = 0.0,
    x: int | Literal["left", "middle", "right"] = "middle",
    y: int | Literal["top", "middle", "bottom"] = "middle",
    anchor: str = '',
    repeat: bool = False,
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
    if text == "" or font_size == 0:
        return image
    
    if font_size is None:
        font_size = min(image.width, image.height) / 10
    
    if len(color) not in (3, 4) or not all(0 <= x <= 255 for x in color):
        raise f"Invalid color: {color}"
    
    if not anchor:
        def get_anchor(pos, pos_str):
            if not isinstance(x, str):
                return "m"
            try:
                return _pos_anchor_map[pos_str][pos]
            except KeyError:
                raise Exception(f"Invalid relative {pos_str} position: {pos}")
        anchor = f"{get_anchor(x, "x")}{get_anchor(y, "y")}"

    if isinstance(x, str):
        if x == "left":
            x = 0
        elif x == "middle":
            x = image.width / 2
        elif x == "right":
            x = image.width
        else:
            raise Exception(f"Invalid relative x position: {x}")
    
    if isinstance(y, str):
        if y == "top":
            y = 0
        elif y == "middle":
            y = image.height / 2
        elif y == "bottom":
            y = image.height
        else:
            raise Exception(f"Invalid relative y position: {y}")
    
    
    old_mode = None
    if (old_mode := image.mode) != ALPHA_MODE:
        image = image.convert(ALPHA_MODE)

    watermark = new(ALPHA_MODE, image.size, (0, 0, 0, 0))



    font = ImageFont.truetype(font, size=font_size)
    ImageDraw.Draw(watermark).text(
        xy=(x, y),
        text=text,
        fill=color,
        font=font,
        anchor=anchor,
    )

    Image.alpha_composite(image, watermark)
    if old_mode != ALPHA_MODE:
        image = image.convert(old_mode)
    return image