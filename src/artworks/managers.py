from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    TrigramWordSimilarity,
)
from django.db import models
from django.db.models import F, Value
from django.db.models.functions import Coalesce


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
            Coalesce('artists__name', Value('')),
        )
        trigram_word_similarity_artists_synonyms = TrigramWordSimilarity(
            text,
            Coalesce('artists__synonyms', Value('')),
        )
        trigram_word_similarity_authors_name = TrigramWordSimilarity(
            text,
            Coalesce('authors__name', Value('')),
        )
        trigram_word_similarity_authors_synonyms = TrigramWordSimilarity(
            text,
            Coalesce('authors__synonyms', Value('')),
        )
        trigram_word_similarity_photographers_name = TrigramWordSimilarity(
            text,
            Coalesce('photographers__name', Value('')),
        )
        trigram_word_similarity_photographers_synonyms = TrigramWordSimilarity(
            text,
            Coalesce('photographers__synonyms', Value('')),
        )
        trigram_word_similarity_graphic_designers_name = TrigramWordSimilarity(
            text,
            Coalesce('graphic_designers__name', Value('')),
        )
        trigram_word_similarity_graphic_designers_synonyms = TrigramWordSimilarity(
            text,
            Coalesce('graphic_designers__synonyms', Value('')),
        )

        rank = (
            search_rank
            + trigram_word_similarity_title
            + trigram_word_similarity_title_english
            + trigram_word_similarity_artists_name
            + trigram_word_similarity_artists_synonyms
            + trigram_word_similarity_authors_name
            + trigram_word_similarity_authors_synonyms
            + trigram_word_similarity_photographers_name
            + trigram_word_similarity_photographers_synonyms
            + trigram_word_similarity_graphic_designers_name
            + trigram_word_similarity_graphic_designers_synonyms
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
                similarity_authors_synonyms=trigram_word_similarity_authors_synonyms,
            )
            .annotate(
                similarity_photographers_name=trigram_word_similarity_photographers_name,
            )
            .annotate(
                similarity_photographers_synonyms=trigram_word_similarity_photographers_synonyms,
            )
            .annotate(
                similarity_graphic_designers_name=trigram_word_similarity_graphic_designers_name,
            )
            .annotate(
                similarity_graphic_designers_synonyms=trigram_word_similarity_graphic_designers_synonyms,
            )
            .filter(rank__gte=0.1)
            .order_by('-rank')
        )
