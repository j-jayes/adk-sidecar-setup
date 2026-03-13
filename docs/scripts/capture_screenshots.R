#!/usr/bin/env Rscript

# Capture frontend screenshots for the RevealJS deck.
# Usage: Rscript docs/scripts/capture_screenshots.R

if (!requireNamespace("webshot2", quietly = TRUE)) {
  stop("Package 'webshot2' is required. Install with install.packages('webshot2').")
}

out_dir <- "docs/assets/screenshots"
if (!dir.exists(out_dir)) {
  dir.create(out_dir, recursive = TRUE)
}

url <- "http://localhost:8501"

# Initial welcome state
webshot2::webshot(
  url = url,
  file = file.path(out_dir, "frontend-welcome.png"),
  vwidth = 1440,
  vheight = 900,
  delay = 2
)

# For the in-progress review state, upload test data manually in the browser,
# then rerun with a longer delay for dynamic updates if needed.
webshot2::webshot(
  url = url,
  file = file.path(out_dir, "frontend-analysis.png"),
  vwidth = 1440,
  vheight = 900,
  delay = 4
)

cat("Saved screenshots to", out_dir, "\n")
