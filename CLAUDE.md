# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Kivy/KivyMD touchscreen dashboard (4 screens) for a Toyota Hilux 2008 datalogger
running on a Raspberry Pi 3 B. This repo currently contains the **UI skeleton**
plus a full **acquisition service** (OBD-II, IMU, 1-Wire sensors, TPMS →
MQTT → SQLite). The two halves communicate only through MQTT topics defined
in `telemetry.py` — they can be developed and run independently.

## Commands

```bash
# setup (repo also ships a venv/ + requirements.txt for the full acquisition stack)
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt        # or: pip install "kivy[base]" kivymd==1.1.1 for UI-only

# run the UI with fake/simulated data (default, no broker needed)
python main.py

# run the UI wired to the acquisition service via MQTT
HILUX_SOURCE=mqtt python main.py

# run the acquisition service (readers run in simulate mode per config.yaml until hardware is wired)
python -m acquisition.main

# convenience wrappers (used for systemd/kiosk autostart, see scripts/)
scripts/start_ui.sh
scripts/start_acquisition.sh

# tests (plain unittest, no pytest config in the repo)
python -m unittest discover -s tests
python -m unittest tests.test_theme                       # single file
python -m unittest tests.test_theme.TestPaletteFunction    # single test class
```

There is no lint/format config in the repo (no flake8/pyproject/ruff config found).

## Architecture

### UI side (root directory)

- `main.py` — `HiluxApp(MDApp)`. Owns the `night_mode` flag, the `c_*`
  `ListProperty` colors (bg/surface/text/text_dim/accent/ok/warn/alarm) that
  every canvas widget reads via `App.get_running_app()`, and the 5 Hz
  `Clock.schedule_interval` tick that copies `source.values` into the widget
  `ids` declared in `hilux.kv`. Picks the data source at startup based on
  `HILUX_SOURCE` env var: `DummyDataSource` (data.py) or `MqttDataSource`
  (mqtt_source.py) — both expose the same `values` dict / `update()` contract.
- `hilux.kv` — declarative layout for the `Root` screen: `MDTopAppBar` (global
  actions: night/day toggle, settings, shutdown) + `MDBottomNavigation` with
  4 tabs (engine / tilt / tires ). The `ValueCard` template
  (gauge card used on the engine screen) is also defined here.
- `widgets.py` — canvas-drawn widgets (chosen for Pi 3 performance over
  heavier KivyMD components): `Gauge` (circular arc gauge), `TiltIndicator`
  (roll/pitch silhouette), `TireDiagram` (4-tire pressure schematic). Each
  redraws on property change and colors itself via thresholds
  (`warn`/`alarm` for Gauge, `target`/`tol` for tires) against `app.c_*`.
- `theme.py` — `DAY`/`NIGHT` palettes (dicts of RGBA tuples) and
  `palette(night: bool)`. Night palette deliberately desaturates/dims
  ok/warn/alarm colors independently (not simple copies of day) to preserve
  the alarm > warn > ok severity ordering without glare in the dark —
  see `tests/test_theme.py` for the invariants this must hold
  (required keys, 0-1 RGBA range, alpha=1, night severity ordering, day
  colors unchanged).
- `data.py` — `DummyDataSource`: generates plausible oscillating values with
  no external dependencies, used for UI dev without a vehicle.
- `mqtt_source.py` — `MqttDataSource`: same `values`/`update()` contract,
  but values are pushed asynchronously by MQTT callbacks (`update()` is a
  no-op); keeps the last known value on NaN/disconnect.
- `telemetry.py` — the **single shared contract** between the UI and the
  acquisition service: broker host/port, topic prefix (`hilux/<key>`), the
  canonical list of telemetry `KEYS`, and `topic()`/`key_from_topic()`
  helpers. Both `mqtt_source.py` and every file under `acquisition/` import
  this module — changing a key name means updating it here.

### Acquisition side (`acquisition/`)

- `acquisition/main.py` — orchestrator: loads `config.yaml`, starts one
  daemon thread per enabled reader (`ObdReader`, `ImuReader`,
  `SensorsReader`, `TpmsReader`), handles SIGINT/SIGTERM for clean shutdown.
- Each `*_reader.py` is a `threading.Thread` that takes `(cfg, pub, stop_event)`,
  polls its source at `cfg["rate"]` Hz, and calls `pub.publish(key, value)`.
  Every reader has a `simulate: true` fallback in `config.yaml` (and
  `obd_reader.py` auto-falls-back to simulation if `python-OBD` or the
  ELM327 connection isn't available) so the service runs end-to-end without
  any hardware attached.
- `acquisition/publisher.py` — `Publisher`: thin paho-mqtt wrapper, publishes
  every value retained (`qos=0, retain=True`) so a UI connecting later
  immediately gets the last known value per topic; encodes `None`/NaN as the
  literal string `"nan"`.
- `acquisition/logger.py` — `DataLogger`: subscribes to all `hilux/#`
  topics and writes one wide row (one column per key) to SQLite per
  `logging.interval`, plus periodic purge past `logging.retention_days`.
  Note: not currently wired into `acquisition/main.py`'s thread list.
- `config.yaml` — single source of truth for enabling/disabling/simulating
  each reader, MQTT host/port, logging retention, and hardware-specific
  settings (OBD port/baudrate, diesel density/AFR for fuel estimation, IMU
  I2C address + roll/pitch calibration offsets, 1-Wire sensor IDs, TPMS
  target/tolerance pressure — the latter also drives the UI's tire alert
  colors).
- `tools/obd_scan.py` — standalone script, not part of the running service.

### Vehicle-specific notes (Hilux 2008 diesel, 1KD-FTV)

`acquisition/obd_reader.py` documents which OBD PIDs are actually reliable
on this engine: coolant temp is standard, boost is derived from
`INTAKE_PRESSURE` minus atmospheric, oil temp is rarely exposed over OBD
(expected to come from `sensors_reader.py`/DS18B20 instead), and there is no
reliable `FUEL_RATE` PID — instantaneous consumption falls back to a MAF ×
AFR estimate when needed.
