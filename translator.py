import time
import re
import xml.etree.ElementTree as ET
from PyDeepLX import PyDeepLX as PDLX
from fp.fp import FreeProxy
from random import randint
import hashlib
import os

class XmlTranslator:
    LOCAL_IP_TIME = 720  # Time interval to use local IP

    def __init__(self, source_language, target_language, char_limit_per_batch):
        self.source_language = source_language
        self.target_language = target_language
        self.char_limit_per_batch = char_limit_per_batch
        self.proxies = FreeProxy(rand=True, timeout=1).get()
        self.local_iptimer = time.time()

    def translate_text(self, text):
        """Translate text using the DeepL API with retries."""
        RANDOM_WAIT = randint(5, 10)
        time.sleep(RANDOM_WAIT)

        while True:
            try:
                result = PDLX.translate(
                    text,
                    self.source_language,
                    self.target_language,
                    proxies=self.proxies
                )
                return result
            except Exception as e:
                self.update_proxy()

    def update_proxy(self):
        """Update the proxy used for translations."""
        duration = time.time() - self.local_iptimer
        if duration > self.LOCAL_IP_TIME:
            self.proxies = None
            self.local_iptimer = time.time()
        else:
            self.proxies = FreeProxy(rand=True, timeout=1).get()
            print(f"Attempting to use a new proxy: {self.proxies}")

    @staticmethod
    def preprocess_text(text, pattern, str_id, wrapper="<>"):
        """Replace placeholders in {} with unique tokens and store replacements in a dictionary."""
        token_counter = 0
        replacement_dict = {}

        def replace_with_token(match):
            nonlocal token_counter
            token = f"{wrapper[0]}{str_id}_{token_counter}{wrapper[1]}"
            token_counter += 1
            replacement_dict[token] = match.group(0)
            return token

        preprocessed_text = re.sub(pattern, replace_with_token, text)
        return preprocessed_text, replacement_dict

    @staticmethod
    def postprocess_text(translated_text, replacement_dict):
        """Restore original placeholders from tokens in the translated text."""
        for token, original in replacement_dict.items():
            translated_text = translated_text.replace(token, original)
        return translated_text

    def extract_text_strings(self, root):
        """Extract text strings from the XML tree."""
        return [
            (element.attrib['InstanceID'], element.attrib['TextString'])
            for element in root.iter('TextStringDefinition')
        ]

    def split_into_batches(self, text_strings, char_limit_per_batch):
        """Split text strings into batches based on character limit."""
        batches = []
        current_batch = []
        current_char_count = 0

        for instance_id, text in text_strings:
            text_size = len(text)
            if current_char_count + text_size > char_limit_per_batch:
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_char_count = 0
            current_batch.append((instance_id, text))
            current_char_count += text_size

        if current_batch:
            batches.append(current_batch)

        return batches

    def translate_batch(self, batch, batch_index):
        """Translate a batch of text strings and update the XML tree."""
        batch_texts = [self.preprocess_text(text, r'\{[^\{\}]*\}', "TOKEN")[0] for _, text in batch]
        replacement_dicts = [self.preprocess_text(text, r'\{[^\{\}]*\}', "TOKEN")[1] for _, text in batch]

        try:
            merged_preprocessed_text = '\n'.join(batch_texts)
            translated_merged_text = self.translate_text(merged_preprocessed_text)
            translated_texts = translated_merged_text.split('\n')

            for i, instance_id in enumerate([elem[0] for elem in batch]):
                postprocessed_text = self.postprocess_text(translated_texts[i], replacement_dicts[i])
                for elem in self.root.iter('TextStringDefinition'):
                    if elem.attrib['InstanceID'] == instance_id:
                        elem.set('TextString', postprocessed_text)
                        break
            print(f"Batch {batch_index + 1}: Translated {sum(len(t) for t in batch_texts)} characters")
            return True
        except Exception as e:
            print(f"Failed to translate batch {batch_index}: {e}")
            return False

    def load_state(self, input_file, output_file, process_file):
        """Checks if we can resume from a previous session."""
        batch = 0
        if os.path.exists(output_file) and os.path.exists(process_file):
            with open(process_file, 'r') as f:
                lines = f.readlines()
                stored_input_file = lines[0].split(": ", 1)[1].strip()
                stored_input_hash = lines[1].split(": ", 1)[1].strip()
                stored_output_file = lines[2].split(": ", 1)[1].strip()
                stored_output_hash = lines[3].split(": ", 1)[1].strip()
                last_batch = int(lines[4].split(": ", 1)[1].strip())

            if (stored_input_file == input_file and
                stored_input_hash == self.calculate_file_hash(input_file) and
                stored_output_file == output_file and
                stored_output_hash == self.calculate_file_hash(output_file)):
                batch = last_batch + 1
                print(f"\nResuming from batch {batch + 1}")
            else:
                print("Cannot resume: file hashes do not match. Starting from the beginning.")
                if os.path.exists(output_file):
                    os.remove(output_file)
        return batch


    def save_xml_output(self, output_file, batch_index, total_batches):
        """Convert the XML tree back to a string and save to a file."""
        if batch_index == 0:
            # For the first batch, write the header and opening tags
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write('<?xml version="1.0" encoding="utf-8"?>\n')
                file.write('<StblData>\n')
                file.write('  <TextStringDefinitions>\n')

        # Write the batch content
        with open(output_file, 'a', encoding='utf-8') as file:
            for elem in self.root.iter('TextStringDefinition'):
                xml_string = ET.tostring(elem, encoding='unicode')
                xml_string = self.postprocess_text(xml_string, self.xml_entity_dict)
                file.write('    ' + xml_string + '\n')

        if batch_index == total_batches - 1:
            # For the last batch, write the closing tags
            with open(output_file, 'a', encoding='utf-8') as file:
                file.write('  </TextStringDefinitions>\n')
                file.write('</StblData>\n')

        print(f"Batch {batch_index + 1} appended to {output_file}")

    @staticmethod
    def calculate_file_hash(file_path):
        """Calculate the SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def update_process_file(self, process_file, input_file, output_file, batch_number):
        """Update the process file with the current state."""
        input_hash = self.calculate_file_hash(input_file)
        output_hash = self.calculate_file_hash(output_file)

        with open(process_file, 'w') as f:
            f.write(f"Input File: {input_file}\n")
            f.write(f"Input Hash: {input_hash}\n")
            f.write(f"Output File: {output_file}\n")
            f.write(f"Output Hash: {output_hash}\n")
            f.write(f"Last Batch: {batch_number}\n")

    def parse_and_translate_xml(self, input_file, output_file):
        """Parse the XML file, translate the text strings, and save the results."""
        process_file = f"{output_file}.prc"
        xml_entity_pattern = r'&(?:#[0-9]+|#x[0-9a-fA-F]+);'

        print("\nStarting translation process:")
        print(f"    Input file: {input_file}")
        print(f"    Output file: {output_file}")
        print(f"    Source language: {self.source_language}")
        print(f"    Target language: {self.target_language}")
        print(f"    Characters per batch: {self.char_limit_per_batch}")
        start_batch = self.load_state(input_file, output_file, process_file)

        # Read the file content
        with open(input_file, 'r', encoding='utf-8') as file:
            content = file.read()

        # Preprocess XML entities
        content, self.xml_entity_dict = self.preprocess_text(content, xml_entity_pattern, "XML", "__")

        # Parse the preprocessed XML content
        full_tree = ET.fromstring(content)

        # Extract text strings
        text_strings = self.extract_text_strings(full_tree)
        total_characters = sum(len(text) for _, text in text_strings)
        processed_characters = 0

        # Split text strings into batches
        batches = self.split_into_batches(text_strings, self.char_limit_per_batch)
        total_batches = len(batches)

        print("\nTranslation overview:")
        print(f"    Total text strings to translate: {len(text_strings)}")
        print(f"    Total characters to translate: {total_characters}")
        print(f"    Number of batches: {total_batches}")
        print(f"    Start batch: {start_batch + 1}")
        print("\nBeginning translation process...\n")

        # Translate each batch
        for i, batch in enumerate(batches[start_batch:], start=start_batch):
            # Create a new root for each batch
            self.root = ET.Element('StblData')
            text_string_defs = ET.SubElement(self.root, 'TextStringDefinitions')
            for instance_id, text in batch:
                elem = ET.SubElement(text_string_defs, 'TextStringDefinition')
                elem.set('InstanceID', instance_id)
                elem.set('TextString', text)

            success = self.translate_batch(batch, i)
            if success:
                processed_characters += sum(len(t) for _, t in batch)
                percent_complete = (processed_characters / total_characters) * 100
                print(f"Progress: {percent_complete:.2f}% | Remaining Characters: {total_characters - processed_characters}")

                # Save the current state after each successful batch
                self.save_xml_output(output_file, i, total_batches)
                self.update_process_file(process_file, input_file, output_file, i)

        # Remove the process file when done
        if os.path.exists(process_file):
            os.remove(process_file)
        print("Translation completed successfully.")
