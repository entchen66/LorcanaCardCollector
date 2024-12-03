import os
from io import BytesIO

import requests
from PIL import Image

EXTRACTED_CARDS = {}

LOGIN_URL = "https://sso.ravensburger.de/token"
CATALOG_URL = "https://api.lorcana.ravensburger.com/v2/catalog/{lang}"

DEBUG = True
DEBUG_CARDS = [("005", "123")]

CARD_RARITY = {
    "COMMON": "CC",  # Common
    "UNCOMMON": "UC",  # Uncommon
    "RARE": "RR",  # Rare
    "SUPER": "SR",  # Super Rare (39, 40, 40)
    "LEGENDARY": "LL",  # Legendary
    "ENCHANTED": "EE",  # Enchanted
    "SPECIAL": "SP",  # Promo and others
}

LANGUAGES = [
    "de",
    "en",
    "fr",
    "it",
    #"cn",
    #"jp",
]


class Card:
    def __init__(self, card_data, card_type, card_set, special_rarities):
        # Common fields
        self.name = card_data.get('name', 'Unknown')
        self.rarity = card_data.get('rarity', 'Unknown')
        self.special_rarity_id = card_data.get('special_rarity_id', None)
        self.special_rarity = special_rarities.get(card_data.get('special_rarity_id', None), None)
        self.ink_cost = card_data.get('ink_cost', 0)
        self.author = card_data.get('author', 'Unknown')
        self.deck_building_id = card_data.get('deck_building_id', None)
        self.culture_invariant_id = card_data.get('culture_invariant_id', None)
        self.sort_number = card_data.get('sort_number', None)
        self.inkable = card_data.get('ink_convertible', False)
        self.rules_text = card_data.get('rules_text', '')
        self.flavor_text = card_data.get('flavor_text', '')
        self.card_identifier = card_data.get('card_identifier', None)
        self.magic_ink_colors = card_data.get('magic_ink_colors', [])
        card_set_ids = card_data.get('card_sets', [])
        self.card_sets = [card_set.get(card_set_id, "Unknown Set") for card_set_id in card_set_ids]

        if self.card_identifier.split("/")[0].isdigit():
            self.id = self.card_identifier.split("/")[0].zfill(3)
        else:
            self.id = self.card_identifier.split("/")[0].zfill(4)
        if self.special_rarity:
            if self.special_rarity_id == 2:
                self.set_id = self.card_identifier.split(" ")[-1]
            else:
                self.set_id = self.card_identifier.split(" ")[0].split("/")[-1]
        else:
            self.set_id = self.card_identifier.split(" ")[-1].zfill(3)

        # Image URLs
        image_urls = card_data.get('image_urls', [])
        self.high_res_image = next((img['url'] for img in image_urls if img['height'] == 2048), None)
        self.foil_mask_url = card_data.get('foil_mask_url', None)

        # Subtypes and additional information
        self.subtypes = card_data.get('subtypes', [])
        self.additional_info = card_data.get('additional_info', [])

        # Type-specific fields
        self.strength = card_data.get('strength', None)
        self.willpower = card_data.get('willpower', None)
        self.quest_value = card_data.get('quest_value', None)
        self.subtitle = card_data.get('subtitle', None)
        self.move_cost = card_data.get('move_cost', None)

        # Determine card type (Character, Action, Item, Location)
        self.card_type = card_type

    def __repr__(self):
        """String representation of the card object."""
        return (f"Card(set={self.set_id}, id={self.id}, color={self.magic_ink_colors}, "
                f"name={self.name}, name_extra={self.subtitle}, rarity={self.rarity}, ink_cost={self.ink_cost}, "
                f"card_type={self.card_type}, high_res_image={self.high_res_image}, "
                f"foil_mask_url={self.foil_mask_url}, set={self.card_sets})")


def map_card_sets_to_dict(card_sets):
    return {card_set['id']: card_set['name'] for card_set in card_sets}


def do_sso_ravensburger(access_token):
    # Function to get the token from Ravensburger's SSO
    payload = {
        'grant_type': 'client_credentials'
    }
    headers = {
        'Authorization': access_token,
        'Content-Type': 'application/x-www-form-urlencoded'  # Use JSON content type
    }

    # Sending POST request to get the token
    response = requests.post(LOGIN_URL, headers=headers, data=payload)

    # Check if the response is successful
    if response.status_code == 200:
        # Return the token if successful
        if DEBUG:
            print(response.text)
        return response.json().get('access_token')
    else:
        # Raise an exception if the request failed
        raise Exception(f"Failed to retrieve token: {response.status_code}, {response.text}")


def get_catalog():
    # Function to get the catalog using the token
    token = do_sso_ravensburger('Basic bG9yY2FuYS1hcGktcmVhZDpFdkJrMzJkQWtkMzludWt5QVNIMHc2X2FJcVZEcHpJenVrS0lxcDlBNXRlb2c5R3JkQ1JHMUFBaDVSendMdERkYlRpc2k3THJYWDl2Y0FkSTI4S096dw==')

    if DEBUG:
        print(token)

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response_by_language = {}

    for lang in LANGUAGES:
        # Sending GET request to fetch the catalog
        response = requests.get(CATALOG_URL.replace("{lang}", lang), headers=headers)

        # Check if the response is successful
        if response.status_code == 200:
            # Return the catalog data
            response_by_language[lang] = response.json()
        else:
            # Raise an exception if the request failed
            raise Exception(f"Failed to retrieve catalog: {response.status_code}, {response.text}")

    return response_by_language


def fill_card_catalog():
    card_catalog = get_catalog()

    for lang in LANGUAGES:
        # determinate card types
        for card_type, cards in card_catalog[lang]["cards"].items():
            for card in cards:
                card_data = Card(card, card_type, map_card_sets_to_dict(card_catalog[lang]["card_sets"]), map_card_sets_to_dict(card_catalog[lang]["special_rarities"]))
                print(card_data)
                card_image = download_image(card_data.high_res_image)
                save_image(os.path.join("cards", lang, "webp", card_data.set_id), f"{card_data.id}_{'_'.join(card_data.magic_ink_colors)}_{CARD_RARITY[card_data.rarity]}_{card_data.card_type}", card_image, "webp")


def download_image(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        # Raise an exception if the request failed
        raise Exception(f"Failed to retrieve image: {response.status_code}, {response.text}")


def save_image(directory, image_name, image_content, format):
    # Erstelle das Verzeichnis, wenn es noch nicht existiert
    if not os.path.exists(directory):
        os.makedirs(directory)

    path = os.path.join(directory, image_name)

    if format == "webp":
        with open(path + ".webp", 'wb') as file:
            file.write(image_content)
    elif format == "png":
        image = Image.open(BytesIO(image_content))
        image.save(path + ".png", "PNG")


def main():
    fill_card_catalog()


if __name__ == "__main__":
    main()
    # download_image("en", "005", "034")
    print(EXTRACTED_CARDS)
