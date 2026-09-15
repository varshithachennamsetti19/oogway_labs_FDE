"""
Artifact Skill: Visual & Code Artifact Synthesizer with XSS Security Sanitization
Generates standalone HTML/CSS visual frameworks, growth loop diagrams, or structured Markdown documents.
Enforces strict XSS sanitization and Content Security Policy (CSP) injection for sandboxed rendering.
"""

import logging
import re
import uuid
from typing import Dict, Any, Optional

from backend.app.agent.provider import get_llm_adapter
from backend.app.agent.skills.rag_skill import search_transcript_chunks

logger = logging.getLogger("lenny_growth.skills.artifact")


class ArtifactSkill:
    def __init__(self):
        self.llm = get_llm_adapter()

    async def execute(self, user_prompt: str, provider_override: str = None) -> Dict[str, Any]:
        logger.info(f"Executing Artifact Skill for: '{user_prompt}'")

        # 1. Check transcript context if relevant
        matches = await search_transcript_chunks(user_prompt, top_k=2)

        context_str = ""
        if matches:
            context_str = "\n".join([f"- {m[0].guest}: {m[0].content}" for m in matches])

        system_prompt = (
            "You are an expert Frontend Developer and Product Strategy Designer.\n"
            "Generate a complete, self-contained HTML/CSS visual artifact based on the user's request.\n\n"
            "REQUIREMENTS:\n"
            "1. Output ONLY a valid HTML snippet inside ````html ... ```` block.\n"
            "2. Include embedded inline `<style>` CSS. Use modern, beautiful glassmorphic styling (dark slate background `#0B0F19`, purple/indigo accents `#6366F1`, rounded corners, responsive grid layout, clean typography).\n"
            "3. Make the artifact visually striking (e.g. interactive framework cards, visual matrix, growth loop diagram, or checklist).\n"
            "4. DO NOT write malicious JavaScript or attempt parent DOM/storage access.\n"
            f"CONTENT CONTEXT:\n{context_str}"
        )

        user_instruction = f"Create an interactive visual HTML artifact for: {user_prompt}"

        llm_result = await self.llm.generate_response(system_prompt, user_instruction, provider_override)

        raw_output = llm_result["text"]

        # Extract & Sanitize HTML content
        extracted_html = self._extract_html(raw_output)
        sanitized_html = self.sanitize_html(extracted_html)

        title = f"Artifact: {user_prompt[:40]}"

        artifact_payload = {
            "id": str(uuid.uuid4()),
            "artifact_type": "html",
            "title": title,
            "content": sanitized_html
        }

        chat_answer = (
            f"I have generated an interactive visual artifact for **{user_prompt}**.\n\n"
            f"👉 **Click the Artifact card on the right to view it in the Sandboxed Viewer.**"
        )

        return {
            "answer": chat_answer,
            "citations": [],
            "artifact": artifact_payload,
            "provider_used": llm_result.get("provider_used"),
            "model_used": llm_result.get("model_used"),
            "skill_name": "artifact_skill"
        }

    def sanitize_html(self, html_content: str) -> str:
        """
        Sanitizes untrusted HTML payloads to neutralize XSS vulnerabilities:
        1. Strips dangerous <script> tags and event handlers (onload, onerror, onclick, etc.).
        2. Injects restrictive Content Security Policy (CSP) header into head.
        """
        if not html_content:
            return ""

        # 1. Strip script tags
        sanitized = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', html_content, flags=re.IGNORECASE)

        # 2. Strip inline event handlers (on*="...")
        sanitized = re.sub(r'\s+on[a-z]+\s*=\s*["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'\s+on[a-z]+\s*=\s*[^>\s]+', '', sanitized, flags=re.IGNORECASE)

        # 3. Strip javascript: URIs
        sanitized = re.sub(r'href\s*=\s*["\']\s*javascript:[^"\']*["\']', 'href="#"', sanitized, flags=re.IGNORECASE)

        # 4. Inject Restrictive CSP Meta Tag if not present
        csp_tag = (
            '<meta http-equiv="Content-Security-Policy" '
            'content="default-src \'none\'; style-src \'unsafe-inline\' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src data: https:;">'
        )

        if "<head>" in sanitized.lower():
            sanitized = re.sub(r'<head>', f'<head>\n  {csp_tag}', sanitized, flags=re.IGNORECASE, count=1)
        else:
            sanitized = f"<!DOCTYPE html>\n<html>\n<head>\n  {csp_tag}\n</head>\n<body>\n{sanitized}\n</body>\n</html>"

        return sanitized

    def _extract_html(self, text: str) -> str:
        """Extracts HTML code block from LLM output or wraps raw text in clean HTML container."""
        if "```html" in text:
            parts = text.split("```html")
            if len(parts) > 1:
                code = parts[1].split("```")[0]
                return code.strip()
        elif "```" in text:
            parts = text.split("```")
            if len(parts) > 1:
                return parts[1].strip()

        # Fallback wrapper
        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      font-family: system-ui, -apple-system, sans-serif;
      background: #0B0F19;
      color: #F9FAFB;
      padding: 2rem;
      margin: 0;
    }}
    .card {{
      background: rgba(30, 41, 59, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 12px;
      padding: 1.5rem;
      backdrop-filter: blur(12px);
    }}
    h2 {{ color: #8B5CF6; margin-top: 0; }}
  </style>
</head>
<body>
  <div class="card">
    {text}
  </div>
</body>
</html>"""
