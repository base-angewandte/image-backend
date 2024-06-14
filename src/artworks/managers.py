from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    TrigramWordSimilarity,
)
from django.db import models
from django.db.models import F


class ArtworkManager(models.Manager):
    def search(self, text):
        search_query = SearchQuery(text)
        search_rank = SearchRank(F('search_vector'), search_query, normalization=32)
        trigram_word_similarity_title = TrigramWordSimilarity(
            text,
            'title',
        )
        trigram_word_similarity_title_english = TrigramWordSimilarity(
            text,
            'title_english',
        )
        trigram_word_similarity_artists_name = TrigramWordSimilarity(
            text,
            'artists__name',
        )
        trigram_word_similarity_artists_synonyms = TrigramWordSimilarity(
            text,
            'artists__synonyms',
        )
        rank = (
            search_rank
            + trigram_word_similarity_title
            + trigram_word_similarity_title_english
            + trigram_word_similarity_artists_name
            + trigram_word_similarity_artists_synonyms
        )
        return (
            self.get_queryset()
            .annotate(rank=rank)
            .filter(rank__gte=0.1)
            .order_by('-rank')
        )
