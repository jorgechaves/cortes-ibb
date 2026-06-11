## ADDED Requirements

### Requirement: Subpasta no Drive usa o job_id como nome
O módulo `drive.upload_all` SHALL criar a subpasta destino com o nome igual ao `job_id` (nome da pasta de output local, ex: `20260611-104011-9259`), em vez da data do dia.

#### Scenario: Upload bem-sucedido
- **WHEN** `upload_all(cuts, out_dir, on_event)` é chamado com `out_dir = ".../output/20260611-104011-9259"`
- **THEN** a subpasta criada no Drive se chama `20260611-104011-9259`

#### Scenario: Subpasta já existe para o mesmo job_id
- **WHEN** uma subpasta com o mesmo `job_id` já existe dentro de `videos-ibb`
- **THEN** o sistema reutiliza a pasta existente (comportamento `get_or_create_folder` já existente)

#### Scenario: Log informativo
- **WHEN** a subpasta é criada ou encontrada
- **THEN** o log exibe `"Pasta destino: videos-ibb/<job_id>"`
