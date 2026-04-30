# Supported Platforms

The bundled checker currently probes:

## Domains

- `.com`
- `.io`
- `.ai`
- `.org`
- `.net`

Domains are checked via RDAP. Results are usually:

- `taken` when a domain record exists
- `available` when the RDAP endpoint returns not found
- `uncertain` when the registry blocks or rate-limits the probe

## Social platforms

- GitHub: `https://github.com/<handle>`
- X: `https://x.com/<handle>`
- Instagram: `https://www.instagram.com/<handle>/`
- TikTok: `https://www.tiktok.com/@<handle>`
- YouTube: `https://www.youtube.com/@<handle>`
- Bluesky: `https://bsky.app/profile/<handle>.bsky.social`
- Reddit: `https://www.reddit.com/user/<handle>/`
- LinkedIn company pages: `https://www.linkedin.com/company/<handle>/`

## Caveats

- X, Instagram, TikTok, and LinkedIn can serve login walls or anti-bot pages.
- A blocked probe should be reported as `uncertain`.
- Some platforms allow a handle to exist while the public page returns a soft
  error or redirect. Do not overclaim certainty.
- This tool does not check trademark databases.

