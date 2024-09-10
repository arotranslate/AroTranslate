import json
import logging
import re
import string

import pandas as pd
from spacy.lang.ro import Romanian

logger = logging.getLogger(__name__)

VALID_LANGUAGES = {
    "Romanian": "ron",
    "Română": "ron",
    "Romãnã": "ron",
    "Aromanian": "rup",
    "Aromână": "rup",
    "Armãnã": "rup",
    "English": "eng",
    "Engleză": "eng",
    "Inglezã": "eng",
}

FUH = {}
FAH = {}

with open("resources/fuh.json", "r") as json_file:
    FUH = json.load(json_file)
with open("resources/fah.json", "r") as json_file:
    FAH = json.load(json_file)
df = pd.read_csv("resources/cunia_diaro.csv")
CUNIA2DIARO_WD_MAP = dict(zip(df.cunia, df.diaro))
del df


# blank romanian processor
NLP = Romanian()
TOKENIZER = NLP.tokenizer
# NLP.add_pipe("sentencizer")


CUNIA2DIARO = {
    "Sh": "Ș",
    "SH": "Ș",
    "sh": "ș",
    "Ts": "Ț",
    "TS": "Ț",
    "ts": "ț",
    "LJ": "Ľ",
    "Lj": "Ľ",
    "lj": "ľ",
    "NJ": "Ń",
    "Nj": "Ń",
    "nj": "ń",
    "DZ": "D̦",
    "Dz": "D̦",
    "dz": "d̦",
}


def get_language_code(language):
    return VALID_LANGUAGES.get(language.strip())


def convert_central_vowel_cunia(text):
    # various letters (some mis-used) for mid-central
    text = text.replace("ă", "ã")
    text = text.replace("Ă", "Ã")
    text = text.replace("ӑ", "ã")
    text = text.replace("Ӑ", "ã")
    text = text.replace("Ǎ", "ã")
    text = text.replace("ǎ", "ã")
    # close central vowel
    text = text.replace("Â", "Ã")
    text = text.replace("â", "ã")
    text = text.replace("Î", "Ã")
    text = text.replace("î", "ã")
    # remove accent from front vowel
    text = text.replace("á", "a")
    text = text.replace("à", "a")
    text = text.replace("Á", "A")
    text = text.replace("À", "A")
    return text


def convert_consonants_cunia(text):
    text = text.replace("ş", "sh")
    text = text.replace("ș", "sh")
    text = text.replace("ţ", "ts")
    text = text.replace("ț", "ts")
    text = text.replace("Ş", "Sh")
    text = text.replace("Ș", "Sh")
    text = text.replace("Ţ", "Ts")
    text = text.replace("Ț", "Ts")

    text = text.replace("ľ", "lj")
    text = text.replace("Ľ", "Lj")
    text = text.replace("l'", "lj")
    text = text.replace("l’", "lj")
    text = text.replace("L'", "Lj")
    text = text.replace("L’", "Lj")

    text = text.replace("ḑ", "dz")
    text = text.replace("Ḑ", "dz")
    text = text.replace("ḍ", "dz")
    text = text.replace("Ḍ", "Dz")
    text = text.replace("d̦", "dz")
    text = text.replace("D̦", "Dz")

    text = text.replace("ń", "nj")
    text = text.replace("Ń", "Nj")
    text = text.replace("ñ", "nj")
    text = text.replace("Ñ", "Nj")
    text = text.replace("n’", "nj")
    text = text.replace("n’", "nj")
    text = text.replace("N'", "Nj")
    text = text.replace("N'", "Nj")
    return text


def convert_other_chars(text):
    # greek letters and other accents
    text = text.replace("ŭ", "u")
    text = text.replace("ς", "c")
    text = text.replace("é", "e")
    text = text.replace("í", "i")
    text = text.replace("ū", "u")
    text = text.replace("ì", "i")
    text = text.replace("ā", "a")
    text = text.replace("ĭ", "i")
    text = text.replace("γ", "y")
    text = text.replace("Γ", "Y")
    text = text.replace("ï", "i")
    text = text.replace("ó", "o")
    text = text.replace("θ", "th")
    text = text.replace("Θ", "Th")
    text = text.replace("δ", "dh")
    text = text.replace("Δ", "Dh")
    return text


def convert_to_cunia(text):
    text = convert_consonants_cunia(text)
    text = convert_central_vowel_cunia(text)
    text = convert_other_chars(text)
    return text


def clean_text(text, lang):
    # consecutive spaces
    text = re.sub(r"\s+", " ", text).strip()
    # old romanian î in the middle of the word
    text = re.sub(r"(?<=\w)î(?=\w)", "â", text)

    # specific to this book !
    # text = text.replace(',,', '"')
    if lang == "ron":
        text = text.replace("Ş", "Ș")
        text = text.replace("ş", "ș")
        text = text.replace("Ţ", "Ț")
        text = text.replace("ţ", "ț")
    else:
        text = convert_to_cunia(text)

    # for both languages:
    text = text.replace("—", "-")
    text = text.replace("…", "...")
    text = text.replace("*", "")
    text = text.replace("<", "")
    text = text.replace(">", "")

    text = text.replace("„", '"')
    text = text.replace("”", '"')
    text = text.replace("“", '"')
    text = text.replace("”", '"')

    text = text.replace("\xa0", "")
    text = text.replace("\ufeff", "")
    return text


def post_process(text):
    # weird bug probably because i handled badly the '-' character
    text = text.replace("<unk>", "-")
    return text


def tokenize(text):
    # return text.split(" ")
    return [token.text for token in TOKENIZER(text)]


def get_mask(s, index):
    """Get a 4 character padded mask around the index
    """
    ans = ""
    if index >= 2:
        ans = s[index - 2: index]
    elif index >= 1:
        ans = " " + s[index - 1: index]
    else:
        ans = "  "
    if index + 2 < len(s):
        ans += s[index + 1: index + 3]
    elif index + 1 < len(s):
        ans += s[index + 1: index + 2] + " "
    else:
        ans += "  "
    assert len(ans) == 4
    return ans


def resolve_with_ngrams(word):
    """DIARO standard to Cunia at the word level
    using pre-computed n-grams ã --> â or ă
    """
    lower_chars = word.lower()  # .replace("î", "â")
    lower_chars_transduced = ""
    for i, ch in enumerate(lower_chars):
        if ch == "ã" and i == 0:
            lower_chars_transduced += "î"
            continue
        elif ch == "ã":
            msk = get_mask(lower_chars, i)
            cnt_ah = FAH.get(msk, 0)
            cnt_uh = FUH.get(msk, 0)
            if cnt_ah > cnt_uh:
                lower_chars_transduced += "â"
            else:
                lower_chars_transduced += "ă"
        else:
            lower_chars_transduced += ch
    case_transduced = ""
    for i, ch in enumerate(lower_chars):
        if i < len(lower_chars_transduced) and lower_chars[i] != word[i]:
            case_transduced += lower_chars_transduced[i].upper()
        else:
            case_transduced += lower_chars_transduced[i]
    return case_transduced


def convert_consonants_diaro(text):
    """Convert only the consontants to Diaro"""
    for from_, to_ in CUNIA2DIARO.items():
        text = text.replace(from_, to_)
    return text


def normalize_diaro(text):
    """When a non-standard text comes in, we
    - convert consontants to Cunia
    - standardize accents
    - convert back the consontants to DIARO
    """
    text = convert_consonants_cunia(text)
    text = convert_other_chars(text)
    text = convert_consonants_diaro(text)
    return text


def diaro_to_cunia(text):
    """DIARO standard to Cunia
    """
    text = normalize_diaro(text)
    return convert_to_cunia(text)


def resolve_with_dictionary(word):
    """DIARO standard to Cunia at the word level
    for words that are in the dictionary
    """
    word = diaro_to_cunia(word.lower())
    cache = CUNIA2DIARO_WD_MAP.get(word, "")
    return cache


def smart_join_words(words):
    """Join words with spaces, but handle the case
    when there words end or begin with punctuation
    """
    arr = []
    for i, word in enumerate(words):
        if i == 0:
            arr.append(word)
        elif word[0] in string.punctuation and word[0] not in ['(', '-']:
            arr[-1] += word
        elif len(arr[-1]) > 0 and arr[-1][-1] in ['(', '-']:
            arr[-1] += word
        else:
            arr.append(word)
    return " ".join(arr)


def cunia_to_diaro(text):
    # ensure cunia is enforced
    text = convert_to_cunia(text)
    # tokens can be found in the dictionary
    # TODO: use sentencepiece
    words = tokenize(text)
    arr = []
    for word in words:
        resolved = word
        if "ã" in word:
            resolved = resolve_with_dictionary(word)
            if not resolved:
                resolved = resolve_with_ngrams(word)
        arr.append(convert_consonants_diaro(resolved))
    return smart_join_words(arr)
