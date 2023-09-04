import shutil
from falinks import resources
from pytest import fixture


@fixture
def tmpfiles(scope="session"):
    return (
        resources / "links" / file
        for file in (
            "links.txt",
            "session_buddy.json",
            "session_buddy_processed.json",
            "telegram.json",
        )
    )


# Adapted From:
# Answer: https://stackoverflow.com/a/32573090
# User: https://stackoverflow.com/users/2108698/steve-saporta
@fixture
def tmpdir(tmp_path, tmpfiles, scope="session"):
    for file in tmpfiles:
        shutil.copy(file, tmp_path / file.name)
    return tmp_path
