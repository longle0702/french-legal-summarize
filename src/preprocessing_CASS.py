import argparse
import hashlib
import logging
import os
import re
import sys
import time
from xml.etree import ElementTree as ET
import spacy

###############################################################################

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

###############################################################################
# ---------- argument parsing --------------------------------------------------


def init_parser():
    parser = argparse.ArgumentParser(
        description="Preprocess Cour de Cassation XML files into .story files"
    )

    parser.add_argument(
        "--data_dir",
        help="Folder containing XML files",
        required=True
    )

    parser.add_argument(
        "--clean_dir",
        help="Output folder for .story files",
        default="cleaned_files"
    )

    return vars(parser.parse_args())


###############################################################################
# ---------- XML extraction ----------------------------------------------------


def remove_html_tags(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    return text


def get_text_summary(filepath: str):

    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except Exception as e:
        LOGGER.warning("Cannot parse %s: %s", filepath, e)
        return None, None

    contenu = root.find(".//CONTENU")
    ana = root.findall(".//ANA")

    if contenu is None or not ana:
        return None, None

    text = ET.tostring(contenu, encoding="unicode", method="text")
    summary = "\n".join(ET.tostring(a, encoding="unicode", method="text") for a in ana)

    text = remove_html_tags(text)
    summary = remove_html_tags(summary)

    text = text.strip()
    summary = summary.strip()

    if not text or not summary:
        return None, None

    return text, summary


###############################################################################
# ---------- cleaning helpers --------------------------------------------------


def clean_ocr_noise(text: str):

    text = re.sub(r"[\x00-\x1f\x7f]", "", text)

    text = re.sub(r"\bnull\b", "", text, flags=re.IGNORECASE)

    return text


def normalize_hyphens(text: str):

    text = re.sub(r"\b(\w+)\s*-\s*(\w+)\b", r"\1-\2", text)

    return text


def fix_numbers(text: str):

    text = re.sub(r"(?<=\d) , (?=\d)", ",", text)
    text = re.sub(r"(?<=\d) \. (?=\d)", ".", text)

    text = re.sub(r"(\d)\.\n(\d)", r"\1.\2", text)

    return text


def fix_punctuation_spacing(text: str):

    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([,.;:!?])(?=[^\s])", r"\1 ", text)

    return text


def clean_whitespace(text: str):

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    return "\n".join(lines)


###############################################################################
# ---------- tokenization ------------------------------------------------------


def tokenize(text: str, nlp):

    doc = nlp(text)

    return "".join(token.text_with_ws for token in doc)


###############################################################################
# ---------- sentence segmentation ---------------------------------------------


def split_sentences(text: str, nlp):

    doc = nlp(text)

    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    return "\n".join(sentences)


###############################################################################
# ---------- story assembly ----------------------------------------------------


def build_story(text: str, summary: str, nlp):

    text = clean_ocr_noise(text)
    summary = clean_ocr_noise(summary)

    text = normalize_hyphens(text)
    summary = normalize_hyphens(summary)

    text = fix_numbers(text)
    summary = fix_numbers(summary)

    text = fix_punctuation_spacing(text)
    summary = fix_punctuation_spacing(summary)

    text = tokenize(text, nlp)
    summary = tokenize(summary, nlp)

    text = split_sentences(text, nlp)
    summary = split_sentences(summary, nlp)

    text = clean_whitespace(text)
    summary = clean_whitespace(summary)

    story = text + "\n@highlight\n" + summary

    return story


###############################################################################
# ---------- writing -----------------------------------------------------------


def write_story(story: str, output_path: str):

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(story)


###############################################################################
# ---------- hashing helper ----------------------------------------------------


def hashhex(string):

    h = hashlib.sha1()
    h.update(string.encode("utf-8"))
    return h.hexdigest()


###############################################################################
# ---------- main pipeline -----------------------------------------------------


def main():

    args = init_parser()

    data_dir = args["data_dir"]
    clean_dir = args["clean_dir"]

    os.makedirs(clean_dir, exist_ok=True)

    LOGGER.info("Loading spaCy tokenizer")

    nlp = spacy.blank("fr")
    nlp.add_pipe("sentencizer")

    start = time.time()

    processed = 0
    skipped = 0

    for root, _, files in os.walk(data_dir):

        for file in files:

            if not file.endswith(".xml"):
                continue

            path = os.path.join(root, file)

            text, summary = get_text_summary(path)

            if not text or not summary:
                skipped += 1
                continue

            try:
                story = build_story(text, summary, nlp)
            except Exception as e:
                LOGGER.warning("Processing error %s: %s", file, e)
                skipped += 1
                continue

            output_name = os.path.splitext(file)[0] + ".story"

            output_path = os.path.join(clean_dir, output_name)

            try:
                write_story(story, output_path)
            except Exception as e:
                LOGGER.warning("Write error %s: %s", output_name, e)
                skipped += 1
                continue

            processed += 1

            if processed % 10000 == 0:

                elapsed = time.time() - start
                speed = processed / elapsed

                LOGGER.info(
                    "Processed %d files | %.1f files/sec",
                    processed,
                    speed
                )

    LOGGER.info("Finished")
    LOGGER.info("Processed: %d", processed)
    LOGGER.info("Skipped: %d", skipped)

if __name__ == "__main__":
    sys.exit(main())