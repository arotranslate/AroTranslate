import logging
import time
import razdel
import ctranslate2
from transformers import AutoTokenizer
from config import Config
from utils.text_processing import (clean_text,
                                   cunia_to_diaro,
                                   diaro_to_cunia,)

logger = logging.getLogger(__name__)

model = ctranslate2.Translator(Config.MODEL_LOAD_NAME)
tokenizers = {
    "ron": AutoTokenizer.from_pretrained(Config.MODEL_LOAD_NAME, src_lang="ron_Latn"),
    "rup": AutoTokenizer.from_pretrained(Config.MODEL_LOAD_NAME, src_lang="rup_Latn"),
    "eng": AutoTokenizer.from_pretrained(Config.MODEL_LOAD_NAME, src_lang="eng_Latn"),
}


def convert_diacritics_from_orthography(orthography, text):
    if orthography == "cunia":
        return cunia_to_diaro(text)
    return diaro_to_cunia(text)


def translate_text(text, lang_from, lang_to):
    text = clean_text(text, lang_from)
    sents = [s.text for s in razdel.sentenize(text)]

    if len(tokenizers[lang_from].tokenize(text)) > Config.MAX_INPUT_TOKENS:
        raise ValueError("Text is too long (Tokenizer limit exceeded).")

    sents_batches = [sents[i: i + Config.BATCH_SIZE] for i in range(0, len(sents), Config.BATCH_SIZE)]

    start_time = time.time()
    Y = []

    for batch in sents_batches:
        X = tokenizers[lang_from](batch, truncation=True)
        source = [tokenizers[lang_from].convert_ids_to_tokens(p) for p in X["input_ids"]]
        target_prefix = [lang_to + "_Latn"]
        results = model.translate_batch(
            source,
            max_decoding_length=Config.MAX_OUTPUT_TOKENS,
            target_prefix=[target_prefix for _ in range(len(source))],
        )

        Y.extend([
            tokenizers[lang_from].decode(
                tokenizers[lang_from].convert_tokens_to_ids(
                    results[_].hypotheses[0][1:]
                )
            )
            for _ in range(len(results))
        ])

    total_time = time.time() - start_time
    return " ".join(Y), total_time
