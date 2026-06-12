# Hermes Session Ending

Hermes Agent oturum sonlandırma iş akışı: tüm konuşmadan başlık üret, kaydet, resetle.

## Kullanım

```bash
# Mevcut son CLI oturumuna title üret ve set et
python3 hermes_ending.py

# Belirli bir oturuma title üret
python3 hermes_ending.py --session-id 20260612_200601_d78863

# Sadece ne üreteceğini gör (set etme)
python3 hermes_ending.py --dry-run
```

## Nasıl Çalışır

1. Session DB'den tüm user+assistant mesajlarını okur
2. Tüm konuşmayı DeepSeek v4 Flash'e gönderir
3. Konuşmanın ana konusunu yansıtan 3-7 kelimelik title üretir
4. Title'ı session DB'ye yazar

## Gereksinimler

- `~/.hermes/.env` dosyasında `DEEPSEEK_API_KEY` tanımlı olmalı
- Hermes Agent kurulu olmalı (hermes_state modülü için)

## Hermes Skill ile Kullanım

Hermes'e `session-ending` skill'ini yükle. Oturum sonunda "ending" dediğinde:
1. Script çalışır, tüm konuşmadan title üretir
2. `/save` ile konuşmayı kaydedersin
3. `/new` ile yeni oturuma geçersin
