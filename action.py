import json
import os
import re
import textwrap
import urllib.parse
import urllib.request
from argparse import ArgumentParser
from typing import Any, Dict, List

class ProjectParser:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, f"_{key}", value)
        self._cards_dir = "project-cards"
        os.makedirs(self._cards_dir, exist_ok=True)

    def fetch_github_data(self, full_repo_path: str) -> Dict[str, Any]:
        if not full_repo_path or "/" not in full_repo_path:
            return {} 
        
        url = f"https://api.github.com/repos/{full_repo_path}"
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", "GitHub Readme Project Cards Action")
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read())
        except Exception:
            return {}

    def get_base64_image(self, image_url: str) -> str:
        if not image_url: return ""
        try:
            req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                img_data = response.read()
                import base64
                b64_encoded = base64.b64encode(img_data).decode('utf-8')
                mime = "image/gif" if ".gif" in image_url.lower() else ("image/jpeg" if ".jpg" in image_url.lower() or ".jpeg" in image_url.lower() else "image/png")
                return f"data:{mime};base64,{b64_encoded}"
        except Exception as e:
            print(f"Errore download immagine: {e}")
            return ""

    def generate_svg(self, file_name: str, title: str, description: str, image_url: str, card_height: int) -> str:
        """Genera la card standard a colonna (Mantiene i font grandi perché viene rimpicciolita)"""
        from xml.sax.saxutils import escape
        title_lines = textwrap.wrap(title, width=23, break_long_words=True)
        title_tspan = ""
        for i, line in enumerate(title_lines):
            clean = re.sub(r'\*\*(.*?)\*\*', r'<tspan fill="#e5c07b">\1</tspan>', escape(line))
            title_tspan += f'<tspan x="26" dy="{"0" if i == 0 else "32"}">{clean}</tspan>\n'

        desc_lines = textwrap.wrap(description or "", width=38, break_long_words=True)
        desc_tspan = ""
        for i, line in enumerate(desc_lines):
            clean = re.sub(r'\*\*(.*?)\*\*', r'<tspan fill="#e5c07b">\1</tspan>', escape(line))
            desc_tspan += f'<tspan x="26" dy="{"0" if i == 0 else "26"}">{clean}</tspan>\n'

        title_start_y = 205
        title_bottom = title_start_y + ((len(title_lines) - 1) * 32) if title_lines else title_start_y
        desc_start_y = title_bottom + 30 
        b64_img = self.get_base64_image(image_url)

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{self._card_width}" height="{card_height}" viewBox="0 0 {self._card_width} {card_height}">
  <defs>
    <clipPath id="img-clip"><path d="M 10 0 L {self._card_width - 10} 0 A 10 10 0 0 1 {self._card_width} 10 L {self._card_width} 160 L 0 160 L 0 10 A 10 10 0 0 1 10 0 Z"/></clipPath>
    <style>
      .title {{ font-family: -apple-system, sans-serif; font-weight: 600; font-size: 28px; fill: {self._title_color}; }}
      .desc {{ font-family: -apple-system, sans-serif; font-weight: 400; font-size: 20px; fill: {self._stats_color}; }}
    </style>
  </defs>
  <rect width="{self._card_width}" height="{card_height}" rx="{self._border_radius}" fill="{self._background_color}" stroke="#30363d" stroke-width="1.5"/>
  <image href="{b64_img}" width="{self._card_width}" height="160" preserveAspectRatio="xMidYMid slice" clip-path="url(#img-clip)"/>
  <line y1="160" x2="{self._card_width}" y2="160" stroke="#30363d" stroke-width="1.5"/>
  <text x="26" y="{title_start_y}" class="title">{title_tspan}</text>
  <text x="26" y="{desc_start_y}" class="desc">{desc_tspan}</text>
</svg>"""
        file_path = os.path.join(self._cards_dir, f"{file_name}.svg")
        with open(file_path, "w", encoding="utf-8") as f: f.write(svg)
        return file_path

    def generate_wide_svg(self, file_name: str, title: str, description: str, image_url: str, card_height: int) -> str:
        """Genera la card Orizzontale con altezza e font proporzionati"""
        from xml.sax.saxutils import escape
        WIDE_WIDTH = 880
        IMG_WIDTH = 380

        # Wrap molto più largo (65) e Font più eleganti per la lettura 1:1
        title_lines = textwrap.wrap(title, width=40, break_long_words=True)
        title_tspan = ""
        for i, line in enumerate(title_lines):
            clean = re.sub(r'\*\*(.*?)\*\*', r'<tspan fill="#e5c07b">\1</tspan>', escape(line))
            title_tspan += f'<tspan x="{IMG_WIDTH + 30}" dy="{"0" if i == 0 else "28"}">{clean}</tspan>\n'

        desc_lines = textwrap.wrap(description or "", width=65, break_long_words=True)
        desc_tspan = ""
        for i, line in enumerate(desc_lines):
            clean = re.sub(r'\*\*(.*?)\*\*', r'<tspan fill="#e5c07b">\1</tspan>', escape(line))
            desc_tspan += f'<tspan x="{IMG_WIDTH + 30}" dy="{"0" if i == 0 else "22"}">{clean}</tspan>\n'

        title_start_y = 50
        title_bottom = title_start_y + ((len(title_lines) - 1) * 28) if title_lines else title_start_y
        desc_start_y = title_bottom + 25
        b64_img = self.get_base64_image(image_url)

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDE_WIDTH}" height="{card_height}" viewBox="0 0 {WIDE_WIDTH} {card_height}">
  <defs>
    <clipPath id="left-clip"><path d="M 10 0 L {IMG_WIDTH} 0 L {IMG_WIDTH} {card_height} L 10 {card_height} A 10 10 0 0 1 0 {card_height - 10} L 0 10 A 10 10 0 0 1 10 0 Z"/></clipPath>
    <style>
      .title {{ font-family: -apple-system, sans-serif; font-weight: 600; font-size: 24px; fill: {self._title_color}; }}
      .desc {{ font-family: -apple-system, sans-serif; font-weight: 400; font-size: 16px; fill: {self._stats_color}; }}
    </style>
  </defs>
  <rect width="{WIDE_WIDTH}" height="{card_height}" rx="{self._border_radius}" fill="{self._background_color}" stroke="#30363d" stroke-width="1.5"/>
  <image href="{b64_img}" width="{IMG_WIDTH}" height="{card_height}" preserveAspectRatio="xMidYMid slice" clip-path="url(#left-clip)"/>
  <line x1="{IMG_WIDTH}" y1="0" x2="{IMG_WIDTH}" y2="{card_height}" stroke="#30363d" stroke-width="1.5"/>
  <text y="{title_start_y}" class="title">{title_tspan}</text>
  <text y="{desc_start_y}" class="desc">{desc_tspan}</text>
</svg>"""
        file_path = os.path.join(self._cards_dir, f"{file_name}-wide.svg")
        with open(file_path, "w", encoding="utf-8") as f: f.write(svg)
        return file_path

    def parse_projects(self) -> str:
        with open(self._projects_config, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        final_markdown = ""

        for section in config_data:
            section_title = section.get("section_title", "")
            if section_title: final_markdown += f"{section_title}\n<br>\n\n"

            section_outputs = []
            processed_projects = []
            max_section_height = 340 
            
            for proj in section.get("projects", [])[: self._max_projects]:
                proj_id = proj.get("id") or proj.get("full_repo_path") or proj.get("repo_name")
                if not proj_id: continue

                github_data = self.fetch_github_data(proj_id)
                custom_title = proj.get("custom_title")
                
                if not github_data and not custom_title: continue

                final_description = proj.get("custom_description") or github_data.get("description", "")
                project_title = custom_title or github_data.get("name", proj_id.split('/')[-1])
                project_url = proj.get("custom_url") or github_data.get("html_url", "#")
                layout = proj.get("layout", "grid")

                # CALCOLO ALTEZZA DINAMICA SEPARATA
                if layout == "wide":
                    title_lines = textwrap.wrap(project_title, width=40, break_long_words=True)
                    desc_lines = textwrap.wrap(final_description or "", width=65, break_long_words=True)
                    title_bottom = 50 + ((len(title_lines) - 1) * 28) if title_lines else 50
                    desc_bottom = (title_bottom + 25) + ((len(desc_lines) - 1) * 22) if desc_lines else (title_bottom + 25)
                    calculated_h = max(240, desc_bottom + 30) # Minimo 240px per contenere bene la foto
                    
                    processed_projects.append({
                        "id": proj_id.replace("/", "-"),
                        "title": project_title, "desc": final_description, "url": project_url,
                        "image": proj.get("image_url", ""), "layout": layout, "height": calculated_h
                    })
                else:
                    title_lines = textwrap.wrap(project_title, width=23, break_long_words=True)
                    desc_lines = textwrap.wrap(final_description or "", width=38, break_long_words=True)
                    title_bottom = 205 + ((len(title_lines) - 1) * 32) if title_lines else 205
                    desc_bottom = (title_bottom + 30) + ((len(desc_lines) - 1) * 26) if desc_lines else (title_bottom + 30)
                    calculated_h = desc_bottom + 35 
                    if calculated_h > max_section_height: max_section_height = calculated_h
                    
                    processed_projects.append({
                        "id": proj_id.replace("/", "-"),
                        "title": project_title, "desc": final_description, "url": project_url,
                        "image": proj.get("image_url", ""), "layout": layout
                    })

            for p in processed_projects:
                escaped_title = p["title"].replace('"', "&quot;")
                if p["layout"] == "wide":
                    # Passiamo l'altezza calcolata appositamente per questa card
                    svg_path = self.generate_wide_svg(p["id"], p["title"], p["desc"], p["image"], p["height"])
                    section_outputs.append(f'<a href="{p["url"]}"><img src="{svg_path}" alt="{escaped_title}" title="{escaped_title}" width="100%"></a><br><br>')
                else:
                    svg_path = self.generate_svg(p["id"], p["title"], p["desc"], p["image"], max_section_height)
                    section_outputs.append(f'<a href="{p["url"]}"><img src="{svg_path}" alt="{escaped_title}" title="{escaped_title}" width="32%"></a>')

            final_markdown += " ".join(section_outputs) + "\n\n"

        return final_markdown.strip()

class FileUpdater:
    @staticmethod
    def update(readme_path: str, comment_tag: str, replace_content: str):
        begin_tag = f"<!-- BEGIN {comment_tag} -->"
        end_tag = f"<!-- END {comment_tag} -->"
        with open(readme_path, "r", encoding="utf-8") as f: readme = f.read()
        b_idx, e_idx = readme.find(begin_tag), readme.find(end_tag)
        if b_idx != -1 and e_idx != -1:
            readme = f"{readme[:b_idx + len(begin_tag)]}\n{replace_content}\n{readme[e_idx:]}"
            with open(readme_path, "w", encoding="utf-8") as f: f.write(readme)

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
    parser.add_argument("--output-only", dest="output_only", default="false", choices=("true", "false"))
    parser.add_argument("--readme-path", dest="readme_path", default="README.md")
    args = parser.parse_args()

    project_parser = ProjectParser(**vars(args))
    video_content = project_parser.parse_projects()

    if args.output_only == "false":
        FileUpdater.update(args.readme_path, args.comment_tag_name, video_content)
