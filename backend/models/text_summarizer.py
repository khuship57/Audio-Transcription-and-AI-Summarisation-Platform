import gc
import torch
from transformers import pipeline
from collections import defaultdict
from typing import List, Dict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import random
from nltk.tokenize import sent_tokenize
import spacy

import nltk
nltk.download('punkt_tab')

class SummaryPostProcessor:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError: 
            self.nlp = None

    def fix_sentence_boundaries(self, text: str) -> str:
        """Fix sentence boundaries and capitalization"""
        if not self.nlp:
            return text

        doc = self.nlp(text)
        sentences = []

        for sent in doc.sents:
            fixed_sent = sent.text.strip()
            if fixed_sent:
                fixed_sent = fixed_sent[0].upper() + fixed_sent[1:]
                if not fixed_sent[-1] in {'.', '!', '?'}:
                    fixed_sent += '.'
                sentences.append(fixed_sent)

        return ' '.join(sentences)

    def remove_incomplete_sentences(self, text: str) -> str:
        """Remove fragments and incomplete sentences"""
        if not self.nlp:
            return text

        doc = self.nlp(text)
        complete_sentences = []

        for sent in doc.sents:
            has_subject = False
            has_verb = False

            for token in sent:
                if token.dep_ in {'nsubj', 'nsubjpass'}:
                    has_subject = True
                if token.pos_ == 'VERB':
                    has_verb = True

            if has_subject and has_verb:
                complete_sentences.append(sent.text.strip())

        return ' '.join(complete_sentences)

    def fix_conjunctions(self, text: str) -> str:
        """Fix common conjunction issues and improve flow"""
        text = re.sub(r'\band\s+and\b', 'and', text)
        text = re.sub(r'\bbut\s+but\b', 'but', text)
        text = re.sub(r'\s+but\s+', ', but ', text)
        text = re.sub(r'\s+however\s+', ', however, ', text)
        return text

    def fix_list_formatting(self, sentences: List[str]) -> List[str]:
        """Improve formatting of list items"""
        formatted_sentences = []
        for sent in sentences:
            sent = re.sub(r'\s+•\s+', '. ', sent)
            sent = re.sub(r'^\s*•\s*', '', sent)
            sent = re.sub(r'^\d+\.\s*([a-z])', lambda m: f"{m.group(1).upper()}", sent)
            formatted_sentences.append(sent)
        return formatted_sentences

    def postprocess_summary(self, text: str) -> str:
        """Apply all post-processing steps"""
        text = self.fix_sentence_boundaries(text)
        text = self.remove_incomplete_sentences(text)
        text = self.fix_conjunctions(text)
        sentences = [s.strip() for s in re.split('[.!?]', text) if s.strip()]
        formatted_sentences = self.fix_list_formatting(sentences)
        return '. '.join(formatted_sentences) + '.'

class TextSummarizer:
    def __init__(self):
        self.summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=0 if torch.cuda.is_available() else -1,
        )

        self.post_processor = SummaryPostProcessor()
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.nlp = None

    def process_chunks(self, chunks: List[str], progress_bar) -> Dict[str, List[str]]:
        """Process chunks and group by topics with post-processing"""
        grouped_chunks = defaultdict(list)
        total_chunks = len(chunks)

        for i, chunk in enumerate(chunks):
            # Extract speaker label if present
            speaker_label = self._extract_speaker_label(chunk)

            # Get the actual content for summarization (without speaker label)
            content_for_summary = self._get_content_without_speaker_label(chunk)

            # Summarize the content
            summary = self.summarizer(content_for_summary, max_length=130, min_length=30)[0]['summary_text']
            processed_summary = self.post_processor.postprocess_summary(summary)

            # Add speaker label back to the summary if it was present
            if speaker_label:
                processed_summary = f"**{speaker_label}:** {processed_summary}"
            else:
                processed_summary = summary

            # Identify topic based on the original content
            topic = self.identify_topics(content_for_summary)

            grouped_chunks[topic].append(processed_summary)

        return grouped_chunks

    def _extract_speaker_label(self, chunk: str) -> str:
        """Extract speaker label from chunk if present"""
        # More specific pattern that captures any text between ** and :**
        speaker_pattern = r'\*\*([^*:]+):\*\*'
        match = re.search(speaker_pattern, chunk)
        if match:
            return match.group(1).strip()
        return ""

    def _get_content_without_speaker_label(self, chunk: str) -> str:
        """Get chunk content without speaker label for summarization"""
        speaker_pattern = r'\*\*([^*]+):\*\*\s*'
        content = re.sub(speaker_pattern, '', chunk, count=1)
        return content.strip()

    def identify_topics(self, text: str) -> str:
        """Identify the main topic of a text segment"""
        if not self.nlp:
            return 'General Discussion'

        doc = self.nlp(text)

        topic_keywords = {
            # Business & Corporate
            'Company Overview': ['company', 'organization', 'mission', 'vision', 'values'],
            'Business Strategy & Management': ['strategy', 'leadership', 'management', 'growth', 'operations', 'business model', 'entrepreneurship', 'stakeholders'],
            'Finance & Investment': ['finance', 'investment', 'funding', 'profit', 'loss', 'budget', 'capital', 'valuation', 'stocks', 'trading'],
            'Marketing & Branding': ['marketing', 'branding', 'advertising', 'SEO', 'social media', 'promotion', 'public relations'],
            'Sales & Customer Relationship': [
                'sales', 'CRM', 'lead generation', 'customer service', 'retention', 'pricing strategy',
                'follow-ups', 'quotations', 'lead status', 'client engagement', 'stakeholder meeting',
                'customer pipeline', 'business development'
            ],
            'E-Commerce & Retail': ['e-commerce', 'retail', 'supply chain', 'inventory', 'logistics', 'warehousing'],
            'Corporate Strategy & Financials': ['investors', 'corporate', 'supply chain', 'mergers', 'acquisitions'],
            'Market Expansion & Globalization': ['market', 'expansion', 'international trade', 'emerging markets'],
            'Client Engagement & Sales Strategy': [
                'client', 'POC', 'demo', 'pipeline', 'licensing', 'collateral', 'roadmap', 'proposal',
                'investment roadmap', 'business negotiations', 'partner meetings'
            ],
            'Project & Report Management': [
                'report format', 'summary report', 'documentation', 'findings', 'meeting notes',
                'proposal customization', 'contract discussions'
            ],

            # Technology & AI
            'Artificial Intelligence & Automation': [
                'AI', 'machine learning', 'deep learning', 'automation', 'data analytics', 'neural networks',
                'ML model', 'data-driven insights', 'intelligent automation', 'predictive analytics'
            ],
            'Cybersecurity & Risk Management': [
                'cybersecurity', 'HTTPS', 'encryption', 'TLS', 'attack', 'authorization', 'security',
                'penetration testing', 'ransomware', 'risk register', 'remediation', 'audit', 'SOC',
                'security compliance', 'risk-based approach', 'security audits', 'VAPT'
            ],
            'Software Development & IT': [
                'software', 'coding', 'cloud computing', 'DevOps', 'databases', 'full stack development',
                'API', 'staging', 'production', 'server', 'software customization', 'IT infrastructure'
            ],
            'Testing & Evaluation': ['testing', 'scoring', 'quantitative', 'qualitative', 'user testing', 'penetration testing'],
            'Blockchain & Cryptocurrency': ['blockchain', 'cryptocurrency', 'bitcoin', 'ethereum', 'NFTs', 'decentralization'],
            'Internet & Digital Trends': ['internet', 'IoT', 'web development', '5G', 'cloud services', 'big data'],

            # Science & Engineering
            'Healthcare & Medicine': [
                'healthcare', 'medicine', 'hospital', 'surgery', 'doctor', 'medical research',
                'healthcare compliance', 'HIPAA', 'patient data security', 'healthcare AI solutions'
            ],
            'Biotechnology & Pharmaceuticals': ['biotech', 'pharmaceuticals', 'drug discovery', 'genomics', 'clinical trials'],
            'Engineering & Innovation': ['engineering', 'mechanical', 'electrical', 'civil', 'robotics', 'nanotechnology'],
            'Environmental Science & Sustainability': ['sustainability', 'climate change', 'carbon footprint', 'renewable energy'],
            'Energy & Emissions': ['energy', 'renewable', 'non-renewable', 'solar', 'wind', 'tidal', 'carbon emissions', 'power plants'],

            # Education & Learning
            'Academic Research & Education': [
                'education', 'learning', 'teaching', 'university', 'school', 'curriculum',
                'educational technology', 'e-learning platforms'
            ],
            'Online Learning & EdTech': ['e-learning', 'MOOCs', 'virtual classroom', 'online courses', 'EdTech'],

            # Government & Policy
            'Regulations & Compliance': [
                'regulation', 'compliance', 'laws', 'policy', 'audit', 'standards',
                'cybersecurity compliance', 'government regulations', 'data privacy laws'
            ],
            'Politics & International Relations': ['politics', 'government', 'elections', 'diplomacy', 'foreign policy'],

            # Personal Development & Lifestyle
            'Self-Improvement & Productivity': ['self-improvement', 'motivation', 'goal setting', 'habits', 'efficiency', 'workflow'],
            'Fitness & Wellness': ['fitness', 'exercise', 'yoga', 'meditation', 'nutrition'],
            'Travel & Adventure': ['travel', 'tourism', 'adventure', 'hotels'],

            # Entertainment & Media
            'Movies & TV Shows': ['movies', 'TV shows', 'cinema', 'streaming', 'actors', 'directors'],
            'Music & Performing Arts': ['music', 'concerts', 'albums', 'orchestra', 'theater'],
            'Gaming & Esports': ['gaming', 'esports', 'video games', 'VR', 'tournaments'],

            # Transportation & Automotive
            'Automobile & Electric Vehicles': ['cars', 'EVs', 'batteries', 'hybrid cars', 'self-driving'],
            'Aviation & Aerospace': ['aviation', 'airlines', 'drones', 'rockets'],

            # Miscellaneous
            'General Discussion': []
        }

        topic_scores = defaultdict(int)
        for token in doc:
            for topic, keywords in topic_keywords.items():
                if token.text.lower() in keywords:
                    topic_scores[topic] += 1

        return max(topic_scores.items(), key=lambda x: x[1])[0] if topic_scores else 'General Discussion'

    def remove_redundancies(self, chunks: List[str]) -> List[str]:
        """Remove redundant content using TF-IDF and cosine similarity"""
        content_chunks = [self._get_content_without_speaker_label(chunk) for chunk in chunks]

        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(content_chunks)
        similarities = cosine_similarity(tfidf_matrix)

        unique_chunks = []
        for i, chunk in enumerate(chunks):
            is_redundant = False
            for j in range(i):
                if similarities[i][j] > 0.7:
                    is_redundant = True
                    break
            if not is_redundant:
                unique_chunks.append(chunk)

        return unique_chunks

    def format_markdown(self, grouped_chunks: Dict[str, List[str]], meeting_duration: str = None, name_standardization_report: List[str] = None) -> str:
        """Format the grouped chunks into a markdown document with meeting duration"""
        md_content = ["# Meeting Summary\n"]

        # Add meeting duration if available
        if meeting_duration:
            md_content.append(f"**Meeting Duration:** {meeting_duration}\n")

        # Add overview section
        md_content.append("## Overview")
        topics = list(grouped_chunks.keys())
        md_content.append("This meeting covered the following topics:")
        for topic in topics:
            if topic:
                md_content.append(f"- {topic}")
        md_content.append("")

        # Add detailed sections
        for topic, chunks in grouped_chunks.items():
            if not topic:
                continue

            md_content.append(f"## {topic}")

            # Process each chunk in the topic
            for chunk in chunks:
                verbs = ["shared", "explained", "mentioned", "noted", "added", "emphasized"]

                speaker_label = self._extract_speaker_label(chunk)
                cleaned_chunk = self._get_content_without_speaker_label(chunk)

                sentences = sent_tokenize(cleaned_chunk)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if speaker_label:
                        verb = random.choice(verbs)
                        md_content.append(f"- {speaker_label} {verb} that {sentence[0].lower() + sentence[1:]}")
                    else:
                        md_content.append(f"- {sentence}")

        md_content.append("## Next Steps")
        md_content.append("- [ ] Review shared materials")
        md_content.append("- [ ] Confirm availability for the next meeting")
        md_content.append("- [ ] Share summary with stakeholders\n")
        return "\n".join(md_content)

    def _remove_speaker_prefix(self, chunk: str) -> str:
        """
        Remove speaker prefix from chunk while preserving natural speaker references within text.

        Args:
            chunk: Text chunk that may start with **Speaker_X:**

        Returns:
            Cleaned chunk without prefix but with natural speaker references preserved
        """
        speaker_prefix_pattern = r'^\*\*([^*]+):\*\*\s*'
        cleaned_chunk = re.sub(speaker_prefix_pattern, '', chunk)
        return cleaned_chunk.strip()
