"""
Test script to prototype and calibrate the NLP Vector Similarity & Entity Resolution Engine.
"""
import re
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def extract_entities(text, tech_stack=""):
    """Extract technical keywords, acronyms, and domain concepts."""
    # Split technical terms
    tech_items = [t.strip().lower() for t in tech_stack.split(',') if t.strip()]
    
    # Extract capitalized compound terms and common acronyms from text
    acronyms = re.findall(r'\b[A-Z]{2,}\b', text)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Common stop words to exclude from entities
    stopwords = {
        'the', 'and', 'for', 'with', 'using', 'based', 'from', 'system', 'project',
        'this', 'that', 'our', 'are', 'was', 'were', 'which', 'will', 'have', 'been',
        'such', 'also', 'into', 'over', 'both', 'through', 'under', 'between'
    }
    meaningful_words = [w for w in words if w not in stopwords]
    
    entities = set(tech_items + [a.lower() for a in acronyms] + meaningful_words[:15])
    return list(entities)

def create_rich_text(title, domain, abstract, methodology="", tech_stack=""):
    """Create weighted composite representation emphasizing title and key tech concepts."""
    # Repeat title to give it appropriate semantic prominence
    return f"{title} {title} {domain} {tech_stack} {abstract} {methodology}"

class SemanticVectorEngine:
    def __init__(self):
        # Hybrid char-wb n-gram vectorizer for robust semantic and morphological matching
        self.vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(3, 5),
            max_features=2048,
            sublinear_tf=True
        )
        self.is_fitted = False
        self.corpus = []

    def fit_corpus(self, documents):
        if not documents:
            documents = ["dummy project baseline initialization"]
        self.vectorizer.fit(documents)
        self.is_fitted = True

    def get_embedding(self, text):
        if not self.is_fitted:
            self.fit_corpus([text])
        vec = self.vectorizer.transform([text]).toarray()[0]
        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def compare_proposals(self, p1, p2):
        """
        Compare two project proposals:
        p = {'title': ..., 'domain': ..., 'abstract': ..., 'methodology': ..., 'tech_stack': ...}
        """
        # 1. Text representations
        t1 = create_rich_text(p1['title'], p1['domain'], p1['abstract'], p1.get('methodology', ''), p1.get('tech_stack', ''))
        t2 = create_rich_text(p2['title'], p2['domain'], p2['abstract'], p2.get('methodology', ''), p2.get('tech_stack', ''))
        
        # Title specific similarity
        vec_title = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5))
        try:
            vt = vec_title.fit_transform([p1['title'], p2['title']])
            sim_title = float(cosine_similarity(vt[0:1], vt[1:2])[0][0])
        except:
            sim_title = 0.0

        # Abstract similarity
        vec_abs = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5))
        try:
            va = vec_abs.fit_transform([p1['abstract'], p2['abstract']])
            sim_abstract = float(cosine_similarity(va[0:1], va[1:2])[0][0])
        except:
            sim_abstract = 0.0

        # Technical Entity Jaccard Similarity
        e1 = set(extract_entities(p1['abstract'] + ' ' + p1['title'], p1.get('tech_stack', '')))
        e2 = set(extract_entities(p2['abstract'] + ' ' + p2['title'], p2.get('tech_stack', '')))
        intersection = e1.intersection(e2)
        union = e1.union(e2)
        sim_entity = len(intersection) / max(1, len(union)) if union else 0.0

        # Domain match
        sim_domain = 1.0 if p1['domain'].strip().lower() == p2['domain'].strip().lower() else 0.0

        # Composite score calculation (calibrated for high fidelity detection)
        # Identical or near identical titles + matching domain & tech yield >85%
        # Moderately overlapping concepts yield 60-80%
        # Distinct yield <30%
        raw_score = (0.40 * sim_title) + (0.35 * sim_abstract) + (0.15 * sim_entity) + (0.10 * sim_domain)
        
        # Dynamic amplification for high correlation matches (sigmoid scaling)
        if sim_title > 0.65 or (sim_title > 0.5 and sim_abstract > 0.5):
            amplified = raw_score * 1.25
        else:
            amplified = raw_score * 1.05
        final_score = min(100.0, max(0.0, amplified * 100))

        # Risk classification
        if final_score >= 80.0:
            risk = "HIGH_DUPLICATE"
            recommendation = "Flag for Duplicate Review. Consider merging student teams or rejecting proposal."
        elif final_score >= 55.0:
            risk = "MODERATE_OVERLAP"
            recommendation = "Significant conceptual overlap detected. Recommend team collaboration or scope divergence."
        else:
            risk = "ORIGINAL"
            recommendation = "Project idea appears original. Approved for academic review."

        return {
            'similarity_percentage': round(final_score, 1),
            'title_similarity': round(sim_title * 100, 1),
            'abstract_similarity': round(sim_abstract * 100, 1),
            'entity_similarity': round(sim_entity * 100, 1),
            'domain_match': p1['domain'].strip().lower() == p2['domain'].strip().lower(),
            'risk_level': risk,
            'recommendation': recommendation,
            'common_entities': list(intersection)
        }

if __name__ == '__main__':
    p1 = {
        'title': 'Smart Attendance System using Face Recognition',
        'domain': 'Artificial Intelligence',
        'abstract': 'An automated student attendance monitoring system that uses OpenCV and deep learning to identify student faces from classroom CCTV camera feeds and records attendance in real-time.',
        'methodology': 'Haar Cascade face detection, FaceNet CNN embeddings, SQLite attendance database.',
        'tech_stack': 'Python, OpenCV, PyTorch, SQLite, Streamlit'
    }
    p2 = {
        'title': 'AI Based Face Recognition Attendance System',
        'domain': 'Artificial Intelligence',
        'abstract': 'Classroom attendance tracking application using computer vision and deep learning to recognize student faces automatically from webcams and update academic logs in database.',
        'methodology': 'MTCNN face detection, ResNet embeddings, MySQL backend.',
        'tech_stack': 'Python, OpenCV, TensorFlow, MySQL, Flask'
    }
    p3 = {
        'title': 'Blockchain Decentralized Supply Chain Provenance Tracker',
        'domain': 'Blockchain',
        'abstract': 'A decentralized ledger platform to verify provenance of organic agricultural produce from farm to consumer using Ethereum smart contracts.',
        'methodology': 'Solidity ERC-721 tokenization, IPFS distributed storage, Web3 web portal.',
        'tech_stack': 'Solidity, Ethereum, React, Web3.js, IPFS'
    }
    
    engine = SemanticVectorEngine()
    res12 = engine.compare_proposals(p1, p2)
    print("Match 1 vs 2 (Expected DUPLICATE):", json.dumps(res12, indent=2))
    
    res13 = engine.compare_proposals(p1, p3)
    print("Match 1 vs 3 (Expected ORIGINAL):", json.dumps(res13, indent=2))
