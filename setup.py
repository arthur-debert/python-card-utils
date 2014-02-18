from distutils.core import setup

version = "0.1"

setup(
    name="cardutils",
    version=version,
    description="Utilities for (credit) card numbers.",
    long_description="""
        Contains functions for checking, analysing and
        generating random card numbers. The random card
        numbers appear valid at first glance (they have
        valid issuers and checksum digits).
    """,
    author="Henry Bucklow",
    author_email="hb@elsie.org.uk",
    maintainer="Henry Bucklow",
    maintainer_email="hb@elsie.org.uk",
    url="http://elsie.org.uk/bits",
    download_url="http://elsie.org.uk/files/cardutils-"+version+".zip",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
    ],
    packages=["cardutils"],
    data_files=[
        ("share/cardutils", [
            "cardData.xml"
        ]),
    ]
)
