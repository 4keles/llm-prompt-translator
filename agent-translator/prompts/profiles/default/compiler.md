# JSON Compiler Constraints

Your final output MUST be a single raw JSON object.

1. DO NOT wrap the JSON in markdown blocks (e.g., no ```json ... ```).
2. DO NOT include any leading or trailing text (e.g., "Here is your translation:").
3. DO NOT escape characters incorrectly; ensure it is fully parseable by `json.loads()`.
4. Your JSON must strictly follow this exact schema:

{
  "compiled": "The final translated text",
  "domain": "inferred-domain-name",
  "mode": "translate",
  "terms_used": [
    {"src": "turkish", "picked": "english", "alts": ["other options"]}
  ],
  "unclear": []
}
