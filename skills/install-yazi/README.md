# install-yazi

Writes an idempotent Homebrew script that installs or upgrades [yazi](https://github.com/sxyazi/yazi) and its preview dependencies on macOS.

The script also:

- shows hidden files
- binds `e` to maximize the preview pane
- previews Markdown with [glow](https://github.com/charmbracelet/glow)
- opens text files in [bat](https://github.com/sharkdp/bat)
- adds the `y` shell wrapper that the `yazi` skill reuses

Reruns change nothing.
