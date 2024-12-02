from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    TrigramWordSimilarity,
)
from django.db import models
from django.db.models import F, Q


class ArtworkManager(models.Manager):
    def search(self, text):
        search_query = SearchQuery(text, search_type='websearch')
        search_rank = SearchRank(F('search_vector'), search_query, normalization=32)
        trigram_word_similarity_title = TrigramWordSimilarity(
            text,
            'title__unaccent',
        )
        trigram_word_similarity_title_english = TrigramWordSimilarity(
            text,
            'title_english__unaccent',
        )
        trigram_word_similarity_persons = TrigramWordSimilarity(
            text,
            'search_persons__unaccent',
        )

        return (
            self.get_queryset()
            .annotate(rank=search_rank)
            .annotate(similarity_title=trigram_word_similarity_title)
            .annotate(similarity_title_english=trigram_word_similarity_title_english)
            .annotate(similarity_persons=trigram_word_similarity_persons)
            .filter(
                Q(rank__gte=0.1)
                | Q(similarity_title__gte=0.6)
                | Q(similarity_title_english__gte=0.6)
                | Q(similarity_persons__gte=0.6),
            )
            .order_by(
                '-rank',
                '-similarity_title',
                '-similarity_title_english',
                '-similarity_persons',
            )
        )
