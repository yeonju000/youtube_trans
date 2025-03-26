import os
import yt_dlp
import whisper
import requests
import json
import subprocess
import torch  #GPU 사용 가능 여부 확인용

def download_audio(youtube_url, output_path="output.mp3"):
    """yt-dlp를 사용해 유튜브 오디오 다운로드"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': output_path,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
    
    print(f"[+] 오디오 다운로드 완료: {output_path}")
    
    #WebM 포맷이면 변환 수행 후 변환된 파일 사용
    fixed_audio_path = "output_fixed.mp3"
    if convert_to_mp3(output_path, fixed_audio_path):
        return fixed_audio_path  #변환된 MP3 사용
    return output_path  #원본 MP3사용

def convert_to_mp3(input_file, output_file):
    """WebM/Opus 형식의 오디오를 MP3로 변환"""
    print("[*] 오디오 형식 확인 중...")
    result = subprocess.run(
        ["ffmpeg", "-i", input_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    if "Audio: opus" in result.stderr:
        print("[!] Opus(WebM) 형식 감지됨, MP3로 변환 중...")
        command = [
            "ffmpeg", "-y", "-i", input_file, "-vn", "-acodec", "libmp3lame",
            "-ar", "44100", "-ac", "2", "-b:a", "192k", output_file
        ]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            print(f"[+] 변환 완료: {output_file}")
            return True
        else:
            print(f"[!] 변환 실패: {stderr}")
            return False
    else:
        print("[+] 오디오 변환 불필요, 기존 MP3 사용")
        return False

def split_audio(audio_path, chunk_length=600):
    """긴 오디오 파일을 chunk_length(초) 단위로 분할"""
    output_dir = "audio_chunks"
    os.makedirs(output_dir, exist_ok=True)
    
    command = [
        "ffmpeg", "-y", "-i", audio_path, "-f", "segment", "-segment_time", str(chunk_length),
        "-c", "copy", f"{output_dir}/chunk_%03d.mp3"
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    chunk_files = sorted([f"{output_dir}/{f}" for f in os.listdir(output_dir) if f.startswith("chunk_")])
    print(f"[+] 오디오 분할 완료: {len(chunk_files)} 개 파일")
    return chunk_files

def transcribe_audio(audio_files, model_size="small"):
    """Whisper를 사용해 일본어 음성을 텍스트로 변환 (긴 영상 지원)"""
    
    #GPU 사용 가능하면 CUDA 사용
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[+] Whisper 모델 로드 중... (모델: {model_size}, 장치: {device})")
    
    model = whisper.load_model(model_size, device=device)
    transcriptions = []
    
    for idx, audio in enumerate(audio_files):
        print(f"[+] {idx+1}/{len(audio_files)} 번째 파일 변환 중...")
        result = model.transcribe(audio, language="ja")
        transcriptions.extend(result["segments"])
    
    print("[+] 모든 오디오 변환 완료")
    return transcriptions  #싱크 정보 포함한 문장 반환

def translate_text(text, use_papago=False, client_id=None, client_secret=None):
    """Papago API 또는 Google Translate API를 사용해 번역"""
    if use_papago:
        if client_id and client_secret:
            url = "https://openapi.naver.com/v1/papago/n2mt"
            headers = {
                "X-Naver-Client-Id": client_id,
                "X-Naver-Client-Secret": client_secret,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {"source": "ja", "target": "ko", "text": text}
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200:
                return response.json()["message"]["result"]["translatedText"]
            else:
                print("[!] Papago 번역 실패", response.text)
                return ""
        else:
            print("[!] Papago API 키가 제공되지 않아 번역할 수 없습니다.")
            return ""
    else:
        # Google Translate API 사용
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "ja",
            "tl": "ko",
            "dt": "t",
            "q": text,
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()[0][0][0]
        else:
            print("[!] Google Translate 번역 실패", response.text)
            return ""

def save_translations(transcriptions, translated_texts, output_file="translated.txt"):
    """번역된 내용을 TXT 파일로 저장 (싱크 유지)"""
    with open(output_file, "w", encoding="utf-8") as f:
        for i, segment in enumerate(transcriptions):
            start_time = segment["start"]
            end_time = segment["end"]
            original_text = segment["text"]
            translated_text = translated_texts[i]
            f.write(f"[{start_time:.2f} - {end_time:.2f}]\n")
            f.write(f"일본어: {original_text}\n")
            f.write(f"한국어: {translated_text}\n\n")
    print(f"[+] 번역된 파일 저장 완료: {output_file}")

def main():
    youtube_url = input("유튜브 링크 입력: ")
    use_papago = input("Papago API를 사용할까요? (y/n): ").strip().lower()
    client_id = client_secret = None
    
    if use_papago == "y":
        client_id = input("Papago Client ID 입력: ")
        client_secret = input("Papago Client Secret 입력: ")
    else:
        print("[+] Google Translate API 사용 중 (Papago API 필요 없음)")
    
    model_size = input("Whisper 모델 크기 선택 (tiny/small/medium/large): ").strip().lower()
    audio_path = download_audio(youtube_url)

    if os.path.exists("output_fixed.mp3"):
        audio_path = "output_fixed.mp3"

    audio_chunks = split_audio(audio_path)
    transcriptions = transcribe_audio(audio_chunks, model_size=model_size)
    
    translated_texts = [translate_text(seg["text"], use_papago == "y", client_id, client_secret) for seg in transcriptions]
    save_translations(transcriptions, translated_texts)

if __name__ == "__main__":
    main()
