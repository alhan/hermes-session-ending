# Hermes Session Ending

Hermes Agent oturum sonlandırma iş akışı: tüm konuşmadan başlık üret, kaydet, resetle.

## Hızlı Kurulum (Hermes Skill olarak)

```bash
# Skill'i Hermes'e yükle
hermes skills install https://git.softmediadesign.com/git_alhan/hermes-session-ending/raw/branch/main/SKILL.md
```

## Manuel Kullanım

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
2. Tüm konuşmayı DeepSeek v4 Flash'e (deepseek-v4-flash) gönderir
3. Konuşmanın ana konusunu yansıtan 3-7 kelimelik title üretir
4. Title'ı session DB'ye yazar

## Gereksinimler

- `~/.hermes/.env` dosyasında `DEEPSEEK_API_KEY` tanımlı olmalı
- Hermes Agent kurulu olmalı (hermes_state modülü için)

## Hermes Skill Kullanımı

Skill yüklendikten sonra, Hermes içinde oturum sonunda "ending" dediğinde:
1. Script çalışır, tüm konuşmadan title üretir
2. Üretilen title'ı görürsün, gerekirse `/title` ile değiştirebilirsin
3. `/save` ile konuşmayı kaydedersin
4. `/new` ile yeni oturuma geçersin

## Mimari Not

Bu araç, Hermes'in varsayılan title üretiminden farklıdır:
- **Varsayılan**: İlk mesaj çiftinden (user+assistant) title üretir, session boyunca bir daha güncellenmez
- **Bu araç**: TÜM konuşma içeriğinden title üretir, oturum sonunda tetiklenir
