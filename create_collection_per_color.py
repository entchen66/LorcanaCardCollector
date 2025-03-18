import csv
import os
from collections import namedtuple

from PIL import Image, ImageDraw, ImageFont

# Global Settings
DEBUG = True
LANGUAGES = ["en"]  # Add "de", "fr", "it" if needed
CHAPTERS = ["001", "002", "003", "004", "005", "006", "007"]
SPECIAL_CHAPTERS = ["P1", "P2", "C1", "D23"]
VARIANTS = ["a", "b", "c", "d", "e", "f"]
CARDS_WITH_VARIANTS = [(("003", 4), 5)]
ColorType = namedtuple("ColorType", ["name", "color"])

CARD_TYPES = [
    ColorType("amber", (211, 149, 45)),  # Yellow
    ColorType("amethyst", (155, 89, 182)),  # Purple
    ColorType("emerald", (46, 204, 113)),  # Green
    ColorType("ruby", (189, 66, 68)),  # Red
    ColorType("sapphire", (35, 138, 175)),  # Blue
    ColorType("steel", (123, 131, 137)),  # Gray
]
CARD_TYPES_ORDER = [ct.name for ct in CARD_TYPES]

CHAPTER_NAMES = {
    "001": "1 - The First Chapter",
    "002": "2 - Rise of the Floodborn",
    "003": "3 - Into the Inklands",
    "004": "4 - Ursula's Return",
    "005": "5 - Shimmering Skies",
    "006": "6 - Azurite Sea",
    "007": "7 - Archazia's Island",
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
    ColorType("SR", (198, 198, 200)),  # Super Rare
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


def csv_to_json(csv_file_path):
    """Convert CSV data to JSON format."""
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            return list(csv_reader)
    except Exception as e:
        if DEBUG:
            print(f"Error reading CSV file {csv_file_path}: {e}")
        return []


def load_my_card_collection_from_chapters():
    """Load the card collection from chapters."""
    json_objects = csv_to_json('export.csv')

    dict_all_chapters = {}

    for chapter in CHAPTERS + SPECIAL_CHAPTERS:
        dict_all_chapters[chapter] = {}

    for entry in json_objects:
        card_dict = {
            "name": entry["Name"],
            "normal": entry["Normal"],
            "foil": entry["Foil"],
            "color": entry["Color"].split(" ")[0],
        }
        entry["Card Number"] = entry["Card Number"].replace("P", "")
        if entry["Card Number"].isdigit():  # Check for variants
            card_num = str(entry["Card Number"]).zfill(3)
        else:
            card_num = str(entry["Card Number"]).zfill(4)
        dict_all_chapters[entry["Set"]][card_num] = card_dict
    return dict_all_chapters


def round_corners(im, rad):
    """Round the corners of an image."""
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
    """Extract the rarity from the filename."""
    parts = filename.split('.')[0].split('_')
    if len(parts) >= 3:
        return parts[2]
    return None


def get_card_color_from_filename(filename):
    """Extract the card color from the filename."""
    parts = filename.split('.')[0].split('_')
    if len(parts) >= 2:
        return parts[1]
    return None


def get_type_from_filename(filename):
    """Extract the type from the filename."""
    parts = filename.split('.')[0].split('_')
    if len(parts) >= 4:
        return parts[3]
    return None


def merge_images(images, vertically, offset_merge, space_color=(255, 255, 255, 0), align='center'):
    """
    Merge multiple images into a single image, either vertically or horizontally.

    :param images: List of Images.
    :param vertically: True to merge images vertically, False for horizontal merge.
    :param offset_merge: Space between the images.
    :param align: Alignment of the images ('left', 'right', 'center', 'top', 'bottom').
    :param space_color: Color of the space between images (default is transparent).
    :return: The merged image.
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


def process_images(lang, chapter_list, filter_func, generate_name, img_per_row=6, color_rgb=(255, 255, 255), mark_completed=False, output_subdir="output"):
    """
    General function to process images based on a filtering function.

    :param lang: Language code.
    :param chapter_list: List of chapters to process.
    :param filter_func: Function to filter images.
    :param generate_name: Base name for the output files.
    :param img_per_row: Number of images per row.
    :param color_rgb: Background color.
    :param mark_completed: Whether to mark completed playsets.
    :param output_subdir: Subdirectory for output files.
    """
    IMAGES_PER_ROW = img_per_row

    all_images_per_chapter = {}
    for chapter in chapter_list:
        chapter_cards = []
        chapter_dir = os.path.join(BASE_DIR, lang, "webp", chapter)

        if not os.path.exists(chapter_dir):
            continue

        image_filenames = [img for img in os.listdir(chapter_dir) if filter_func(img)]
        image_filenames.sort(key=lambda x: CARD_RARITY_ORDER.index(get_rarity_from_filename(x)))

        if DEBUG:
            print(f"Processing directory: {chapter_dir}")
            print(f"Image filenames: {image_filenames}")

        # Load images and add metadata
        for img_filename in image_filenames:
            if chapter not in MY_COLLECTION:
                continue
            card_number = img_filename.split("_")[0]
            if card_number not in MY_COLLECTION[chapter]:
                continue

            card_info = MY_COLLECTION[chapter][card_number]
            normal_count = int(card_info["normal"])
            foil_count = int(card_info["foil"])
            total_count = normal_count + foil_count

            img_path = os.path.join(chapter_dir, img_filename)
            img = Image.open(img_path).convert("RGBA")

            # Determine if the card should have an overlay
            overlay = None
            if total_count == 0:
                # Create red overlay for missing cards
                overlay = Image.new('RGBA', img.size, (155, 110, 110, 160))  # Red overlay
            elif total_count >= 4 and mark_completed:
                # Create green overlay for completed playsets
                overlay = Image.new('RGBA', img.size, (110, 155, 110, 160))  # Green overlay

            if overlay:
                img = Image.alpha_composite(img, overlay)

            metadata = {
                "chapter": chapter,
                "card_number": card_number,
                "color": card_info["color"],
                "color_rgb": color_rgb,
                "filename": img_filename,
                "is_missing": total_count == 0,
                "normal_count": normal_count,
                "foil_count": foil_count,
                "total_count": total_count,
            }
            chapter_cards.append((img, metadata))

        all_images_per_chapter[chapter] = chapter_cards

    images_to_merge = []
    total_missing = 0
    for chapter, images_with_metadata in all_images_per_chapter.items():
        font = ImageFont.truetype("assets/black.ttf", int(50 * SCALING))

        # Sort images by card number
        images_with_metadata.sort(key=lambda x: x[1]["card_number"])

        # Calculate dimensions
        num_images = len(images_with_metadata)
        if num_images == 0:
            continue
        rows = (num_images + IMAGES_PER_ROW - 1) // IMAGES_PER_ROW
        total_width = (CARD_WIDTH + PADDING) * min(IMAGES_PER_ROW, num_images) + PADDING
        total_height = (CARD_HEIGHT + PADDING) * rows + PADDING

        # Create a new image with the background color
        new_image = Image.new('RGBA', (total_width, total_height), (*color_rgb, 255))

        x_offset, y_offset = PADDING, PADDING

        for index, (img, metadata) in enumerate(images_with_metadata):
            img = img.resize((CARD_WIDTH, CARD_HEIGHT), resample=Image.LANCZOS)
            img = round_corners(img, CORNER_RADIUS)

            new_image.paste(img, (x_offset, y_offset), img)

            chapter_key = metadata["chapter"]
            card_number = metadata["card_number"]
            normal_count = metadata["normal_count"]
            foil_count = metadata["foil_count"]
            total_count = metadata["total_count"]

            if total_count > 0:
                # Add counts
                normal_count_img = Image.open("assets/normal_card_count.png")
                normal_count_img = normal_count_img.resize(
                    (int(normal_count_img.width * 0.75 * SCALING), int(normal_count_img.height * 0.75 * SCALING)),
                    resample=Image.LANCZOS
                )

                foil_count_img = Image.open("assets/foil_card_count.png")
                foil_count_img = foil_count_img.resize(
                    (int(foil_count_img.width * 0.75 * SCALING), int(foil_count_img.height * 0.75 * SCALING)),
                    resample=Image.LANCZOS
                )

                # Draw counts
                draw = ImageDraw.Draw(foil_count_img)
                text = str(foil_count)
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_x = (foil_count_img.width - (text_bbox[2] - text_bbox[0])) // 2
                text_y = (foil_count_img.height - (text_bbox[3] - text_bbox[1])) // 2 - int(10 * SCALING)
                draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))

                draw = ImageDraw.Draw(normal_count_img)
                text = str(normal_count)
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_x = (normal_count_img.width - (text_bbox[2] - text_bbox[0])) // 2
                text_y = (normal_count_img.height - (text_bbox[3] - text_bbox[1])) // 2 - int(10 * SCALING)
                draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))

                # Add completed marker if playset is complete
                if total_count >= 4 and mark_completed:
                    done_img = Image.open("assets/done.png")
                    done_img = done_img.resize(
                        (int(done_img.width * 0.2 * SCALING), int(done_img.height * 0.2 * SCALING)),
                        resample=Image.LANCZOS
                    )
                    new_image.paste(
                        done_img,
                        (x_offset + int(15 * SCALING), y_offset + CARD_HEIGHT - done_img.height - int(15 * SCALING)),
                        done_img
                    )

                # Paste counts onto the main image
                new_image.paste(
                    foil_count_img,
                    (x_offset + CARD_WIDTH - foil_count_img.width - 5, y_offset + int(foil_count_img.height * 0.75) + 5),
                    foil_count_img
                )
                new_image.paste(
                    normal_count_img,
                    (x_offset + CARD_WIDTH - normal_count_img.width - int(normal_count_img.width * 0.75) - 5, y_offset + 5),
                    normal_count_img
                )
            else:
                # Add missing icon
                missing_img = Image.open("assets/missing.png")
                missing_img = missing_img.resize(
                    (int(missing_img.width * 0.36 * SCALING), int(missing_img.height * 0.36 * SCALING)),
                    resample=Image.LANCZOS
                )
                new_image.paste(
                    missing_img,
                    (x_offset + CARD_WIDTH - missing_img.width - int(5 * SCALING), y_offset + int(5 * SCALING)),
                    missing_img
                )
                total_missing += 1

            x_offset += CARD_WIDTH + PADDING

            if (index + 1) % IMAGES_PER_ROW == 0:
                x_offset = PADDING
                y_offset += CARD_HEIGHT + PADDING

        # Add chapter name
        chapter_name_image = Image.new('RGBA', (new_image.width, int(210 * SCALING)), (*color_rgb, 255))
        draw = ImageDraw.Draw(chapter_name_image)
        font = ImageFont.truetype("assets/black.ttf", int(180 * SCALING))
        draw.text((PADDING, 5), f"{CHAPTER_NAMES.get(chapter, chapter)}:", font=font, fill=(255, 255, 255))

        images_to_merge.append(chapter_name_image)
        images_to_merge.append(new_image)

    if not images_to_merge:
        if DEBUG:
            print("No images to merge.")
        return

    # Merge all images
    final_image = merge_images(images_to_merge, True, PADDING, color_rgb, align="left")

    # Save the final image
    output_dir = os.path.join(BASE_DIR, output_subdir, "all_by_color", lang)
    os.makedirs(os.path.join(output_dir, "webp"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "png"), exist_ok=True)
    final_image.save(os.path.join(output_dir, "png", f"{generate_name}.png"), "PNG")
    try:
        final_image.save(os.path.join(output_dir, "webp", f"{generate_name}.webp"), "WebP", quality=90)
    except Exception as e:
        if DEBUG:
            print(f"Failed to save WebP image: {e}")
    print(f"Image saved: {os.path.join(output_dir, f'{generate_name}')}")
    if total_missing > 0:
        print(f"Total missing cards: {total_missing}")


def merge_cards(lang, color_rgb, img_per_row, generate_name, mark_completed, chapter_list):
    """Merge all cards in the specified chapters."""

    def filter_func(img_filename):
        return True  # Include all images

    process_images(lang, chapter_list, filter_func, generate_name, img_per_row, color_rgb, mark_completed)


def merge_cards_for_color(lang, color, color_rgb, img_per_row, generate_name, mark_completed, chapter_list):
    """Merge cards of a specific color into a single image."""

    def filter_func(img_filename):
        return color.lower() in img_filename.lower()

    process_images(lang, chapter_list, filter_func, f"{generate_name}_{color}", img_per_row, color_rgb, mark_completed)


def merge_cards_missing_for_playset(lang, img_per_row, generate_name, chapter_list=CHAPTERS, rarity=None):
    """Merge missing cards for playset completion into a single image."""

    def filter_func(img_filename):
        if rarity:
            return f"_{rarity}_" in img_filename
        else:
            return True  # Include all images

    # Modify the process_images function to handle missing cards differently
    IMAGES_PER_ROW = img_per_row

    all_images_per_chapter = {}
    bg_color = (255, 255, 255)
    text_color = (0, 0, 0)
    total_missing_cards = 0
    for chapter in chapter_list:
        chapter_cards = []
        chapter_dir = os.path.join(BASE_DIR, lang, "webp", chapter)

        if not os.path.exists(chapter_dir):
            continue

        image_filenames = [img for img in os.listdir(chapter_dir) if filter_func(img)]
        image_filenames.sort(key=lambda x: CARD_RARITY_ORDER.index(get_rarity_from_filename(x)))

        if DEBUG:
            print(f"Processing directory: {chapter_dir}")
            print(f"Image filenames: {image_filenames}")

        # Load images and add metadata
        for img_filename in image_filenames:
            if chapter not in MY_COLLECTION:
                continue
            card_number = img_filename.split("_")[0]
            if card_number not in MY_COLLECTION[chapter]:
                continue

            card_info = MY_COLLECTION[chapter][card_number]
            normal_count = int(card_info["normal"])
            foil_count = int(card_info["foil"])
            total_count = normal_count + foil_count

            if total_count >= 4:
                continue  # Skip cards where playset is complete

            img_path = os.path.join(chapter_dir, img_filename)
            img = Image.open(img_path).convert("RGBA")

            # Highlight the missing amount
            missing_count = 4 - total_count

            metadata = {
                "chapter": chapter,
                "card_number": card_number,
                "filename": img_filename,
                "missing_count": missing_count,
            }
            chapter_cards.append((img, metadata))
            total_missing_cards += missing_count

        all_images_per_chapter[chapter] = chapter_cards

    images_to_merge = []
    for chapter, images_with_metadata in all_images_per_chapter.items():
        font = ImageFont.truetype("assets/black.ttf", int(100 * SCALING))

        # Sort images by card number
        images_with_metadata.sort(key=lambda x: x[1]["card_number"])

        # Calculate dimensions
        num_images = len(images_with_metadata)
        if num_images == 0:
            continue
        rows = (num_images + IMAGES_PER_ROW - 1) // IMAGES_PER_ROW
        total_width = (CARD_WIDTH + PADDING) * min(IMAGES_PER_ROW, num_images) + PADDING
        total_height = (CARD_HEIGHT + PADDING) * rows + PADDING

        # Create a new image with the background color
        new_image = Image.new('RGBA', (total_width, total_height), (*bg_color, 255))

        x_offset, y_offset = PADDING, PADDING

        for index, (img, metadata) in enumerate(images_with_metadata):
            img = img.resize((CARD_WIDTH, CARD_HEIGHT), resample=Image.LANCZOS)
            img = round_corners(img, CORNER_RADIUS)

            new_image.paste(img, (x_offset, y_offset), img)

            missing_count = metadata["missing_count"]

            # Display missing count
            count_img = Image.open("assets/foil_card_count.png")
            count_img = count_img.resize(
                (int(count_img.width * 1.5 * SCALING), int(count_img.height * 1.5 * SCALING)),
                resample=Image.LANCZOS
            )

            draw = ImageDraw.Draw(count_img)
            text = str(missing_count)
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_x = (count_img.width - (text_bbox[2] - text_bbox[0])) // 2
            text_y = (count_img.height - (text_bbox[3] - text_bbox[1])) // 2 - int(10 * SCALING)
            draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))

            new_image.paste(
                count_img,
                (x_offset + CARD_WIDTH - count_img.width - 5, y_offset + 5),
                count_img
            )

            x_offset += CARD_WIDTH + PADDING

            if (index + 1) % IMAGES_PER_ROW == 0:
                x_offset = PADDING
                y_offset += CARD_HEIGHT + PADDING

        # Add chapter name
        chapter_name_image = Image.new('RGBA', (new_image.width, int(210 * SCALING)), (*bg_color, 255))
        draw = ImageDraw.Draw(chapter_name_image)
        font = ImageFont.truetype("assets/black.ttf", int(180 * SCALING))
        draw.text((PADDING, 5), f"{CHAPTER_NAMES.get(chapter, chapter)}:", font=font, fill=text_color)

        images_to_merge.append(chapter_name_image)
        images_to_merge.append(new_image)

    if not images_to_merge:
        if DEBUG:
            print("No images to merge.")
        return

    # Merge all images
    final_image = merge_images(images_to_merge, True, PADDING, bg_color, align="left")
    print(f"Total missing cards for playset completion: {total_missing_cards}")

    # Save the final image
    output_dir = os.path.join(BASE_DIR, "output", "missing_playset", lang)
    os.makedirs(os.path.join(output_dir, "webp"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "png"), exist_ok=True)
    final_image.save(os.path.join(output_dir, "png", f"{generate_name}.png"), "PNG")
    try:
        final_image.save(os.path.join(output_dir, "webp", f"{generate_name}.webp"), "WebP", quality=90)
    except Exception as e:
        if DEBUG:
            print(f"Failed to save WebP image: {e}")
    print(f"Image saved: {os.path.join(output_dir, f'{generate_name}')}")


# Load your card collection
MY_COLLECTION = load_my_card_collection_from_chapters()

# Process cards for each language
for lang in LANGUAGES:
    # Merge special chapters
    for set_name in SPECIAL_CHAPTERS:
        merge_cards(lang, (176, 192, 116), 9, f"P_{set_name}", True, [set_name])

    # Merge cards by color for each chapter
    for ct in CARD_TYPES:
        for set_name in CHAPTERS:
            merge_cards_for_color(lang, ct.name, ct.color, 9, set_name, True, [set_name])

    # Merge missing cards for playset completion
    for rarity in CARD_RARITY:
        if rarity.name == "SP":
            merge_cards_missing_for_playset(lang, 9, f"x_missing_{rarity.name}", SPECIAL_CHAPTERS, rarity.name)
        else:
            merge_cards_missing_for_playset(lang, 9, f"x_missing_{rarity.name}", CHAPTERS, rarity.name)
