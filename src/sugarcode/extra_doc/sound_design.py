"""Row 301 Sound Design: bounded deterministic PCM triangle-tone synthesis.

Creates signed 16-bit mono PCM samples and a WAV byte stream from a supplied
integer period, amplitude and sample count. Period divisible by four permits
exact integer triangle vertices. No clipping or float quantization.
NOT_CLAIMED: acoustic realism, artistic quality, perceptual loudness, stereo
mixing, hardware playback, arbitrary instrument simulation or deployment.
"""
import io
import struct
import wave


def synthesize_triangle(period,sample_count,amplitude=8192,sample_rate=8000):
    if type(period) is not int or not 4<=period<=1024 or period%4:
        raise ValueError('period must be a nonbool multiple of four between 4 and 1024')
    if type(sample_count) is not int or not 1<=sample_count<=4096:
        raise ValueError('sample_count must be a nonbool integer between 1 and 4096')
    if type(amplitude) is not int or not 0<=amplitude<=32767:
        raise ValueError('amplitude must be a nonbool integer between zero and 32767')
    if type(sample_rate) is not int or not 8000<=sample_rate<=48000:
        raise ValueError('sample_rate must be a nonbool integer between 8000 and 48000')
    values=[]
    for i in range(sample_count):
        phase=i%period
        numerator=4*phase-period if phase<period//2 else 3*period-4*phase
        value=amplitude*numerator
        # Symmetric truncation toward zero preserves integer-sign symmetry.
        sample=(1 if value>=0 else -1)*(abs(value)//period)
        values.append(sample)
    pcm=struct.pack('<'+'h'*len(values),*values)
    buffer=io.BytesIO()
    with wave.open(buffer,'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(sample_rate);wav.writeframes(pcm)
    return {'samples':values,'wav_bytes':buffer.getvalue(),'sample_rate':sample_rate,
            'peak_amplitude':max(abs(v) for v in values),'playback_performed':False}
