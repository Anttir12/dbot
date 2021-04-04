import logging
import threading
from pathlib import Path
from tempfile import NamedTemporaryFile

import scipy
import scipy.io.wavfile
import numpy as np
from TTS.bin import synthesize
from TTS.utils.manage import ModelManager
from TTS.utils.synthesizer import Synthesizer


logger = logging.getLogger(__name__)


class Tts:

    MODEL_NAME = "tts_models/en/ljspeech/tacotron2-DCA"
    VOCODER_NAME = "vocoder_models/en/ljspeech/multiband-melgan"

    def __init__(self):
        path = Path(synthesize.__file__).parent / "../.models.json"
        logger.info("path")
        logger.info("Creating ModelManager")
        self.manager = ModelManager(path)
        logger.info("Downloading model")
        model_path, config_path, _ = self.manager.download_model(self.MODEL_NAME)
        logger.info("Downloading vcoder")
        vocoder_path, vocoder_config_path, _ = self.manager.download_model(self.VOCODER_NAME)
        logger.info("Finished downloading TTS model & vcoder")
        self.synthesizer = Synthesizer(model_path, config_path, vocoder_path, vocoder_config_path, False)
        self.tts_lock = threading.Lock()

    def synthesize_speech(self, tts: str):
        """
        This is largely copy pasted from TTS library (TTS.utils.synthesizer.Synthesizer.save_wav) but slightly modified
        to allow NamedTemporaryFile as output instead of writing it to a file

        :param tts: Text to speech
        :return: Speech in NamedTemporaryFile (wav)
        """
        if not self.tts_lock.acquire(blocking=True, timeout=0.1):
            raise TTSAlreadyProcessingException
        try:
            wav = self.synthesizer.tts(tts)
            wav = np.array(wav)
            wav_norm = wav * (32767 / max(0.01, np.max(np.abs(wav))))
            temp_file = NamedTemporaryFile(suffix=".wav")
            scipy.io.wavfile.write(temp_file, self.synthesizer.output_sample_rate, wav_norm.astype(np.int16))
            return temp_file
        finally:
            self.tts_lock.release()


class TTSAlreadyProcessingException(Exception):
    pass


class TTSProcessException(Exception):
    pass


def download_tts_model_and_vocodec():
    path = Path(synthesize.__file__).parent / "../.models.json"
    manager = ModelManager(path)
    logger.info("Downloading model")
    manager.download_model(Tts.MODEL_NAME)
    logger.info("Downloading vcoder")
    manager.download_model(Tts.VOCODER_NAME)
    logger.info("Finished downloading TTS model & vocoder")


if __name__ == "__main__":
    download_tts_model_and_vocodec()
