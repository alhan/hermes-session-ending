# Hermes Session Ending

Hermes Agent oturum sonlandırma iş akışı: tüm konuşmadan başlık üret, kaydet, resetle.

## Kurulum

### Yöntem 1: Hermes Skill olarak (önerilen)

```bash
hermes skills install https://git.softmediadesign.com/git_alhan/hermes-session-ending/raw/branch/main/SKILL.md
```

### Yöntem 2: Manuel (git clone)

```bash
git clone https://git.softmediadesign.com/git_alhan/hermes-session-ending.git
cd hermes-session-ending
python3 hermes_ending.py --dry-run
```

## Hermes İçinde Kullanım

Skill yüklendikten sonra oturumu bitirmek istediğinde şunlardan birini söyle:

| Ne dersin? | Ne olur? |
|---|---|
| `ending` | Title üretir, konuşmayı kaydeder, `/new` yapmanı söyler |
| `bitir` | Aynısı (Türkçe) |
| `tamam` | Aynısı (Türkçe) |

Adım adım:
1. Hermes agent tüm konuşmadan title üretir ve session DB'ye kaydeder
2. Konuşmayı `~/.hermes/sessions/saved/` altına JSON olarak export eder
3. Sana title'ı gösterir, gerekirse `/title yeni başlık` ile değiştirebilirsin
4. **Sen `/new` yazarsın** → yeni oturum başlar

## Manuel Kullanım

```bash
python3 hermes_ending.py                    # Son CLI oturumunu bulur
python3 hermes_ending.py --session-id SID   # Belirli oturum
python3 hermes_ending.py --dry-run          # Sadece title'ı gör
python3 hermes_ending.py --no-save          # Title üret ama export etme
```

## Nasıl Çalışır

1. Session DB'den tüm user+assistant mesajlarını okur
2. DeepSeek v4 Flash API ile title üretir (public, her yerde çalışır)
3. Title'ı session DB'ye yazar
4. Konuşmayı `~/.hermes/sessions/saved/hermes_<timestamp>.json` dosyasına export eder

## Gereksinimler

- `~/.hermes/.env` dosyasında `DEEPSEEK_API_KEY` tanımlı olmalı
- Alternatif: env override ile local Ollama kullanılabilir

## Yapılandırma

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `HERMES_ENDING_MODEL` | `deepseek-v4-flash` | Title üretimi için model |
| `HERMES_ENDING_ENDPOINT` | `https://api.deepseek.com/v1/chat/completions` | API adresi |
| `HERMES_ENDING_API_KEY` | `.env` dosyasından `DEEPSEEK_API_KEY` | API anahtarı |

Local Ollama için:
```bash
export HERMES_ENDING_ENDPOINT="http://localhost:11434/v1/chat/completions"
export HERMES_ENDING_MODEL="hermes3:latest"
export HERMES_ENDING_API_KEY=""
```

## Mimari Not

Bu araç, Hermes'in varsayılan title üretiminden farklıdır:
- **Varsayılan**: İlk mesaj çiftinden title üretir, session boyunca bir daha güncellenmez
- **Bu araç**: TÜM konuşma içeriğinden title üretir, oturum sonunda tetiklenir
