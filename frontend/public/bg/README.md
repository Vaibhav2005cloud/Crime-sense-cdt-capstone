# Background image

The Login and Home pages reference `/bg/command-center.jpg` as a hero background.
That file isn't bundled here — the build sandbox's network policy can reach Canva's
editor to *generate* the design, but can't download from Canva's export CDN
(`export-download.canva.com` isn't on the sandbox's allowed domain list), so I
couldn't pull the exported image into this zip automatically.

The pages work fine without it (there's a layered CSS gradient behind it that
looks good on its own), but if you want the actual Canva artwork:

1. Open the design here: https://www.canva.com/d/ZytooHaxFDGOLIR
2. Download it (Share → Download → PNG or JPG, 1920px wide recommended)
3. Save it as `command-center.jpg` in this folder (`frontend/public/bg/`)

That's it — both Login.jsx and Home.jsx already point at this path, so it'll show
up automatically once the file exists here. No code changes needed.
