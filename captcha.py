from PIL import Image, ImageDraw, ImageFont
import random


def rndChar():
    return chr(random.randint(65, 90))


def rndColor():
    return (random.randint(64, 255), random.randint(64, 255), random.randint(64, 255))


def rndColor2():
    return (random.randint(32, 127), random.randint(32, 127), random.randint(32, 127))


def getCaptcha():
    str=""
    width = 30 * 4
    height = 30
    image = Image.new('RGB', (width, height), (255, 255, 255))
    font = ImageFont.truetype('font/Arial.ttf', 20)
    draw = ImageDraw.Draw(image)
    for x in range(width):
        for y in range(height):
            draw.point((x, y), fill=rndColor())
    for t in range(4):
        str += rndChar()
    for t in range(4):
        draw.text((30 * t + 10, 5), str[t], font=font, fill=rndColor2())
    image.save('static/captcha/' + str + '.jpg', 'jpeg')
    return str