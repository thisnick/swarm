import os
from jinja2 import Environment, FileSystemLoader

def generate_swarm_cores():
  current_dir = os.path.dirname(__file__)
  templates_dir = os.path.join(current_dir, 'templates')
  env = Environment(loader=FileSystemLoader(templates_dir),
                    trim_blocks=True,
                    lstrip_blocks=True)

  for root, dirs, files in os.walk(templates_dir):
    for file_name in files:
      if not file_name.endswith('.jinja2'):
        continue

      # Compute full relative path inside the templates directory
      template_path = os.path.join(root, file_name)
      rel_path = os.path.relpath(template_path, templates_dir)

      for is_async in [False, True]:
        out_sync_folder = '_sync' if not is_async else '_async'
        out_rel_path = rel_path.replace('(sync)', out_sync_folder).replace('.jinja2', '')
        out_dir = os.path.join(current_dir, '..', os.path.dirname(out_rel_path))
        os.makedirs(out_dir, exist_ok=True)

        print(f"Generate output {file_name} from {rel_path} to {out_rel_path}")

        template = env.get_template(rel_path)
        rendered = template.render(is_async=is_async, class_name='Swarm')

        out_file = os.path.join(out_dir, os.path.basename(out_rel_path))
        with open(out_file, 'w', encoding='utf-8') as f:
          f.write(rendered)


if __name__ == '__main__':
  generate_swarm_cores()
