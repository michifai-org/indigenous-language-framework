# Tools

Scripts here are plain Python (3.8 or newer) with no installation step. They run on your own computer, read only the folder you point them at, and send nothing anywhere.

## validate_content.py

Checks a content folder against the schema (see [schema/README.md](../schema/README.md)).

```
python tools/validate_content.py YOUR_CONTENT_FOLDER          # check
python tools/validate_content.py YOUR_CONTENT_FOLDER --strict # warnings count as failures
python tools/validate_content.py YOUR_CONTENT_FOLDER --check-files   # also check audio files exist
python tools/validate_content.py --init NEW_FOLDER            # create blank tables to fill in
```

Optional: `pip install pyyaml` lets it also check `community.yaml`.

## test_validate_content.py

Tests for the checker, using the fictional demo. Run from the repository root:

```
python tools/test_validate_content.py
```

## Not here yet

The builder scripts (content in; lesson pages, flashcards and printable PDFs out) come next, once the schema has been tried against real material.
