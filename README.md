# VAIWA Cloud for Home Assistant

A community integration that reads the air quality measurements of your VAIWA SEN66 devices from your VAIWA Firebase account. One Home Assistant device per physical sensor, with entities for **CO₂**, **Temperature**, **Humidity**, **PM2.5**, **PM10**, **VOC index**, **NOx index**, and **Online**. **PM1.0 and PM4.0 are intentionally excluded.**

> **Experimental release**. This version has passed static Python and simulated Firebase API checks but has not yet been validated on a real Home Assistant installation. It is not an official Home Assistant Core integration.

## Install with HACS

1. Install [HACS](https://www.hacs.dev/) in your Home Assistant instance if it is not already installed.
2. In HACS open the menu **⋮ → Custom repositories**.
3. Enter `https://github.com/vaiwagroup/vaiwa-home-assistant`, choose the category **Integration**, and select **Add**.
4. Find **VAIWA Cloud** in HACS and choose **Download**.
5. Restart Home Assistant.
6. Open **Settings → Devices & services → Add integration → VAIWA Cloud**.
7. Sign in with your VAIWA **email and password**.

The Firebase Web API Key is preconfigured by the VAIWA developer. Users do not need to know or enter it. Never use a Google Cloud service-account JSON key.

## Data and automation

Each physical VAIWA sensor contributes the following Home Assistant entities:

| Entity | Unit |
| --- | --- |
| CO₂ | ppm |
| Temperature | °C |
| Humidity | % |
| PM2.5, PM10 | µg/m³ |
| VOC index, NOx index | index (unitless) |
| Online | ON / OFF |

The integration polls the Firebase Realtime Database approximately every **15 seconds** (`const.py`). It requires an internet connection. In Home Assistant you can use a Numeric state trigger, for example **VAIWA Room CO₂ rises above 1200 ppm**, with all automation configuration staying in Home Assistant.

## Security

- Authentication uses Firebase Identity Toolkit email/password sign-in. The password is **not stored** after login; the Home Assistant configuration stores a refresh token and the public Firebase Web API Key (for legacy entries only).
- Sensor reads use the ID token and your existing Firebase Realtime Database security rules.
- Keep Home Assistant backups protected, because they can include refresh tokens.
- No changes to ESP32 firmware or the VAIWA Flutter app are needed.

## Limitations

- Account sign-in via email and password only; MFA and other providers are not supported yet.
- Realtime Database is polled, not streamed; changes appear with a delay and need internet.
- Newly added sensors are automatically discovered during a refresh. Removed sensors become unavailable until cleaned up from the HA registry.
- Public use and HACS default-list inclusion need additional QA; see [Slovak setup guide](README_SK.md).

## Support

Report errors through [GitHub Issues](https://github.com/vaiwagroup/vaiwa-home-assistant/issues) and include your HA version and redacted logs. **Do not post API tokens, emails, sensor UIDs, or passwords.**

## Developer setup – Firebase Web API Key

Before publishing this repository, set `PUBLIC_FIREBASE_WEB_API_KEY` in `custom_components/vaiwa/const.py` to the Firebase **web** app `apiKey` for project `vaiwa-vaiwagroup`. This is a public client configuration value, **not** an admin secret or service-account JSON. Firebase Authentication and Realtime Database rules must continue to enforce user access.

No end user needs to enter this key. For a HACS release, commit the change to `main`, create a GitHub release/tag `v0.1.3`, and verify HACS offers the update. If this constant still has the placeholder value, users will see a configuration error rather than a confusing authentication error.
