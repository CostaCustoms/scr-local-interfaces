# PasswordPanel — password prompt

**Live when:** a password prompt is shown 📄; presumably when joining a private game from the Join list
(**UNCONFIRMED**). Never attached live.

## OUT (page → game) 📄

| Endpoint | Data | When |
|---|---|---|
| `ConfirmPassword` | `{password}` | Ok / Enter with a non-empty password |
| `Exit` | none | Escape, or the Cancel hotkey |

## IN (game → page) 📄

Only `GetStrings.response`.
