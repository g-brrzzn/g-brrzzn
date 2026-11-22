"""Fetches contribution history and public language stats into tools/profile/data.

Token: PROFILE_TOKEN (classic PAT with read:user, counts private contributions)
       or GITHUB_TOKEN (public contributions only).
"""
import json, os, sys, urllib.request

USER = os.environ.get("PROFILE_USER", "g-brrzzn")
TOKEN = os.environ.get("PROFILE_TOKEN") or os.environ.get("GITHUB_TOKEN")
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def gql(query, **variables):
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers={"Authorization": f"bearer {TOKEN}", "User-Agent": "profile-renderer"})
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if out.get("errors"):
        sys.exit(f"GraphQL error: {out['errors']}")
    return out["data"]


def main():
    if not TOKEN:
        sys.exit("Set GITHUB_TOKEN or PROFILE_TOKEN")
    os.makedirs(DATA, exist_ok=True)
    u = gql("""query($u:String!){user(login:$u){createdAt followers{totalCount}
      contributionsCollection{contributionYears}}}""", u=USER)["user"]
    days = set()
    for y in u["contributionsCollection"]["contributionYears"]:
        c = gql("""query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){contributionsCollection(from:$f,to:$t){
          contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}""",
                u=USER, f=f"{y}-01-01T00:00:00Z", t=f"{y}-12-31T23:59:59Z")
        for w in c["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            days.update((d["date"], d["contributionCount"]) for d in w["contributionDays"])
    # public, non-fork repos you own: same source as github-readme-stats
    pub = gql("""query($u:String!){user(login:$u){repositories(ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC,first:100){
      nodes{name stargazerCount languages(first:20){edges{size node{name}}}}}}}""", u=USER)
    json.dump({"data": pub}, open(os.path.join(DATA, "pub.json"), "w"))
    json.dump(dict(days=sorted(days), followers=u["followers"]["totalCount"], created=u["createdAt"]),
              open(os.path.join(DATA, "profile.json"), "w"))
    print(f"{len(days)} days, {sum(n for _, n in days)} contributions")


if __name__ == "__main__":
    main()
