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
        trigram_word_similarity_authors_name = TrigramWordSimilarity(
            text,
            'authors__name',
        )
        trigram_word_similarity_photographers_name = TrigramWordSimilarity(
            text,
            'photographers__name',
        )
        trigram_word_similarity_graphic_designers_name = TrigramWordSimilarity(
            text,
            'graphic_designers__name',
        )

        rank = (
            search_rank
            + trigram_word_similarity_title
            + trigram_word_similarity_title_english
            + trigram_word_similarity_artists_name
            + trigram_word_similarity_artists_synonyms
            + trigram_word_similarity_authors_name
            + trigram_word_similarity_photographers_name
            + trigram_word_similarity_graphic_designers_name
        )
        return (
            self.get_queryset()
            .annotate(rank=rank)
            .annotate(similarity_title=trigram_word_similarity_title)
            .annotate(similarity_artists_name=trigram_word_similarity_artists_name)
            .annotate(
                similarity_artists_synonyms=trigram_word_similarity_artists_synonyms,
            )
            .annotate(similarity_authors_name=trigram_word_similarity_authors_name)
            .annotate(
                similarity_photographers_name=trigram_word_similarity_photographers_name,
            )
            .annotate(
                similarity_graphic_designers_name=trigram_word_similarity_graphic_designers_name,
            )
            .filter(rank__gte=0.1)
            .order_by('-rank')
        )
