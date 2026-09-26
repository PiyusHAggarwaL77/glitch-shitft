# GLITCH//SHIFT — Reality Heist
## Out Liars · Piyush Aggarwal · Prompt & Play

### Browser version
The `game/` folder contains the Pygbag-compatible source. GitHub Actions builds it to WebAssembly and deploys it to GitHub Pages.

### How to publish
1. Create a **public GitHub repository** (GitHub Free requires a public repo for Pages).
2. Upload the contents of this folder to the repository root.
3. Commit/push to the `main` branch.
4. In **Settings → Pages**, set **Source** to **GitHub Actions**.
5. Open **Actions** and wait for **Build and Deploy GLITCH SHIFT** to finish.
6. The published URL will be `https://YOUR-USERNAME.github.io/REPOSITORY/`.

### Important
The browser build is not a normal Python page. Pygbag packages the Pygame game as WebAssembly so it can run in a modern browser.

### Controls
- Menu: W/S or ↑/↓, Enter, mouse
- Game: WASD / arrows, Space, R, P, Esc
- Boss: A/D or ←/→, Space, Esc
