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
        trigram_word_similarity_persons = TrigramWordSimilarity(
            text,
            'search_persons',
        )

        rank = (
            search_rank
            + trigram_word_similarity_title
            + trigram_word_similarity_title_english
            + trigram_word_similarity_persons
        )
        return (
            self.get_queryset()
            .annotate(rank=rank)
            .annotate(similarity_title=trigram_word_similarity_title)
            .annotate(similarity_persons=trigram_word_similarity_persons)
            .filter(rank__gte=0.1)
            .order_by('-rank')
        )
