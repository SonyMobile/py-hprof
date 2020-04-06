# Contributing
Contributions in all forms are welcome!

## Reporting bugs and suggesting features
Submit a bug report on the [issue tracker](https://github.com/SonyMobile/py-hprof/issues).

When reporting a bug, please include:
* your library version (available as `hprof.version`)
* a thorough explanation of the problem
* stacktraces or error prints, if applicable
* the behavior you expect

If you are able to provide test cases, please do.

### Before sharing .hprof files

Remember that .hprof files may contain sensitive information. As such, you should probably not post them publicly unless you are very sure that they don't.

If you are able to create an artificial .hprof file showing the same problem, please share it. If not, a project developer may be able to do it. In some cases, we may need you to trust us and share the file privately with a developer.

## Contributing code
### Tests
Tests can be executed by running `run_tests.sh`.

Unit tests are placed in the `test/unit` folder, and should test small components of the library. py-hprof should have 100% coverage by unit tests.

Acceptance tests are placed in the `test/accept` folder, and should test that the library can properly open and parse a file, and that it provides the functionality that we want.

When fixing a bug or adding a feature, you will definitely need to add a unit test. Acceptance tests are less common.

### Code style
Tabs, not spaces -- except when indenting to align with other text.

Each commit should do one thing. Smaller commits are easier to review.

### Commit messages
Describe what you did, why you did it, and why you did it the way you did.

Add an `Issue: #XYZ` tag at the end to indicate which issue the commit is related to.

You may add other tags at the end of your commit message. Please use tags like `Suggested-by`, `Analyzed-by`, `Co-authored-by`, `Tested-by` or others to credit anyone you feel contributed to the patch. It's not hard, and it makes people feel appreciated!

Run `git config commit.template git_commit_msg_template` to start with a convenient template on commit.

Including the `Soundtrack` tag is strongly encouraged. It can be what you listened to when writing the commit message, while writing the patch, or just something you've been digging a lot lately.
