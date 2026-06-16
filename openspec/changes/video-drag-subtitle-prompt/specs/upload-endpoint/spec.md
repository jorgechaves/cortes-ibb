## ADDED Requirements

### Requirement: Endpoint /upload aceita campo subtitle
O endpoint `POST /upload` SHALL aceitar um campo adicional `subtitle` no form-data multipart com valor `"true"` ou `"false"`. Quando ausente, SHALL assumir `true` (comportamento legado). O campo SHALL ser repassado ao pipeline como `with_subtitles: bool`.

#### Scenario: Upload com subtitle=true
- **WHEN** o cliente envia `POST /upload` com `video=<arquivo>` e `subtitle=true`
- **THEN** o servidor aceita o upload e chama `pipeline.run()` com `with_subtitles=True`

#### Scenario: Upload com subtitle=false
- **WHEN** o cliente envia `POST /upload` com `video=<arquivo>` e `subtitle=false`
- **THEN** o servidor aceita o upload e chama `pipeline.run()` com `with_subtitles=False`

#### Scenario: Upload sem campo subtitle (retrocompatibilidade)
- **WHEN** o cliente envia `POST /upload` sem o campo `subtitle`
- **THEN** o servidor assume `with_subtitles=True` e processa normalmente
