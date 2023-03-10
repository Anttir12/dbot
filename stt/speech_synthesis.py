from typing import Callable, Optional

import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import AudioDataStream
from django.conf import settings


SSML = """
<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts"
xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">
<voice name="fi-FI-SelmaNeural">
<mstts:silence type="Sentenceboundary-exact" value="300ms"/>
<prosody rate="{rate}%" pitch="{pitch}%">
{text}
</prosody></voice></speak>
"""


class SpeechSynthesis:

    def __init__(self, send: Callable = None):
        self.speech_config = speechsdk.SpeechConfig(subscription=settings.AZURE_KEY, region='northeurope')
        self.speech_config.speech_synthesis_voice_name = 'fi-FI-SelmaNeural'
        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Ogg24Khz16BitMonoOpus)
        self.pitch = 5
        self.rate = 10

        self.speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, audio_config=None)
        self.send = send

    def text_to_speech(self, text: str) -> Optional[bytes]:
        ssml = self.create_ssml(text)
        result = self.speech_synthesizer.speak_ssml_async(ssml).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            stream = AudioDataStream(result)
            return self._stream_to_bytes(stream)

        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    print("Error details: {}".format(cancellation_details.error_details))
                    print("Did you set the speech resource key and region values?")
        return None

    def create_ssml(self, text: str, rate: int = None, pitch: int = None):
        if not rate:
            rate = self.rate
        if not pitch:
            pitch = self.pitch
        return SSML.format(rate=rate, pitch=pitch, text=text)

    def _stream_to_bytes(self, stream: AudioDataStream) -> bytes:
        pos = 0
        output_bytes = bytes()
        chunk_size = 4096
        while True:
            buffer = bytes(chunk_size)
            bytes_filled = stream.read_data(buffer, pos)
            output_bytes += buffer
            if bytes_filled < chunk_size:
                break
            pos += bytes_filled
        return output_bytes
