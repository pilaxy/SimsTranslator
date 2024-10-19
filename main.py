import argparse
from translator import XmlTranslator

def parse_arguments():
    parser = argparse.ArgumentParser(description="Translate XML files using the DeepL API.")
    parser.add_argument('-m', '--max_char', type=int, default=5000, help="Character limit per batch (default: 5000)")
    parser.add_argument('-s', '--source_lang', required=True, help="Source language (e.g., EN)")
    parser.add_argument('-t', '--target_lang', required=True, help="Target language (e.g., TR)")
    parser.add_argument('-i', '--input', required=True, help="Input XML file path")
    parser.add_argument('-o', '--output', required=True, help="Output XML file path")

    args = parser.parse_args()
    return args

def main():
    args = parse_arguments()

    translator = XmlTranslator(args.source_lang, args.target_lang, args.max_char)
    translator.parse_and_translate_xml(args.input, args.output)

if __name__ == "__main__":
    main()

