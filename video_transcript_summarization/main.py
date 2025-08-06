from video_transcript_summarization.model.local_type import LocalType
from video_transcript_summarization.model.youtube_type import YoutubeType
from video_transcript_summarization.utils.utils import clear_intermediate_files

if __name__ == '__main__':
    # currentType = YoutubeType(url='https://www.youtube.com/watch?v=ngsxzZt5DoY',use_youtube_captions=False)
    currentType = LocalType(url='/Users/that.phamvan/Downloads/app_bar.mp4')

    currentType.fetch_video()
    currentType.get_transcription_text()
    currentType.summarize_and_elaborate()
    clear_intermediate_files()
