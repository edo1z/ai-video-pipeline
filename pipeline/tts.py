"""Text-to-speech. Uses OpenAI tts when OPENAI_API_KEY is set (natural voice),
otherwise falls back to Windows SAPI / Haruka (offline, robotic but free).
Returns the path actually written (mp3 for OpenAI, wav for SAPI).
"""

import os
import subprocess
import tempfile

_PS = r"""param([string]$TextFile,[string]$OutFile,[string]$VoiceName)
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
try { $s.SelectVoice($VoiceName) } catch {}
$s.Rate = -1
$s.SetOutputToWaveFile($OutFile)
$text = Get-Content -Raw -Encoding UTF8 $TextFile
$s.Speak($text)
$s.SetOutputToNull()
$s.Dispose()
"""


def synthesize(text, out_base, openai_voice="nova", openai_model="tts-1",
               sapi_voice="Microsoft Haruka Desktop"):
    if os.getenv("OPENAI_API_KEY"):
        path = str(out_base) + ".mp3"
        _openai_tts(text, path, openai_voice, openai_model)
    else:
        path = str(out_base) + ".wav"
        _sapi_tts(text, path, sapi_voice)
    return path


def _openai_tts(text, path, voice, model):
    from openai import OpenAI
    client = OpenAI()
    with client.audio.speech.with_streaming_response.create(
        model=model, voice=voice, input=text, response_format="mp3",
    ) as resp:
        resp.stream_to_file(path)


def _sapi_tts(text, path, voice):
    txt = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
    txt.write(text)
    txt.close()
    ps = tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="ascii")
    ps.write(_PS)
    ps.close()
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps.name,
             "-TextFile", txt.name, "-OutFile", path, "-VoiceName", voice],
            check=True, capture_output=True,
        )
    finally:
        os.unlink(txt.name)
        os.unlink(ps.name)


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    ).stdout.strip()
    return float(out)
