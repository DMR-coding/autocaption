import click
from google.cloud import storage, speech
from google.protobuf.duration_pb2 import Duration
from os import path, stat, remove
from uuid import uuid4
import subprocess
from contextlib import contextmanager
import errno
from pysubs2 import SSAFile, SSAEvent
from pysubs2.formats import FORMAT_IDENTIFIERS, get_file_extension
import datetime

BUCKET_NAME = "voice-recognition-staging"
TEMP_SUFFIX = ".flac.tmp"
SAMPLE_RATE = 24000


@click.command()
@click.argument(
    "av_path",
    required=True,
    type=click.Path(exists=True),
)
@click.option("--language", "-l", default="en-US")
@click.option("--format", "-f", type=click.Choice(FORMAT_IDENTIFIERS), default="srt")
def main(av_path: str, language: str, format: str):
    bucket = storage.Client().get_bucket(BUCKET_NAME)

    with get_working_file(av_path) as (file_obj, working_path, size_mib):
        print(f"Uploading media ({round(size_mib, 2)}MiB)")

        staged_file_name = f"{path.basename(working_path)}-{uuid4()}"

        blob = storage.Blob(staged_file_name, bucket)
        blob.upload_from_file(file_obj)

        print("Upload complete. Beginning transcription...")

        response = recognize_blob(f"gs://{BUCKET_NAME}/{staged_file_name}", language)

        subtitles = to_subtitles(response)

        subtitle_path = f"{av_path}{get_file_extension(format)}"

        subtitles.save(subtitle_path, format=format)
        print(f"Done. Output to {subtitle_path}")


def to_subtitles(response):
    subtitles = SSAFile()
    subtitles.events = [
        SSAEvent(
            text=result.alternatives[0].transcript,
            start=duration_to_ms(result.alternatives[0].words[0].start_time),
            end=duration_to_ms(result.alternatives[0].words[-1].end_time),
        )
        for result in response.results
    ]

    return subtitles


def duration_to_ms(d: datetime.timedelta) -> int:
    return int(d.total_seconds() * 1000)


def recognize_blob(uri: str, language: str):
    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(uri=uri)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
        sample_rate_hertz=SAMPLE_RATE,
        language_code=language,
        enable_word_time_offsets=True,
        enable_automatic_punctuation=True,
        max_alternatives=1,
    )
    operation = client.long_running_recognize(config=config, audio=audio)

    print("Waiting for operation to complete...")
    return operation.result()  # Blocking


@contextmanager
def get_working_file(original_path: str):
    temp_path = original_path + TEMP_SUFFIX
    try:
        print("transcoding")

        # Transcribe to:
        # audio only (-vn -sn), flac codec (-c:a), flac container (-f), fixed sample rate (-ar), mono (-ac 1)
        subprocess.run(
            f"ffmpeg -i '{original_path}' -vn -sn -c:a flac -f flac -ar {SAMPLE_RATE} -ac 1 '{temp_path}'",
            shell=True,
        )

        with open(temp_path, "rb") as file:
            yield file, temp_path, stat(temp_path).st_size / 1024 / 1024
    finally:
        try:
            remove(temp_path)
        except OSError as e:
            if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
                raise


if __name__ == "__main__":
    # execute only if run as a script
    main()
