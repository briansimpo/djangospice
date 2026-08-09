import re

def format_number(amount, decimal_places=0, thousand_separator=','):
    return f"{amount:,.{decimal_places}f}".replace(",", thousand_separator)


def alphanum_to_digits(value: str, width: int = 0) -> int:
        """
        Encode value so that:
        Letters: A=1, B=2, ... Z=26
        Digits: stay as they are
        Then remove leading zeros, truncate to fixed width, and pad if shorter.
        """
        value = value.upper()
        encoded_parts = []
        for char in value:
            if char.isalpha():
                encoded_parts.append(str(ord(char) - ord('A') + 1))
            elif char.isdigit():
                encoded_parts.append(char)

        encoded_str = "".join(encoded_parts).lstrip("0") or "0"

        if width > 0:
            if len(encoded_str) > width:
                encoded_str = encoded_str[:width]
            encoded_str = encoded_str.zfill(width)

        return encoded_str


def normalize(phrase: str) -> str:
    lowercase_words = {
        "a", "an", "the", "and", "but", "or", "nor", "on", "in", 
        "is", "with", "at", "to", "from", "by", "for", "of"
    }
    
    roman_numeral_pattern = re.compile(
        r"^(?=[MDCLXVI])M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", 
        re.IGNORECASE
    )
    
    words = phrase.split()
    normalized_words = []
    for i, word in enumerate(words):
        if (
            word.isdigit() or 
            roman_numeral_pattern.fullmatch(word) or 
            re.fullmatch(r"\([A-Z]+\)", word)
        ):
            normalized_words.append(word)
        else:
            if i == 0 or word.lower() not in lowercase_words:
                normalized_words.append(word.capitalize())
            else:
                normalized_words.append(word.lower())
    
    interim_phrase = " ".join(normalized_words)
    
    def title_case_no_parentheses(segment: str) -> str:
        words_in_seg = segment.split()
        normalized_seg_words = []
        for j, w in enumerate(words_in_seg):
            if w.isdigit() or roman_numeral_pattern.fullmatch(w):
                normalized_seg_words.append(w)
            else:
                if j == 0 or w.lower() not in lowercase_words:
                    normalized_seg_words.append(w.capitalize())
                else:
                    normalized_seg_words.append(w.lower())
        return " ".join(normalized_seg_words)
    
    def replace_func(match: re.Match) -> str:
        content = match.group(1)
        if content.isupper():
            return f"({content})"
        else:
            return f"({title_case_no_parentheses(content)})"
    
    result = re.sub(r"\((.*?)\)", replace_func, interim_phrase)
    return result

