# Präsentation

Eine HTML-Präsentation der discomorse-Architektur: eine durchgehende SVG-Szene,
Slides sind Kamerafahrten (Zoom rein/raus) über dieselben Elemente.

## Öffnen

`index.html` direkt im Browser öffnen (Doppelklick genügt), oder:

```sh
python3 -m http.server -d presentation 8137
```

## Steuerung

| Taste / Aktion | Wirkung |
| --- | --- |
| `→` `↓` `Space` `PgDn` | nächste Slide |
| `←` `↑` `PgUp` | vorherige Slide |
| `Home` / `End` | erste / letzte Slide |
| Klick auf eine Stage (auf `stages`, `streams`, `pull`, `consumer`) | in die Stage zoomen (Interface + Implementierung) |
| `←` / `→` im Stage-Zoom | vorherige / nächste Stage |
| `Esc` / `Space` im Stage-Zoom | zurück zur Slide |
| Klick auf die Punkte unten | zu einer Slide springen |
| `f` | Vollbild |
