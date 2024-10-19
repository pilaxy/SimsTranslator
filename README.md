# SimsTranslator

Translates Sims XML files using [PyDeepLX](https://github.com/OwO-Network/PyDeepLX) for API-free DeepL AI translations. It uses [FreeProxy](https://github.com/jundymek/free-proxy) for managing 429 blocking issues. The tool also supports resuming from closed sessions, handling large files efficiently, and includes both CLI and GUI options.

## Features

- **DeepL Translation without API**: Utilizes [PyDeepLX](https://github.com/OwO-Network/PyDeepLX) and [FreeProxy](https://github.com/jundymek/free-proxy) for unlimited api-free translations.
- **Batch Processing**: Splits large files into manageable batches to avoid hitting deepl limits and it provides resumable process.
- **Session Resumption**: Can resume procession from a saved state if process is interrupted or closed, it will continue from the last completed batch.
- **Proxy Management**: Automatically switches between multiple proxies to handle rate limiting and broken proxies.
- **Simle GUI**: Optional GUI built with `customtkinter`.

## Installation

### Requirements

Ensure you have Python installed (Python 3.9+ recommended).

Install the necessary dependencies using pip:

```
pip install -r requirements.txt
```

### Dependencies

- `customtkinter`: A modern Tkinter-based widget set.
- `PyDeepLX`: An unofficial Python client for the DeepL API.
- `free-proxy`: Library to fetch free public HTTP(S) proxies.

## Usage

### Command Line Interface (CLI)

#### Examples

Run the translator from the command line using the following syntax:

```
python main.py --source_lang SOURCE_LANG --target_lang TARGET_LANG --input INPUT_FILE --output OUTPUT_FILE [--max_char MAX_CHAR]
```

To translate an XML file named `example.xml` from English (`EN`) to Turkish (`TR`) with 5000 character limit per batch:

```
python main.py --source_lang EN --target_lang TR --input example.xml --output example_tr.xml
```

To translate an XML file named `example.xml` from English (`EN`) to German (`DE`) with a maximum of 1000 characters per batch:

```
python main.py --source_lang EN --target_lang DE --input example.xml --output example_de.xml --max_char 1000
```

### Graphical User Interface (GUI)

The customtkinter GUI will provide simple interface for selecting multiple xml files with to translate:

```
python gui.py
```

### Creating an Executable with PyInstaller

To create a standalone executable for the gui.py script, follow these steps:

1. Install PyInstaller

```
pip install pyinstaller
```

2. Navigate to the directory and Generate the Execuble

For Unix-like systems (Linux, macOS):

```
pyinstaller --name="Auto Sims Translator" --add-data="tkinter.ico;." --onefile --windowed gui.py
```

For Windows:

```
pyinstaller --name="Auto Sims Translator" --add-data=tkinter.ico;. --onefile --windowed gui.py
```

