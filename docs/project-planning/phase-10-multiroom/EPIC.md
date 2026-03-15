# Phase 10 – Multi-Room Zonen (EPIC)

**Epic-ID:** EPIC-010  
**Story Points Total:** 48 SP  
**Priorität:** MEDIUM  
**Abhängigkeiten:** Phase 0 (MVP), Phase 1 (Device Discovery), Phase 3 (Playback/Volume Control)  

---

## 1. Überblick

Multi-Room ermöglicht es, mehrere Bose SoundTouch-Geräte zu einer Zone zusammenzufassen, sodass sie synchron dieselbe Audioquelle abspielen. Ein Gerät ist der **Master** (kontrolliert die Quelle), die anderen sind **Slaves** (folgen dem Master). Die Lautstärke bleibt pro Gerät individuell steuerbar.

### Kernfunktionen
- Zone erstellen (Master + 1..n Slaves)
- Zone auflösen (alle Members entfernen)
- Members dynamisch hinzufügen/entfernen
- Zone-Status live abfragen
- Individuelle Lautstärkeregelung pro Gerät innerhalb der Zone

---

## 2. Technische Analyse

### 2.1 Bose SoundTouch Zone API (HTTP, Port 8090)

| Endpoint | Methode | Zweck |
|---|---|---|
| `/getZone` | `GET` | Aktuellen Zone-Status abfragen |
| `/setZone` | `PUT` | Zone erstellen (Master + Members) |
| `/addZoneSlave` | `PUT` | Members zu bestehender Zone hinzufügen |
| `/removeZoneSlave` | `PUT` | Members aus Zone entfernen |

### 2.2 XML-Strukturen

**GET /getZone Response:**
```xml
<zone master="AABBCC112233" senderIPAddress="192.168.1.100" senderIsMaster="true">
  <member ipaddress="192.168.1.100">AABBCC112233</member>
  <member ipaddress="192.168.1.101">DDEEFF445566</member>
</zone>
```

**PUT /setZone Request (Zone erstellen):**
```xml
<zone master="AABBCC112233" senderIPAddress="192.168.1.100">
  <member ipaddress="192.168.1.100">AABBCC112233</member><!-- Master = 1. Member -->
  <member ipaddress="192.168.1.101">DDEEFF445566</member><!-- Slave -->
</zone>
```

**PUT /addZoneSlave / removeZoneSlave Request:**
```xml
<zone master="AABBCC112233">
  <member ipaddress="192.168.1.102">112233445566</member>
</zone>
```

### 2.3 bosesoundtouchapi Library (Python)

Die installierte Library (`bosesoundtouchapi >= 1.0.86`) bietet folgende Zone-Methoden auf `SoundTouchClient`:

| Methode | Parameter | Return | Beschreibung |
|---|---|---|---|
| `GetZoneStatus(refresh=True)` | — | `Zone` | Aktuellen Zone-Status vom Gerät lesen |
| `CreateZone(zone, delay=3)` | `Zone` obj | `SoundTouchMessage` | Zone erstellen via `PUT /setZone` |
| `CreateZoneFromDevices(master, members)` | `SoundTouchDevice`, `list` | `Zone` | Convenience: Erstellt Zone aus Device-Objekten |
| `AddZoneMembers(members, delay=3)` | `list[ZoneMember]` | `SoundTouchMessage` | Members hinzufügen via `PUT /addZoneSlave` |
| `RemoveZoneMembers(members, delay=3)` | `list[ZoneMember]` | `SoundTouchMessage` | Members entfernen via `PUT /removeZoneSlave` |
| `RemoveZone(delay=1)` | — | `SoundTouchMessage` | Alle Members entfernen = Zone auflösen |
| `ToggleZoneMember(member, delay=2)` | `ZoneMember` | `SoundTouchMessage` | Add/Remove Toggle |

**Datenmodelle:**
- `Zone(masterDeviceId, masterIpAddress, isZoneMaster, members[])`
- `ZoneMember(ipAddress, deviceId, deviceRole)`

**WebSocket-Notification:**
- `zoneUpdated` — Wird gefeuert wenn Zone erstellt/geändert/aufgelöst wird

### 2.4 Architektur-Constraints

| Constraint | Detail |
|---|---|
| **Master-zentrisch** | ALLE Zone-Operationen MÜSSEN auf dem Master-Gerät ausgeführt werden |
| **Gleiche Quelle** | Alle Zone-Members spielen automatisch die Quelle des Masters |
| **Individuelle Lautstärke** | Jedes Gerät behält seine eigene Lautstärke |
| **Gleiches Netzwerk** | Alle Geräte müssen im selben Subnetz sein |
| **Keine Fehler-Rückgabe** | Bose-API gibt bei ungültigen Member-IDs **keinen Error** zurück (silent ignore) |
| **Built-in Delays** | Library hat 1-3 Sekunden Delays nach Zone-Operationen eingebaut |
| **Master = 1. Member** | Im setZone-XML muss der Master als erster `<member>` stehen |
| **Nur bestimmte Quellen** | AUX funktioniert NICHT in Multi-Room (nur Netzwerk-Quellen) |
| **Zone-Support prüfen** | `has_zone_support` Capability-Flag muss True sein |

### 2.5 Bestandscode-Analyse

| Komponente | Status | Details |
|---|---|---|
| `capabilities.py` | ✅ Fertig | `has_zone_support` Flag wird via `getZone`/`setZone` Endpoint-Detection erkannt |
| `MultiRoom.tsx` | 🟡 Mock | Vollständige UI mit Zonen-Liste, Device-Selection, Create/Dissolve/Edit — aber nur Mock-Daten |
| `MultiRoom.css` | ✅ Fertig | Komplettes Styling vorhanden |
| `client_adapter.py` | ❌ Fehlt | Keine Zone-Methoden implementiert |
| `devices/api/routes.py` | ❌ Fehlt | Keine Zone-API-Endpoints |
| `marge/routes.py` | 🟡 Placeholder | `GET /v1/systems/devices/{id}/devices` existiert, gibt leere Liste zurück |
| `marge/xml_builder.py` | 🟡 Placeholder | `build_devices_xml()` existiert, hat TODO-Kommentar |
| Frontend API | ❌ Fehlt | Kein `api/zones.ts`, keine Zone-Hooks |
| Frontend Routing | ✅ Fertig | `/multiroom` Route existiert in `App.tsx` |

---

## 3. Architektur-Entscheidungen

### 3.1 Zone-Management auf Backend-Seite

Alle Zone-Operationen laufen über das **Backend**, welches direkt mit dem Bose-Gerät kommuniziert. Das Frontend ruft nur unsere REST-API auf.

**Begründung:** Zone-Operationen erfordern IP-Adressen und Device-IDs aller beteiligten Geräte. Das Backend hat Zugriff auf das Device-Registry und die `BoseDeviceClientAdapter`-Instanzen.

### 3.2 Kein Zone-Persistence in DB

Zonen werden **nicht** in der Datenbank persistiert. Der Zone-Status wird immer **live** vom Master-Gerät abgefragt (`GET /getZone`).

**Begründung:**
- Bose-Geräte sind Source of Truth für Zone-Status
- Zonen können sich außerhalb von OCT ändern (Bose App, Gerätetasten)
- Vermeidet Sync-Probleme zwischen DB und tatsächlichem Gerätestatus
- Einfacherer Code, weniger Fehlerquellen

### 3.3 Zone-Discovery: Polling statt WebSocket

Phase 10 nutzt **Polling** (Frontend pollt Backend, Backend pollt Geräte) statt WebSocket-basierte Live-Updates.

**Begründung:**
- WebSocket zu Bose-Geräten ist Infrastruktur-Aufwand (Story für spätere Phase)
- Polling alle 5s ist für Zone-Status ausreichend
- Einfacher zu implementieren und zu testen
- WebSocket-Integration kann in Phase 11 als Upgrade erfolgen

### 3.4 Zone-Namen via LocalStorage

Die Bose-API unterstützt **keine benannten Zonen**. Zonen werden technisch anhand ihres Masters identifiziert. Damit der User trotzdem eigene Zone-Namen vergeben kann (z.B. "Erdgeschoss"), werden diese im **localStorage** des Browsers persistiert (Key: `zone-names`, Map: `masterId → name`). Default-Name: `"{MasterDeviceName} Zone"`.

---

## 4. Stories

---

### STORY-1001: Backend Zone-Methods im ClientAdapter (5 SP)

**Als** Backend-Entwickler  
**möchte ich** Zone-Methoden im `BoseDeviceClientAdapter` haben,  
**damit** ich Zonen über die Library steuern kann.

**Scope:** `apps/backend/src/opencloudtouch/devices/client_adapter.py`

**Akzeptanzkriterien:**
- [ ] `get_zone_status() → ZoneStatus | None` — Ruft `GetZoneStatus()` auf, gibt None bei leerer Zone
- [ ] `create_zone(master_ip: str, members: list[ZoneMemberInfo]) → ZoneStatus` — Erstellt Zone via `CreateZone()`
- [ ] `add_zone_members(members: list[ZoneMemberInfo])` — Fügt Members hinzu via `AddZoneMembers()`
- [ ] `remove_zone_members(members: list[ZoneMemberInfo])` — Entfernt Members via `RemoveZoneMembers()`
- [ ] `remove_zone()` — Löst Zone auf via `RemoveZone()`
- [ ] Alle Methoden sind `async` (wrapped via `asyncio.to_thread()`)
- [ ] `ZoneStatus` Pydantic-Model mit `master_id`, `master_ip`, `is_master`, `members: list[ZoneMemberInfo]`
- [ ] `ZoneMemberInfo` Pydantic-Model mit `device_id`, `ip_address`, `role`
- [ ] Error-Handling: `DeviceConnectionError` bei Kommunikationsfehlern
- [ ] Unit-Tests mit gemocktem `SoundTouchClient` (≥90% Coverage)

**Technische Hinweise:**
- `SoundTouchClient.GetZoneStatus()` gibt `Zone`-Objekt zurück, `Zone.Members` ist leer wenn nicht in Zone
- `CreateZone()` muss auf dem Master-Client aufgerufen werden
- Members brauchen `ipAddress` UND `deviceId` — beides muss aus Device-Registry kommen
- Library hat built-in Delays (3s default) — in Tests mocken
- `Zone.ToDictionary()` und `ZoneMember.ToDictionary()` für einfache Konvertierung nutzen

---

### STORY-1002: Backend Zone-Service (5 SP)

**Als** Backend-Entwickler  
**möchte ich** einen Zone-Service der die Geschäftslogik kapselt,  
**damit** die API-Routes schlank bleiben.

**Scope:** Neues Modul `apps/backend/src/opencloudtouch/zones/`

**Akzeptanzkriterien:**
- [ ] `ZoneService` Klasse mit Dependency Injection (DeviceRepository, ClientAdapterFactory)
- [ ] `get_zone_status(device_id) → ZoneStatus | None` — Holt Client für Device, ruft `get_zone_status()` auf
- [ ] `create_zone(master_device_id, slave_device_ids: list[str]) → ZoneStatus` — Validiert alle Devices, erstellt Zone
- [ ] `add_members(master_device_id, slave_device_ids: list[str]) → ZoneStatus` — Members hinzufügen
- [ ] `remove_members(master_device_id, slave_device_ids: list[str])` — Members entfernen
- [ ] `dissolve_zone(master_device_id)` — Zone komplett auflösen
- [ ] **Validierungen:**
  - Alle Device-IDs müssen im Device-Repository existieren
  - Master-Device muss `has_zone_support == True` haben
  - Slave-Devices müssen `has_zone_support == True` haben
  - Master darf nicht bereits Slave in anderer Zone sein
  - Mindestens 1 Slave bei Zone-Erstellung
  - Source-Check: Warnung wenn Master auf AUX/STANDBY steht
- [ ] Structured Logging für alle Zone-Operationen
- [ ] Unit-Tests mit gemocktem ClientAdapter und Repository (≥90% Coverage)

**Technische Hinweise:**
- Service braucht Zugriff auf ALLE Device-Clients (Master + Slaves) — ClientAdapterFactory erstellt Client per Device-IP
- create_zone muss den Client des MASTER-Geräts nutzen (nicht eines Slaves!)
- IP-Adressen der Slaves müssen aus Device-Repository geladen werden (DB hat `ip` Feld)
- Kein Persistence Layer nötig — Zone-Status kommt immer live vom Gerät

---

### STORY-1003: Backend Zone-API-Endpoints (5 SP)

**Als** Frontend-Entwickler  
**möchte ich** REST-Endpoints für Zone-Management haben,  
**damit** ich Zonen über die UI steuern kann.

**Scope:** `apps/backend/src/opencloudtouch/zones/routes.py`

**Akzeptanzkriterien:**
- [ ] `GET /api/zones` — Alle aktiven Zonen aller bekannten Geräte zurückgeben
- [ ] `GET /api/devices/{device_id}/zone` — Zone-Status für ein spezifisches Gerät
- [ ] `POST /api/zones` — Zone erstellen: `{ master_id: str, slave_ids: str[] }`
- [ ] `POST /api/zones/{master_id}/members` — Members hinzufügen: `{ device_ids: str[] }`
- [ ] `DELETE /api/zones/{master_id}/members` — Members entfernen: `{ device_ids: str[] }`
- [ ] `DELETE /api/zones/{master_id}` — Zone auflösen
- [ ] Response-Modelle als Pydantic-Schemas mit OpenAPI-Doku
- [ ] HTTP-Statuscodes: 200 (OK), 201 (Created), 204 (No Content), 404 (Device not found), 409 (Device already in zone), 422 (Validation error)
- [ ] FastAPI-Router registriert in App
- [ ] Integration-Tests gegen gemockten ZoneService (≥90% Coverage)

**Response-Beispiel `GET /api/devices/{id}/zone`:**
```json
{
  "master_id": "AABBCC112233",
  "master_ip": "192.168.1.100",
  "is_master": true,
  "members": [
    { "device_id": "AABBCC112233", "ip_address": "192.168.1.100", "role": "master" },
    { "device_id": "DDEEFF445566", "ip_address": "192.168.1.101", "role": "slave" }
  ]
}
```

**Response bei keiner aktiven Zone: `204 No Content`**

---

### STORY-1004: GET /api/zones – Zonen-Übersicht aller Geräte (3 SP)

**Als** Frontend-Entwickler  
**möchte ich** eine Übersicht aller aktiven Zonen über alle Geräte hinweg erhalten,  
**damit** ich die MultiRoom-Seite korrekt rendern kann.

**Scope:** `ZoneService.get_all_zones()`, Route `GET /api/zones`

**Akzeptanzkriterien:**
- [ ] Iteriert über alle Geräte mit `has_zone_support == True`
- [ ] Ruft `get_zone_status()` pro Gerät auf (parallel via `asyncio.gather`)
- [ ] Deduplizierung: Zone erscheint nur einmal (via Master-ID), nicht pro Member
- [ ] Timeouts: Einzelnes Gerät-Timeout (3s) bricht nicht den gesamten Request ab
- [ ] Response enthält enriched Device-Infos (Name, Model) aus Device-Repository
- [ ] Performance: Parallel-Abfrage aller Geräte, nicht sequenziell
- [ ] Unit-Tests: Szenarien mit 0/1/3 Zonen, Geräte-Timeout, Duplikat-Filtering

**Technische Hinweise:**
- Ein Slave-Gerät gibt bei `getZone` die Zone-Info mit `isZoneMaster=false` zurück
- Dedup-Strategie: Nur Zone-Responses mit `is_master=true` verwenden, oder nach `master_id` groupen
- `asyncio.gather(*tasks, return_exceptions=True)` für fehlertolerante Parallel-Abfrage

---

### STORY-1005: Frontend Zone-API-Client und Hooks (5 SP)

**Als** Frontend-Entwickler  
**möchte ich** API-Client-Funktionen und React-Hooks für Zone-Management haben,  
**damit** die MultiRoom-Seite echte Daten nutzen kann.

**Scope:** `apps/frontend/src/api/zones.ts`, `apps/frontend/src/hooks/useZones.ts`

**Akzeptanzkriterien:**
- [ ] API-Client (`api/zones.ts`):
  - `getZones() → ZoneInfo[]` — `GET /api/zones`
  - `getDeviceZone(deviceId) → ZoneInfo | null` — `GET /api/devices/{id}/zone`
  - `createZone(masterId, slaveIds) → ZoneInfo` — `POST /api/zones`
  - `addMembers(masterId, deviceIds)` — `POST /api/zones/{id}/members`
  - `removeMembers(masterId, deviceIds)` — `DELETE /api/zones/{id}/members`
  - `dissolveZone(masterId)` — `DELETE /api/zones/{id}`
- [ ] React Hook (`hooks/useZones.ts`):
  - `zones: ZoneInfo[]` — Aktuelle Zonen-Liste
  - `isLoading: boolean` — Ladezustand
  - `error: string | null` — Fehlermeldung
  - `createZone(masterId, slaveIds)` — Mit Optimistic Update
  - `dissolveZone(masterId)` — Mit Optimistic Update
  - `addMembers(masterId, deviceIds)` — Mutation
  - `removeMembers(masterId, deviceIds)` — Mutation
  - `refetch()` — Manuelles Neuladen
  - Polling: Auto-Refetch alle 5 Sekunden
- [ ] TypeScript Interfaces: `ZoneInfo`, `ZoneMemberInfo`
- [ ] Error-Handling: Toast-Benachrichtigungen bei Fehlern
- [ ] Unit-Tests mit MSW (Mock Service Worker) (≥80% Coverage)

**TypeScript-Interfaces:**
```typescript
interface ZoneMemberInfo {
  device_id: string;
  ip_address: string;
  role: "master" | "slave";
  name?: string;    // enriched from device info
  model?: string;   // enriched from device info
}

interface ZoneInfo {
  master_id: string;
  master_ip: string;
  is_master: boolean;
  members: ZoneMemberInfo[];
}
```

---

### STORY-1006: Frontend MultiRoom Live-Anbindung (5 SP)

**Als** Benutzer  
**möchte ich** auf der MultiRoom-Seite echte Zonen sehen und verwalten können,  
**damit** ich meine Geräte gruppieren kann.

**Scope:** `apps/frontend/src/pages/MultiRoom.tsx` (Refactoring von Mock auf Live)

**Akzeptanzkriterien:**
- [ ] `MOCK_ZONES` entfernt, ersetzt durch `useZones()` Hook
- [ ] Zone-Name-Konzept entfernt (Bose unterstützt keine benannten Zonen)
- [ ] Zonen-Label = Master-Gerätename + "Zone" (z.B. "Wohnzimmer Zone")
- [ ] Zone erstellen:
  - Erstes ausgewähltes Gerät = Master
  - Mindestens 2 Geräte auswählen
  - Button disabled wenn weniger als 2 Geräte gewählt
  - Loading-State während API-Call
  - Fehlermeldung wenn Zone-Erstellung fehlschlägt
- [ ] Zone auflösen:
  - Bestätigungsdialog vor dem Auflösen
  - Loading-State während API-Call
- [ ] Members hinzufügen/entfernen:
  - Bearbeiten-Modus zeigt aktuelle Members
  - Checkbox-Toggle für Add/Remove
  - Speichern-Button für Änderungen
- [ ] Geräte ohne `zone_support` werden NICHT angezeigt (oder disabled mit Hinweis)
- [ ] Geräte auf AUX/STANDBY zeigen Warnung (Multi-Room funktioniert nicht mit lokalen Quellen)
- [ ] Empty State: "Keine aktiven Zonen. Wähle mindestens 2 Geräte aus, um eine Zone zu erstellen."
- [ ] Loading State: Skeleton-Cards während Zone-Daten geladen werden
- [ ] Error State: Fehlermeldung mit Retry-Button
- [ ] Vitest-Tests für alle UI-Zustände (≥80% Coverage)

**Technische Hinweise:**
- Bestehende UI-Struktur (Cards, Grid, Badges) kann großteils wiederverwendet werden
- `device.capabilities?.zone_support` aus dem Device-Objekt für Feature-Detection nutzen
- Framer-motion Animationen beibehalten

---

### STORY-1007: Zone-Lautstärke pro Gerät (3 SP)

**Als** Benutzer  
**möchte ich** die Lautstärke jedes Geräts in einer Zone einzeln steuern können,  
**damit** ich die Lautstärke pro Raum anpassen kann.

**Scope:** `MultiRoom.tsx` Zone-Card-Erweiterung

**Akzeptanzkriterien:**
- [ ] Zone-Card zeigt pro Member ein Volume-Slider (Mini-Version des `VolumeSlider`)
- [ ] Volume-API-Call geht direkt an das jeweilige Gerät (nicht an den Master)
- [ ] Mute pro Gerät (Button neben Slider)
- [ ] Aktueller Volume-Level wird per Polling aktualisiert (5s)
- [ ] Volume-Change ist sofort reaktiv (Optimistic Update)
- [ ] VolumeSlider-Komponente wird als `compact` Variante wiederverwendet
- [ ] Unit-Tests (≥80% Coverage)

**Technische Hinweise:**
- Bestehender `useVolume()` Hook kann für jedes Gerät einzeln genutzt werden
- Volume-API existiert bereits (`GET/PUT /api/devices/{id}/volume`)
- Keine neuen Backend-Endpoints nötig

---

### STORY-1008: Error-Handling und Edge-Cases (3 SP)

**Als** Benutzer  
**möchte ich** verständliche Fehlermeldungen bei Zone-Problemen sehen,  
**damit** ich weiß was schiefgelaufen ist.

**Scope:** Backend + Frontend Error-Handling

**Akzeptanzkriterien:**
- [ ] Backend:
  - Gerät offline → `503 Service Unavailable` mit Gerätename
  - Gerät hat kein `zone_support` → `422 Unprocessable Entity` mit Hinweis
  - Gerät bereits in anderer Zone → `409 Conflict` mit Zone-Details
  - Master-Gerät nicht erreichbar → spezifische Fehlermeldung
  - Slave-Gerät nicht erreichbar → Zone wurde erstellt, aber Warnung für fehlende Slaves
- [ ] Frontend:
  - Toast-Notifications für alle Zone-Fehler
  - Offline-Geräte werden visuell markiert (ausgegraut, Offline-Badge)
  - Retry-Mechanismus bei temporären Fehlern (3 Versuche, exponential backoff)
  - Graceful Degradation: Wenn nur 1 von 3 Slaves nicht erreichbar, Zone trotzdem erstellen
- [ ] Unit-Tests für alle Error-Szenarien (≥90% Coverage)

**Technische Hinweise:**
- Bose-API gibt bei ungültigen Member-IDs keinen Error zurück → Post-Validation durch Zone-Status-Check nach Operation
- `asyncio.gather(return_exceptions=True)` für tolerante Multi-Device-Operations

---

### STORY-1009: Zone-Name editierbar (2 SP)

**Als** Benutzer  
**möchte ich** einer Zone einen eigenen Namen geben können (z.B. "Erdgeschoss"),  
**damit** ich meine Zonen besser unterscheiden kann.

**Scope:** `MultiRoom.tsx`, `localStorage`

**Akzeptanzkriterien:**
- [ ] Zone-Card zeigt den Zone-Namen als Inline-Editierfeld (Click-to-Edit)
- [ ] Default-Name: `"{Master-Gerätename} Zone"` (z.B. "Wohnzimmer Zone")
- [ ] Name wird im `localStorage` gespeichert (Key: `zone-names`, Value: `{ [masterId]: string }`)
- [ ] Name bleibt nach Browser-Refresh erhalten
- [ ] Name wird beim Auflösen der Zone aus localStorage entfernt
- [ ] Leerer Name → Fallback auf Default-Name
- [ ] Max 30 Zeichen, keine Sonderzeichen-Validierung nötig
- [ ] Vitest-Tests (≥80% Coverage)

**Technische Hinweise:**
- Bose-API hat kein Zone-Name-Konzept → rein clientseitig
- Custom Hook `useZoneNames()` für localStorage-Zugriff (get/set/delete)
- Kein Backend-Endpoint nötig

---

### STORY-1010: Master wechseln innerhalb bestehender Zone (3 SP)

**Als** Benutzer  
**möchte ich** den Master einer Zone wechseln können,  
**damit** die Audioquelle von einem anderen Gerät kommt.

**Scope:** Backend `ZoneService`, Frontend `MultiRoom.tsx`

**Akzeptanzkriterien:**
- [ ] Zone-Card im Edit-Modus zeigt "Master wechseln"-Option (Dropdown/Select)
- [ ] Backend: `change_master(old_master_id, new_master_id)` in `ZoneService`
  - Alte Zone auflösen (`remove_zone()` auf altem Master)
  - Neue Zone erstellen (`create_zone()` auf neuem Master mit bisherigen Members)
  - Atomarität: Bei Fehler in Step 2 → Rollback (alte Zone wiederherstellen)
- [ ] Frontend: Loading-State während Master-Wechsel (2-Schritt-Operation = ~6s Delay)
- [ ] Frontend: Warnung "Audio wird kurz unterbrochen" vor Bestätigung
- [ ] Backend-Endpoint: `PUT /api/zones/{master_id}/master` mit `{ new_master_id: string }`
- [ ] Unit-Tests für Success + Rollback-Szenario (≥90% Coverage)

**Technische Hinweise:**
- Bose-API hat KEIN "change master"-Kommando → muss als Dissolve+Recreate implementiert werden
- Built-in Delays: `RemoveZone(delay=1)` + `CreateZone(delay=3)` = ~4-6s
- Rollback-Logik: Wenn `CreateZone` fehlschlägt, `CreateZone` mit altem Master + Members erneut versuchen
- Zone-Name (localStorage) muss auf neuen Master-Key umgemappt werden

---

### STORY-1011: Device-Reihenfolge & Master-Auswahl (3 SP)

**Als** Benutzer  
**möchte ich** den Master explizit auswählen können statt dass das erste Gerät automatisch Master wird,  
**damit** ich volle Kontrolle über die Zone-Konfiguration habe.

**Scope:** `MultiRoom.tsx` Device-Selection-Bereich

**Akzeptanzkriterien:**
- [ ] **Desktop**: Drag & Drop Sortierung der ausgewählten Geräte (erstes = Master)
  - Drag-Handle sichtbar bei Hover
  - Smooth Animation beim Umsortieren (framer-motion `Reorder`)
- [ ] **Mobile**: Kein Drag & Drop — stattdessen "Als Master setzen" Button pro Gerät
  - Button nur sichtbar bei ausgewählten Geräten
  - Touch-Target ≥44px
- [ ] Responsive Detection: `useMediaQuery('(pointer: fine)')` für Desktop vs. Touch
- [ ] Master-Badge aktualisiert sich sofort bei Änderung
- [ ] Checkbox-Selection bleibt bestehen (Geräte an/abwählen)
- [ ] Vitest-Tests für Desktop + Mobile Variante (≥80% Coverage)

**Technische Hinweise:**
- `framer-motion` `<Reorder.Group>` + `<Reorder.Item>` für Drag & Drop
- Mobile-Fallback: Einfacher Button-Click swappt das Gerät an Position 0 im `selectedDevices` Array
- Feature Detection statt User-Agent-Sniffing
- Bestehende Checkbox-UI bleibt für Geräte-Auswahl, Drag & Drop nur für Reihenfolge

---

### STORY-1012: Zone-Status-Anzeige – Now Playing in Zone-Card (3 SP)

**Als** Benutzer  
**möchte ich** in der Zone-Card sehen was gerade in der Zone spielt,  
**damit** ich weiß welcher Content läuft ohne die Seite zu wechseln.

**Scope:** `MultiRoom.tsx` Zone-Card-Erweiterung

**Akzeptanzkriterien:**
- [ ] Zone-Card zeigt Now-Playing-Info des Master-Geräts:
  - Album-Art (Thumbnail, 48x48px)
  - Track/Station Name
  - Artist (falls vorhanden)
  - Source-Badge (BT/Radio/Spotify/etc.)
- [ ] Standby-Status: Zone-Card zeigt "Standby" statt Now-Playing
- [ ] Daten kommen aus bestehendem `GET /api/devices/{master_id}/now-playing` Endpoint
- [ ] Polling alle 5s (synchron mit Zone-Status-Polling)
- [ ] Kompakte Darstellung — Now-Playing unterhalb des Zone-Headers, vor der Member-Liste
- [ ] Vitest-Tests (≥80% Coverage)

**Technische Hinweise:**
- `useNowPlaying(masterId)` Hook existiert bereits oder wird aus `useDeviceStatus` extrahiert
- Bestehende `NowPlaying`-Komponente als `compact`-Variante wiederverwenden
- Album-Art URL kommt aus Bose-API (`ContentItem.ContainerArt` oder `art.url`)

---

### STORY-1013: Quick-Add – Zone-Aktion auf DeviceCard (3 SP)

**Als** Benutzer  
**möchte ich** direkt von der Geräte-Übersicht (Dashboard) ein Gerät zu einer Zone hinzufügen können,  
**damit** ich nicht extra zur MultiRoom-Seite navigieren muss.

**Scope:** `DeviceCard.tsx` / Dashboard-Seite, `useZones()` Hook

**Akzeptanzkriterien:**
- [ ] DeviceCard zeigt Zone-Indikator wenn Gerät in einer Zone ist:
  - Icon/Badge: 🔗 + "Zone: {Zonename}" (oder "Master" wenn Master)
  - Klick auf Badge → Navigation zu `/multiroom`
- [ ] DeviceCard Context-Menu (Long-Press / Rechtsklick) oder Action-Button:
  - "Zu Zone hinzufügen" → Dropdown mit aktiven Zonen
  - "Neue Zone erstellen mit..." → Öffnet Device-Picker (Modal oder Redirect zu `/multiroom` mit Pre-Selection)
  - "Aus Zone entfernen" (nur wenn bereits in Zone)
- [ ] Quick-Actions nutzen bestehende `useZones()` Mutations (`addMembers`, `removeMembers`)
- [ ] Toast-Feedback: "Gerät wurde zu Zone 'Erdgeschoss' hinzugefügt"
- [ ] Gerät ohne `zone_support` → Kein Quick-Add Button
- [ ] Vitest-Tests (≥80% Coverage)

**Technische Hinweise:**
- DeviceCard braucht Zugriff auf Zone-Daten → `useZones()` im Parent (Dashboard) oder via Context
- Pre-Selection für `/multiroom` via URL-Param: `/multiroom?preselect=deviceId1,deviceId2`
- Action-Buttons: Bestehende Card-Action-Leiste erweitern (neben Volume/Mute)

---

## 5. Story-Abhängigkeiten

```
STORY-1001 (ClientAdapter Zone Methods)
    ↓
STORY-1002 (Zone Service)  ←── STORY-1010 (Master wechseln, erweitert Service)
    ↓
STORY-1003 (API Endpoints)  +  STORY-1004 (GET /api/zones)
    ↓                              ↓
STORY-1005 (Frontend API + Hooks) ←┘
    ↓
STORY-1006 (MultiRoom Live UI)
    ↓
    ├── STORY-1007 (Volume per Device)
    ├── STORY-1009 (Zone-Name editierbar)       ← nur Frontend
    ├── STORY-1011 (Drag&Drop / Master-Auswahl) ← nur Frontend
    ├── STORY-1012 (Now Playing in Zone-Card)   ← nur Frontend
    └── STORY-1013 (Quick-Add vom Dashboard)    ← nur Frontend
    ↓
STORY-1008 (Error Handling)
```

**Implementierungs-Reihenfolge:**
1. STORY-1001 → Backend Foundation
2. STORY-1002 → Business Logic
3. STORY-1003 + STORY-1004 → API Layer (parallel möglich)
4. STORY-1005 → Frontend-Backend Glue
5. STORY-1006 → MultiRoom Live UI (Mocks → echte Daten)
6. STORY-1009 + STORY-1011 + STORY-1012 → UI-Erweiterungen (parallel möglich)
7. STORY-1007 + STORY-1010 + STORY-1013 → Advanced Features (parallel möglich)
8. STORY-1008 → Polish & Hardening

---

## 6. Risiken & Mitigationen

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|---|---|---|---|
| Bose Library Zone-Methoden funktionieren nicht wie erwartet | Mittel | Hoch | STORY-1001 enthält ausführliche Integration-Tests; Fallback auf Direct HTTP |
| Silent Ignore bei ungültigen Member-IDs | Hoch | Mittel | Post-Operation Zone-Status-Check in STORY-1002 |
| Delay-Handling (1-3s built-in) verlangsamt UX | Hoch | Mittel | Optimistic Updates im Frontend, Background-Polling |
| Geräte in verschiedenen Subnetzen | Niedrig | Hoch | Validierung in STORY-1002, Hinweis in UI |
| AUX-Quelle in Zone | Mittel | Mittel | Source-Check + Warnung in STORY-1006 |

---

## 7. Nicht in Scope (explizit ausgeschlossen)

- **WebSocket Live-Updates** → Eigene Story/Phase für Device-WebSocket-Integration
- **Zone-Persistenz in DB** → Zone-Status kommt immer live vom Gerät
- ~~**Benannte Zonen**~~ → Jetzt in Scope (STORY-1009, localStorage-basiert)
- **Stereo-Pairing** → Separates Feature (`getGroup`/`setGroup`), nicht Multi-Room
- **Cross-Network Zonen** → Ausgeschlossen, Bose unterstützt nur Same-Subnet
- **Marge/Cloud-Emulator Zone-Support** → Marge-Routen bleiben Placeholder bis Cloud-Sync implementiert wird

---

## 8. Testabdeckung

| Bereich | Ziel | Methode |
|---|---|---|
| `client_adapter.py` Zone-Methods | ≥90% | Unit-Tests mit gemocktem `SoundTouchClient` |
| `zone_service.py` | ≥90% | Unit-Tests mit gemocktem Adapter + Repository |
| `zones/routes.py` | ≥90% | Integration-Tests mit TestClient |
| `api/zones.ts` + `useZones.ts` | ≥80% | Vitest mit MSW |
| `MultiRoom.tsx` | ≥80% | Vitest + React Testing Library |
| `useZoneNames.ts` | ≥80% | Vitest (localStorage mock) |
| `DeviceCard.tsx` Quick-Add | ≥80% | Vitest + React Testing Library |
| Drag & Drop / Master-Auswahl | ≥80% | Vitest (Desktop + Mobile) |
| E2E | Smoke-Test | Cypress: Zone erstellen → Status prüfen → Zone auflösen |
