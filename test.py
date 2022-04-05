import numpy as np
import math
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests

chars = np.asarray(list(" .,:;irsXA253hMHGS#9B&@"))
url = input("URL: ")


image_bytes = requests.get(url).content
path = BytesIO(image_bytes)

f, WCF, GCF = path, 7 / 4, 0.6
img = Image.open(path)
# Make sure we have frame 1
img = img.convert("RGBA")

# Let's scale down
w, h = 0, 0
adjust = 2
w = img.size[0] * adjust
h = img.size[1]

# Make sure we're under max params of 50h, 50w
ratio = 1
max_wide = 1000
if h * 2 > w:
    if h > max_wide / adjust:
        ratio = max_wide / adjust / h
else:
    if w > max_wide:
        ratio = max_wide / w
h = ratio * h
w = ratio * w

# Shrink to an area of 1900 or so (allows for extra chars)
target = 10000
if w * h > target:
    r = h / w
    w1 = math.sqrt(target / r)
    h1 = target / w1
    w = w1
    h = h1

S = (round(w), round(h))
img = np.sum(np.asarray(img.resize(S)), axis=2)
img -= img.min()
img = (1.0 - img / img.max()) ** GCF * (chars.size - 1)
text = "\n".join(("".join(r) for r in chars[len(chars) - img.astype(int) - 1]))
print(text)

image = Image.new("RGB", (2000, 2000), "#000000")  # 060e16")
draw = ImageDraw.Draw(image)
font = ImageFont.truetype("./data/assets/SourceCodePro-Regular.ttf", 24)
draw.text((0, 0), text, "#FFFFFF", font=font)
image.save("image.png")
# buffer = BytesIO()
# image.save(buffer, "png")  # 'save' function for PIL
# buffer.seek(0)
# return buffer
# a = "```\n" + a + "```"
