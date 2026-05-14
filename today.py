import datetime
from dateutil import relativedelta
import requests
import os
from lxml import etree
import time

HEADERS = {
    'authorization': 'Bearer ' + os.environ['ACCESS_TOKEN']
}

USER_NAME = "MrTrotid"

QUERY_COUNT = {
    'user_getter': 0,
    'follower_getter': 0,
    'graph_repos_stars': 0,
    'graph_loc_and_commits': 0
}


# -----------------------------
# Helpers
# -----------------------------

def query_count(name):
    QUERY_COUNT[name] += 1


def simple_request(func_name, query, variables):
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=HEADERS
    )

    if r.status_code == 200:
        return r

    raise Exception(f"{func_name} failed: {r.status_code} {r.text}")


def perf_counter(func, *args):
    start = time.perf_counter()
    result = func(*args)
    return result, time.perf_counter() - start


def format_plural(n):
    return "s" if n != 1 else ""


# -----------------------------
# GitHub Data
# -----------------------------

def user_getter(username):
    query_count("user_getter")

    query = """
    query($login: String!) {
        user(login: $login) {
            id
            createdAt
        }
    }
    """

    r = simple_request(
        "user_getter",
        query,
        {"login": username}
    )

    data = r.json()["data"]["user"]

    return {"id": data["id"]}, data["createdAt"]


def follower_getter(username):
    query_count("follower_getter")

    query = """
    query($login: String!) {
        user(login: $login) {
            followers {
                totalCount
            }
        }
    }
    """

    r = simple_request(
        "follower_getter",
        query,
        {"login": username}
    )

    return int(
        r.json()["data"]["user"]["followers"]["totalCount"]
    )


def graph_repos_stars(count_type, affiliations):
    query_count("graph_repos_stars")

    query = """
    query($login: String!, $aff: [RepositoryAffiliation]) {
        user(login: $login) {
            repositories(first: 100, ownerAffiliations: $aff) {
                totalCount
                edges {
                    node {
                        stargazers { totalCount }
                    }
                }
            }
        }
    }
    """

    r = simple_request(
        "graph_repos_stars",
        query,
        {
            "login": USER_NAME,
            "aff": affiliations
        }
    )

    repos = r.json()["data"]["user"]["repositories"]

    stars = sum(
        n["node"]["stargazers"]["totalCount"]
        for n in repos["edges"]
    )

    if count_type == "stars":
        return stars

    return repos["totalCount"]


def graph_loc_and_commits(affiliations):
    query_count("graph_loc_and_commits")

    query = """
    query($login: String!, $aff: [RepositoryAffiliation]) {
        user(login: $login) {
            repositories(first: 100, ownerAffiliations: $aff) {
                edges {
                    node {
                        defaultBranchRef {
                            target {
                                ... on Commit {
                                    history { totalCount }
                                }
                            }
                        }
                        languages(first: 20) {
                            edges { size }
                        }
                    }
                }
            }
        }
    }
    """

    r = simple_request(
        "graph_loc_and_commits",
        query,
        {
            "login": USER_NAME,
            "aff": affiliations
        }
    )

    repos = r.json()["data"]["user"]["repositories"]

    total_loc = 0
    total_commits = 0

    for repo in repos["edges"]:
        node = repo["node"]

        try:
            total_commits += node["defaultBranchRef"]["target"]["history"]["totalCount"]
        except:
            pass

        try:
            for lang in node["languages"]["edges"]:
                total_loc += lang["size"]
        except:
            pass

    return total_loc, total_commits


# -----------------------------
# SVG UPDATE (FIXED)
# -----------------------------

def find_and_replace(root, element_id, text):
    el = root.find(f".//*[@id='{element_id}']")
    if el is not None:
        el.text = str(text)


def justify_format(root, element_id, new_text, *_):
    """
    ONLY updates numbers. NO formatting, NO dots, NO layout logic.
    """

    if isinstance(new_text, int):
        new_text = f"{new_text:,}"

    el = root.find(f".//*[@id='{element_id}']")

    if el is not None:
        el.text = str(new_text)


def svg_overwrite(
    filename,
    age_data,
    commit_data,
    star_data,
    repo_data,
    contrib_data,
    follower_data,
    total_loc
):

    tree = etree.parse(filename)
    root = tree.getroot()

    justify_format(root, "commit_data", commit_data)
    justify_format(root, "star_data", star_data)
    justify_format(root, "repo_data", repo_data)
    justify_format(root, "contrib_data", contrib_data)
    justify_format(root, "follower_data", follower_data)

    justify_format(root, "total_loc", total_loc)

    tree.write(filename, encoding="utf-8", xml_declaration=True)


# -----------------------------
# MAIN
# -----------------------------

if __name__ == "__main__":

    print("Calculation times:")

    user_data, t = perf_counter(user_getter, USER_NAME)
    print("   account data:", round(t, 4), "s")

    follower_data, t = perf_counter(follower_getter, USER_NAME)
    print("   followers:", round(t, 4), "s")

    stats_data, t = perf_counter(
        graph_loc_and_commits,
        ["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"]
    )

    total_loc, commit_data = stats_data
    print("   github stats:", round(t, 4), "s")

    star_data, _ = perf_counter(
        graph_repos_stars,
        "stars",
        ["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"]
    )

    repo_data, _ = perf_counter(
        graph_repos_stars,
        "repos",
        ["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"]
    )

    contrib_data = repo_data

    svg_overwrite(
        "dark_mode.svg",
        None,
        commit_data,
        star_data,
        repo_data,
        contrib_data,
        follower_data,
        total_loc
    )

    svg_overwrite(
        "light_mode.svg",
        None,
        commit_data,
        star_data,
        repo_data,
        contrib_data,
        follower_data,
        total_loc
    )

    print("\nSVG updated successfully")
    print("Total API calls:", sum(QUERY_COUNT.values()))
