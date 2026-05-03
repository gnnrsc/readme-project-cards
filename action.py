import json
import os
import textwrap
import urllib.parse
import urllib.request
from argparse import ArgumentParser
from typing import Any, Dict, List

class ProjectParser:
    def __init__(
        self,
        *,
        github_username: str,
        projects_config: str,
        lang: str,
        max_projects: int,
        card_width: int,
        border_radius: int,
        background_color: str,
        title_color: str,
        stats_color: str,
        output_type: str,
    ):
        self._github_username = github_username
        self._projects_config = projects_config
        self._lang = lang
        self._max_projects = max_projects
        self._card_width = card_width
        self._border_radius = border_radius
        self._background_color = background_color
        self._title_color = title_color
        self._stats_color = stats_color
        self._output_type = output_type
        
        self._cards_dir = "project-cards"
        os.makedirs(self._cards_dir, exist_ok=True)

    def fetch_github_data(self, full_repo_path: str) -> Dict[str, Any]:
        url = f"https://api.github.com/repos/{full_repo_path}"
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", "GitHub Readme Project Cards Action")
        
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read())
        except Exception as e:
            print(f"Errore nel recupero dati per {full_repo_path}: {e}")
            return {}

    def generate_svg(self, full_repo_path: str, title: str, description: str, image_url: str, card_height: int) -> str:
        from xml.sax.saxutils import escape
        import base64

        # 1. FORMATTAZIONE TITOLO MULTIRIGA (Font 28px, max 23 caratteri)
        title_lines = textwrap.wrap(title, width=23, break_long_words=True)
        title_tspan_elements = ""
        for i, line in enumerate(title_lines):
            clean_line = escape(line)
            dy = "0" if i == 0 else "32" # Salto riga bilanciato
            title_tspan_elements += f'<tspan x="26" dy="{dy}">{clean_line}</tspan>\n    '

        # 2. FORMATTAZIONE DESCRIZIONE (Font 20px, max 38 caratteri)
        description = description or "Nessuna descrizione fornita."
        desc_lines = textwrap.wrap(description, width=38, break_long_words=True)
        desc_tspan_elements = ""
        for i, line in enumerate(desc_lines):
            clean_line = escape(line)
            dy = "0" if i == 0 else "26" # Salto riga bilanciato
            desc_tspan_elements += f'<tspan x="26" dy="{dy}">{clean_line}</tspan>\n    '

        # 3. CALCOLO POSIZIONE INIZIALE DESCRIZIONE
        title_start_y = 205
        title_bottom = title_start_y + ((len(title_lines) - 1) * 32) if title_lines else title_start_y
        desc_start_y = title_bottom + 30 

        # 4. IMMAGINE BASE64
        b64_image_data = ""
        if image_url:
            try:
                req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    img_data = response.read()
                    b64_encoded = base64.b64encode(img_data).decode('utf-8')
                    mime = "image/jpeg" if ".jpg" in image_url.lower() or ".jpeg" in image_url.lower() else "image/png"
                    b64_image_data = f"data:{mime};base64,{b64_encoded}"
            except Exception as e:
                print(f"Errore nel download dell'immagine {image_url}: {e}")

        # 5. CREAZIONE SVG (Font-size a 28px e 20px)
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{self._card_width}" height="{card_height}" viewBox="0 0 {self._card_width} {card_height}">
  <defs>
    <clipPath id="image-clip">
      <path d="M 10 0 L {self._card_width - 10} 0 A 10 10 0 0 1 {self._card_width} 10 L {self._card_width} 160 L 0 160 L 0 10 A 10 10 0 0 1 10 0 Z" />
    </clipPath>
    <style>
      .title {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-weight: 600; font-size: 28px; fill: {self._title_color}; }}
      .desc {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-weight: 400; font-size: 20px; fill: {self._stats_color}; }}
    </style>
  </defs>
  
  <rect x="0" y="0" width="{self._card_width}" height="{card_height}" rx="{self._border_radius}" ry="{self._border_radius}" fill="{self._background_color}" stroke="#30363d" stroke-width="1.5"/>
  <image href="{b64_image_data}" x="0" y="0" width="{self._card_width}" height="160" preserveAspectRatio="xMidYMid slice" clip-path="url(#image-clip)"/>
  <line x1="0" y1="160" x2="{self._card_width}" y2="160" stroke="#30363d" stroke-width="1.5" />
  
  <text x="26" y="{title_start_y}" class="title">
    {title_tspan_elements}
  </text>
  <text x="26" y="{desc_start_y}" class="desc">
    {desc_tspan_elements}
  </text>
</svg>"""

        file_name = full_repo_path.split('/')[-1]
        file_path = os.path.join(self._cards_dir, f"{file_name}.svg")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
            
        return f"{self._cards_dir}/{file_name}.svg"

    def parse_projects(self) -> str:
        if not os.path.exists(self._projects_config):
            raise RuntimeError(f"Config file non trovato: {self._projects_config}")
            
        with open(self._projects_config, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        final_markdown = ""

        for section in config_data:
            section_title = section.get("section_title", "")
            projects = section.get("projects", [])
            
            if section_title:
                final_markdown += f"{section_title}\n<br>\n\n"

            section_outputs = []
            processed_projects = []
            max_section_height = 340 # Altezza minima riequilibrata
            
            # --- PASS 1: Troviamo l'altezza MASSIMA ---
            for proj in projects[: self._max_projects]:
                full_repo_path = proj.get("full_repo_path") or proj.get("repo_name")
                if not full_repo_path:
                    continue

                github_data = self.fetch_github_data(full_repo_path)
                if not github_data:
                    continue

                custom_desc = proj.get("custom_description", "")
                final_description = custom_desc if custom_desc else github_data.get("description", "")
                project_title = github_data.get("name", full_repo_path.split('/')[-1])
                
                # Calcoli spazi aggiornati
                title_lines = textwrap.wrap(project_title, width=23, break_long_words=True)
                desc_lines = textwrap.wrap(final_description or "Nessuna descrizione fornita.", width=38, break_long_words=True)
                
                title_bottom = 205 + ((len(title_lines) - 1) * 32) if title_lines else 205
                desc_start_y = title_bottom + 30
                desc_bottom = desc_start_y + ((len(desc_lines) - 1) * 26) if desc_lines else desc_start_y
                calculated_h = desc_bottom + 35 
                
                if calculated_h > max_section_height:
                    max_section_height = calculated_h
                
                processed_projects.append({
                    "path": full_repo_path,
                    "title": project_title,
                    "desc": final_description,
                    "url": github_data.get("html_url", "#"),
                    "image": proj.get("image_url", "")
                })

            # --- PASS 2: Generiamo gli SVG ---
            for p in processed_projects:
                svg_path = self.generate_svg(p["path"], p["title"], p["desc"], p["image"], max_section_height)
                escaped_title = p["title"].replace('"', "&quot;")
                
                section_outputs.append(
                    f'<a href="{p["url"]}"><img src="{svg_path}" alt="{escaped_title}" title="{escaped_title}" width="32%"></a>'
                )

            final_markdown += " ".join(section_outputs) + "\n\n"

        return final_markdown.strip()


class FileUpdater:
    @staticmethod
    def update(readme_path: str, comment_tag: str, replace_content: str):
        begin_tag = f"<!-- BEGIN {comment_tag} -->"
        end_tag = f"<!-- END {comment_tag} -->"
        
        with open(readme_path, "r", encoding="utf-8") as readme_file:
            readme = readme_file.read()
            
        begin_index = readme.find(begin_tag)
        end_index = readme.find(end_tag)
        
        if begin_index == -1 or end_index == -1:
            raise RuntimeError(f"Could not find tags {begin_tag} and {end_tag} in {readme_path}")
            
        readme = f"{readme[:begin_index + len(begin_tag)]}\n{replace_content}\n{readme[end_index:]}"
        
        with open(readme_path, "w", encoding="utf-8") as readme_file:
            readme_file.write(readme)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--github-username", dest="github_username", required=True)
    parser.add_argument("--projects-config", dest="projects_config", default="projects-config.json")
    parser.add_argument("--lang", dest="lang", default="en")
    parser.add_argument("--comment-tag-name", dest="comment_tag_name", default="PROJECT-CARDS")
    parser.add_argument("--max-projects", dest="max_projects", default=6, type=int)
    parser.add_argument("--card-width", dest="card_width", default=400, type=int)
    parser.add_argument("--border-radius", dest="border_radius", default=10, type=int)
    parser.add_argument("--background-color", dest="background_color", default="#0d1117")
    parser.add_argument("--title-color", dest="title_color", default="#58a6ff")
    parser.add_argument("--stats-color", dest="stats_color", default="#8b949e")
    parser.add_argument("--theme-context-light", dest="theme_context_light", default="{}")
    parser.add_argument("--theme-context-dark", dest="theme_context_dark", default="{}")
    parser.add_argument("--max-title-lines", dest="max_title_lines", default=1, type=int)
    parser.add_argument("--readme-path", dest="readme_path", default="README.md")
    parser.add_argument("--output-only", dest="output_only", default="false", choices=("true", "false"))
    parser.add_argument("--output-type", dest="output_type", default="markdown", choices=("html", "markdown"))
    
    args = parser.parse_args()

    project_parser = ProjectParser(
        github_username=args.github_username,
        projects_config=args.projects_config,
        lang=args.lang,
        max_projects=args.max_projects,
        card_width=args.card_width,
        border_radius=args.border_radius,
        background_color=args.background_color,
        title_color=args.title_color,
        stats_color=args.stats_color,
        output_type=args.output_type,
    )

    video_content = project_parser.parse_projects()

    if args.output_only == "false":
        FileUpdater.update(args.readme_path, args.comment_tag_name, video_content)
