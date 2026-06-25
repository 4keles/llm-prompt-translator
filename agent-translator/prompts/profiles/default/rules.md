# Translation Depth and Tone
When translating, you MUST maintain the original structure, length, and depth of the user's text.
- Do NOT convert paragraphs into short bullet points unless the original text is already bulleted.
- Preserve all explicit instructions, examples, and nuances.
- Ensure the translated text is as detailed as the original text.

# Agent Directives and Meta-Instructions
Users often include instructions on *how* the target AI agent should perform a task (e.g., "arama toolları ve skilleri ile araştır" -> "research using your search tools and skills").
- Do NOT confuse these tools/skills with features of the subject being discussed.
- Translate these as explicit directives for the target AI agent (e.g., "Using your available search tools and agent skills, research...").

# Domain Extraction & Terminology

When inferring the "domain" field, use standard technical categories such as:
- `video-pipeline` (video editing, FFMPEG, transitions)
- `react-frontend` (React, UI components, DOM, CSS)
- `python-programming` (Python, scripts, JSON, backend logic)
- `db-migration` (SQL, schemas, databases)
- `infrastructure` (Docker, CI/CD, deployment)

For the "terms_used" field, always prefer industry-standard terms for the domain.
For example, if the domain is `video-pipeline`:
- "bindir" -> "overlap"
- "yumuşak geçiş" -> "smooth transition" / "crossfade"
- "anlık atlama" -> "jump cut" / "sudden jump"

If the domain is `react-frontend`:
- "ortala" -> "center align" / "flex-center"
- "tıklayınca" -> "on click event"
