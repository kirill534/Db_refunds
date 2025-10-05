import json
import os
import requests

TELEGRAM_BOT_TOKEN = '8350139863:AAHcHIyPFpEpWn8V0lOap35IWjlAy0c0-sU'
TELEGRAM_CHAT_ID = '-1002523341296'  # или список ID, если нужно нескольким
MESSAGE_THREAD_ID = 3

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'message_thread_id': MESSAGE_THREAD_ID
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")

def send_telegram_photo_with_message(photo_paths, video_paths, message):
    # Если есть видео — отправляем группу видео с подписью
    if video_paths and len(video_paths) > 0:
        send_media_group_with_caption(video_paths, message, media_type='video')
    # Иначе если есть фото — отправляем группу фото с подписью
    elif photo_paths and len(photo_paths) > 0:
        send_media_group_with_caption(photo_paths, message, media_type='photo')
    else:
        # Нет файлов — просто отправляем сообщение
        send_telegram_message(message)

def send_media_group_with_caption(file_paths, caption, media_type='photo'):
    media = []
    files = {}
    for idx, path in enumerate(file_paths):
        if os.path.isfile(path):
            media.append({
                'type': media_type,
                'media': f'attach://file{idx}',
                'caption': caption if idx == 0 else '',  # подпись только у первого файла
                'parse_mode': 'HTML'
            })
            files[f'file{idx}'] = open(path, 'rb')
        else:
            print(f"Файл не найден или недопустимый путь: {path}")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMediaGroup"
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'media': json.dumps(media),
        'message_thread_id': MESSAGE_THREAD_ID
    }

    try:
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()
    except Exception as e:
        print(f"Ошибка при отправке медиа-группы: {e}")
    finally:
        for f in files.values():
            f.close()
