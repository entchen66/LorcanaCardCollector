# -*- coding: utf-8 -*-
import csv
import os
import re  # Import regex module
from collections import namedtuple, defaultdict

from PIL import Image, ImageDraw, ImageFont

# Global Settings
DEBUG = True
LANGUAGES = ["en"]  # Add "de", "fr", "it" if needed
CHAPTERS = ["001", "002", "003", "004", "005", "006", "007"]
SPECIAL_CHAPTERS = ["P1", "P2", "C1", "D23"]  # Add others as needed
ColorType = namedtuple("ColorType", ["name", "color"])

# Global dictionary to store multicolor card assignments
# Structure: {(chapter, card_key): assigned_color_name}
MULTICOLOR_ASSIGNMENTS = {}

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
CARD_RARITY_ORDER = ["CC", "UC", "RR", "SR", "LL", "EE", "SP"]

SCALING = 1
BASE_DIR = "cards"
PADDING = int(50 * SCALING)
CARD_WIDTH, CARD_HEIGHT = int(630 * SCALING), int(880 * SCALING)
IMAGES_PER_ROW = 6
CORNER_RADIUS = int(20 * SCALING)


def csv_to_json(csv_file_path):
    """Convert CSV data to JSON format."""
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
            # Read the first line to get headers, handle potential BOM
            header_line = csv_file.readline()
            headers = [h.strip().replace('\ufeff', '') for h in header_line.split(',')]  # Assuming comma delimiter for header check
            csv_file.seek(0)  # Reset read pointer

            # Determine dialect more robustly
            try:
                dialect = csv.Sniffer().sniff(csv_file.read(2048), delimiters=',;\t|')  # Sniff common delimiters
            except csv.Error:
                print("Warning: Could not automatically determine CSV delimiter. Assuming comma.")
                dialect = 'excel'  # Default fallback
            csv_file.seek(0)

            csv_reader = csv.DictReader(csv_file, dialect=dialect)
            # Ensure fieldnames are cleaned even if DictReader got them differently
            csv_reader.fieldnames = [key.strip().replace('\ufeff', '') for key in csv_reader.fieldnames or headers]

            return list(csv_reader)
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_file_path}")
        return []
    except Exception as e:
        if DEBUG:
            print(f"Error reading CSV file {csv_file_path}: {e}")
        return []


# --- NEW Helper function to generate standardized keys ---
def generate_card_key(set_code, card_num_raw):
    """Generates a standardized card key matching the filename format."""
    card_num_raw = card_num_raw.strip()
    if set_code in CHAPTERS:
        # Use regex to separate numeric part and optional alphabetic variant suffix
        match = re.match(r'^(\d+)([a-zA-Z]*)$', card_num_raw)
        if match:
            num_part = match.group(1)
            variant_part = match.group(2).lower()  # Store variant suffix consistently (e.g., lowercase)
            # Pad numeric part to 3 digits
            padded_num = num_part.zfill(3)
            return padded_num + variant_part  # e.g., '004' + 'a' -> '004a', '083' + '' -> '083'
        else:
            # Fallback for unexpected formats in main chapters
            if DEBUG: print(f"Warning: Unexpected card number format '{card_num_raw}' for chapter {set_code}. Using raw value as key.")
            return card_num_raw
    else:
        # For special chapters (P1, D23, etc.), use the raw number directly as the key
        return card_num_raw


# --- End Helper function ---


def load_my_card_collection_from_chapters():
    """Load the card collection, generating standardized keys."""
    json_objects = csv_to_json('export.csv')
    if not json_objects:
        print("Failed to load data from export.csv. Exiting.")
        exit()

    dict_all_chapters = defaultdict(dict)
    # Adjust expected keys based on the provided CSV example header
    expected_keys = ["Name", "Normal", "Foil", "Color", "Rarity", "Set", "Card Number"]  # Assuming these are the correct final headers

    if json_objects and not all(key in json_objects[0] for key in expected_keys):
        print(f"Error: CSV missing one or more expected columns: {expected_keys}")
        print(f"Found columns: {list(json_objects[0].keys())}")
        # Optional: Try to map based on position if headers are missing/wrong? More complex.
        exit()

    for entry in json_objects:
        try:
            color_str = entry.get("Color", "").strip()
            colors = color_str.split(" ") if color_str else []
            colors = [c for c in colors if c]

            rarity = entry.get("Rarity", "").strip().upper()  # Normalize case

            card_dict = {
                "name": entry.get("Name", "Unknown").strip(),
                "normal": entry.get("Normal", "0").strip() or "0",
                "foil": entry.get("Foil", "0").strip() or "0",
                "color": colors,
                "rarity": rarity,
                "multicolor": len(colors) > 1,
            }

            card_num_raw = entry.get("Card Number", "").strip()
            set_code = entry.get("Set", "").strip()

            # *** Use the helper function to generate the key ***
            card_key = generate_card_key(set_code, card_num_raw)

            if not card_key:  # Handle cases where key generation might fail
                if DEBUG: print(f"Warning: Could not generate valid key for row: {entry}. Skipping.")
                continue

            # Store using the standardized key
            dict_all_chapters[set_code][card_key] = card_dict

        except Exception as e:
            if DEBUG:
                print(f"Error processing row: {entry}")
                print(f"Error details: {e}")
            continue

    return dict_all_chapters


def calculate_multicolor_assignments(collection):
    """Calculates assignments using standardized card keys."""
    global MULTICOLOR_ASSIGNMENTS
    MULTICOLOR_ASSIGNMENTS = {}
    cards_by_combo = defaultdict(list)

    for chapter, cards in collection.items():
        # card_key is already the standardized key from loading
        for card_key, card_info in cards.items():
            is_multi = card_info.get("multicolor", False)
            rarity = card_info.get("rarity", "")
            if not is_multi or rarity == "ENCHANTED":
                continue

            colors = card_info.get("color", [])
            if len(colors) < 2: continue

            color_pair = tuple(sorted([c.lower() for c in colors]))
            combo_key = (chapter, color_pair)
            # Append the standardized card_key
            cards_by_combo[combo_key].append(card_key)

    # Assign cards within each group
    for (chapter, color_pair), card_keys in cards_by_combo.items():
        # Sort the standardized keys (handles '004a', '004b', '083' correctly)
        sorted_card_keys = sorted(card_keys)
        num_cards = len(sorted_card_keys)
        split_point = (num_cards + 1) // 2

        color1, color2 = color_pair

        for i, card_key in enumerate(sorted_card_keys):
            # Use the standardized key for the assignment dictionary
            assignment_key = (chapter, card_key)
            if i < split_point:
                MULTICOLOR_ASSIGNMENTS[assignment_key] = color1
            else:
                MULTICOLOR_ASSIGNMENTS[assignment_key] = color2

        if DEBUG and num_cards > 0:
            print(f"Assigning {chapter} {color_pair}: {split_point} to '{color1}', {num_cards - split_point} to '{color2}'")


def round_corners(im, rad):
    """Round the corners of an image."""
    # (Code remains the same)
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
    """Extract rarity code from filename."""
    # (Code remains the same)
    parts = filename.split('.')[0].split('_')
    if len(parts) >= 3:
        rarity_code = parts[2].upper()
        return rarity_code
    return None


def get_card_color_from_filename(filename):
    """Extract card color(s) from filename."""
    # (Code remains the same)
    parts = filename.split('.')[0].split('_')
    if len(parts) >= 2:
        colors = parts[1].lower().split("&")
        return colors
    return []


def merge_images(images, vertically, offset_merge, space_color=(255, 255, 255, 0), align='center'):
    """Merges multiple images vertically or horizontally."""
    # (Code remains the same)
    if not images:
        return Image.new('RGBA', (1, 1), space_color)
    widths, heights = zip(*(i.size for i in images))
    if vertically:
        max_width = max(widths) if widths else 1
        total_height = sum(heights) + (offset_merge * (len(images) - 1)) if heights else 1
        new_im = Image.new('RGBA', (max_width, total_height), space_color)
        y_offset = 0
        for im in images:
            if align == 'left':
                x_position = 0
            elif align == 'right':
                x_position = max_width - im.size[0]
            else:
                x_position = (max_width - im.size[0]) // 2
            paste_im = im if im.mode == 'RGBA' else im.convert('RGBA')
            new_im.paste(paste_im, (x_position, y_offset), paste_im)
            y_offset += im.size[1] + offset_merge
    else:  # horizontally
        max_height = max(heights) if heights else 1
        total_width = sum(widths) + (offset_merge * (len(images) - 1)) if widths else 1
        new_im = Image.new('RGBA', (total_width, max_height), space_color)
        x_offset = 0
        for im in images:
            if align == 'top':
                y_position = 0
            elif align == 'bottom':
                y_position = max_height - im.size[1]
            else:
                y_position = (max_height - im.size[1]) // 2
            paste_im = im if im.mode == 'RGBA' else im.convert('RGBA')
            new_im.paste(paste_im, (x_offset, y_position), paste_im)
            x_offset += im.size[0] + offset_merge
    return new_im


def process_images(lang, chapter_list, generate_name,
                   target_color=None,
                   multicolor_assignments=None,
                   img_per_row=6, color_rgb=(255, 255, 255),
                   mark_completed=False, output_subdir="output"):
    """Processes images, using standardized keys for lookup."""
    IMAGES_PER_ROW = img_per_row
    all_images_per_chapter = defaultdict(list)
    total_processed_cards = 0

    # Load assets once per call
    font_count, font_chapter = None, None
    normal_count_img_base, foil_count_img_base, done_img_base, missing_img_base = None, None, None, None
    try:
        # (Asset loading code remains the same)
        font_count = ImageFont.truetype("assets/black.ttf", int(50 * SCALING))
        font_chapter = ImageFont.truetype("assets/black.ttf", int(180 * SCALING))
        normal_count_img_base = Image.open("assets/normal_card_count.png")
        foil_count_img_base = Image.open("assets/foil_card_count.png")
        done_img_base = Image.open("assets/done.png")
        missing_img_base = Image.open("assets/missing.png")
    except Exception as e:
        print(f"Warning: Error loading assets/fonts: {e}. Some overlays/text might be missing.")
        if not font_count: font_count = ImageFont.load_default()
        if not font_chapter: font_chapter = ImageFont.load_default()

    for chapter in chapter_list:
        chapter_cards = []
        chapter_dir = os.path.join(BASE_DIR, lang, "webp", chapter)

        if not os.path.exists(chapter_dir): continue
        if chapter not in MY_COLLECTION: continue

        if DEBUG:
            log_msg = f"Processing: {chapter_dir}"
            if target_color: log_msg += f" for target color: {target_color}"
            print(log_msg)

        for img_filename in os.listdir(chapter_dir):
            if not (img_filename.lower().endswith(".webp") or img_filename.lower().endswith(".png")):
                continue

            # *** Use the filename part directly as the key ***
            card_key = img_filename.split("_")[0]  # e.g., '004a', '083'

            # *** Lookup using this key ***
            if card_key not in MY_COLLECTION[chapter]:
                if DEBUG: print(f"Debug: Key '{card_key}' from filename '{img_filename}' not found in MY_COLLECTION[{chapter}]. Skipping.")
                continue  # Skip if card info wasn't loaded for this key

            card_info = MY_COLLECTION[chapter][card_key]
            colors = [c.lower() for c in card_info.get("color", [])]
            rarity = card_info.get("rarity", "")
            is_multicolor = card_info.get("multicolor", False)

            # --- Updated Filtering Logic ---
            include_card = False
            if target_color:
                target_color_lower = target_color.lower()

                if is_multicolor:
                    # --- Handle Enchanted Multicolor First ---
                    if rarity == "ENCHANTED":  # Check your standard EE code
                        # Include if ANY of its colors match the target
                        if target_color_lower in colors:
                            include_card = True
                            if DEBUG: print(f"  Including EE Multi: {card_key} ({colors}) for target {target_color_lower}")

                    # --- Handle Non-Enchanted Multicolor (Use Assignment) ---
                    else:
                        assignment_key = (chapter, card_key)
                        assigned_color = multicolor_assignments.get(assignment_key)
                        # We expect an assignment here if it's non-EE multi
                        if assigned_color == target_color_lower:
                            include_card = True
                            if DEBUG: print(f"  Including Non-EE Multi: {card_key} assigned to {assigned_color} for target {target_color_lower}")
                        # Optional: Log if assignment missing for non-EE multi
                        elif assigned_color is None and DEBUG:
                            print(f"  Warning: Missing assignment for Non-EE Multi {card_key} ({colors})")

                # --- Handle Single Color Cards ---
                elif len(colors) == 1:
                    if colors[0] == target_color_lower:
                        include_card = True
                        if DEBUG: print(f"  Including Single Color: {card_key} ({colors[0]}) for target {target_color_lower}")

            else:  # No target_color specified (e.g., merge_cards 'all')
                include_card = True

            if not include_card:
                continue
            # --- End Filtering Logic ---

            total_processed_cards += 1
            normal_count = int(card_info.get("normal", 0))
            foil_count = int(card_info.get("foil", 0))
            total_count = normal_count + foil_count

            img_path = os.path.join(chapter_dir, img_filename)
            try:
                img = Image.open(img_path).convert("RGBA")
            except Exception as e:
                if DEBUG: print(f"Error opening image {img_path}: {e}")
                continue

            # Apply overlays (code remains the same)
            overlay = None
            if total_count == 0:
                overlay = Image.new('RGBA', img.size, (155, 110, 110, 160))
            elif total_count >= 4 and mark_completed:
                overlay = Image.new('RGBA', img.size, (110, 155, 110, 160))
            if overlay:
                img = Image.alpha_composite(img, overlay)

            metadata = {
                "chapter": chapter,
                "card_number": card_key,  # Store the standardized key
                "color": card_info["color"], "color_rgb": color_rgb,
                "filename": img_filename, "is_missing": total_count == 0,
                "normal_count": normal_count, "foil_count": foil_count,
                "total_count": total_count, "rarity": rarity,
            }
            chapter_cards.append((img, metadata))

        # Sort using the standardized card_number key
        chapter_cards.sort(key=lambda x: x[1]["card_number"])
        all_images_per_chapter[chapter] = chapter_cards
        if DEBUG and chapter_cards:
            print(f"Chapter {chapter}: Found {len(chapter_cards)} cards matching filter.")

    # --- Image Merging Section ---
    if total_processed_cards == 0:
        print(f"No cards found matching the criteria for {generate_name}. Skipping image generation.")
        return

    images_to_merge = []
    total_missing_in_view = 0

    for chapter, images_with_metadata in all_images_per_chapter.items():
        if not images_with_metadata: continue

        num_images = len(images_with_metadata)
        rows = (num_images + IMAGES_PER_ROW - 1) // IMAGES_PER_ROW
        grid_width = (CARD_WIDTH + PADDING) * min(IMAGES_PER_ROW, num_images) - PADDING + (2 * PADDING)
        grid_height = (CARD_HEIGHT + PADDING) * rows - PADDING + (2 * PADDING)

        chapter_image_grid = Image.new('RGBA', (grid_width, grid_height), (*color_rgb, 255))
        x_offset, y_offset = PADDING, PADDING

        for index, (img, metadata) in enumerate(images_with_metadata):
            # Resize, round, paste (code remains the same)
            img_resized = img.resize((CARD_WIDTH, CARD_HEIGHT), resample=Image.LANCZOS)
            img_rounded = round_corners(img_resized, CORNER_RADIUS)
            chapter_image_grid.paste(img_rounded, (x_offset, y_offset), img_rounded)

            # Draw overlays (code remains the same)
            normal_count = metadata["normal_count"]
            foil_count = metadata["foil_count"]
            total_count = metadata["total_count"]
            if total_count > 0:
                if normal_count_img_base and font_count:
                    # (Draw normal count)
                    n_img = normal_count_img_base.copy();
                    n_img = n_img.resize((int(n_img.width * 0.75 * SCALING), int(n_img.height * 0.75 * SCALING)), resample=Image.LANCZOS);
                    draw_n = ImageDraw.Draw(n_img);
                    text_n = str(normal_count);
                    bbox_n = draw_n.textbbox((0, 0), text_n, font=font_count);
                    tx_n = (n_img.width - (bbox_n[2] - bbox_n[0])) // 2;
                    ty_n = (n_img.height - (bbox_n[3] - bbox_n[1])) // 2 - int(10 * SCALING);
                    draw_n.text((tx_n, ty_n), text_n, font=font_count, fill=(255, 255, 255));
                    chapter_image_grid.paste(n_img, (x_offset + CARD_WIDTH - n_img.width - int(n_img.width * 0.75) - 5, y_offset + 5), n_img)  # noqa e501
                if foil_count_img_base and font_count:
                    # (Draw foil count)
                    f_img = foil_count_img_base.copy();
                    f_img = f_img.resize((int(f_img.width * 0.75 * SCALING), int(f_img.height * 0.75 * SCALING)), resample=Image.LANCZOS);
                    draw_f = ImageDraw.Draw(f_img);
                    text_f = str(foil_count);
                    bbox_f = draw_f.textbbox((0, 0), text_f, font=font_count);
                    tx_f = (f_img.width - (bbox_f[2] - bbox_f[0])) // 2;
                    ty_f = (f_img.height - (bbox_f[3] - bbox_f[1])) // 2 - int(10 * SCALING);
                    draw_f.text((tx_f, ty_f), text_f, font=font_count, fill=(255, 255, 255));
                    chapter_image_grid.paste(f_img, (x_offset + CARD_WIDTH - f_img.width - 5, y_offset + int(f_img.height * 0.75) + 5), f_img)  # noqa e501
                if total_count >= 4 and mark_completed and done_img_base:
                    # (Draw completed marker)
                    d_img = done_img_base.copy();
                    d_img = d_img.resize((int(d_img.width * 0.2 * SCALING), int(d_img.height * 0.2 * SCALING)), resample=Image.LANCZOS);
                    chapter_image_grid.paste(d_img, (x_offset + int(15 * SCALING), y_offset + CARD_HEIGHT - d_img.height - int(15 * SCALING)), d_img)  # noqa e501
            else:  # total_count == 0
                total_missing_in_view += 1
                if missing_img_base:
                    # (Draw missing icon)
                    m_img = missing_img_base.copy();
                    m_img = m_img.resize((int(m_img.width * 0.36 * SCALING), int(m_img.height * 0.36 * SCALING)), resample=Image.LANCZOS);
                    chapter_image_grid.paste(m_img, (x_offset + CARD_WIDTH - m_img.width - int(5 * SCALING), y_offset + int(5 * SCALING)), m_img)  # noqa e501

            x_offset += CARD_WIDTH + PADDING
            if (index + 1) % IMAGES_PER_ROW == 0:
                x_offset = PADDING
                y_offset += CARD_HEIGHT + PADDING

        # Add chapter name header (only if chapter_list has exactly one item)
        if len(chapter_list) == 1 and font_chapter:
            # (Draw chapter header code remains the same)
            chapter_name_image = Image.new('RGBA', (grid_width, int(210 * SCALING)), (*color_rgb, 255));
            draw_title = ImageDraw.Draw(chapter_name_image);
            title_text = f"{CHAPTER_NAMES.get(chapter, chapter)}:";
            title_color = (255, 255, 255);
            draw_title.text((PADDING, 5), title_text, font=font_chapter, fill=title_color);
            images_to_merge.append(chapter_name_image)  # noqa e501

        images_to_merge.append(chapter_image_grid)

    # --- Final Image Saving ---
    if not images_to_merge:
        if DEBUG: print(f"No images generated for any chapter for {generate_name}.")
        return

    # (Merging and Saving code remains the same)
    if len(images_to_merge) > 1:
        final_image = merge_images(images_to_merge, True, PADDING, (*color_rgb, 255), align="left")
    elif images_to_merge:
        final_image = images_to_merge[0]
    else:
        print(f"Error: No images available to save for {generate_name}");
        return

    output_base_dir = os.path.join(BASE_DIR, output_subdir)
    sub_folder = "all_by_color" if target_color else "all_sets"
    output_dir = os.path.join(output_base_dir, sub_folder, lang)
    os.makedirs(os.path.join(output_dir, "webp"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "png"), exist_ok=True)

    png_path = os.path.join(output_dir, "png", f"{generate_name}.png")
    webp_path = os.path.join(output_dir, "webp", f"{generate_name}.webp")

    try:
        final_image.save(png_path, "PNG")
        print(f"Image saved: {png_path}")
        try:
            final_image.save(webp_path, "WebP", quality=90)
        except Exception as e:
            print(f"Failed to save WebP image {webp_path}: {e}")
    except Exception as e:
        print(f"Failed to save PNG image {png_path}: {e}")

    if total_missing_in_view > 0:
        print(f"Total missing cards shown in {generate_name}: {total_missing_in_view}")


def merge_cards(lang, color_rgb, img_per_row, generate_name, mark_completed, chapter_list):
    """Merge all cards."""
    # (Call remains the same)
    print(f"--- Merging all cards for chapters: {chapter_list} ---")
    process_images(lang=lang, chapter_list=chapter_list, generate_name=generate_name, target_color=None, multicolor_assignments=MULTICOLOR_ASSIGNMENTS, img_per_row=img_per_row, color_rgb=color_rgb,
                   mark_completed=mark_completed, output_subdir="output")


def merge_cards_for_color(lang, merge_color, color_rgb, img_per_row, generate_name, mark_completed, chapter_list):
    """Merge cards of a specific color for specific chapter(s)."""
    # (Call remains the same)
    print(f"--- Merging cards for color: {merge_color} in chapters: {chapter_list} ---")
    process_images(lang=lang, chapter_list=chapter_list, generate_name=generate_name, target_color=merge_color, multicolor_assignments=MULTICOLOR_ASSIGNMENTS, img_per_row=img_per_row, color_rgb=color_rgb,
                   mark_completed=mark_completed, output_subdir="output")


def merge_cards_missing_for_playset(lang, img_per_row, generate_name, chapter_list, rarity_filter=None):
    """Merge cards missing for playset completion, using standardized keys."""
    print(f"--- Merging missing playset cards: {chapter_list} "
          f"{'Rarity: ' + rarity_filter if rarity_filter else ''} ---")

    IMAGES_PER_ROW = img_per_row
    bg_color = (255, 255, 255)
    text_color = (0, 0, 0)
    all_images_per_chapter = defaultdict(list)
    total_cards_needed = 0

    # Load assets once
    font_missing_count, font_chapter_missing = None, None
    count_img_base = None
    try:
        # (Asset loading code remains the same)
        font_missing_count = ImageFont.truetype("assets/black.ttf", int(100 * SCALING))
        font_chapter_missing = ImageFont.truetype("assets/black.ttf", int(180 * SCALING))
        count_img_base = Image.open("assets/foil_card_count.png")
    except Exception as e:
        print(f"Warning: Error loading assets/fonts for missing playset: {e}. Overlays/text may be missing.")
        if not font_missing_count: font_missing_count = ImageFont.load_default()
        if not font_chapter_missing: font_chapter_missing = ImageFont.load_default()

    for chapter in chapter_list:
        chapter_cards = []
        chapter_dir = os.path.join(BASE_DIR, lang, "webp", chapter)

        if not os.path.exists(chapter_dir): continue
        if chapter not in MY_COLLECTION: continue

        for img_filename in os.listdir(chapter_dir):
            if not (img_filename.lower().endswith(".webp") or img_filename.lower().endswith(".png")):
                continue

            # --- Filtering Logic ---
            filename_rarity = get_rarity_from_filename(img_filename)
            if rarity_filter and (not filename_rarity or filename_rarity.upper() != rarity_filter.upper()):
                continue

            # *** Use the filename part directly as the key ***
            card_key = img_filename.split("_")[0]  # e.g., '004a', '083'

            # *** Lookup using this key ***
            if card_key not in MY_COLLECTION[chapter]:
                if DEBUG: print(f"Debug: Key '{card_key}' from filename '{img_filename}' not found in MY_COLLECTION[{chapter}] for missing check. Skipping.")
                continue  # Skip if card info wasn't loaded

            card_info = MY_COLLECTION[chapter][card_key]

            # Check playset count
            normal_count = int(card_info.get("normal", 0))
            foil_count = int(card_info.get("foil", 0))
            total_count = normal_count + foil_count
            if total_count >= 4: continue
            # --- End Filtering Logic ---

            missing_count = 4 - total_count
            total_cards_needed += missing_count

            img_path = os.path.join(chapter_dir, img_filename)
            try:
                img = Image.open(img_path).convert("RGBA")
            except Exception as e:
                if DEBUG: print(f"Error opening image {img_path}: {e}")
                continue

            metadata = {
                "chapter": chapter,
                "card_number": card_key,  # Store standardized key
                "filename": img_filename, "missing_count": missing_count,
                "rarity": card_info.get("rarity", ""),
            }
            chapter_cards.append((img, metadata))

        # Sort using the standardized card_number key
        chapter_cards.sort(key=lambda x: x[1]["card_number"])
        all_images_per_chapter[chapter] = chapter_cards

    # --- Image Merging Section ---
    if total_cards_needed == 0:
        print(f"No cards missing for playset found matching criteria for {generate_name}. Skipping.")
        return

    images_to_merge = []
    for chapter, images_with_metadata in all_images_per_chapter.items():
        if not images_with_metadata: continue
        # (Grid creation code remains the same)
        num_images = len(images_with_metadata);
        rows = (num_images + IMAGES_PER_ROW - 1) // IMAGES_PER_ROW;
        grid_width = (CARD_WIDTH + PADDING) * min(IMAGES_PER_ROW, num_images) - PADDING + (2 * PADDING);
        grid_height = (CARD_HEIGHT + PADDING) * rows - PADDING + (2 * PADDING);
        chapter_image_grid = Image.new('RGBA', (grid_width, grid_height), (*bg_color, 255));
        x_offset, y_offset = PADDING, PADDING  # noqa e501
        for index, (img, metadata) in enumerate(images_with_metadata):
            # (Paste image code remains the same)
            img_resized = img.resize((CARD_WIDTH, CARD_HEIGHT), resample=Image.LANCZOS);
            img_rounded = round_corners(img_resized, CORNER_RADIUS);
            chapter_image_grid.paste(img_rounded, (x_offset, y_offset), img_rounded)  # noqa e501
            # (Draw missing count overlay code remains the same)
            missing_count = metadata["missing_count"]
            if count_img_base and font_missing_count:
                c_img = count_img_base.copy();
                c_img = c_img.resize((int(c_img.width * 1.5 * SCALING), int(c_img.height * 1.5 * SCALING)), resample=Image.LANCZOS);
                draw_c = ImageDraw.Draw(c_img);
                text_c = str(missing_count);
                bbox_c = draw_c.textbbox((0, 0), text_c, font=font_missing_count);
                tx_c = (c_img.width - (bbox_c[2] - bbox_c[0])) // 2;
                ty_c = (c_img.height - (bbox_c[3] - bbox_c[1])) // 2 - int(10 * SCALING);
                draw_c.text((tx_c, ty_c), text_c, font=font_missing_count, fill=(255, 255, 255));
                chapter_image_grid.paste(c_img, (x_offset + CARD_WIDTH - c_img.width - 5, y_offset + 5), c_img)  # noqa e501
            # (Update offset code remains the same)
            x_offset += CARD_WIDTH + PADDING;
            if (index + 1) % IMAGES_PER_ROW == 0: x_offset = PADDING; y_offset += CARD_HEIGHT + PADDING  # noqa e501

        # Add chapter name header
        if font_chapter_missing:
            # (Draw chapter header code remains the same)
            chapter_name_image = Image.new('RGBA', (grid_width, int(210 * SCALING)), (*bg_color, 255));
            draw_title = ImageDraw.Draw(chapter_name_image);
            title_text = f"{CHAPTER_NAMES.get(chapter, chapter)}:";
            draw_title.text((PADDING, 5), title_text, font=font_chapter_missing, fill=text_color);
            images_to_merge.append(chapter_name_image)  # noqa e501

        images_to_merge.append(chapter_image_grid)

    # Merge and Save (code remains the same)
    if not images_to_merge: print(f"No images generated for {generate_name}"); return
    final_image = merge_images(images_to_merge, True, PADDING, (*bg_color, 255), align="left")
    print(f"Total individual cards needed for playset completion (shown): {total_cards_needed}")
    output_dir = os.path.join(BASE_DIR, "output", "missing_playset", lang);
    os.makedirs(os.path.join(output_dir, "webp"), exist_ok=True);
    os.makedirs(os.path.join(output_dir, "png"), exist_ok=True)  # noqa e501
    png_path = os.path.join(output_dir, "png", f"{generate_name}.png");
    webp_path = os.path.join(output_dir, "webp", f"{generate_name}.webp")  # noqa e501
    try:
        final_image.save(png_path, "PNG");
        print(f"Image saved: {png_path}")
        try:
            final_image.save(webp_path, "WebP", quality=90)
        except Exception as e:
            print(f"Failed to save WebP image {webp_path}: {e}")
    except Exception as e:
        print(f"Failed to save PNG image {png_path}: {e}")


# --- Main Execution ---
if __name__ == "__main__":
    MY_COLLECTION = load_my_card_collection_from_chapters()
    if not MY_COLLECTION:
        print("Exiting due to failure loading card collection.")
        exit()
    print("Card collection loaded.")

    calculate_multicolor_assignments(MY_COLLECTION)
    print("Multicolor assignments calculated.")

    for lang in LANGUAGES:
        print(f"\n--- Processing Language: {lang.upper()} ---")

        # --- Generate Images By Color - Per Chapter ---
        print("\nGenerating images by color (per chapter)...")
        process_chapters = ["007"]  # + SPECIAL_CHAPTERS # Choose which sets to process
        for chapter in process_chapters:
            if chapter not in MY_COLLECTION:
                if DEBUG: print(f"Skipping image generation for chapter {chapter} (not in collection).")
                continue
            print(f"  Processing Chapter: {chapter}")
            for ct in CARD_TYPES:
                merge_cards_for_color(
                    lang=lang,
                    merge_color=ct.name,
                    color_rgb=ct.color,
                    img_per_row=9,  # Adjust as needed
                    # Use chapter name in the output filename
                    generate_name=f"{chapter}_{ct.name}",
                    mark_completed=True,
                    # Pass only the current chapter in the list
                    chapter_list=[chapter]
                )

        # --- Generate Images for Missing Playsets ---
        print("\nGenerating images for missing playsets...")
        for rarity_ct in CARD_RARITY:
            merge_cards_missing_for_playset(
                lang=lang, img_per_row=9,
                generate_name=f"missing_playsets_{rarity_ct.name}",
                chapter_list=CHAPTERS + SPECIAL_CHAPTERS,
                rarity_filter=rarity_ct.name
            )

        # --- Optional: Generate image of ALL cards (combined chapters) ---
        # print("\nGenerating image of all cards...")
        # merge_cards(
        #     lang=lang, color_rgb=(50, 50, 50), img_per_row=10,
        #     generate_name="all_cards_collection", mark_completed=True,
        #     chapter_list=CHAPTERS + SPECIAL_CHAPTERS
        # )

    print("\n--- Processing Complete ---")
