#!/usr/bin/env python3
"""Point the Expo-prebuild release buildType at the nightly keystore."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def main() -> int:
    gradle_path = Path("apps/mobile/android/app/build.gradle")
    keystore = Path(os.environ["NIGHTLY_KEYSTORE"]).resolve()
    if not gradle_path.is_file():
        print(f"missing {gradle_path}", file=sys.stderr)
        return 1
    if not keystore.is_file():
        print(f"missing keystore {keystore}", file=sys.stderr)
        return 1

    text = gradle_path.read_text()
    if "nightlyRelease" in text:
        print("Release signing already configured")
        return 0

    marker = "signingConfigs {"
    if marker not in text:
        print("signingConfigs block not found", file=sys.stderr)
        return 1

    inject = (
        "signingConfigs {\n"
        "        nightlyRelease {\n"
        f'            storeFile file("{keystore}")\n'
        '            storePassword "android"\n'
        '            keyAlias "androiddebugkey"\n'
        '            keyPassword "android"\n'
        "        }\n"
    )
    text = text.replace(marker, inject, 1)

    release_match = re.search(r"release\s*\{", text)
    if release_match is None:
        print("release buildType not found", file=sys.stderr)
        return 1

    start = release_match.end()
    window = text[start : start + 500]
    if re.search(r"signingConfig\s+signingConfigs\.", window):
        text, count = re.subn(
            r"(release\s*\{[\s\S]*?)signingConfig\s+signingConfigs\.[A-Za-z0-9_]+",
            r"\1signingConfig signingConfigs.nightlyRelease",
            text,
            count=1,
        )
        if count != 1:
            print("failed to rewrite release signingConfig", file=sys.stderr)
            return 1
    else:
        text = text[:start] + "\n            signingConfig signingConfigs.nightlyRelease" + text[start:]

    gradle_path.write_text(text)
    print(f"Configured release signing with {keystore}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
