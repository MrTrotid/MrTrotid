import datetime
from dateutil import relativedelta
import requests
import os
import sys
from lxml import etree
import time
import hashlib

ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', '')
HEADERS = {'authorization': 'Bearer ' + ACCESS_TOKEN} if ACCESS_TOKEN else {}
USER_NAME = os.environ.get('USER_NAME') or os.environ.get('GITHUB_REPOSITORY_OWNER') or "MrTrotid"
OWNER_ID = None  # set after user_getter runs (plain GraphQL id string)

QUERY_COUNT = {
    'user_getter': 0,
    'follower_getter': 0,
    'graph_repos_stars': 0,
    'recursive_loc': 0,
    'loc_query': 0,
}


# -----------------------------
# Helpers
# -----------------------------

def query_count(name):
    QUERY_COUNT[name] += 1


def simple_request(func_name, query, variables):
    r = requests.post(
        'https://api.github.com/graphql',
        json={'query': query, 'variables': variables},
        headers=HEADERS
    )
    if r.status_code == 200:
        return r
    raise Exception(func_name, 'failed with', r.status_code, r.text, QUERY_COUNT)


def perf_counter(func, *args):
    start = time.perf_counter()
    result = func(*args)
    return result, time.perf_counter() - start


def format_plural(n):
    return 's' if n != 1 else ''


def daily_readme(birthday):
    """
    Returns the length of time since the given birthday.
    e.g. '18 years, 06 months, 09 days'
    """
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    return '{} {}, {:02d} {}, {:02d} {}{}'.format(
        diff.years,  'year'  + format_plural(diff.years),
        diff.months, 'month' + format_plural(diff.months),
        diff.days,   'day'   + format_plural(diff.days),
        ' 🎂' if (diff.months == 0 and diff.days == 0) else ''
    )


# -----------------------------
# GitHub Data
# -----------------------------

def user_getter(username):
    query_count('user_getter')
    query = '''
    query($login: String!) {
        user(login: $login) {
            id
            createdAt
        }
    }'''
    r = simple_request('user_getter', query, {'login': username})
    data = r.json()['data']['user']
    if data is None:
        raise Exception(f"user_getter: user '{username}' not found. Check USER_NAME.", QUERY_COUNT)
    return data['id'], data['createdAt']


def follower_getter(username):
    query_count('follower_getter')
    query = '''
    query($login: String!) {
        user(login: $login) {
            followers { totalCount }
        }
    }'''
    r = simple_request('follower_getter', query, {'login': username})
    user = (r.json().get('data') or {}).get('user') or {}
    return int((user.get('followers') or {}).get('totalCount') or 0)


def graph_repos_stars(count_type, owner_affiliation, cursor=None):
    query_count('graph_repos_stars')
    query = '''
    query($owner_affiliation: [RepositoryAffiliation], $login: String!, $cursor: String) {
        user(login: $login) {
            repositories(first: 100, after: $cursor, ownerAffiliations: $owner_affiliation) {
                totalCount
                edges {
                    node {
                        nameWithOwner
                        stargazers { totalCount }
                    }
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }'''
    r = simple_request('graph_repos_stars', query, {
        'owner_affiliation': owner_affiliation,
        'login': USER_NAME,
        'cursor': cursor
    })
    if count_type == 'repos':
        return (r.json()['data']['user'] or {}).get('repositories', {}).get('totalCount', 0) or 0
    elif count_type == 'stars':
        repos = (r.json()['data']['user'] or {}).get('repositories') or {}
        return stars_counter(repos.get('edges') or [])
    raise ValueError(f"graph_repos_stars: unknown count_type '{count_type}'")


def stars_counter(data):
    total = 0
    for edge in data or []:
        try:
            node = (edge or {}).get('node') or {}
            stargazers = node.get('stargazers') or {}
            total += int(stargazers.get('totalCount') or 0)
        except (TypeError, ValueError, AttributeError):
            continue
    return total


# -----------------------------
# LOC (cache-based)
# -----------------------------

def loc_query(owner_affiliation, comment_size=0, force_cache=False, cursor=None, edges=None):
    """
    Queries all repositories and delegates LOC counting to cache_builder.
    Paginates in batches of 60 to avoid 502 timeouts.
    """
    if edges is None:
        edges = []
    query_count('loc_query')
    query = '''
    query($owner_affiliation: [RepositoryAffiliation], $login: String!, $cursor: String) {
        user(login: $login) {
            repositories(first: 60, after: $cursor, ownerAffiliations: $owner_affiliation) {
                edges {
                    node {
                        nameWithOwner
                        defaultBranchRef {
                            target {
                                ... on Commit {
                                    history { totalCount }
                                }
                            }
                        }
                    }
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }'''
    r = simple_request('loc_query', query, {
        'owner_affiliation': owner_affiliation,
        'login': USER_NAME,
        'cursor': cursor
    })
    repos = (r.json()['data'] or {}).get('user') or {}
    repos = repos.get('repositories') or {}
    page = repos.get('pageInfo') or {}
    batch = [e for e in (repos.get('edges') or []) if (e or {}).get('node')]
    if page.get('hasNextPage'):
        edges += batch
        return loc_query(owner_affiliation, comment_size, force_cache,
                         page.get('endCursor'), edges)
    else:
        return cache_builder(edges + batch, comment_size, force_cache)


def cache_builder(edges, comment_size, force_cache, loc_add=0, loc_del=0):
    """
    Checks each repository to see if it has been updated since last cache.
    If it has, runs recursive_loc to update the LOC count.
    """
    cached = True
    os.makedirs('cache', exist_ok=True)
    filename = 'cache/' + hashlib.sha256(USER_NAME.encode('utf-8')).hexdigest() + '.txt'

    try:
        with open(filename, 'r') as f:
            data = f.readlines()
    except FileNotFoundError:
        data = []
        if comment_size > 0:
            for _ in range(comment_size):
                data.append('This line is a comment block. Write whatever you want here.\n')
        with open(filename, 'w') as f:
            f.writelines(data)

    if len(data) - comment_size != len(edges) or force_cache:
        cached = False
        flush_cache(edges, filename, comment_size)
        with open(filename, 'r') as f:
            data = f.readlines()

    cache_comment = data[:comment_size]
    data = data[comment_size:]

    for index in range(len(edges)):
        parts = data[index].split()
        if len(parts) < 2:
            continue
        repo_hash, commit_count = parts[0], parts[1]
        if repo_hash == hashlib.sha256(edges[index]['node']['nameWithOwner'].encode('utf-8')).hexdigest():
            try:
                ref = (edges[index]['node'].get('defaultBranchRef') or {})
                target = (ref.get('target') or {})
                history = (target.get('history') or {})
                total = history.get('totalCount')
                if total is None:
                    raise TypeError('missing history totalCount')
                if int(commit_count) != total:
                    owner, repo_name = edges[index]['node']['nameWithOwner'].split('/', 1)
                    print(f"   updating LOC: {edges[index]['node']['nameWithOwner']}")
                    loc = recursive_loc(owner, repo_name, data, cache_comment)
                    data[index] = (
                        repo_hash + ' ' +
                        str(total) + ' ' +
                        str(loc[2]) + ' ' + str(loc[0]) + ' ' + str(loc[1]) + '\n'
                    )
            except (TypeError, KeyError, ValueError, AttributeError):
                data[index] = repo_hash + ' 0 0 0 0\n'

    with open(filename, 'w') as f:
        f.writelines(cache_comment)
        f.writelines(data)

    for line in data:
        loc = line.split()
        if len(loc) < 5:
            continue
        try:
            loc_add += int(loc[3])
            loc_del += int(loc[4])
        except ValueError:
            continue

    return [loc_add, loc_del, loc_add - loc_del, cached]


def flush_cache(edges, filename, comment_size):
    """
    Wipes the cache file and writes a blank entry for each repo.
    """
    with open(filename, 'r') as f:
        data = []
        if comment_size > 0:
            data = f.readlines()[:comment_size]
    with open(filename, 'w') as f:
        f.writelines(data)
        for node in edges:
            f.write(hashlib.sha256(node['node']['nameWithOwner'].encode('utf-8')).hexdigest() + ' 0 0 0 0\n')


def force_close_file(data, cache_comment):
    """
    Saves the cache file before a crash to avoid data loss.
    """
    filename = 'cache/' + hashlib.sha256(USER_NAME.encode('utf-8')).hexdigest() + '.txt'
    with open(filename, 'w') as f:
        f.writelines(cache_comment)
        f.writelines(data)
    print('Error during cache write. Partial data saved to', filename)


def recursive_loc(owner, repo_name, data, cache_comment, addition_total=0, deletion_total=0, my_commits=0, cursor=None):
    """
    Paginates through 100 commits at a time via GraphQL and counts
    only additions/deletions from commits authored by OWNER_ID.
    """
    query_count('recursive_loc')
    query = '''
    query($repo_name: String!, $owner: String!, $cursor: String) {
        repository(name: $repo_name, owner: $owner) {
            defaultBranchRef {
                target {
                    ... on Commit {
                        history(first: 100, after: $cursor) {
                            totalCount
                            edges {
                                node {
                                    ... on Commit {
                                        committedDate
                                    }
                                    author {
                                        user { id }
                                    }
                                    deletions
                                    additions
                                }
                            }
                            pageInfo {
                                endCursor
                                hasNextPage
                            }
                        }
                    }
                }
            }
        }
    }'''
    r = requests.post(
        'https://api.github.com/graphql',
        json={'query': query, 'variables': {'repo_name': repo_name, 'owner': owner, 'cursor': cursor}},
        headers=HEADERS
    )
    if r.status_code == 200:
        repo = r.json()['data']['repository']
        if repo is None or repo.get('defaultBranchRef') is None:
            return 0, 0, 0
        return loc_counter_one_repo(
            owner, repo_name, data, cache_comment,
            repo['defaultBranchRef']['target']['history'],
            addition_total, deletion_total, my_commits
        )
    force_close_file(data, cache_comment)
    if r.status_code == 403:
        raise Exception('Rate limit hit! Too many requests in a short time.')
    raise Exception('recursive_loc() failed with', r.status_code, r.text, QUERY_COUNT)


def loc_counter_one_repo(owner, repo_name, data, cache_comment, history, addition_total, deletion_total, my_commits):
    """
    Accumulates additions/deletions for commits authored by OWNER_ID.
    Recursively calls recursive_loc if there are more pages.
    """
    for node in history['edges']:
        try:
            author = (node.get('node') or {}).get('author') or {}
            author_user = author.get('user') or {}
            if author_user.get('id') is not None and author_user.get('id') == OWNER_ID:
                my_commits += 1
                addition_total += node['node'].get('additions', 0) or 0
                deletion_total += node['node'].get('deletions', 0) or 0
        except (TypeError, KeyError, AttributeError):
            continue

    if history['edges'] == [] or not history['pageInfo']['hasNextPage']:
        return addition_total, deletion_total, my_commits
    else:
        return recursive_loc(owner, repo_name, data, cache_comment,
                             addition_total, deletion_total, my_commits,
                             history['pageInfo']['endCursor'])


def commit_counter(comment_size):
    """
    Reads total commits from the cache file.
    """
    filename = 'cache/' + hashlib.sha256(USER_NAME.encode('utf-8')).hexdigest() + '.txt'
    with open(filename, 'r') as f:
        data = f.readlines()
    data = data[comment_size:]
    total = 0
    for line in data:
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            total += int(parts[2])
        except ValueError:
            continue
    return total


# -----------------------------
# SVG UPDATE
# -----------------------------

def justify_format(root, element_id, new_text, length=0):
    if isinstance(new_text, int):
        new_text = '{:,}'.format(new_text)
    new_text = str(new_text)
    find_and_replace(root, element_id, new_text)
    # dots are intentionally not touched — preserve original SVG formatting


def find_and_replace(root, element_id, new_text):
    el = root.find(f".//*[@id='{element_id}']")
    if el is not None:
        el.text = new_text


def svg_overwrite(filename, age_data, commit_data, star_data, repo_data, contrib_data, follower_data, loc_data):
    tree = etree.parse(filename)
    root = tree.getroot()
    justify_format(root, 'age_data',      age_data)
    justify_format(root, 'commit_data',   commit_data)
    justify_format(root, 'star_data',     star_data)
    justify_format(root, 'repo_data',     repo_data)
    justify_format(root, 'contrib_data',  contrib_data)
    justify_format(root, 'follower_data', follower_data)
    justify_format(root, 'total_loc',     loc_data[2])   # loc_add - loc_del
    justify_format(root, 'loc_add',       loc_data[0])
    justify_format(root, 'loc_del',       loc_data[1])
    tree.write(filename, encoding='utf-8', xml_declaration=True)


# -----------------------------
# MAIN
# -----------------------------

if __name__ == '__main__':

    if not ACCESS_TOKEN:
        print("Error: ACCESS_TOKEN environment variable is not set.", file=sys.stderr)
        print("Set it via GitHub Actions secrets or: export ACCESS_TOKEN=<token>", file=sys.stderr)
        sys.exit(1)

    print('Calculation times:')

    user_data, user_time = perf_counter(user_getter, USER_NAME)
    OWNER_ID, acc_date = user_data
    print('   account data:      %.4f s' % user_time)

    age_data, age_time = perf_counter(daily_readme, datetime.datetime(2007, 11, 5))
    print('   age calculation:   %.4f s' % age_time)

    follower_data, follower_time = perf_counter(follower_getter, USER_NAME)
    print('   followers:         %.4f s' % follower_time)

    total_loc, loc_time = perf_counter(loc_query, ['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER'], 7)
    label = 'LOC (cached)' if total_loc[-1] else 'LOC (no cache)'
    print(f'   {label}:   %.4f s' % loc_time)

    commit_data, commit_time = perf_counter(commit_counter, 7)
    print('   commits:           %.4f s' % commit_time)

    star_data, star_time = perf_counter(graph_repos_stars, 'stars', ['OWNER'])
    print('   stars:             %.4f s' % star_time)

    repo_data, repo_time = perf_counter(graph_repos_stars, 'repos', ['OWNER'])
    print('   repos:             %.4f s' % repo_time)

    contrib_data, contrib_time = perf_counter(
        graph_repos_stars, 'repos', ['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER']
    )
    print('   contrib repos:     %.4f s' % contrib_time)

    for index in range(len(total_loc) - 1):
        total_loc[index] = '{:,}'.format(total_loc[index])

    for svg in ('dark_mode.svg', 'light_mode.svg'):
        svg_overwrite(svg, age_data, commit_data, star_data, repo_data, contrib_data, follower_data, total_loc[:-1])

    print('\nSVG updated successfully')
    print('Total GitHub GraphQL API calls:', sum(QUERY_COUNT.values()))
    for name, count in QUERY_COUNT.items():
        print(f'   {name}: {count}')
