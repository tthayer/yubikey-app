# yubikey-app

A standalone [Light Phone III](https://www.thelightphone.com/) tool that reads
TOTP codes from a hardware security key's OATH applet over NFC or USB. It is a
thin, self-contained repo built against the upstream **Light SDK**, and it is
laid out to drop straight into Light's tool build / review pipeline.

## Layout

```
yubikey-app/
├── light-sdk/            # git submodule → upstream Light SDK (pinned commit)
├── tool/                 # the ONLY dev-owned module
│   ├── lighttool.toml    # tool id, label, version, declared permissions
│   ├── build.gradle.kts  # dependencies (project(":sdk:client") + light.sdk plugin)
│   └── src/main/kotlin/com/thelightphone/yubikey/*.kt
├── settings.gradle.kts   # grafts the submodule's SDK projects into this build
├── build.gradle.kts      # thin root: plugin classpath + ext build knobs
├── gradle.properties
└── gradlew, gradle/       # wrapper (matches the pinned SDK)
```

### Why a submodule?

Neither `:sdk:client` (the tool-facing SDK library) nor the
`com.thelightphone.light-sdk` Gradle plugin are published as artifacts — only
`sdk:ui` / `sdk:server` / `sdk:shared` and the keyboard go to GitHub Packages.
So the SDK must be consumed **as source**. This repo pins the upstream SDK as
the `light-sdk/` submodule and, in `settings.gradle.kts`, includes its
`:sdk:client` / `:sdk:ui` / `:sdk:shared` / `:lint-rules` projects as real
projects and its `plugin` as an included build. It also reuses the submodule's
own version catalog (`light-sdk/gradle/libs.versions.toml`) so this shell never
drifts from what the pinned SDK expects.

## Building locally

Requires JDK 17 and an Android SDK. Provide a GitHub token with `read:packages`
so the transitive keyboard dependency resolves — either in `local.properties`:

```properties
sdk.dir=/path/to/android-sdk
gpr.user=<your-github-user>
gpr.key=<token with read:packages>
```

or as env vars `GH_PACKAGES_USER` / `GH_PACKAGES_TOKEN`. Then:

```bash
./gradlew :tool:assembleDebug
# → tool/build/outputs/apk/debug/tool-debug.apk
```

The APK is signed with the shared Light dev keystore (from the submodule) for
local sideloading. Light's build service re-signs with its own key.

## Bumping the SDK

```bash
git -C light-sdk fetch origin
git -C light-sdk checkout <commit-or-tag>
git add light-sdk && git commit -m "bump light-sdk to <ref>"
```

> The tool currently pins `tthayer/light-sdk@feat/yubikey-app`, which carries
> the `LightSecurityKey` OATH capability the tool depends on. Repoint the
> submodule to `lightphone/light-sdk` once that capability lands upstream.

## Light's build & review pipeline

Light's containerized builder clones this repo and extracts **only**
`tool/build.gradle.kts`, `tool/lighttool.toml`, and `tool/src/main/**`, then
compiles them against its own pinned, sandboxed copy of the SDK (the submodule
and gradle shell here are ignored by the builder — they exist for local
builds). It generates `AndroidManifest.xml` from `lighttool.toml`, so this repo
intentionally contains no hand-written manifest and never sets `applicationId`,
`versionCode`, `versionName`, or `namespace`.
