# LorcanaCardCollector

LorcanaCardCollector is a Python tool that helps you visualize your Disney Lorcana card collection. It fetches card data and images from the official Ravensburger Lorcana API and generates customized images showcasing your collection based on an export from [dreamborn.ink](https://dreamborn.ink).

## Features

- Fetches the latest card data and high-resolution images from the official Lorcana API.
- Processes your collection data exported from dreamborn.ink.
- Generates composite images of your collection, organized by card attributes such as color, rarity, and set.
- Highlights missing cards and indicates the quantity of each card you own.
- Supports multiple languages (English, German, French, Italian).

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
  - [1. Export Your Collection](#1-export-your-collection)
  - [2. Run the Script](#2-run-the-script)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/entchen66/LorcanaCardCollector.git
   cd LorcanaCardCollector
   ```

2. **Create a virtual environment (optional but recommended):**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use 'venv\Scripts\activate'
   ```

3. **Install the required Python packages:**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Export Your Collection

- Visit [dreamborn.ink](https://dreamborn.ink) and log in to your account.
- Navigate to your collection and export it as a CSV file.
- Save the exported file as `export.csv` in the project root directory.

### 2. Run the Script

Execute the main script to start processing:

```bash
python main.py
```

**What the script does:**

- Fetches card data and images from the Lorcana API for each supported language.
- Downloads and saves high-resolution images of the cards to `cards/{language}/webp/{set_id}/`.
- Reads your collection data from `export.csv`.
- Generates composite images of your collection, highlighting collected and missing cards.
- Saves the final images in `cards/output/all_by_color/{language}/`.

## Configuration

You can adjust the script's behavior by modifying the following variables in `main.py`:

- `LANGUAGES`: A list of language codes to fetch and process (`"en"`, `"de"`, `"fr"`, `"it"`).
- `CHAPTERS`: A list of set identifiers to include.
- `SCALING`: Adjusts the size of the output images.
- `IMAGES_PER_ROW`: Number of card images per row in the composite image.
- `DEBUG`: Set to `True` to enable debug output.

**Example:**

```python
LANGUAGES = ["en", "de"]
CHAPTERS = ["001", "002", "P1"]
SCALING = 0.8
IMAGES_PER_ROW = 6
DEBUG = False
```

## Dependencies

- Python 3.6 or higher
- [requests](https://pypi.org/project/requests/)
- [Pillow](https://pypi.org/project/Pillow/)
- [numpy](https://pypi.org/project/numpy/)

Install dependencies using:

```bash
pip install -r requirements.txt
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit your changes with clear messages.
4. Submit a pull request describing your changes.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgements

- [dreamborn.ink](https://dreamborn.ink) for providing the platform to manage Lorcana collections.
- Ravensburger for the official Lorcana API.

**Disclaimer:** This project is not affiliated with Disney Lorcana or Ravensburger.

# End of README
