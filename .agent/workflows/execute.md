---
description: Execute a specific KickLang task from the tasks/ directory.
---

1. List available tasks in `tasks/` using `list_dir`.
2. Identify the target task ID (e.g., `T-YYYYMMDD-00X`).
3. Read the task content from the corresponding `.kl` file.
4. Gather any additional missing context for the specific objectives.
5. Create an `implementation_plan.md` in the current brain directory.
6. Request user approval via `notify_user`.
7. Upon approval, execute the changes using `replace_file_content` or `run_command`.
8. Verify changes and provide a `walkthrough.md`.
