import datetime
from dateutil import relativedelta
import requests
import os
from lxml import etree
import time
import hashlib

HEADERS = {'authorization': 'Bearer ' + os.environ['ACCESS_TOKEN']}
USER_NAME = "MrTrotid"
OWNER_ID = None  # set after user_getter runs

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
    return {'id': data['id']}, data['createdAt']


def follower_getter(username):
    query_count('follower_getter')
    query = '''
    query($login: String!) {
        user(login: $login) {
            followers { totalCount }
        }
    }'''
    r = simple_request('follower_getter', query, {'login': username})
    return int(r.json()['data']['user']['followers']['totalCount'])


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
        return r.json()['data']['user']['repositories']['totalCount']
    elif count_type == 'stars':
        return stars_counter(r.json()['data']['user']['repositories']['edges'])


def stars_counter(data):
    total = 0
    for node in data:
        total += node['node']['stargazers']['totalCount']
    return total


# -----------------------------
# LOC (cache-based)
# -----------------------------

def loc_query(owner_affiliation, comment_size=0, force_cache=False, cursor=None, edges=[]):
    """
    Queries all repositories and delegates LOC counting to cache_builder.
    Paginates in batches of 60 to avoid 502 timeouts.
    """
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
    repos = r.json()['data']['user']['repositories']
    if repos['pageInfo']['hasNextPage']:
        edges += repos['edges']
        return loc_query(owner_affiliation, comment_size, force_cache,
                         repos['pageInfo']['endCursor'], edges)
    else:
        return cache_builder(edges + repos['edges'], comment_size, force_cache)


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
        repo_hash, commit_count, *__ = data[index].split()
        if repo_hash == hashlib.sha256(edges[index]['node']['nameWithOwner'].encode('utf-8')).hexdigest():
            try:
                if int(commit_count) != edges[index]['node']['defaultBranchRef']['target']['history']['totalCount']:
                    owner, repo_name = edges[index]['node']['nameWithOwner'].split('/')
                    print(f"   updating LOC: {edges[index]['node']['nameWithOwner']}")
                    loc = recursive_loc(owner, repo_name, data, cache_comment)
                    data[index] = (
                        repo_hash + ' ' +
                        str(edges[index]['node']['defaultBranchRef']['target']['history']['totalCount']) + ' ' +
                        str(loc[2]) + ' ' + str(loc[0]) + ' ' + str(loc[1]) + '\n'
                    )
            except TypeError:
                data[index] = repo_hash + ' 0 0 0 0\n'

    with open(filename, 'w') as f:
        f.writelines(cache_comment)
        f.writelines(data)

    for line in data:
        loc = line.split()
        loc_add += int(loc[3])
        loc_del += int(loc[4])

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
        if r.json()['data']['repository']['defaultBranchRef'] is not None:
            return loc_counter_one_repo(
                owner, repo_name, data, cache_comment,
                r.json()['data']['repository']['defaultBranchRef']['target']['history'],
                addition_total, deletion_total, my_commits
            )
        else:
            return 0
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
        if node['node']['author']['user'] == OWNER_ID:
            my_commits += 1
            addition_total += node['node']['additions']
            deletion_total += node['node']['deletions']

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
    return sum(int(line.split()[2]) for line in data)


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
