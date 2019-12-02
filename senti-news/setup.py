import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="senti-news",
    version="0.0.12",
    author="Nicholas Broad",
    author_email="nicholas@nmbroad.com",
    description="News title sentiment analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nbroad1881/senti-news",
    packages=setuptools.find_packages(),
    package_dir={'':'src'},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)