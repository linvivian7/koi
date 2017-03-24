import random


def generate_random_color(ntimes, base=(255, 255, 255)):
    """ Generate random pastel blue-greenish and red-orange colors for charts """

    colors = set()

    i = 1

    while len(colors) < ntimes + 1:

            if i % 2 == 0:
                red = random.randint(0, 50)
                green = random.randint(150, 170)
                blue = random.randint(155, 219)

            if i % 2 != 0:
                red = random.randint(240, 250)
                green = random.randint(104, 168)
                blue = random.randint(0, 114)

            if base:
                red = (red + base[0]) / 2
                green = (green + base[1]) / 2
                blue = (blue + base[2]) / 2

            color = (red, green, blue)
            colors.add(color)
            i += 1

    return colors
