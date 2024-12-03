import csv
import os
from collections import namedtuple

from PIL import Image, ImageDraw, ImageFont

# Globale Einstellungen
DEBUG = True
LANGUAGES = ["en"]#, "de", "fr", "it"]
CHAPTERS = ["001", "002", "003", "004", "005", "006"]
SPECIAL_CHAPTERS = ["P1", "P2", "C1", "D23"]
VARIANTS = ["a", "b", "c", "d", "e", "f"]
CARDS_WITH_VARIANTS = [(("003", 4), 5)]
ColorType = namedtuple("ColorType", ["name", "color"])

CARD_TYPES = [
    ColorType("amber", (211, 149, 45)),  # Gelb
    ColorType("amethyst", (155, 89, 182)),  # Lila
    ColorType("emerald", (46, 204, 113)),  # Grün
    ColorType("ruby", (189, 66, 68)),  # Rot
    ColorType("sapphire", (35, 138, 175)),  # Blau
    ColorType("steel", (123, 131, 137)),  # Grau
]
CARD_TYPES_ORDER = [ct.name for ct in CARD_TYPES]

CHAPTER_NAMES = {
    "001": "1 - The First Chapter",
    "002": "2 - Rise of the Floodborn",
    "003": "3 - Into the Inklands",
    "004": "4 - Ursula's Return",
    "005": "5 - Shimmering Skies",
    "006": "6 - Azurite Sea",
    "C1": "Lorcana Challenge 1",
    "P1": "Promo Cards Year 1",
    "P2": "Promo Cards Year 2",
    "Q1": "Ursula's quest",
    "D23": "Disney D23",
}

CARD_RARITY = [
    ColorType("CC", (168, 166, 169)),  # Common
    ColorType("UC", (255, 255, 255)),  # Uncommon
    ColorType("RR", (179, 91, 48)),  # Rare
    ColorType("SR", (198, 198, 200)),  # Super Rare (39, 40, 40)
    ColorType("LL", (219, 192, 89)),  # Legendary
    ColorType("EE", (176, 192, 116)),  # Enchanted
    ColorType("SP", (0, 0, 0)),  # Special Rarity
]
CARD_RARITY_ORDER = [ct.name for ct in CARD_RARITY]

SCALING = 1
BASE_DIR = "cards"
PADDING = int(50 * SCALING)
PADDING_BETWEEN_CHAPTERS = int(100 * SCALING)
CARD_WIDTH, CARD_HEIGHT = int(630 * SCALING), int(880 * SCALING)
IMAGES_PER_ROW = 6
CORNER_RADIUS = int(20 * SCALING)


def csv_zu_json(csv_datei_pfad):
    try:
        with open(csv_datei_pfad, 'r', encoding='utf-8') as csvdatei:
            csv_reader = csv.DictReader(csvdatei)
            return list(csv_reader)
    except:
        return {}


def load_my_card_collection_from_chapters():
    json_objekts = csv_zu_json(f'export.csv')

    dict_all_chapters = {}

    for chapter in CHAPTERS + SPECIAL_CHAPTERS:
        dict_all_chapters[chapter] = {}

    for entry in json_objekts:
        card_dict = {
            "name": entry["Name"],
            "normal": entry["Normal"],
            "foil": entry["Foil"],
            "color": entry["Color"],
        }
        entry["Card Number"] = entry["Card Number"].replace("P", "")
        if entry["Card Number"].isdigit():  # Check for variants
            dict_all_chapters[entry["Set"]][str(entry["Card Number"]).zfill(3)] = card_dict
        else:
            dict_all_chapters[entry["Set"]][str(entry["Card Number"]).zfill(4)] = card_dict
    return dict_all_chapters


def round_corners(im, rad):
    """Runde die Ecken eines Bildes."""
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im


def get_rarity_from_filename(filename):
    """Holt die Seltenheit aus dem Dateinamen."""
    parts = filename.split('.')[0].split('_')
    if len(parts) >= 3:
        return parts[2]
    return None


def get_card_color_from_filename(filename):
    """Holt die Kartenfarbe aus dem Dateinamen."""
    parts = filename.split('.')[0].split('_')
    if len(parts) >= 2:
        return parts[1]
    return None


def get_type_from_filename(filename):
    """Holt den Typen aus dem Dateinamen."""
    parts = filename.split('.')[0].split('_')
    if len(parts) >= 4:
        return parts[3]
    return None


def merge_images(images, vertically, offset_merge, space_color=(255, 255, 255, 0), align='center'):
    """
    Fügt mehrere Bilder zu einem Bild zusammen, entweder vertikal oder horizontal.

    :param images: Liste von Images.
    :param vertically: True, um die Bilder vertikal zu verbinden, False für horizontal.
    :param offset_merge: Abstand zwischen den Bildern.
    :param align: Ausrichtung der Bilder ('left', 'right', 'center', 'top', 'bottom').
    :param space_color: Farbe des Raumes zwischen den Bildern (standardmäßig transparent).
    :return: Das zusammengesetzte Bild.
    """

    widths, heights = zip(*(i.size for i in images))

    if vertically:
        max_width = max(widths)
        total_height = sum(heights) + (offset_merge * (len(images) - 1))
        new_im = Image.new('RGBA', (max_width, total_height), space_color)

        y_offset = 0
        for im in images:
            if align == 'left':
                x_position = 0
            elif align == 'right':
                x_position = max_width - im.size[0]
            else:  # center
                x_position = (max_width - im.size[0]) // 2

            new_im.paste(im, (x_position, y_offset), im)
            y_offset += im.size[1] + offset_merge

    else:  # horizontal
        max_height = max(heights)
        total_width = sum(widths) + (offset_merge * (len(images) - 1))
        new_im = Image.new('RGBA', (total_width, max_height), space_color)

        x_offset = 0
        for im in images:
            if align == 'top':
                y_position = 0
            elif align == 'bottom':
                y_position = max_height - im.size[1]
            else:  # center
                y_position = (max_height - im.size[1]) // 2

            new_im.paste(im, (x_offset, y_position), im)
            x_offset += im.size[0] + offset_merge

    return new_im


def merge_cards(lang, color_rgb, img_per_row, generate_name, mark_completed, chapter_list: CHAPTERS):
    IMAGES_PER_ROW = img_per_row

    all_color_images_per_chapter = {}
    for chapter in chapter_list:
        chapter_cards = []
        chapter_dir = os.path.join(BASE_DIR, lang, "webp", chapter)

        # Filtere und sortiere die Bilder dieses Typs
        image_filenames = [img for img in os.listdir(chapter_dir)]
        image_filenames.sort(key=lambda x: CARD_RARITY_ORDER.index(get_rarity_from_filename(x)))

        if DEBUG:
            print(chapter_dir, image_filenames)

        # Lade Bilder und füge Metadaten hinzu
        for img_filename in image_filenames:
            if chapter not in MY_COLLECTION:
                continue
            card_number = img_filename.split("_")[0]
            if card_number not in MY_COLLECTION[chapter]:
                continue

            if int(MY_COLLECTION[chapter][card_number]["normal"]) == 0 and int(MY_COLLECTION[chapter][card_number]["foil"]) == 0:
                img = Image.open(os.path.join(chapter_dir, img_filename)).convert("RGBA")
                # Graue Schicht erstellen
                grey_overlay = Image.new('RGBA', img.size, (155, 110, 110, 160))  # Grey: 128, 128, 128, 160
                # Graue Schicht über das Bild legen
                img = Image.alpha_composite(img, grey_overlay)
                metadata = (chapter, card_number, MY_COLLECTION[chapter][card_number]["color"], color_rgb, img_filename, 1)  # Hinzugefügt: Farbe und Farb-RGB
                chapter_cards.append((img, metadata))
            elif int(MY_COLLECTION[chapter][card_number]["normal"]) + int(MY_COLLECTION[chapter][card_number]["foil"]) >= 4 and mark_completed:
                img = Image.open(os.path.join(chapter_dir, img_filename)).convert("RGBA")
                # Graue Schicht erstellen
                grey_overlay = Image.new('RGBA', img.size, (110, 155, 110, 160))
                # Graue Schicht über das Bild legen
                img = Image.alpha_composite(img, grey_overlay)
                metadata = (chapter, card_number, MY_COLLECTION[chapter][card_number]["color"], color_rgb, img_filename, 1)  # Hinzugefügt: Farbe und Farb-RGB
                chapter_cards.append((img, metadata))
            else:
                img = Image.open(os.path.join(chapter_dir, img_filename))
                metadata = (chapter, card_number, MY_COLLECTION[chapter][card_number]["color"], color_rgb, img_filename, 0)  # Hinzugefügt: Farbe und Farb-RGB
                chapter_cards.append((img, metadata))

        all_color_images_per_chapter[chapter] = chapter_cards

    images_to_merge = []
    for chapter, all_color_images in all_color_images_per_chapter.items():
        font = ImageFont.truetype("assets/black.ttf", int(50 * SCALING))

        # Sort by in Collection or not and Rarity
        # all_color_images.sort(key=lambda x: (x[1][5], CARD_RARITY_ORDER.index(get_rarity_from_filename(x[1][4]))))
        # Sort by ID
        all_color_images.sort(key=lambda x: (x[1][1]))
        # all_color_images.sort(key=lambda x: (x[1][0], CARD_RARITY_ORDER.index(get_rarity_from_filename(x[1][4]))))

        # Berechne die Anzahl der Bilder in der letzten Zeile
        bilder_pro_letzte_zeile = len(all_color_images) % IMAGES_PER_ROW
        ist_letzte_zeile = bilder_pro_letzte_zeile > 0

        rows = (len(all_color_images) // IMAGES_PER_ROW) + (1 if len(all_color_images) % IMAGES_PER_ROW else 0)
        total_width = (CARD_WIDTH + PADDING) * min(IMAGES_PER_ROW, len(all_color_images)) + PADDING
        max_height = (CARD_HEIGHT + PADDING) * rows + PADDING

        # Erstelle ein neues Bild mit dem Hintergrund der gewählten Farbe
        new_image = Image.new('RGBA', (total_width, max_height), (color_rgb[0], color_rgb[1], color_rgb[2], 255))

        x_offset, y_offset = PADDING, PADDING

        for index, img_mix in enumerate(all_color_images):
            img = img_mix[0]
            img = img.resize((CARD_WIDTH, CARD_HEIGHT), resample=Image.LANCZOS)
            img = round_corners(img, CORNER_RADIUS)

            new_image.paste(img, (x_offset, y_offset), img)

            # # Überprüfe, ob wir in der letzten Reihe sind und ob sie nicht voll ist
            # if (index // IMAGES_PER_ROW) == rows - 1 and len(images) % IMAGES_PER_ROW != 0:
            #     remaining_images = len(images) % IMAGES_PER_ROW
            #     total_images_width = remaining_images * CARD_WIDTH + (remaining_images - 1) * PADDING
            #     x_offset = (total_width - total_images_width) // 2

            if (int(MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["foil"]) + int(MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["normal"])) > 0:
                normal_count = Image.open("assets/normal_card_count.png")
                normal_count = normal_count.resize((int(normal_count.width * 0.75 * SCALING), int(normal_count.height * 0.75 * SCALING)), resample=Image.LANCZOS)

                foil_count = Image.open("assets/foil_card_count.png")
                foil_count = foil_count.resize((int(foil_count.width * 0.75 * SCALING), int(foil_count.height * 0.75 * SCALING)), resample=Image.LANCZOS)

                draw = ImageDraw.Draw(foil_count)
                text = str(MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["foil"])
                text_bbox = draw.textbbox((0, 0), text, font=font)
                textwidth = text_bbox[2] - text_bbox[0]
                textheight = text_bbox[3] - text_bbox[1]
                text_x = (foil_count.width - textwidth) // 2
                text_y = (foil_count.height - textheight) // 2 - int(10 * SCALING)
                draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))  # Schwarzer Text

                draw = ImageDraw.Draw(normal_count)
                text = str(MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["normal"])
                text_bbox = draw.textbbox((0, 0), text, font=font)
                textwidth = text_bbox[2] - text_bbox[0]
                textheight = text_bbox[3] - text_bbox[1]
                text_x = (normal_count.width - textwidth) // 2
                text_y = (normal_count.height - textheight) // 2 - int(10 * SCALING)
                draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))  # Schwarzer Text

                # Add Set completed marker
                if (int(MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["foil"]) + int(MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["normal"])) >= 4 and mark_completed:
                    done = Image.open("assets/done.png")
                    done = done.resize((int(done.width * 0.2 * SCALING), int(done.height * 0.2 * SCALING)), resample=Image.LANCZOS)
                    new_image.paste(done, (int(x_offset) + int(15 * SCALING), int(y_offset) + CARD_HEIGHT - done.height - int(15 * SCALING)), done)

                new_image.paste(foil_count, (x_offset + CARD_WIDTH - foil_count.width - 0 - 5, int(y_offset + foil_count.height * 0.75) + 5), foil_count)
                new_image.paste(normal_count, (int(x_offset + CARD_WIDTH - normal_count.width - normal_count.width * 0.75 - 0) - 5, y_offset + 5), normal_count)
            else:
                missing = Image.open("assets/missing.png")
                missing = missing.resize((int(missing.width * 0.36 * SCALING), int(missing.height * 0.36 * SCALING)), resample=Image.LANCZOS)

                new_image.paste(missing, (int(x_offset + CARD_WIDTH - missing.width - int(5 * SCALING)), y_offset + int(5 * SCALING)), missing)
            x_offset += CARD_WIDTH + PADDING

            if (index + 1) % IMAGES_PER_ROW == 0:
                x_offset = PADDING
                y_offset += CARD_HEIGHT + PADDING

        chapter_name_image = Image.new('RGBA', (new_image.width, int(210 * SCALING)), (color_rgb[0], color_rgb[1], color_rgb[2], 255))

        draw = ImageDraw.Draw(chapter_name_image)
        font = ImageFont.truetype("assets/black.ttf", int(180 * SCALING))
        draw.text((PADDING, 5), f"{CHAPTER_NAMES[chapter]}:", font=font, fill=(255, 255, 255))  # Schwarzer Text

        images_to_merge.append(chapter_name_image)
        images_to_merge.append(new_image)

    new_image = merge_images(images_to_merge, True, PADDING, color_rgb, align="left")

    # Speichere das neue Bild
    output_dir = os.path.join(BASE_DIR, "output", "all_by_color", lang)
    os.makedirs(os.path.join(output_dir, "webp"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "png"), exist_ok=True)
    new_image.save(os.path.join(output_dir, "png", f"{generate_name}.png"), "PNG")
    new_image.save(os.path.join(output_dir, "webp", f"{generate_name}.webp"), "WebP", quality=90)
    print(f"Image saved: {os.path.join(output_dir, f'{generate_name}')}")


def merge_cards_for_color(lang, color, color_rgb, img_per_row, generate_name, mark_completed, chapter_list: CHAPTERS):
    IMAGES_PER_ROW = img_per_row

    all_color_images_per_chapter = {}
    for chapter in chapter_list:
        chapter_cards = []
        chapter_dir = os.path.join(BASE_DIR, lang, "webp", chapter)

        # Filtere und sortiere die Bilder dieses Typs
        image_filenames = [img for img in os.listdir(chapter_dir) if f"{color}" in img.lower()]
        image_filenames.sort(key=lambda x: CARD_RARITY_ORDER.index(get_rarity_from_filename(x)))

        if DEBUG:
            print(chapter_dir, image_filenames)

        # Lade Bilder und füge Metadaten hinzu
        for img_filename in image_filenames:
            if chapter not in MY_COLLECTION:
                continue
            card_number = img_filename.split("_")[0]
            if card_number not in MY_COLLECTION[chapter]:
                continue

            if int(MY_COLLECTION[chapter][card_number]["normal"]) == 0 and int(MY_COLLECTION[chapter][card_number]["foil"]) == 0:
                img = Image.open(os.path.join(chapter_dir, img_filename)).convert("RGBA")
                # Graue Schicht erstellen
                grey_overlay = Image.new('RGBA', img.size, (155, 110, 110, 160))  # Grey: 128, 128, 128, 160
                # Graue Schicht über das Bild legen
                img = Image.alpha_composite(img, grey_overlay)
                metadata = (chapter, card_number, color, color_rgb, img_filename, 1)  # Hinzugefügt: Farbe und Farb-RGB
                chapter_cards.append((img, metadata))
            elif int(MY_COLLECTION[chapter][card_number]["normal"]) + int(MY_COLLECTION[chapter][card_number]["foil"]) >= 4 and mark_completed:
                img = Image.open(os.path.join(chapter_dir, img_filename)).convert("RGBA")
                # Graue Schicht erstellen
                grey_overlay = Image.new('RGBA', img.size, (110, 155, 110, 160))
                # Graue Schicht über das Bild legen
                img = Image.alpha_composite(img, grey_overlay)
                metadata = (chapter, card_number, color, color_rgb, img_filename, 1)  # Hinzugefügt: Farbe und Farb-RGB
                chapter_cards.append((img, metadata))
            else:
                img = Image.open(os.path.join(chapter_dir, img_filename))
                metadata = (chapter, card_number, color, color_rgb, img_filename, 0)  # Hinzugefügt: Farbe und Farb-RGB
                chapter_cards.append((img, metadata))

        all_color_images_per_chapter[chapter] = chapter_cards

    images_to_merge = []
    for chapter, all_color_images in all_color_images_per_chapter.items():
        font = ImageFont.truetype("assets/black.ttf", int(50 * SCALING))

        # Sort by in Collection or not and Rarity
        # all_color_images.sort(key=lambda x: (x[1][5], CARD_RARITY_ORDER.index(get_rarity_from_filename(x[1][4]))))
        # Sort by ID
        all_color_images.sort(key=lambda x: (x[1][1]))
        # all_color_images.sort(key=lambda x: (x[1][0], CARD_RARITY_ORDER.index(get_rarity_from_filename(x[1][4]))))

        # Berechne die Anzahl der Bilder in der letzten Zeile
        bilder_pro_letzte_zeile = len(all_color_images) % IMAGES_PER_ROW
        ist_letzte_zeile = bilder_pro_letzte_zeile > 0

        rows = (len(all_color_images) // IMAGES_PER_ROW) + (1 if len(all_color_images) % IMAGES_PER_ROW else 0)
        total_width = (CARD_WIDTH + PADDING) * min(IMAGES_PER_ROW, len(all_color_images)) + PADDING
        max_height = (CARD_HEIGHT + PADDING) * rows + PADDING

        # Erstelle ein neues Bild mit dem Hintergrund der gewählten Farbe
        new_image = Image.new('RGBA', (total_width, max_height), (color_rgb[0], color_rgb[1], color_rgb[2], 255))

        x_offset, y_offset = PADDING, PADDING

        for index, img_mix in enumerate(all_color_images):
            img = img_mix[0]
            img = img.resize((CARD_WIDTH, CARD_HEIGHT), resample=Image.LANCZOS)
            img = round_corners(img, CORNER_RADIUS)

            new_image.paste(img, (x_offset, y_offset), img)

            # # Überprüfe, ob wir in der letzten Reihe sind und ob sie nicht voll ist
            # if (index // IMAGES_PER_ROW) == rows - 1 and len(images) % IMAGES_PER_ROW != 0:
            #     remaining_images = len(images) % IMAGES_PER_ROW
            #     total_images_width = remaining_images * CARD_WIDTH + (remaining_images - 1) * PADDING
            #     x_offset = (total_width - total_images_width) // 2

            if (int(MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["foil"]) + int(MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["normal"])) > 0:
                normal_count = Image.open("assets/normal_card_count.png")
                normal_count = normal_count.resize((int(normal_count.width * 0.75 * SCALING), int(normal_count.height * 0.75 * SCALING)), resample=Image.LANCZOS)

                foil_count = Image.open("assets/foil_card_count.png")
                foil_count = foil_count.resize((int(foil_count.width * 0.75 * SCALING), int(foil_count.height * 0.75 * SCALING)), resample=Image.LANCZOS)

                draw = ImageDraw.Draw(foil_count)
                text = str(MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["foil"])
                text_bbox = draw.textbbox((0, 0), text, font=font)
                textwidth = text_bbox[2] - text_bbox[0]
                textheight = text_bbox[3] - text_bbox[1]
                text_x = (foil_count.width - textwidth) // 2
                text_y = (foil_count.height - textheight) // 2 - int(10 * SCALING)
                draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))  # Schwarzer Text

                draw = ImageDraw.Draw(normal_count)
                text = str(MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["normal"])
                text_bbox = draw.textbbox((0, 0), text, font=font)
                textwidth = text_bbox[2] - text_bbox[0]
                textheight = text_bbox[3] - text_bbox[1]
                text_x = (normal_count.width - textwidth) // 2
                text_y = (normal_count.height - textheight) // 2 - int(10 * SCALING)
                draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))  # Schwarzer Text

                # Add Set completed marker
                if (int(MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["foil"]) + int(MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["normal"])) >= 4 and mark_completed:
                    done = Image.open("assets/done.png")
                    done = done.resize((int(done.width * 0.2 * SCALING), int(done.height * 0.2 * SCALING)), resample=Image.LANCZOS)
                    new_image.paste(done, (int(x_offset) + int(15 * SCALING), int(y_offset) + CARD_HEIGHT - done.height - int(15 * SCALING)), done)

                new_image.paste(foil_count, (x_offset + CARD_WIDTH - foil_count.width - 0 - 5, int(y_offset + foil_count.height * 0.75) + 5), foil_count)
                new_image.paste(normal_count, (int(x_offset + CARD_WIDTH - normal_count.width - normal_count.width * 0.75 - 0) - 5, y_offset + 5), normal_count)
            else:
                missing = Image.open("assets/missing.png")
                missing = missing.resize((int(missing.width * 0.36 * SCALING), int(missing.height * 0.36 * SCALING)), resample=Image.LANCZOS)

                new_image.paste(missing, (int(x_offset + CARD_WIDTH - missing.width - int(5 * SCALING)), y_offset + int(5 * SCALING)), missing)
            x_offset += CARD_WIDTH + PADDING

            if (index + 1) % IMAGES_PER_ROW == 0:
                x_offset = PADDING
                y_offset += CARD_HEIGHT + PADDING

        chapter_name_image = Image.new('RGBA', (new_image.width, int(210 * SCALING)), (color_rgb[0], color_rgb[1], color_rgb[2], 255))

        draw = ImageDraw.Draw(chapter_name_image)
        font = ImageFont.truetype("assets/black.ttf", int(180 * SCALING))
        draw.text((PADDING, 5), f"{CHAPTER_NAMES[chapter]}:", font=font, fill=(255, 255, 255))  # Schwarzer Text

        images_to_merge.append(chapter_name_image)
        images_to_merge.append(new_image)

    new_image = merge_images(images_to_merge, True, PADDING, color_rgb, align="left")

    # Speichere das neue Bild
    output_dir = os.path.join(BASE_DIR, "output", "all_by_color", lang)
    os.makedirs(os.path.join(output_dir, "webp"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "png"), exist_ok=True)
    new_image.save(os.path.join(output_dir, "png", f"{generate_name}_{color}.png"), "PNG")
    new_image.save(os.path.join(output_dir, "webp", f"{generate_name}_{color}.webp"), "WebP", quality=90)
    print(f"Image saved: {os.path.join(output_dir, f'{generate_name}_{color}')}")


def merge_cards_missing_for_playset(lang, img_per_row, generate_name, chapter_list=CHAPTERS, rarity=None):
    IMAGES_PER_ROW = img_per_row

    all_images_per_chapter = {}
    bg_color = (255, 255, 255)
    text_color = (0, 0, 0)
    for chapter in chapter_list:
        chapter_cards = []
        chapter_dir = os.path.join(BASE_DIR, lang, "webp", chapter)

        # Filter and sort the images by rarity
        if rarity:
            image_filenames = [img for img in os.listdir(chapter_dir) if f"_{rarity}_" in img]
            image_filenames.sort(key=lambda x: CARD_RARITY_ORDER.index(get_rarity_from_filename(x)))
        else:
            image_filenames = [img for img in os.listdir(chapter_dir)]
            image_filenames.sort(key=lambda x: CARD_RARITY_ORDER.index(get_rarity_from_filename(x)))

        # Load images and add metadata
        for img_filename in image_filenames:
            if chapter not in MY_COLLECTION:
                continue
            card_number = img_filename.split("_")[0]
            if card_number not in MY_COLLECTION[chapter]:
                continue

            # Skip this card if the playset is already complete
            normal_count = int(MY_COLLECTION[chapter][card_number]["normal"])
            foil_count = int(MY_COLLECTION[chapter][card_number]["foil"])
            if normal_count + foil_count >= 4:
                continue

            img = Image.open(os.path.join(chapter_dir, img_filename))
            metadata = (chapter, card_number, "Blaugrau", bg_color, img_filename, 0)  # Added color and RGB color
            chapter_cards.append((img, metadata))
        all_images_per_chapter[chapter] = chapter_cards

    images_to_merge = []
    total_count = 0
    for chapter, all_images in all_images_per_chapter.items():
        # Sort images by card number
        all_images.sort(key=lambda x: x[1][1])

        # Calculate the number of images per row and rows required
        images_per_last_row = len(all_images) % IMAGES_PER_ROW
        is_last_row = images_per_last_row > 0

        rows = (len(all_images) // IMAGES_PER_ROW) + (1 if is_last_row else 0)
        total_width = (CARD_WIDTH + PADDING) * min(IMAGES_PER_ROW, len(all_images)) + PADDING
        max_height = (CARD_HEIGHT + PADDING) * rows + PADDING

        # Create a new image with the background of the chosen color
        new_image = Image.new('RGBA', (total_width, max_height), (bg_color[0], bg_color[1], bg_color[2], 255))

        x_offset, y_offset = PADDING, PADDING

        for index, img_mix in enumerate(all_images):
            img = img_mix[0]
            img = img.resize((CARD_WIDTH, CARD_HEIGHT), resample=Image.LANCZOS)
            img = round_corners(img, CORNER_RADIUS)

            new_image.paste(img, (x_offset, y_offset), img)

            # Adjust the normal count
            MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["normal"] = 4 - int(MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["normal"]) - int(MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["foil"])

            count = Image.open("assets/foil_card_count.png")
            count = count.resize((int(count.width * 1.5 * SCALING), int(count.height * 1.5 * SCALING)), resample=Image.LANCZOS)

            font = ImageFont.truetype("assets/black.ttf", int(100 * SCALING))

            draw = ImageDraw.Draw(count)
            text = str(MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["normal"])
            text_bbox = draw.textbbox((0, 0), text, font=font)
            textwidth = text_bbox[2] - text_bbox[0]
            textheight = text_bbox[3] - text_bbox[1]
            text_x = (count.width - textwidth) // 2
            text_y = (count.height - textheight) // 2 - int(10 * SCALING)
            draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))

            new_image.paste(count, (int(x_offset + CARD_WIDTH - count.width) - 5, y_offset + 5), count)
            x_offset += CARD_WIDTH + PADDING

            if DEBUG:
                print(MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["normal"], MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["name"])
            total_count += MY_COLLECTION[img_mix[1][0]][img_mix[1][1]]["normal"]
            if (index + 1) % IMAGES_PER_ROW == 0:
                x_offset = PADDING
                y_offset += CARD_HEIGHT + PADDING

        chapter_name_image = Image.new('RGBA', (new_image.width, int(210 * SCALING)), (bg_color[0], bg_color[1], bg_color[2], 255))

        draw = ImageDraw.Draw(chapter_name_image)
        font = ImageFont.truetype("assets/black.ttf", int(180 * SCALING))
        draw.text((PADDING, 5), f"{CHAPTER_NAMES[chapter]}:", font=font, fill=text_color)

        images_to_merge.append(chapter_name_image)
        images_to_merge.append(new_image)

    new_image = merge_images(images_to_merge, True, PADDING, bg_color, align="left")
    print("Cards missing:", total_count)

    # Save the new image
    output_dir = os.path.join(BASE_DIR, "output", "all_by_color", lang)
    os.makedirs(os.path.join(output_dir, "webp"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "png"), exist_ok=True)
    new_image.save(os.path.join(output_dir, "png", f"{generate_name}.png"), "PNG")
    try:
        new_image.save(os.path.join(output_dir, "webp", f"{generate_name}.webp"), "WebP", quality=90)
    except Exception as e:
        pass
    print(f"Image saved: {os.path.join(output_dir, f'{generate_name}')}")


MY_COLLECTION = load_my_card_collection_from_chapters()

# Gehe durch jede Sprache und jedes Kapitel und führe die Funktion für jede Farbe aus
for lang in LANGUAGES:
    chapters_dir = os.path.join(BASE_DIR, lang, "png")
    for set_name in SPECIAL_CHAPTERS:
        merge_cards(lang, (176, 192, 116), 9, f"P_{set_name}", True, [set_name])
    for ct in CARD_TYPES:
        for set_name in CHAPTERS:
            merge_cards_for_color(lang, ct.name, ct.color, 9, set_name, True, [set_name])
        pass
    for rarity in CARD_RARITY:
        if rarity[0] == "SP":
            merge_cards_missing_for_playset(lang, 9, f"x_missing_{rarity[0]}", SPECIAL_CHAPTERS, rarity[0])
        else:
            merge_cards_missing_for_playset(lang, 9, f"x_missing_{rarity[0]}", CHAPTERS, rarity[0])
