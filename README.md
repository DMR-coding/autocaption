# autocaption
Automatically transcribe audio/visual files to a variety of subtitle formats.

## Prerequisites
The user is responsible for providing a working Python environment for this application. If you need help with this step, see [the PythonWiki beginner's guide](https://wiki.python.org/moin/BeginnersGuide/Download).

Additionally, this application relies on `ffmpeg` (specifically, `ffplay`) to play audio at the command line. The user is responsible
for ensuring this utility is installed and on the `PATH`.

Unfortunately, google-cloud is a developer-oriented experience, so the following steps are pretty technical.
* Set up a google cloud account.
* Activate the speech and cloud storage APIs.
* Create a cloud storage bucket named `voice-recognition-staging`.
  * Highly recommended: Set a lifecycle management policy to delete objects in this bucket after 1 day.
* Set up credentials on your system.

## Installing
At the command line, type `pip install autocaption`.

## Using
`autocaption path/to/audio/or/video`.
* By default, the tool will assume US English. To specify another language code, use `--language`. See [Supported Languages](https://cloud.google.com/speech-to-text/docs/languages) on the Google API documentation for a list of available language codes.
* By default, the tool will output SubRip formatted captions. For other options, use `--format`

## Developing
Environment and prerequisites are managed by `poetry`. See https://python-poetry.org/docs/#installation to get started with poetry.

* To create an environment and install prerequisites, run `poetry install` in the top level of the repository.
* Invoke the application with `poetry run autocaption`.
* Build packages with `poetry build`.

