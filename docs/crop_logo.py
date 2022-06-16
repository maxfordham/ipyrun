from PIL import Image

im = Image.open("images/logo.png")
im.getbbox()
im2 = im.crop(im.getbbox())
im2.save("images/logo.png")
