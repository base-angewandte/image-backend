import json

from rest_framework import status

VERSION = 'v1'


def assert_limit_responses(test_case, url, limit, max_items, test_type):
    # Check basic limit setting
    response = test_case.client.get(f'{url}?limit={limit}', format='json')
    test_case.assertEqual(response.status_code, status.HTTP_200_OK)
    content = json.loads(response.content)
    if test_type == 'artworks':
        test_case.assertEqual(len(content['results']), min(limit, max_items))
    elif test_type == 'folders':
        test_case.assertEqual(len(content), min(limit, max_items))

    # Check setting a negative limit
    response = test_case.client.get(f'{url}?limit=-1', format='json')
    test_case.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    content = json.loads(response.content)
    test_case.assertEqual(content['detail'], 'limit must be a positive integer')

    # Check setting 0 as limit
    response = test_case.client.get(f'{url}?limit=0', format='json')
    test_case.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    content = json.loads(response.content)
    test_case.assertEqual(content['detail'], 'limit must be a positive integer')

    # Check setting limit over maximum available items
    response = test_case.client.get(f'{url}?limit=5000', format='json')
    # We should check in the code why the limit doesn't have a maximum value.
    test_case.assertEqual(response.status_code, status.HTTP_200_OK)
    content = json.loads(response.content)
    if test_type == 'artworks':
        test_case.assertEqual(len(content['results']), max_items)
    elif test_type == 'folders':
        test_case.assertEqual(len(content), max_items)


def assert_offset_responses(test_case, url, combinations, max_items, test_type):
    # Test different limit and offset combinations
    for val in combinations:
        response = test_case.client.get(
            f'{url}?limit={val["limit"]}&offset={val["offset"]}',
            format='json',
        )
        test_case.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        if test_type == 'artworks':
            test_case.assertEqual(len(content['results']), val['limit'])
        elif test_type == 'folders':
            test_case.assertEqual(len(content), val['limit'])

    # Check setting a negative offset
    response = test_case.client.get(f'{url}?offset=-1', format='json')
    content = json.loads(response.content)
    test_case.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    test_case.assertEqual(content['detail'], 'negative offset is not allowed')

    # Check setting a 0 offset
    response = test_case.client.get(f'{url}?offset=0', format='json')
    content = json.loads(response.content)
    test_case.assertEqual(response.status_code, status.HTTP_200_OK)
    if test_type == 'artworks':
        test_case.assertEqual(content['total'], max_items)
        test_case.assertEqual(len(content['results']), max_items)
    elif test_type == 'folders':
        test_case.assertEqual(len(content), max_items)

    # Check setting no limit but setting offset
    response = test_case.client.get(f'{url}?offset=5', format='json')
    test_case.assertEqual(response.status_code, status.HTTP_200_OK)

    # Check setting offset more than the maximum available items
    response = test_case.client.get(f'{url}?offset=5000', format='json')
    test_case.assertEqual(response.status_code, status.HTTP_200_OK)

    # Check setting offset but with a small limit
    response = test_case.client.get(f'{url}?limit=1&offset=2', format='json')
    content = json.loads(response.content)
    if test_type == 'artworks':
        test_case.assertEqual(len(content['results']), 1)
    elif test_type == 'folders':
        test_case.assertEqual(len(content), 1)
