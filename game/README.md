# GLITCH//SHIFT — Reality Heist (Browser Build)

This folder is the browser-ready source for the Prompt & Play submission **Out Liars**.

## Local build/test

```bash
python -m pip install pygbag
python -m pygbag game
```

Then open the local URL printed by pygbag (normally `http://localhost:8000`).

## GitHub Pages

The repository includes a GitHub Actions workflow at `.github/workflows/deploy.yml` that builds the Pygame game with pygbag and deploys the generated `build/web` folder to GitHub Pages.

The browser build uses WebAssembly through pygbag, so judges can play without installing Python/Pygame.
