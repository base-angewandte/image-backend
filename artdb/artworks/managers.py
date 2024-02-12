from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramWordSimilarity,
)
from django.db import models

search_vectors = (
    SearchVector('title', weight='A')
    + SearchVector('title_english', weight='A')
    + SearchVector(StringAgg('artists__name', delimiter=' '), weight='A')
    + SearchVector(StringAgg('artists__synonyms', delimiter=' '), weight='A')
    + SearchVector('description', weight='B')
    + SearchVector(StringAgg('keywords__name', delimiter=' '), weight='B')
    + SearchVector(StringAgg('place_of_production__name', delimiter=' '), weight='B')
    + SearchVector(
        StringAgg('place_of_production__synonyms', delimiter=' '),
        weight='B',
    )
    + SearchVector(StringAgg('location_current__name', delimiter=' '), weight='B')
    + SearchVector(StringAgg('location_current__synonyms', delimiter=' '), weight='B')
    + SearchVector('credits', weight='C')
    + SearchVector('material', weight='C')
    + SearchVector('dimensions', weight='C')
    + SearchVector('date', weight='C')
)


class ArtworkManager(models.Manager):
    def search(self, text):
        search_query = SearchQuery(text)
        search_rank = SearchRank(search_vectors, search_query)
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
            .filter(rank__gte=0.2)
            .order_by('-rank')
        )
