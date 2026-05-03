import json
import os
import re
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
        
        # Crea la cartella per salvare gli SVG se non esiste
        self._cards_dir = "project-cards"
        os.makedirs(self._cards_dir, exist_ok=True)

    def fetch_github_data(self, full_repo_path: str) -> Dict[str, Any]:
        """Fetch project data from the GitHub API"""
        # RIMOSSO self._github_username perché full_repo_path ha già l'utente
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

    def generate_svg(self, full_repo_path: str, title: str, description: str, image_url: str) -> str:
        """Genera il codice SVG calcolando l'altezza dinamicamente"""
        from xml.sax.saxutils import escape
        import base64
        import urllib.request
        import os

        # 1. Dividiamo il testo in righe (senza limiti massimi!)
        description = description or "Nessuna descrizione fornita."
        lines = textwrap.wrap(description, width=35)
        
        # 2. CALCOLO ALTEZZA DINAMICA
        # L'immagine, il titolo e i margini occupano circa 240 pixel in altezza.
        # Ogni riga di testo aggiunge circa 18 pixel.
        # Aggiungiamo 20 pixel per il bordo inferiore.
        calculated_height = 240 + (len(lines) * 18) + 20
        
        # Manteniamo un'altezza minima di 320px per non avere card troppo "schiacciate" se il testo è corto
        total_height = max(320, calculated_height)
            
        tspan_elements = ""
        for line in lines:
            clean_line = escape(line)
            tspan_elements += f'<tspan x="18" dy="18">{clean_line}</tspan>\n    '

        clean_title = escape(title)

        # 3. Conversione Immagine in Base64 (come prima)
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

        # 4. Creazione SVG usando {total_height} invece di 320
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{self._card_width}" height="{total_height}" viewBox="0 0 {self._card_width} {total_height}">
  <defs>
    <clipPath id="image-clip">
      <path d="M 10 0 L {self._card_width - 10} 0 A 10 10 0 0 1 {self._card_width} 10 L {self._card_width} 180 L 0 180 L 0 10 A 10 10 0 0 1 10 0 Z" />
    </clipPath>
    <style>
      .title {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-weight: 600; font-size: 18px; fill: {self._title_color}; }}
      .desc {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-weight: 400; font-size: 13px; fill: {self._stats_color}; }}
    </style>
  </defs>
  
  <!-- Il rettangolo di sfondo si allunga con {total_height} -->
  <rect x="0" y="0" width="{self._card_width}" height="{total_height}" rx="{self._border_radius}" ry="{self._border_radius}" fill="{self._background_color}" stroke="#30363d" stroke-width="1.5"/>
  
  <image href="{b64_image_data}" x="0" y="0" width="{self._card_width}" height="180" preserveAspectRatio="xMidYMid slice" clip-path="url(#image-clip)"/>
  
  <line x1="0" y1="180" x2="{self._card_width}" y2="180" stroke="#30363d" stroke-width="1.5" />
  <text x="18" y="215" class="title">{clean_title}</text>
  <text x="18" y="235" class="desc">
    {tspan_elements}
  </text>
</svg>"""

        # Salva il file
        file_name = full_repo_path.split('/')[-1]
        file_path = os.path.join(self._cards_dir, f"{file_name}.svg")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
            
        return f"{self._cards_dir}/{file_name}.svg"

    def parse_projects(self) -> str:
        """Legge il config, scarica i dati, genera gli SVG e crea il Markdown"""
        if not os.path.exists(self._projects_config):
            raise RuntimeError(f"Config file non trovato: {self._projects_config}")
            
        with open(self._projects_config, "r", encoding="utf-8") as f:
            my_projects = json.load(f)

        my_projects = my_projects[: self._max_projects]
        markdown_outputs = []

        for proj in my_projects:
            full_repo_path = proj.get("full_repo_path")
            image_url = proj.get("image_url", "")
            custom_desc = proj.get("custom_description", "")
            
            github_data = self.fetch_github_data(full_repo_path)
            
            if not github_data:
                continue

            # Override della descrizione se fornita nel JSON
            final_description = custom_desc if custom_desc else github_data.get("description", "")
            project_title = github_data.get("name", full_repo_path)
            project_url = github_data.get("html_url", "#")

            # Genera il file SVG
            svg_path = self.generate_svg(full_repo_path, project_title, final_description, image_url)
            
            # Crea il link per il README
            if self._output_type == "html":
                escaped_title = project_title.replace('"', "&quot;")
                markdown_outputs.append(
                    f'<a href="{project_url}"><img src="{svg_path}" alt="{escaped_title}" title="{escaped_title}"></a>'
                )
            else:
                escaped_title = project_title.replace('"', '\\"')
                markdown_outputs.append(
                    f'[![{project_title}]({svg_path} "{escaped_title}")]({project_url})'
                )

        # Affianca le card con uno spazio tra loro
        return " ".join(markdown_outputs)


class FileUpdater:
    """Update the readme file"""

    @staticmethod
    def update(readme_path: str, comment_tag: str, replace_content: str):
        """Replace the text between the begin and end tags with the replace content"""
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
    parser.add_argument("--card-width", dest="card_width", default=250, type=int)
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

    print("Contenuto generato con successo:")
    print(video_content)

    if args.output_only == "false":
        FileUpdater.update(args.readme_path, args.comment_tag_name, video_content)
        print(f"File {args.readme_path} aggiornato!")