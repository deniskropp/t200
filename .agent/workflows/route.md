---
description: Transform research findings or simple requests into a formal KickLang task for delegation.
---

1. Scan the codebase and gather relevant context (file structure, dependencies, legacy code).
2. Examine existing tasks to determine the next available ID and appropriate recipient.
3. Create a new `.kl` file in `tasks/` using the formal KickLang template (front matter: id, title, author, recipient, status).
4. Detail the Context, Objectives, Constraints, and Resources in the task body.
5. Clean up any redundant files (e.g., the original markdown task or temporary notes).
6. Provide an `implementation_plan.md` for the routing process itself if complex.
7. Notify the user of the delegation.
