import re
from math import log
from collections import Counter
from app.models import SearchResult
from typing import List, Dict, Set, Tuple
from app.services.embeddings import SearchResult


class QueryTermScorer:
    def __init__(self, min_term_length: int = 3):
        """
        Initialize the QueryTermScorer.

        Args:
            min_term_length: Minimum length of terms to consider for importance scoring
        """
        self.min_term_length = min_term_length
        c_words = open("./data/stopwords.txt").read().split("\n")
        self.common_words = set(c_words)

    def _tokenize(self, text: str) -> List[str]:
        """Convert text to lowercase and split into tokens."""
        return [
            str(token).lower()
            for token in re.findall(r"\w+", text)
            if len(token) >= self.min_term_length
            and str(token).lower() not in self.common_words
        ]

    def _calculate_term_frequencies(
        self, documents: List[SearchResult]
    ) -> Dict[str, int]:
        """Calculate how many documents each term appears in."""
        term_doc_freq = Counter()

        for doc in documents:
            # Get unique terms in this document
            doc_terms = set(self._tokenize(doc.chunk_content))
            # Update term frequencies
            term_doc_freq.update(doc_terms)

        return term_doc_freq

    def _calculate_term_importance(
        self, query_terms: Set[str], term_frequencies: Dict[str, int], total_docs: int
    ) -> Dict[str, float]:
        """Calculate importance score for each query term."""
        term_importance = {}

        for term in query_terms:
            # Skip common words and very short terms
            if term in self.common_words or len(term) < self.min_term_length:
                continue

            # Calculate inverse document frequency
            doc_freq = term_frequencies.get(term, 0)
            if doc_freq == 0:
                # Term doesn't appear in corpus - might be very important
                importance = 2.0
            else:
                # Terms that appear in fewer documents get higher importance
                importance = 1 + log(total_docs / (1 + doc_freq))

            term_importance[term] = importance

        return term_importance

    def calculate_boosted_scores(
        self, query: str, results: List[SearchResult], boost_factor: float = 0.5
    ) -> List[Dict]:
        """
        Recalculate scores considering term importance.

        Args:
            query: Original search query
            results: List of search results
            boost_factor: How much to boost scores based on term importance (0-1)

        Returns:
            List of results with updated scores
        """
        # Get query terms
        query = query.lower()
        query_terms = set(self._tokenize(query))

        # Calculate term frequencies across all documents
        term_frequencies = self._calculate_term_frequencies(results)

        # Calculate importance scores for query terms
        term_importance = self._calculate_term_importance(
            query_terms, term_frequencies, len(results)
        )

        # Boost scores based on term presence and importance
        boosted_results = []
        for result in results:
            doc_terms = set(self._tokenize(result.chunk_content))

            # Calculate boost based on important terms present
            boost = 0.0
            matching_terms = query_terms.intersection(doc_terms)
            for term in matching_terms:
                boost += term_importance.get(term, 0)

            # Normalize boost
            if matching_terms:
                boost = boost / len(matching_terms)

            # Create new result with boosted score
            new_result = {
                **result.__dict__,
                "termBoost": boost,
                "matchingTerms": list(matching_terms),
            }

            boosted_results.append(new_result)

        boosted_results.sort(key=lambda x: x["termBoost"], reverse=True)
        ranked_sources = []
        for boosted_result in boosted_results:
            if (
                boosted_result["termBoost"] != 0
                or len(boosted_result["matchingTerms"]) != 0
            ):
                ranked_sources.append(boosted_result)

        return boosted_results
