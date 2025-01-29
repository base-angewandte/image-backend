import operator
import re
from functools import reduce

from django.db.models import Q


def websearch_transformation(q_param: str, lookups: list[str]) -> (Q, Q | None):
    """Transforms q_param to Q filter and exclude objects for every provided
    lookup.

    :param q_param: 'websearch' formatted search query parameter
    :param lookups: field lookups to apply transformed q_param to
    :return: filter Q and exclude Q (or None if no exclusion was used in
        search query parameter)
    """

    exclude = None
    param_filtered = q_param.replace('"', '')
    if '-' in param_filtered:
        regex = r'^-\w+| -\w+'
        exclude = [w.lstrip('-') for w in re.findall(regex, param_filtered)]
        param_filtered = re.sub(regex, '', param_filtered).strip()

    param_filtered = re.split(' or ', param_filtered, flags=re.IGNORECASE)

    q_filters_list = []
    q_filters_exclude_list = []

    for lookup in lookups:
        q_filters_list.append(
            reduce(operator.and_, (Q(**{lookup: x}) for x in param_filtered)),
        )
        if exclude:
            q_filters_exclude_list.append(
                reduce(operator.and_, (Q(**{lookup: x}) for x in exclude)),
            )

    q_filters = reduce(operator.or_, q_filters_list)
    q_filters_exclude = (
        reduce(operator.or_, q_filters_exclude_list) if q_filters_exclude_list else None
    )

    return q_filters, q_filters_exclude
