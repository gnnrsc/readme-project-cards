# 🚀 Readme Project Cards Action

A sleek, dynamic, and fully customizable GitHub Action to generate beautiful SVG cards for your portfolio projects directly inside your profile `README.md`.

Transform your standard GitHub profile into a professional portfolio landing page in minutes.

![Example Banner](https://img.shields.io/badge/Maintained%3A-Yes-success?style=flat-square) ![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)

## ✨ Features

- **Automated SVG Generation**: Fetches project data via GitHub API and generates crisp, responsive SVG cards.
- **Multiple Layouts**: Support for classic **Grid Layout** (3 columns) and **Wide Layout** (perfect for highlighting a Master's Thesis or a main project).
- **Categorization**: Group your projects by topics (e.g., VR/AR, Machine Learning, Web Dev) with optional custom titles and elegant dividers.
- **Independent Links**: You are not forced to link only GitHub repos! Link Medium articles, Academic Papers, or external websites.
- **Keyword Highlighting**: Wrap words in `**` (e.g., `**React**`) in your JSON configuration to automatically highlight them in a sleek golden color.
- **Zero Maintenance**: Once set up, the Action runs automatically on a schedule to keep your stats and descriptions up to date.

---

## 🛠️ How to use it on your profile

Follow these 3 simple steps to integrate the **Readme Project Cards** into your `user/user` special repository.

### Step 1: Create the configuration file
In the root of your profile repository, create a file named `projects-config.json`. This file acts as the brain of your layout.

Here is a quick example of the structure:
```json
[
  {
    "add_divider": true,
    "group_title": "### 🎓 Highlighted Work",
    "section_title": "",
    "projects": [
      {
        "id": "my-main-project",
        "layout": "wide",
        "custom_title": "My Awesome Master's Thesis",
        "custom_url": "[https://link-to-your-thesis.com](https://link-to-your-thesis.com)",
        "image_url": "[https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/images/thesis-preview.jpg](https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/images/thesis-preview.jpg)", 
        "custom_description": "A high-fidelity project built with **Unreal Engine** and **C++**."
      }
    ]
  },
  {
    "add_divider": true,
    "group_title": "### 🚀 Portfolio",
    "section_title": "#### 📱 Software Engineering",
    "projects": [
      {
        "full_repo_path": "your-username/your-repo-name",
        "image_url": "[https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/images/project-preview.gif](https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/images/project-preview.gif)",
        "custom_description": "Full-stack app built with **React** and **Node.js**."
      }
    ]
  }
]
```

#### JSON Parameters Explained:
*   `add_divider` *(boolean)*: Adds a horizontal line (`---`) before the section.
*   `group_title` *(string)*: The main title for a block of categories.
*   `section_title` *(string)*: The subtitle for a specific category.
*   `layout` *(string)*: Use `"wide"` for a full-width card. Leave empty or use `"grid"` for standard 3-column cards.
*   `full_repo_path` *(string)*: The target GitHub repo (e.g., `octocat/hello-world`).
*   `id` *(string)*: Use this instead of `full_repo_path` if you are linking an external website (like a Thesis).
*   `image_url` *(string)*: Link to your preview image. **Tip:** Use `raw.githubusercontent.com` URLs for images hosted in your own repo to support `.gif` animations!
*   `custom_title` / `custom_description` / `custom_url`: Optional overrides. If omitted, the Action will automatically fetch them from the GitHub API.

### Step 2: Prepare your README.md
Add the following HTML comments exactly where you want the cards to be generated inside your `README.md`:
```html
<!-- BEGIN PROJECT-CARDS -->
<!-- END PROJECT-CARDS -->
```

### Step 3: Create the GitHub Action Workflow
Inside your profile repository, create a new file at `.github/workflows/update-cards.yml` and paste the following code:
```yaml
name: Update Project Cards
on:
  workflow_dispatch:
  schedule:
    - cron: "0 0 * * *" # Runs every day at midnight

jobs:
  update-cards:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Generate Cards
        uses: gnnrsc/readme-project-cards@main
        with:
          github_username: ${{ github.repository_owner }}
          projects_config: "projects-config.json"
          
      - name: Commit and Push changes
        uses: EndBug/add-and-commit@v9
        with:
          author_name: "GitHub Actions"
          message: "docs(readme): Update Project cards"
          add: "."
```

That's it! Go to your repo's **Actions** tab and trigger the workflow manually for the first time. Enjoy your new portfolio!

---

## 🎨 Advanced Customization

You can customize colors and sizing by passing additional `with` parameters in your `update-cards.yml` file:

| Parameter | Default | Description |
| --- | --- | --- |
| `card_width` | `400` | Width of the standard grid cards (in pixels). |
| `border_radius` | `10` | Corner roundness of the SVG cards. |
| `background_color` | `#0d1117` | Card background color (Default: GitHub Dark). |
| `title_color` | `#58a6ff` | Color for the project title. |
| `stats_color` | `#8b949e` | Color for the description text. |
| `comment_tag_name`| `PROJECT-CARDS` | Change this if you want to use a different HTML comment block. |

*(Example: `background_color: "#ffffff"` for light mode themes).*

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome!
Feel free to check the [issues page](https://github.com/gnnrsc/readme-project-cards/issues).

## 📝 License
This project is licensed under the MIT License.
