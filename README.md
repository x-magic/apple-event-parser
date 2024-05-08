# apple-event-parser
A Python parser for vod m3u8 files from [apple.com/apple-events](https://apple.com/apple-events)

<!-- TOC -->
* [Usage](#usage)
* [How it works?](#how-it-works)
* [License](#license)
* [Acknowledgement](#acknowledgement)
<!-- TOC -->

## Usage
- Create a virtual env (optional)
- Install required packages with `pip install -r /path/to/requirements.txt`
- Run the script `python main.py` and follow on-screen instructions
- ???
- PROFIT!

## How it works?
It will parse and download all audio tracks (both stereo and Dolby Atmos, as well as normal and AD version in most cases) and subtitles (in all languages), alongside any video tracks you'd like (you can choose from whatever is available from the stream and any combination of it), and finally it will generate mkvmerge commands to help you mux all files into a MKV container for ease of mind. 

Now that Apple Events are also offered in SDR, HDR10 and Dolby Vision, you can choose to mux the best track in all 3 flavours and switch on demand. 

## License
See [LICENSE](LICENSE)

## Acknowledgement
- [Apple Events](https://apple.com/apple-events)
- [m3u8](https://pypi.org/project/m3u8/)
- [ffmpy](https://pypi.org/project/ffmpy/)
- [tabulate](https://pypi.org/project/tabulate/)