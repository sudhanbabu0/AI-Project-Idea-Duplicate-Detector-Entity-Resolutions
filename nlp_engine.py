"""
AI Embedding & NLP Similarity Engine.
Implements:
- Dense semantic vector generation
- Cosine distance / similarity calculation
- Technical Entity Resolution & Jaccard overlap
- Overlapping phrase text highlighter for side-by-side review
"""
import re
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Common academic & general stop words
STOPWORDS = {
    'the', 'and', 'for', 'with', 'using', 'based', 'from', 'system', 'project',
    'this', 'that', 'our', 'are', 'was', 'were', 'which', 'will', 'have', 'been',
    'such', 'also', 'into', 'over', 'both', 'through', 'under', 'between', 'out',
    'has', 'had', 'its', 'can', 'may', 'could', 'should', 'would', 'each', 'all',
    'any', 'some', 'than', 'when', 'who', 'how', 'why', 'what', 'where', 'while',
    'propose', 'proposed', 'paper', 'study', 'approach', 'model', 'method', 'via',
    'application', 'framework', 'portal', 'tool', 'technique', 'solution', 'into'
}

def clean_text(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_entities(text, tech_stack=""):
    """
    Extract domain terms, libraries, frameworks, acronyms, and key noun entities.
    """
    entities = set()
    
    # Explicit tech stack elements
    if tech_stack:
        for t in tech_stack.split(','):
            cleaned = t.strip().lower()
            if cleaned and len(cleaned) > 1:
                entities.add(cleaned)

    # Uppercase acronyms from raw text
    raw_acronyms = re.findall(r'\b[A-Z0-9]{2,}\b', text)
    for a in raw_acronyms:
        entities.add(a.lower())

    # Key nouns and technical terms
    words = re.findall(r'\b[a-z]{3,}\b', clean_text(text))
    meaningful = [w for w in words if w not in STOPWORDS]

    for w in meaningful[:30]:
        entities.add(w)

    return sorted(list(entities))

def highlight_overlapping_phrases(text1, text2):
    """
    Finds overlapping phrases and keywords between two texts
    and returns HTML formatted strings with highlighted overlaps.
    """
    if not text1 or not text2:
        return text1, text2

    words1 = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9\-]+\b', text1)]
    words2 = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9\-]+\b', text2)]
    
    phrases = set()
    # 3-word phrases
    for i in range(len(words1) - 2):
        p = " ".join(words1[i:i+3])
        if p in text2.lower() and len(p) > 7:
            phrases.add(p)

    # 2-word phrases
    for i in range(len(words1) - 1):
        p = " ".join(words1[i:i+2])
        w1, w2 = words1[i], words1[i+1]
        if w1 not in STOPWORDS and w2 not in STOPWORDS and p in text2.lower() and len(p) > 5:
            phrases.add(p)

    # High-value technical keywords
    set1 = set(words1) - STOPWORDS
    set2 = set(words2) - STOPWORDS
    common_singles = set1.intersection(set2)
    for s in common_singles:
        if len(s) > 4:
            phrases.add(s)

    sorted_phrases = sorted(list(phrases), key=len, reverse=True)

    h1 = text1
    h2 = text2

    for p in sorted_phrases[:20]:
        pattern = re.compile(r'\b' + re.escape(p) + r'\b', re.IGNORECASE)
        h1 = pattern.sub(f'<mark class="bg-amber-200 text-amber-950 font-semibold px-1 py-0.5 rounded shadow-sm">{p}</mark>', h1)
        h2 = pattern.sub(f'<mark class="bg-amber-200 text-amber-950 font-semibold px-1 py-0.5 rounded shadow-sm">{p}</mark>', h2)

    return h1, h2

class SemanticVectorEngine:
    def __init__(self, vector_dim=512):
        self.vector_dim = vector_dim
        # Subword & word n-gram TF-IDF vectorizer captures semantic stem similarities
        self.vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(3, 5),
            max_features=self.vector_dim,
            sublinear_tf=True
        )
        self.is_fitted = False

    def build_rich_text(self, title, domain, abstract, methodology="", tech_stack=""):
        return f"{title} {title} {title} {domain} {tech_stack} {abstract} {methodology}"

    def fit_baseline_corpus(self, project_list):
        docs = []
        for p in project_list:
            docs.append(self.build_rich_text(
                p.get('title', ''),
                p.get('domain', ''),
                p.get('abstract', ''),
                p.get('methodology', ''),
                p.get('tech_stack', '')
            ))
        if not docs:
            docs = ["smart ai machine learning deep learning attendance database web system"]
        
        self.vectorizer.fit(docs)
        self.is_fitted = True

    def ensure_fitted(self):
        if not self.is_fitted:
            try:
                import database
                projects = database.get_all_projects()
                if projects:
                    self.fit_baseline_corpus(projects)
                else:
                    self.fit_baseline_corpus([])
            except Exception:
                self.fit_baseline_corpus([])

    def generate_embedding(self, title, domain, abstract, methodology="", tech_stack=""):
        self.ensure_fitted()
        rich_text = self.build_rich_text(title, domain, abstract, methodology, tech_stack)
        vec = self.vectorizer.transform([rich_text]).toarray()[0]
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def compare_proposals(self, p1, p2):
        """
        Compare two project proposals and compute multifaceted similarity scores.
        Calibrated for university academic duplicate detection:
        - Directly overlapping proposals (e.g., face recognition attendance) -> 85% to 98% (HIGH_DUPLICATE)
        - Moderate conceptual overlap -> 50% to 84% (MODERATE_OVERLAP)
        - Distinct ideas -> < 40% (ORIGINAL)
        """
        t1, t2 = p1.get('title', ''), p2.get('title', '')
        a1, a2 = p1.get('abstract', ''), p2.get('abstract', '')

        # 1. Content words in Title overlap
        title_stops = {'system', 'using', 'based', 'for', 'and', 'with', 'the', 'an', 'in', 'of', 'to', 'a'}
        words_t1 = set([w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', t1) if w.lower() not in title_stops])
        words_t2 = set([w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', t2) if w.lower() not in title_stops])
        
        if words_t1 and words_t2:
            min_title_len = min(len(words_t1), len(words_t2))
            title_word_overlap = len(words_t1.intersection(words_t2)) / max(1, min_title_len)
        else:
            title_word_overlap = 0.0

        # Title char n-gram cosine
        v_title = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5))
        try:
            vt = v_title.fit_transform([t1, t2])
            sim_title_char = float(cosine_similarity(vt[0:1], vt[1:2])[0][0])
        except Exception:
            sim_title_char = 0.0

        title_metric = max(title_word_overlap, (title_word_overlap * 0.6 + sim_title_char * 0.4))

        # 2. Abstract Semantic Cosine Similarity
        v_abs = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5))
        try:
            va = v_abs.fit_transform([a1, a2])
            sim_abstract = float(cosine_similarity(va[0:1], va[1:2])[0][0])
        except Exception:
            sim_abstract = 0.0

        # Abstract content word overlap
        words_a1 = set([w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', a1) if w.lower() not in STOPWORDS])
        words_a2 = set([w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', a2) if w.lower() not in STOPWORDS])
        abs_word_overlap = len(words_a1.intersection(words_a2)) / max(1, min(len(words_a1), len(words_a2))) if (words_a1 and words_a2) else 0.0

        abs_metric = max(sim_abstract, (sim_abstract * 0.5 + abs_word_overlap * 0.5))

        # 3. Entity Resolution & Tech Stack Jaccard Similarity
        e1 = set(extract_entities(t1 + ' ' + a1, p1.get('tech_stack', '')))
        e2 = set(extract_entities(t2 + ' ' + a2, p2.get('tech_stack', '')))
        intersection = e1.intersection(e2)
        union = e1.union(e2)
        sim_entity = len(intersection) / max(1, len(union)) if union else 0.0

        min_len = min(len(e1), len(e2)) if (len(e1) and len(e2)) else 1
        overlap_coeff = len(intersection) / min_len
        entity_metric = max(sim_entity, (sim_entity * 0.3 + overlap_coeff * 0.7))

        # 4. Domain matching
        dom1 = p1.get('domain', '').strip().lower()
        dom2 = p2.get('domain', '').strip().lower()
        domain_match = (dom1 == dom2) if (dom1 and dom2) else False
        sim_domain = 1.0 if domain_match else 0.0

        # Base composite score
        base_score = (0.40 * title_metric) + (0.30 * abs_metric) + (0.20 * entity_metric) + (0.10 * sim_domain)

        # Academic Duplicate Scaling Logic
        if title_metric >= 0.55 and len(intersection) >= 5 and domain_match:
            # Overwhelming evidence of same project concept
            calibrated = min(0.97, 0.82 + 0.15 * title_metric)
        elif title_metric >= 0.40 and len(intersection) >= 4 and domain_match:
            calibrated = min(0.88, 0.68 + 0.20 * title_metric)
        elif len(intersection) >= 5 or (domain_match and abs_metric > 0.45):
            calibrated = min(0.75, 0.50 + 0.30 * base_score)
        else:
            calibrated = base_score * 0.75

        final_percentage = round(min(99.4, max(1.2, float(calibrated * 100))), 1)

        # Risk Classification (aligned with slide 8: >85% warning)
        if final_percentage >= 80.0:
            risk = "HIGH_DUPLICATE"
            recommendation = "CRITICAL DUPLICATE (>80% Match): Immediate faculty action required. Recommended to Reject duplicate or Merge student teams."
        elif final_percentage >= 50.0:
            risk = "MODERATE_OVERLAP"
            recommendation = "MODERATE OVERLAP (50-79% Match): Substantial conceptual overlap. Suggest student collaboration or differentiating scope."
        else:
            risk = "ORIGINAL"
            recommendation = "ORIGINAL PROPOSAL (<50% Match): Project demonstrates independent innovation. Cleared for academic review."

        return {
            'similarity_percentage': final_percentage,
            'title_similarity': round(title_metric * 100, 1),
            'abstract_similarity': round(abs_metric * 100, 1),
            'entity_similarity': round(entity_metric * 100, 1),
            'domain_match': domain_match,
            'risk_level': risk,
            'recommendation': recommendation,
            'common_entities': sorted(list(intersection))
        }

    def search_query_against_vectors(self, query_text, stored_vectors, top_k=6):
        """
        Fast cosine similarity search over stored database vector embeddings.
        """
        if not stored_vectors:
            return []

        query_vec = np.array(self.generate_embedding(query_text, "", query_text))
        
        results = []
        for item in stored_vectors:
            vec = np.array(item['vector'])
            dot_product = float(np.dot(query_vec, vec))
            sim_score = max(0.0, min(100.0, dot_product * 100))
            
            results.append({
                'project_id': item['project_id'],
                'title': item['title'],
                'domain': item['domain'],
                'abstract': item['abstract'],
                'tech_stack': item.get('tech_stack', ''),
                'submitted_by_name': item['submitted_by_name'],
                'status': item['status'],
                'similarity_score': round(sim_score, 1)
            })

        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results[:top_k]

# Global singleton engine instance
engine = SemanticVectorEngine()
