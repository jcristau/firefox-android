#!/usr/bin/env python3

import json
import logging
from pathlib import Path


log = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)

DATA_DIR = (Path(__file__).parent / "data").absolute()
GITHUB_URL_TEMPLATE = "https://github.com/{repo_owner}/{repo_name}/{number_type}"
REPO_OWNER = "mozilla-mobile"
REPO_NAME_TO_IMPORT = "firefox-android"


def divide_chunks(sequence, n):
    for i in range(0, len(sequence), n):
        yield sequence[i : i + n]


def order_repo_names(repo_names):
    ordered_list = list(repo_names)
    ordered_list.remove(REPO_NAME_TO_IMPORT)
    # The regex of the repo to import may take precedence over other regexes.
    # Running them last makes sure the other URLs got replaced first.
    ordered_list.append(REPO_NAME_TO_IMPORT)
    return ordered_list


def main():
    with open(DATA_DIR / "repo-numbers.json") as f:
        repo_numbers = json.load(f)

    # fix up wrong replacements from previous migrations
    regexes = [
        # restore branch names
        r"regex:(Merge .*branch '.*' into .*)https://github.com/mozilla-mobile/[a-z-]*/(pull|issues)/(.*)==>\1#\3",
        # remove extra prefix
        r"regex:mozilla-mobilehttps:==>https:",
        # restore github references to other repos
        r"regex:perf-frontend-issueshttps://github.com/mozilla-mobile/fenix/(pull|issues)/([0-9]*):==>https://github.com/mozilla-mobile/perf-frontend-issues/issues/\2",
        r"regex:mozilla/glean-dictionaryhttps://github.com/mozilla-mobile/fenix/pull/([0-9]*)==>https://github.com/mozilla/glean-dictionary/issues/\1",
        r"regex:mozilla/glean_parserhttps://github.com/mozilla-mobile/android-components/issues/([0-9]*)==>https://github.com/mozilla/glean_parser/issues/\1",
        r"regex:mozilla/application-serviceshttps://github.com/mozilla-mobile/android-components/(issues|pull)/==>https://github.com/mozilla/application-services/issues/",
        "literal:robolectric/robolectrichttps://github.com/mozilla-mobile/android-components/pull/5496==>https://github.com/robolectric/robolectric/issues/5496",
        "literal:AChttps://github.com/mozilla-mobile/fenix/issues/10231==>https://github.com/mozilla-mobile/android-components/issues/10231",
        "literal:AC#https://github.com/mozilla-mobile/fenix/pull/9024==>https://github.com/mozilla-mobile/android-components/pull/9024",
        "literal:AChttps://github.com/mozilla-mobile/fenix/issues/3695==>https://github.com/mozilla-mobile/android-components/issues/3695",
        "regex:(mozilla-l10n/focus-android-l10n)https://github.com/mozilla-mobile/focus-android/issues/==>https://github.com/\1/pull/",
        # separate link from previous word
        r"regex:(closes|For|Bug|issue|Issue)(https:)==>\1 \2",
        "literal:Fixforhttps:==>Fix for https:",
        # non-github links with anchor/line number that got mistaken for an issue/PR
        r"regex:lifecyclehttps://github.com/mozilla-mobile/fenix/pull/2.2.0-rc02==>lifecycle#2.2.0-rc02",
        r"regex:(jsm|java)https://github.com/mozilla-mobile/android-components/(pull|issues)/==>\1#",
        # https://github.com/mozilla-mobile/android-components/commit/6dd40c4e0ac7e15c59b4bffbb0bb7a7eaa34071e got its links messed up, amongst others
        r"regex:\[(@&)?https://github.com/mozilla-mobile/(android-components|fenix|focus-android)/(pull|issues)/([^]]*\]\(https://github)==>[\1#\4",
        r"regex:(\[MRI\] .*\[)https://github.com/mozilla-mobile/android-components/issues/1953==>\1#",
        # code excerpt in a commit message got messed up
        'literal:("https://github.com/mozilla-mobile/android-components/issues/12345"))==>("mozilla-mobile/android-components#12345"))',
        'literal:(" https://github.com/mozilla-mobile/android-components/issues/12345 "))==>(" #12345 "))',
    ]

    for repo_name in order_repo_names(repo_numbers.keys()):
        numbers = repo_numbers[repo_name]
        if repo_name.startswith("$"):
            continue

        for number_type in ("issues", "pulls"):
            for chunk in divide_chunks(numbers[number_type], 100):
                regex = "regex:((({repo_owner}/)?{repo_name}){repo_suffix})#({current_numbers})(\D|$)==>{url}/\\3\\4\n".format(
                    repo_owner=REPO_OWNER,
                    repo_name=f"[{repo_name[0].upper()}{repo_name[0].lower()}]{repo_name[1:]}",
                    repo_suffix=r"|\s" if repo_name == REPO_NAME_TO_IMPORT else "\\s*",
                    current_numbers="|".join(str(number) for number in chunk),
                    url=GITHUB_URL_TEMPLATE.format(
                        repo_owner=REPO_OWNER,
                        repo_name=repo_name,
                        number_type="pull" if number_type == "pulls" else number_type,
                    ),
                )
                regexes.append(regex)

    with open(DATA_DIR / "message-expressions.txt", "w") as f:
        f.write("".join(regexes))


__name__ == "__main__" and main()
