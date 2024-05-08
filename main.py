"""
A parse for Apple Event

The script downloads all subtitles and audio tracks, as well as the highest quality video,
and finally merge everything into a MKV file.
"""

import os

import ffmpy
import m3u8
from tabulate import tabulate


def parse_m3u8(url):
    """
    Parse the provided m3u8 playlist from URI provided

    :param url: The URI to m3u8 playlist of the Apple Event
    :return: A dictionary containing subtitle, audio tracks and video URLs
    :raise Exception: When URI is not provided
    """

    if url is None:
        raise Exception("A URI must be provided!")

    print("Parsing the URI: " + url)
    playlist = m3u8.load(url)

    audio_tracks = []
    subtitles = []
    videos = []

    # Parse subtitles and audio tracks - they're usually in media section
    for media_index, media_item in enumerate(playlist.media):
        if media_item.type == "SUBTITLES":
            subtitles.append({
                "uri": media_item.uri,
                "name": media_item.name,
                "language": media_item.language,
                "default": (media_item.language == 'en'),
                "file_name": "subtitle_{0}.{1}".format(media_index, "vtt")
            })
        elif media_item.type == "AUDIO":
            # Determine the encoding type and extension in filename
            if "aac" in media_item.group_id:
                file_extension = 'aac'
            elif "eac3" in media_item.group_id:
                file_extension = 'eac3'
            else:
                raise Exception("Unsupported audio type: " + media_item.group_id)

            audio_tracks.append({
                "uri": media_item.uri,
                "name": media_item.name,
                "language": media_item.language,
                "group_id": media_item.group_id,
                "characteristics": media_item.characteristics,
                "default": (
                        media_item.language == "en" and
                        media_item.group_id.startswith("audio-stereo") and
                        media_item.characteristics is None
                ),
                "file_name": "audio_{0}.{1}".format(media_index, file_extension)
            })

    # Print the quality matrix and let user choose which stream to download
    video_streams_info = []
    for video_index, video_stream in enumerate(playlist.playlists):
        video_streams_info.append([
            video_index,
            video_stream.stream_info.audio,
            video_stream.stream_info.average_bandwidth,
            video_stream.stream_info.bandwidth,
            video_stream.stream_info.closed_captions or "None",
            video_stream.stream_info.codecs,
            video_stream.stream_info.frame_rate,
            video_stream.stream_info.hdcp_level or "None",
            video_stream.stream_info.pathway_id or "None",
            video_stream.stream_info.program_id or "None",
            'x'.join(map(str, video_stream.stream_info.resolution)),
            video_stream.stream_info.stable_variant_id or "None",
            video_stream.stream_info.subtitles,
            video_stream.stream_info.video or "None",
            video_stream.stream_info.video_range,
        ])

    print("\nStreams available: ")
    print(tabulate(video_streams_info, headers=[
        'index',
        'audio',
        'average_bandwidth',
        'bandwidth',
        'closed_captions',
        'codecs',
        'frame_rate',
        'hdcp_level',
        'pathway_id',
        'program_id',
        'resolution',
        'stable_variant_id',
        'subtitles',
        'video',
        'video_range',
    ], tablefmt='github'))
    print("\n\nEnter indexes which its video stream will be downloaded, separated by plus-signs ('+'). ")
    print("The first video stream will be used as the main video stream at the time of merge. ")
    video_stream_indexes = input("Enter indexes: ") or None

    # Collect selected video streams
    for seq, video_index in enumerate(video_stream_indexes.split('+')):
        current_stream = playlist.playlists[int(video_index)]
        videos.append({
            "uri": current_stream.uri,
            "codec": "{0} ({1})".format(
                current_stream.stream_info.video_range,
                current_stream.stream_info.codecs.split(",")[0]
            ),
            "default": (seq is 0),
            "file_name": "video_{0}.{1}".format(video_index, "ts")
        })

    return {
        "audio_tracks": audio_tracks,
        "subtitles": subtitles,
        "videos": videos
    }


def download_with_ffmpeg(audio_tracks, subtitles, videos):
    """
    Download individual components with FFMPEG

    :param audio_tracks: A dictionary of all available audio tracks
    :param subtitles: A dictionary of all available subtitles
    :param videos: A dictionary of all selected video sources
    :return: None
    :raise Exception: If the audio type or characteristics is not recognized
    """

    # Download audio tracks
    for audio_track in audio_tracks:
        filename = os.path.join(
            "downloads",
            audio_track['file_name']
        )

        ff_audio = ffmpy.FFmpeg(
            inputs={audio_track['uri']: None},
            outputs={filename: ['-c', 'copy']}
        )

        print("Executing: " + ff_audio.cmd)
        ff_audio.run()

    # Download subtitles
    for subtitle in subtitles:
        filename = os.path.join(
            "downloads",
            subtitle['file_name']
        )

        ff_subtitle = ffmpy.FFmpeg(
            inputs={subtitle['uri']: None},
            outputs={filename: ['-c', 'copy']}
        )

        print("Executing: " + ff_subtitle.cmd)
        ff_subtitle.run()

    # Download the video
    for video in videos:
        filename = os.path.join(
            "downloads",
            video['file_name']
        )

        ff_video = ffmpy.FFmpeg(
            inputs={video['uri']: None},
            outputs={filename: ['-c', 'copy']}
        )

        print("Executing: " + ff_video.cmd)
        ff_video.run()


def merge_as_mkv(audio_tracks, subtitles, videos):
    """
    Merge all files downloaded into MKV format with necessary language labels and names

    :param audio_tracks: A dictionary of all available audio tracks
    :param subtitles: A dictionary of all available subtitles
    :param videos: A dictionary of all selected video sources
    :return: None
    """

    # Initialize mkvmerge command line arguments and add the video file
    cmd_args = [
        "mkvmerge",
        "--output output.mkv",
    ]

    # Add video tracks
    for video in videos:
        cmd_args.append("--language 0:en")
        cmd_args.append("--track-name '0:{0}'".format(video['codec']))
        # Set non default-track flag
        if video['default'] is False:
            cmd_args.append("--default-track-flag 0:no")
        cmd_args.append(os.path.join('downloads', video['file_name']))

    # Add audio tracks
    for audio_track in audio_tracks:
        cmd_args.append("--language 0:{0}".format(audio_track['language']))
        cmd_args.append("--track-name '0:{0}'".format(
            audio_track['name'] +
            (" (Dolby Atmos)" if "eac3" in audio_track['group_id'] else "")  # Add Dolby Atmos signature in name
        ))
        # Set non default-track flag
        if audio_track['default'] is False:
            cmd_args.append("--default-track-flag 0:no")
        # Set visual-impaired flag
        if audio_track['characteristics'] is not None and "describes-video" in audio_track['characteristics']:
            cmd_args.append("--visual-impaired-flag 0:yes")
        cmd_args.append(os.path.join('downloads', audio_track['file_name']))

    # Add subtitles
    for subtitle in subtitles:
        cmd_args.append("--language 0:{0}".format(subtitle['language']))
        cmd_args.append("--track-name '0:{0}'".format(subtitle['name']))
        # Set non default-track flag
        if subtitle['default'] is False:
            cmd_args.append("--default-track-flag 0:no")
        cmd_args.append(os.path.join('downloads', subtitle['file_name']))

    # Execute mkvmerge command with arguments
    print("Execute the following command to generate MKV file: \n{0}".format(' '.join(cmd_args)))


if __name__ == '__main__':
    print("Apple Event Video High-quality Downloader")
    print("The target URL should look something like: ")
    print("https://events-delivery.apple.com/random_string/m3u8/vod_index-random_string.m3u8")
    event_url = input("Enter the m3u8 URI: ") or None

    # Parse the M3U8 playlist
    parsed = parse_m3u8(event_url)
    # Download individual components
    download_with_ffmpeg(parsed['audio_tracks'], parsed['subtitles'], parsed['videos'])
    # Merge the files in to MKV
    merge_as_mkv(parsed['audio_tracks'], parsed['subtitles'], parsed['videos'])
