# fmt: off

LANGUAGES = {
    "en": {
        "fi": "Finnish",
        "en": "English",
        "de": "German",
        "fr": "French",
    },
    "fi": {
        "fi": "suomi",
        "en": "englanti",
        "de": "saksa",
        "fr": "ranska",
    },
    "de": {
        "fi": "Finnisch",
        "en": "Englisch",
        "de": "Deutsch",
        "fr": "Französisch",
    }
}


CONJUNCTIONS = {
    "en": {
        "default_combiner": "and",
        "inverse_combiner": "but",
    },
    "fi": {
        "default_combiner": "ja",
        "inverse_combiner": "mutta",
    },
    "de": {
        "default_combiner": "und",
        "inverse_combiner": "aber",
    }
}


def get_error_message(language: str, identifier: str) -> str:
    language = language if language in ERRORS else 'en'
    return ERRORS.get(language, {}).get(identifier, 'ERROR')


ERRORS = {
    "en": {
        "no-interesting-messages-for-selection": "<p>The reporter found nothing interesting to report.</p>",
        "no-messages-for-selection": "<p>The reporter does not know how to describe the results.</p>",
        "general-error": "<p>Something went wrong. Please try again later.</p>",
        "no-template": "[<i>I don't know how to express my thoughts here</i>]",
    }
}


MORPHOLOGY_SPECIAL_CASES = {
    "en": {
        "he": {
            "genitive": "his",
            "accusative": "him",
        },
        "she": {
            "genitive": "her",
            "accusative": "her",
        },
        "they": {
            "genitive": "their",
            "accusative": "they",
        },
    }
}


SMALL_ORDINALS = {
    "en": {
        "1": "first",
        "2": "second",
        "3": "third",
        "4": "fourth",
        "5": "fifth",
        "6": "sixth",
        "7": "seventh",
        "8": "eighth",
        "9": "ninth",
        "10": "tenth",
        "11": "eleventh",
        "12": "twelfth",
    }
}


SMALL_CARDINALS = {
    "en": {
        "1": "one",
        "2": "two",
        "3": "three",
        "4": "four",
        "5": "five",
        "6": "six",
        "7": "seven",
        "8": "eight",
        "9": "nine",
        "10": "ten",
        "11": "eleven",
        "12": "twelve",
    }
}


MONTHS = {
    "en": {
        "01": "January",
        "02": "February",
        "03": "March",
        "04": "April",
        "05": "May",
        "06": "June",
        "07": "July",
        "08": "August",
        "09": "September",
        "10": "October",
        "11": "November",
        "12": "December",
    }
}
