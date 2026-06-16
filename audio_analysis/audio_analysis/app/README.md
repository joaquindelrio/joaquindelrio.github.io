# Audio Analysis

This repository contains an audio analysis app that processes local WAV folders and generates SPL reports and spectrograms.

## Two deployments

The same codebase can support two versions:

- Production on `quim.obsea.es`, which uses the full backend and the `web/` app.
- GitHub Pages on `joaquindelrio.github.io`, which serves the static root `index.html` only.

## GitHub Pages note

GitHub Pages can host only static content. The PHP endpoint in `web/api.php` and the Python processing pipeline cannot run on Pages.

The published Pages site therefore serves as a static project landing page. To run the full application, host the backend on a server that supports PHP and Python, then serve `web/index.html` from that environment.

## Local usage

Run the Python app from the repository root to process audio folders locally.