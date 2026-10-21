# Demo language (fictional)

This folder shows the shape of a community's content folder. **The language is invented.** It is not based on any real language, community or recording, and it should not be read as an example of how any real language works. Words are made up, and any resemblance to a real word is coincidence.

It is here so you can see what filled-in tables look like, and so the checker has something to test against.

Try it from the repository root:

```
python tools/validate_content.py examples/demo-language
```

You should see no errors. Two small lessons show how the lesson template is filled in. The checker confirms that lesson 2 assumes only what lesson 1 introduced, and that sentences use only words and patterns taught so far.

The rows deliberately include a few loose ends so you can see what the checker reports: a word (`w003`) that no lesson uses, and an audio row pointing at a file that does not exist (run with `--check-files` to see it).

**Your own content never goes in this folder or anywhere in the public repository.** Make your own private copy from the template first (see [PROTOCOLS.md](../../PROTOCOLS.md)).
