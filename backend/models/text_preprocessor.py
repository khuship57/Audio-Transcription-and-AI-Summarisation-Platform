import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from typing import List
from dataclasses import dataclass
import spacy
import fuzzy
import Levenshtein

nltk.download('punkt_tab')

@dataclass
class PreprocessingConfig:
    remove_timestamps: bool = True
    remove_fillers: bool = True
    fix_contractions: bool = True
    remove_duplicates: bool = True
    fix_punctuation: bool = True
    segment_sentences: bool = True
    remove_stopwords: bool = False
    chunk_size: int = 512
    chunk_overlap: int = 50

@dataclass
class SpeakerChunk:
    speaker: str
    text: str
    start_sentence: int
    end_sentence: int

class NameStandardizer:
    """Class for standardizing human names using phonetic algorithms with improved filtering"""
    def __init__(self):
        self.name_mapping = {}
        self.name_groups = {}
        self.metaphone_mapping = {}
        self.person_context = {}

        # Initialize spaCy
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.nlp = None

        # Load common human names datasets
        self.load_name_datasets()

        # Create an extended set of English words (non-names)
        self.english_words = set(nltk.corpus.words.words())
        self.stopwords = set(stopwords.words('english'))

        # Common words that are often capitalized but not names
        self.common_capitalized = {
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
            "January", "February", "March", "April", "May", "June", "July", "August",
            "September", "October", "November", "December", "The", "A", "An", "And", "But",
            "Or", "For", "Nor", "So", "Yet", "I", "Internet", "World", "Web", "Email", "Yes",
            "No", "Ok", "Okay", "Hi", "Hello", "Thanks", "Thank", "You", "Please", "University",
            "College", "School", "Hospital", "Bank", "Station", "Airport", "Government",
            "Company", "Corporation", "Department", "Association", "Organization"
        }

    def load_name_datasets(self):
        """Load common first and last name datasets including multicultural names"""
        # Get male and female names from NLTK (primarily Western names)
        male_names = set(nltk.corpus.names.words('male.txt'))
        female_names = set(nltk.corpus.names.words('female.txt'))

        # Add common Indian names
        indian_names = {
            "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Reyansh", "Ayaan", "Atharva",
            "Krishna", "Ishaan", "Shaurya", "Advik", "Rudra", "Kabir", "Anik", "Armaan",
            "Dhruv", "Yuvan", "Virat", "Rohan", "Veer", "Gaurav", "Aahan", "Arnav",
            "Aanya", "Aadhya", "Aaradhya", "Ananya", "Pari", "Anika", "Navya", "Diya",
            "Avani", "Anaya", "Sara", "Myra", "Saanvi", "Ira", "Disha", "Kiara",
            "Riya", "Aahana", "Anvi", "Prisha", "Siya", "Divya", "Avni", "Mahika",
            "Sharma", "Patel", "Singh", "Kumar", "Gupta", "Kaur", "Shah", "Mehta",
            "Chopra", "Reddy", "Bose", "Verma", "Kapoor", "Anand", "Khanna", "Chowdhury",
            "Mukherjee", "Chatterjee", "Agarwal", "Mukhopadhyay", "Das", "Banerjee", "Desai", "Malhotra"
        }

        # Add common Muslim names
        muslim_names = {
            "Mohammed", "Muhammad", "Ahmad", "Mahmoud", "Abdullah", "Ali", "Omar", "Hassan",
            "Hussein", "Ibrahim", "Khalid", "Tariq", "Waleed", "Yusuf", "Zaid", "Bilal",
            "Hamza", "Mustafa", "Samir", "Rayan", "Malik", "Jamal", "Karim", "Amir",
            "Fatima", "Aisha", "Maryam", "Zainab", "Layla", "Noor", "Hana", "Samira",
            "Amina", "Leila", "Salma", "Yasmin", "Zahra", "Rania", "Sara", "Lina",
            "Noura", "Khadija", "Sana", "Farah", "Iman", "Nadia", "Aliyah", "Dalia",
            "Khan", "Rahman", "Ahmed", "Pasha", "Malik", "Syed", "Qureshi", "Aziz",
            "Hussain", "Farooq", "Javed", "Iqbal", "Abbas", "Rashid", "Mirza", "Asif"
        }

        # Combine all name sets
        self.first_names = male_names.union(female_names).union(indian_names).union(muslim_names)

        # Add some common name prefixes and suffixes for various cultures
        self.name_prefixes = {
            "Al", "El", "Abd", "Abdul", "Bin", "Ibn", "Abu",
            "Mc", "Mac", "De", "Van", "Von", "O'", "St.", "San"
        }

        self.name_suffixes = {
            "Jr", "Jr.", "Sr", "Sr.", "II", "III", "IV",
            "Khan", "Lal", "Devi", "Wala", "Bhai", "Ji", "Babu"
        }

        # We'll use a probability threshold for accepting names
        self.name_probability = {}
        for name in self.first_names:
            self.name_probability[name] = 1.0
            # Also add lowercase version with slightly lower probability
            self.name_probability[name.lower()] = 0.9

    def is_likely_human_name(self, word):
        """Determine if a word is likely to be a human name with multicultural awareness"""
        # If word is in our known name list, it's highly likely
        if word in self.first_names:
            return True

        # Check for name prefixes and suffixes that indicate a name
        for prefix in self.name_prefixes:
            if word.startswith(prefix) and len(word) > len(prefix) + 1:
                return True

        for suffix in self.name_suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 1:
                return True

        # Check if it's a common non-name word
        if word.lower() in self.stopwords:
            return False

        if word in self.common_capitalized:
            return False

        # Cultural name patterns
        indian_suffixes = ['ji', 'nath', 'raj', 'dev', 'pal', 'kar', 'wati', 'deep', 'preet', 'jeet']
        for suffix in indian_suffixes:
            if word.lower().endswith(suffix) and len(word) > len(suffix) + 2:
                return True

        # Common Muslim name patterns
        muslim_prefixes = ['al-', 'abdul', 'ibn', 'abu', 'bin', 'mohammad', 'muhammad']
        for prefix in muslim_prefixes:
            if word.lower().startswith(prefix) and len(word) > len(prefix) + 2:
                return True

        # For multicultural names, be less strict about excluding based on English dictionary
        if len(word) <= 4 and word.lower() in self.english_words and word.lower() not in self.name_probability:
            return False

        # Additional checks
        if any(c.isdigit() for c in word):
            return False

        allowed_chars = "-'., "
        if any(c not in allowed_chars and not c.isalpha() for c in word):
            return False

        if len(word) < 2 or len(word) > 30:
            return False

        non_name_suffixes = ['ing', 'ed', 'ly', 'tion', 'ment', 'ness', 'ity', 'ism']
        if (word.lower().endswith(tuple(non_name_suffixes)) and
            len(word) > 5 and
            not any(word.lower().endswith(cultural_suffix) for cultural_suffix in indian_suffixes)):
            return False

        if word[0].isupper():
            return True

        return any(word.lower().startswith(p) for p in muslim_prefixes) or any(word.lower().endswith(s) for s in indian_suffixes)

    def verify_person_entity(self, ent_text):
        """Verify a spaCy PERSON entity is likely a real name with multicultural awareness"""
        parts = ent_text.split()

        if len(parts) == 1:
            return self.is_likely_human_name(parts[0])

        for part in parts:
            if part in self.first_names:
                return True

        compound_parts = []
        for part in parts:
            compound_parts.extend([p for p in re.split(r'[-\s]', part) if p])

        for part in compound_parts:
            if part in self.first_names:
                return True

        if len(parts) >= 2:
            indian_suffixes = ['ji', 'nath', 'raj', 'dev', 'pal', 'kar', 'wati', 'deep', 'preet', 'jeet']
            muslim_prefixes = ['al-', 'abdul', 'ibn', 'abu', 'bin', 'mohammad', 'muhammad']

            for part in parts:
                if any(part.lower().endswith(suffix) for suffix in indian_suffixes):
                    return True
                if any(part.lower().startswith(prefix) for prefix in muslim_prefixes):
                    return True

        if len(parts) == 2 or len(parts) == 3:
            if all(p[0].isupper() for p in parts):
                verb_suffixes = ['ing', 'ed']
                if all(not any(p.lower().endswith(s) for s in verb_suffixes) for p in parts):
                    return True

        if len(parts) >= 3:
            if all(p[0].isupper() for p in parts):
                return True

        return len(parts) >= 2 and all(p[0].isupper() for p in parts)

    def add_name(self, name, confidence=1.0):
        """Add a name to be processed, with confidence filter"""
        if confidence < 0.5 or not name or len(name) < 2:
            return

        if not any(part in self.first_names for part in name.split()):
            if confidence < 0.8:
                return

        try:
            metaphone_code = fuzzy.DMetaphone()(name)[0]
            if not metaphone_code:
                return

            metaphone_code = metaphone_code.decode('utf-8') if isinstance(metaphone_code, bytes) else metaphone_code

            if metaphone_code not in self.metaphone_mapping:
                self.metaphone_mapping[metaphone_code] = name
                self.name_groups[metaphone_code] = {name}
            else:
                standard_name = self.metaphone_mapping[metaphone_code]
                distance = Levenshtein.distance(name.lower(), standard_name.lower())

                if distance <= min(len(name), len(standard_name)) * 0.4:
                    self.name_groups[metaphone_code].add(name)

                    if len(name) < len(standard_name) and len(name) > 2:
                        self.metaphone_mapping[metaphone_code] = name
                    elif len(name) > len(standard_name) and sum(1 for c in name if c.isupper()) > sum(1 for c in standard_name if c.isupper()):
                        self.metaphone_mapping[metaphone_code] = name
                else:
                    new_key = f"{metaphone_code}_{len([k for k in self.metaphone_mapping if k.startswith(metaphone_code)])}"
                    self.metaphone_mapping[new_key] = name
                    self.name_groups[new_key] = {name}

            standard_name = self.metaphone_mapping[metaphone_code]
            self.name_mapping[name] = standard_name

        except Exception as e:
            pass

    def extract_names_from_text(self, text):
        """Extract potential names from text with improved filtering"""
        if not self.nlp:
            return

        doc = self.nlp(text)

        name_indicators = ["mr", "mr.", "ms", "ms.", "mrs", "mrs.", "dr", "dr.",
                          "professor", "prof", "prof.", "sir", "madam", "miss"]

        extracted_names = {}

        for ent in doc.ents:
            if ent.label_ == "PERSON":
                if self.verify_person_entity(ent.text):
                    confidence = 0.9

                    for token in doc:
                        if token.text.lower() in name_indicators and token.i < ent.start and token.i >= ent.start - 3:
                            confidence = 1.0

                    if len(ent.text.split()) > 1:
                        extracted_names[ent.text] = confidence

                    for name_part in ent.text.split():
                        if name_part[0].isupper() and len(name_part) > 1:
                            if self.is_likely_human_name(name_part):
                                extracted_names[name_part] = confidence - 0.1

        words = word_tokenize(text)
        for i, word in enumerate(words):
            if word in extracted_names:
                continue

            if i > 0 and words[i-1].lower().rstrip('.') in [ind.rstrip('.') for ind in name_indicators]:
                if word[0].isupper() and self.is_likely_human_name(word):
                    extracted_names[word] = 0.95

                    if i < len(words) - 1 and words[i+1][0].isupper() and self.is_likely_human_name(words[i+1]):
                        full_name = f"{word} {words[i+1]}"
                        extracted_names[full_name] = 0.98

        for name, confidence in extracted_names.items():
            self.add_name(name, confidence)

    def standardize_name(self, name):
        """Return the standardized version of a name"""
        if not name or len(name) < 2:
            return name

        if not self.is_likely_human_name(name.split()[0]):
            return name

        if name in self.name_mapping:
            return self.name_mapping[name]

        try:
            metaphone_code = fuzzy.DMetaphone()(name)[0]
            if metaphone_code:
                metaphone_code = metaphone_code.decode('utf-8') if isinstance(metaphone_code, bytes) else metaphone_code
                if metaphone_code in self.metaphone_mapping:
                    standard_name = self.metaphone_mapping[metaphone_code]
                    self.name_mapping[name] = standard_name
                    return standard_name
        except:
            pass

        if self.is_likely_human_name(name.split()[0]):
            self.add_name(name, 0.8)
        return name

    def standardize_names_in_text(self, text):
        """Find and standardize all names in a text"""
        self.extract_names_from_text(text)

        names_by_length = sorted(self.name_mapping.keys(), key=len, reverse=True)

        for name in names_by_length:
            pattern = r'\b' + re.escape(name) + r'\b'
            text = re.sub(pattern, self.name_mapping[name], text)
        return text

    def get_name_variants(self):
        """Return all name variants and their standardized forms"""
        return self.name_mapping

    def get_name_groups(self):
        """Return groups of names that were matched together"""
        return self.name_groups

class TextPreprocessor:
    def __init__(self, config: PreprocessingConfig = PreprocessingConfig()):
        self.config = config
        self.stop_words = set(stopwords.words('english'))
        self.name_standardizer = NameStandardizer()

        self.fillers = [
            "um", "uh", "like", "you know", "i mean",
            "so", "basically", "actually", "literally",
            "sort of", "kind of", "well"
        ]

        self.contractions = {
            "won't": "will not", "can't": "cannot", "n't": " not",
            "i'm": "i am", "i've": "i have", "you're": "you are",
            "you've": "you have", "we're": "we are", "we've": "we have",
            "they're": "they are", "they've": "they have",
            "it's": "it is", "that's": "that is", "what's": "what is",
            "let's": "let us", "who's": "who is"
        }

        # Compile regex patterns
        self.timestamp_pattern = re.compile(r'\[\d{2}:\d{2}:\d{2}\]')
        self.filler_pattern = re.compile(r'\b(?:' + '|'.join(self.fillers) + r')\b', re.IGNORECASE)
        self.duplicate_pattern = re.compile(r'\b(\w+)(?:\s+\1)+\b', re.IGNORECASE)
        self.punctuation_pattern = re.compile(r'([.,!?])([^\s])')
        self.spaces_pattern = re.compile(r'\s+')
        self.quotes_pattern = re.compile(r'"\s*([^"]*?)\s*"')

    def preprocess(self, text: str) -> str:
        """Apply all preprocessing steps based on configuration"""
        if self.config.remove_timestamps:
            text = self.timestamp_pattern.sub('', text)
        if self.config.remove_fillers:
            text = self.filler_pattern.sub('', text)
        if self.config.fix_contractions:
            for contraction, expansion in self.contractions.items():
                text = re.sub(rf'\b{contraction}\b', expansion, text, flags=re.IGNORECASE)
        if self.config.remove_duplicates:
            text = self.duplicate_pattern.sub(r'\1', text)
        if self.config.fix_punctuation:
            text = self.punctuation_pattern.sub(r'\1 \2', text)
            text = self.spaces_pattern.sub(' ', text)
            text = self.quotes_pattern.sub(r'"\1"', text)
            text = text.strip()

        # Extract and standardize names before segmenting
        self.name_standardizer.extract_names_from_text(text)
        text = self.name_standardizer.standardize_names_in_text(text)

        if self.config.segment_sentences:
            text = ' '.join(sent_tokenize(text))
        if self.config.remove_stopwords:
            words = text.split()
            text = ' '.join(word for word in words if word.lower() not in self.stop_words)
        return text

    def split_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks"""
        words = text.split()
        chunks = []

        for i in range(0, len(words), self.config.chunk_size - self.config.chunk_overlap):
            chunk = ' '.join(words[i:i + self.config.chunk_size])
            chunks.append(chunk)

        return chunks

    def get_name_standardization_report(self):
        """Get a report of name standardization"""
        name_groups = self.name_standardizer.get_name_groups()
        report = []

        for metaphone, names in name_groups.items():
            if len(names) > 1:
                standard_name = self.name_standardizer.metaphone_mapping.get(metaphone, list(names)[0])
                variants = [name for name in names if name != standard_name]
                if variants:
                    report.append(f"Standardized '{standard_name}' from variants: {', '.join(variants)}")

        return report